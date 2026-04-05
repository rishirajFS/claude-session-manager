import tomllib
from pathlib import Path

DEFAULTS: dict = {
    "session": {
        "wake_time": "08:00",
        "kickoff_offset_h": 3,
        "session_hours": 5,
    },
    "queue": {
        "vault_path": "~/Documents/Obsidian",
        "queue_file": "active-projects.md",
    },
    "api": {
        "kickoff_message": "k",
    },
    "notifications": {
        "enabled": True,
        "warn_at_minutes": 30,
    },
}


def load_config(path: Path) -> dict:
    if not path.exists():
        return DEFAULTS

    with open(path, "rb") as f:
        user = tomllib.load(f)

    config = {section: dict(values) for section, values in DEFAULTS.items()}
    for section, values in user.items():
        if section in config and isinstance(config[section], dict):
            config[section] = {**config[section], **values}
        else:
            config[section] = values

    return config
