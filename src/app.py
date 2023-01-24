import json
from datetime import datetime

from pydantic.error_wrappers import ValidationError

import internals
import config
import models
import services.aws


def pre_process(contents: str) -> list[models.DataPlane]:
    internals.logger.debug("pre_process")
    results = []
    if not contents:
        return results
    for line in contents.splitlines():
        if line.startswith('#'):
            continue
        if not line.strip():
            continue
        asn, asn_text, ip_address, last_seen, category = line.split("  |  ")
        try:
            results.append(models.DataPlane(
                asn=None if asn.strip() == "NA" else int(asn.strip()),
                asn_text=None if asn_text.strip() == "NA" else asn_text.strip(),
                ip_address=ip_address.strip(),
                last_seen=datetime.fromisoformat(last_seen.strip()),
                category=category.strip(),
            ))
        except ValidationError as err:
            internals.logger.warning(err, exc_info=True)
            internals.logger.warning(f"""
            asn, asn_text, ip_address, last_seen, category
            {asn}, {asn_text}, {ip_address}, {last_seen}, {category}
            """)
    return results


def fetch(feed: models.FeedConfig) -> list[models.DataPlane]:
    internals.logger.debug("fetch")
    if feed.disabled:
        internals.logger.info(f"{feed.name} [magenta]disabled[/magenta]")
        return []
    file_path = internals.download_file(feed.url)
    if file_path.exists():
        return pre_process(file_path.read_text(encoding='utf8'))
    return []


def process(feed: models.FeedConfig, feed_items: list[models.DataPlane]) -> list[models.FeedStateItem]:
    state = models.FeedState(source='dataplane.org', feed_name=feed.name)
    # step 0, initial ONLY block
    if not state.load():
        internals.logger.warning("process step 0 initial ONLY")
        state.url = feed.url
        state.records = {}
        for item in feed_items:
            state.records[str(item.ip_address)] = models.FeedStateItem(
                key=str(item.ip_address),
                data=item,
                data_model='DataPlane',
                first_seen=item.last_seen,
                current=True,
                entrances=[],
                exits=[],
            )

    # step 1, exit any records that no longer appear in the feed
    internals.logger.info("process step 1 exit records")
    feed_index = set()
    for item in feed_items:
        feed_index.add(str(item.ip_address))

    for state_item in state.records.keys():
        if state_item not in feed_index:
            state.exit(state_item)

    # step 2, process new entrants
    entrants = []
    internals.logger.info("process step 2 process new entrants")
    for feed_item in feed_items:
        if item := state.records.get(str(feed_item.ip_address)):
            if item.current:
                continue
            item.current = True
            item.entrances.append(datetime.utcnow())
            state.records[item.key] = item
        else:
            item = models.FeedStateItem(
                key=str(feed_item.ip_address),
                data=feed_item,
                data_model='DataPlane',
                first_seen=datetime.utcnow(),
                current=True,
                entrances=[datetime.utcnow()],
                exits=[],
            )
            state.records[item.key] = item
        entrants.append(item)

    # step 3, persist state
    internals.logger.info("process step 3 persist state")
    state.last_checked = datetime.utcnow()
    state.save()
    return entrants


def handler(event, context):
    start = datetime.utcnow()
    for feed in config.feeds:
        results = fetch(feed)
        if not results:
            continue
        # services.aws.delete_s3(f"{internals.APP_ENV}/feeds/dataplane.org/{feed.name}/state.json")
        services.aws.store_s3(
            path_key=f"{internals.APP_ENV}/feeds/dataplane.org/{feed.name}/{start.strftime('%Y%m%d%H')}.json",
            value=json.dumps(results, default=str)
        )
        for state_item in process(feed, results):
            services.aws.store_sqs(
                queue_name=f'{internals.APP_ENV.lower()}-early-warning-service',
                message_body=json.dumps({**feed.dict(), **state_item.dict()}, cls=internals.JSONEncoder),
                deduplicate=False,
            )
        internals.logger.debug(f"done {feed.name}")
