import models

feeds: list[models.FeedConfig] = [
    models.FeedConfig(
        name="sshclient",
        description="IP addresses that has been seen initiating an SSH connection to a remote host. This report lists hosts that are suspicious of more than just port scanning. These hosts may be SSH server cataloging or conducting authentication attack attempts",
        url="https://dataplane.org/sshclient.txt",
        alert_title="SSH Port Scanning and Bruteforcing Authentication",
        source="dataplane.org",
        abuse_email="info@dataplane.org",
        disabled=False
    ),
    models.FeedConfig(
        name="sshpwauth",
        description="IP addresses that has been seen attempting to remotely login to a host using SSH password authentication. This report lists hosts that are highly suspicious and are likely conducting malicious SSH password authentication attacks",
        url="https://dataplane.org/sshpwauth.txt",
        alert_title="SSH dictionary attacks",
        source="dataplane.org",
        abuse_email="info@dataplane.org",
        disabled=False
    ),
    models.FeedConfig(
        name="dnsrd",
        description="IP addresses that have been identified as sending recursive DNS queries to a remote host. This report lists addresses that may be cataloging open DNS resolvers or evaluating cache entries",
        url="https://dataplane.org/dnsrd.txt",
        alert_title="Recursive DNS query cataloging",
        source="dataplane.org",
        abuse_email="info@dataplane.org",
        disabled=False
    ),
    models.FeedConfig(
        name="vncrfb",
        description="IP addresses that have been seen initiating a VNC remote frame buffer {RFB) session to a remote host. This report lists hosts that are suspicious of more than just port scanning. These hosts may be VNC server cataloging or conducting various forms of remote access abuse",
        url="https://dataplane.org/vncrfb.txt",
        alert_title="Suspicious VNC remote frame buffer (RFB) sessions",
        source="dataplane.org",
        abuse_email="info@dataplane.org",
        disabled=False
    ),
]
