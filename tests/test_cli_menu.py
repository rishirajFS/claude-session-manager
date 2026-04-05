from datetime import datetime, timedelta

import pytest

from cli_menu import format_duration, get_status

BASE_CONFIG = {
    "session": {"wake_time": "08:00", "kickoff_offset_h": 3, "session_hours": 5},
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
