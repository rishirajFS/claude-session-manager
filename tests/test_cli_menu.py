from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli_menu import (
    _handle_option_1,
    _handle_option_4,
    _handle_option_5,
    format_duration,
    get_queue_count,
    get_status,
    manual_start,
    queue_file_path,
)

BASE_CONFIG = {
    "session": {"wake_time": "08:00", "kickoff_offset_h": 3, "session_hours": 5},
    "queue": {"vault_path": "~/Documents/Obsidian", "queue_file": "active-projects.md"},
}


def test_format_duration_hours_and_minutes():
    assert format_duration(timedelta(hours=4, minutes=58)) == "4h 58m"


def test_format_duration_minutes_only():
    assert format_duration(timedelta(minutes=45)) == "45m"


def test_format_duration_expired():
    assert format_duration(timedelta(seconds=-1)) == "expired"


def test_get_status_inactive_when_no_state():
    assert get_status(BASE_CONFIG, {})["active"] is False


def test_get_status_inactive_when_expired():
    start = datetime.now() - timedelta(hours=6)
    state = {"session_active": True, "session_start": start.isoformat()}
    assert get_status(BASE_CONFIG, state)["active"] is False


def test_get_status_active_for_live_session():
    start = datetime.now() - timedelta(hours=1)
    state = {"session_active": True, "session_start": start.isoformat()}
    status = get_status(BASE_CONFIG, state)
    assert status["active"] is True
    assert "remaining" in status
    assert "resets" in status


def test_option_1_sets_user_active():
    state = {"session_active": True, "session_start": datetime.now().isoformat()}
    saved = {}

    with patch("cli_menu.save_state", side_effect=lambda s: saved.update(s)):
        _handle_option_1(state)

    assert saved["user_active"] is True
    assert saved.get("skipped") is False


def test_option_4_sets_skipped():
    state = {"session_active": True, "session_start": datetime.now().isoformat()}
    saved = {}

    with patch("cli_menu.save_state", side_effect=lambda s: saved.update(s)):
        _handle_option_4(state)

    assert saved["skipped"] is True
    assert saved.get("user_active") is False


def test_option_5_sets_session_active(tmp_path):
    config = {
        **BASE_CONFIG,
        "queue": {"vault_path": str(tmp_path), "queue_file": "active-projects.md"},
    }
    saved = {}
    with patch("cli_menu.save_state", side_effect=lambda s: saved.update(s)):
        _handle_option_5(config)
    assert saved["session_active"] is True
    assert saved["user_active"] is False
    assert saved["skipped"] is False


def test_manual_start_sets_clock(tmp_path):
    config = {
        **BASE_CONFIG,
        "queue": {"vault_path": str(tmp_path), "queue_file": "active-projects.md"},
    }
    saved = {}
    with patch("cli_menu.save_state", side_effect=lambda s: saved.update(s)):
        manual_start(config)
    assert saved["session_active"] is True
    start = datetime.fromisoformat(saved["session_start"])
    assert abs((start - datetime.now()).total_seconds()) < 2


def test_get_queue_count_returns_zero_when_file_missing(tmp_path):
    config = {
        **BASE_CONFIG,
        "queue": {"vault_path": str(tmp_path), "queue_file": "missing.md"},
    }
    assert get_queue_count(config) == 0


def test_get_queue_count_counts_active_projects(tmp_path):
    queue = tmp_path / "active-projects.md"
    queue.write_text(
        "## active-projects\n\n"
        "### 1. Project A\nstatus: in-progress\n\n"
        "### 2. Project B\nstatus: in-progress\n"
    )
    config = {**BASE_CONFIG, "queue": {"vault_path": str(tmp_path), "queue_file": "active-projects.md"}}
    assert get_queue_count(config) == 2
