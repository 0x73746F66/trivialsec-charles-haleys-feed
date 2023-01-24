import models

feeds: list[models.FeedConfig] = [
    models.FeedConfig(
        name="ssh-dictionary-attacks",
        description="IP addresses that has been seen initiating an SSH connection to a remote host. This report lists hosts that are suspicious of more than just port scanning. These hosts may be SSH server cataloging or conducting authentication attack attempts",
        url="http://charles.the-haleys.org/ssh_dico_attack_with_timestamps.php?days=1",
        alert_title="SSH Port Scanning and Bruteforcing Authentication",
        source="charles.the-haleys.org",
        abuse_email="contact@frogfishtech.com",
        disabled=False
    ),
]
