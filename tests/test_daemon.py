from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from daemon import next_scheduled_kickoff, session_end_time

BASE_CONFIG = {
    "session": {"wake_time": "08:00", "kickoff_offset_h": 3, "session_hours": 5},
    "notifications": {"enabled": False, "warn_at_minutes": 30},
    "api": {"kickoff_message": "k"},
}


def test_next_scheduled_kickoff_returns_future_time():
    result = next_scheduled_kickoff(BASE_CONFIG)
    assert result > datetime.now()


def test_next_scheduled_kickoff_is_3h_before_wake():
    result = next_scheduled_kickoff(BASE_CONFIG)
    # Kickoff should be at 05:00 (08:00 - 3h)
    assert result.hour == 5
    assert result.minute == 0


def test_session_end_time_returns_none_when_no_state():
    assert session_end_time(BASE_CONFIG, {}) is None


def test_session_end_time_returns_none_when_inactive():
    state = {"session_active": False, "session_start": datetime.now().isoformat()}
    assert session_end_time(BASE_CONFIG, state) is None


def test_session_end_time_returns_end_for_active_session():
    start = datetime.now() - timedelta(hours=1)
    state = {"session_active": True, "session_start": start.isoformat()}
    end = session_end_time(BASE_CONFIG, state)
    assert end is not None
    expected = start + timedelta(hours=5)
    assert abs((end - expected).total_seconds()) < 1


def test_session_end_time_returns_none_for_expired_session():
    start = datetime.now() - timedelta(hours=6)
    state = {"session_active": True, "session_start": start.isoformat()}
    assert session_end_time(BASE_CONFIG, state) is None
