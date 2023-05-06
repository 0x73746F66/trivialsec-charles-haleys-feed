import json
from datetime import datetime, timezone
from uuid import uuid5
from typing import Union
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network

import validators
from lumigo_tracer import lumigo_tracer

import internals
import config
import models
import services.aws


def extract_ip_address(line: str) -> Union[IPv4Address, IPv4Network, IPv6Address, IPv6Network, None]:
    if line.startswith('#') or line.startswith('//') or not line:
        return None
    if ' : ' in line:
        ip_line = line.split(' : ')[1]
        ip_address, *_ = ip_line.split(' # ')
    else:
        ip_address, *_ = line.split(' # ')
    ip_address = ip_address.strip()
    if validators.ipv4_cidr(ip_address) is True:
        return IPv4Network(ip_address)
    if validators.ipv4(ip_address) is True:
        return IPv4Address(ip_address)
    if validators.ipv6_cidr(ip_address) is True:
        return IPv6Network(ip_address)
    return IPv6Network(ip_address) if validators.ipv6(ip_address) is True else None


def extract_date(contents: str, ip_address: Union[IPv4Address, IPv4Network, IPv6Address, IPv6Network]) -> Union[datetime, None]:
    for line in contents.splitlines():
        if line.startswith('#') or line.startswith('//') or not line:
            continue
        if ' : ' in line:
            ip_line = line.split(' : ')[1]
            line_ip, date_line = ip_line.split(' # ')
        else:
            line_ip, date_line = line.split(' # ')

        if str(ip_address) != line_ip.strip():
            continue

        timestamp, *_ = date_line.split()
        timestamp = int(timestamp.strip())
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return None


def compare_contents(old_contents: str, new_contents: str):
    old_index = set()
    for line in old_contents.splitlines():
        if ip_address := extract_ip_address(line):
            old_index.add(ip_address)

    for line in new_contents.splitlines():
        ip_address = extract_ip_address(line)
        if ip_address and ip_address not in old_index:
            yield ip_address


def main(event):
    if event.get("source"):
        internals.trace_tag({
            "source": event["source"],
            "resources": ",".join([
                e.split(":")[-1] for e in event["resources"]
            ]),
        })
    instance_date = datetime.now(timezone.utc).strftime('%Y%m%d%H')
    results = 0
    for feed in config.feeds:
        if feed.disabled:
            internals.logger.info(f"{feed.name} [magenta]disabled[/magenta]")
            continue
        object_prefix = f"{internals.APP_ENV}/feeds/{feed.source}/{feed.name}/"
        # services.aws.delete_s3(f"{object_prefix}/latest.txt")
        last_contents = services.aws.get_s3(path_key=f"{object_prefix}latest.txt")
        file_path = internals.download_file(feed.url)
        if not file_path.exists():
            internals.logger.warning(f"Failed to retrieve {feed.name}")
            continue
        contents = file_path.read_text(encoding='utf8')
        if not contents:
            internals.logger.warning(f"{feed.name} [magenta]no data[/magenta]")
            continue
        services.aws.store_s3(
            path_key=f"{object_prefix}{instance_date}.txt",
            value=contents
        )
        if not last_contents:
            last_contents = ''
            # split contents in half, all are being processed the first time
            contents = "\n".join(contents.splitlines()[:round(len(contents.splitlines())/2)])
            internals.logger.info(f"halving to {round(len(contents.splitlines())/2)} lines -> {feed.name}")
        queued = 0
        for ip_address in compare_contents(last_contents, contents):
            dates = []
            if old_date := extract_date(last_contents, ip_address):
                dates.append(old_date)
            if new_date := extract_date(contents, ip_address):
                dates.append(new_date)
            if not dates:
                dates.append(datetime.now(timezone.utc).replace(microsecond=0))
            data = models.CharlesHaley(
                address_id=uuid5(internals.CH_NAMESPACE, str(ip_address)),
                ip_address=ip_address,
                feed_name=feed.name,
                feed_url=feed.url,
                first_seen=min(dates),
                last_seen=max(dates),
            )
            if not data.exists() and data.save() and services.aws.store_sqs(
                queue_name=f'{internals.APP_ENV.lower()}-early-warning-service',
                message_body=json.dumps({**data.dict(), **{'source': feed.source}}, cls=internals.JSONEncoder),
                deduplicate=False,
            ):
                queued += 1
                results += 1
        internals.logger.info(f"{queued} queued records -> {feed.name}")
        services.aws.store_s3(
            path_key=f"{object_prefix}latest.txt",
            value=contents
        )
    internals.logger.info(f"{results} processed records")

@lumigo_tracer(
    token=services.aws.get_ssm(f'/{internals.APP_ENV}/{internals.APP_NAME}/Lumigo/token', WithDecryption=True),
    should_report=internals.APP_ENV == "Prod",
    skip_collecting_http_body=True,
    verbose=internals.APP_ENV != "Prod"
)
def handler(event, context):
    try:
        main(event)
    except Exception as err:
        raise internals.UnspecifiedError from err
