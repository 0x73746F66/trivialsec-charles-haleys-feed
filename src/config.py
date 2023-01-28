import models

feeds: list[models.FeedConfig] = [
    models.FeedConfig(
        name="ssh-dictionary-attacks",
        url="http://charles.the-haleys.org/ssh_dico_attack_with_timestamps.php?days=1",
        source="charles.the-haleys.org",
        disabled=False
    ),
]
