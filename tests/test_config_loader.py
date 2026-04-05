import tempfile
from pathlib import Path

import pytest

from config_loader import DEFAULTS, load_config


def test_returns_defaults_when_no_file():
    config = load_config(Path("/nonexistent/config.toml"))
    assert config == DEFAULTS


def test_loads_and_merges_config(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text('[session]\nwake_time = "09:00"\n')
    config = load_config(toml)
    assert config["session"]["wake_time"] == "09:00"
    assert config["session"]["kickoff_offset_h"] == DEFAULTS["session"]["kickoff_offset_h"]


def test_user_config_overrides_defaults(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text('[notifications]\nenabled = false\n')
    config = load_config(toml)
    assert config["notifications"]["enabled"] is False
    assert config["notifications"]["warn_at_minutes"] == DEFAULTS["notifications"]["warn_at_minutes"]


def test_unknown_section_preserved(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text('[custom]\nfoo = "bar"\n')
    config = load_config(toml)
    assert config["custom"]["foo"] == "bar"
