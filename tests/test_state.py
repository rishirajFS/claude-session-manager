import json
from pathlib import Path
from unittest.mock import patch

import pytest

import state as state_module
from state import load_state, save_state


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    state_dir = tmp_path / ".claude-session"
    state_file = state_dir / "state.json"
    monkeypatch.setattr(state_module, "STATE_DIR", state_dir)
    monkeypatch.setattr(state_module, "STATE_FILE", state_file)
    return state_file


def test_load_state_returns_empty_dict_when_no_file():
    assert load_state() == {}


def test_save_and_load_roundtrip():
    data = {"session_active": True, "session_start": "2026-04-05T05:00:00"}
    save_state(data)
    assert load_state() == data


def test_save_creates_directory(isolated_state):
    save_state({"foo": "bar"})
    assert isolated_state.exists()


def test_save_overwrites_existing(isolated_state):
    save_state({"key": "v1"})
    save_state({"key": "v2"})
    assert load_state()["key"] == "v2"
