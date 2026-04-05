import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from config_loader import load_config
from notifier import notify
from state import load_state, save_state

CONFIG_FILE = Path(__file__).parent / "config.toml"


def fire_kickoff(config: dict) -> bool:
    message = config["api"]["kickoff_message"]
    result = subprocess.run(
        ["claude", "-p", message],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        print(f"[ERROR] Kickoff failed: {result.stderr.strip()}", file=sys.stderr)
        return False

    session_start = datetime.now()
    reset_time = session_start + timedelta(hours=config["session"]["session_hours"])
    save_state({
        "session_start": session_start.isoformat(),
        "session_active": True,
        "warned": False,
    })

    if config["notifications"]["enabled"]:
        notify(
            title="Claude Session Manager",
            message=f"Session started. Resets at {reset_time.strftime('%I:%M %p')}.",
        )

    print(
        f"[{session_start.strftime('%H:%M:%S')}] Kickoff sent. "
        f"Session resets at {reset_time.strftime('%I:%M %p')}."
    )
    return True


def next_scheduled_kickoff(config: dict) -> datetime:
    """Return today's scheduled kickoff time, or tomorrow's if already past."""
    wake_h, wake_m = map(int, config["session"]["wake_time"].split(":"))
    offset_h = config["session"]["kickoff_offset_h"]
    now = datetime.now()
    scheduled = now.replace(
        hour=wake_h, minute=wake_m, second=0, microsecond=0
    ) - timedelta(hours=offset_h)
    if scheduled <= now:
        scheduled += timedelta(days=1)
    return scheduled


def session_end_time(config: dict, state: dict) -> datetime | None:
    """Return when the active session expires, or None if no active session."""
    if not state.get("session_active") or not state.get("session_start"):
        return None
    start = datetime.fromisoformat(state["session_start"])
    end = start + timedelta(hours=config["session"]["session_hours"])
    return end if end > datetime.now() else None


def check_low_session_warning(config: dict, state: dict) -> None:
    if state.get("warned"):
        return
    end = session_end_time(config, state)
    if end is None:
        return
    remaining = end - datetime.now()
    threshold = timedelta(minutes=config["notifications"]["warn_at_minutes"])
    if remaining <= threshold:
        mins = int(remaining.total_seconds() / 60)
        if config["notifications"]["enabled"]:
            notify(
                title="Claude Session Manager",
                message=f"{mins}m remaining in this session.",
            )
        save_state({**state, "warned": True})
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: {mins} minutes remaining.")


def run_daemon(config: dict) -> None:
    print("Claude Session Manager started. Press Ctrl+C to stop.")

    while True:
        state = load_state()
        end = session_end_time(config, state)

        if end is not None:
            # Active session — monitor for expiry and low-time warning
            check_low_session_warning(config, state)
            time.sleep(60)
            continue

        # Session is expired or never started
        if state.get("session_active"):
            # Mark expired so next logic fires a new kickoff
            state = {**state, "session_active": False, "warned": False}
            save_state(state)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Session expired. Firing next kickoff.")
            fire_kickoff(config)
            time.sleep(60)
            continue

        # No active session — wait for the next scheduled kickoff
        next_fire = next_scheduled_kickoff(config)
        wait = (next_fire - datetime.now()).total_seconds()
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] No active session. "
            f"Next kickoff at {next_fire.strftime('%I:%M %p')} ({int(wait / 60)}m away)."
        )
        time.sleep(min(wait, 60))


if __name__ == "__main__":
    run_daemon(load_config(CONFIG_FILE))
