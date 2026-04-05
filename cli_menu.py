import sys
from datetime import datetime, timedelta
from pathlib import Path

from config_loader import load_config
from state import load_state, save_state

CONFIG_FILE = Path(__file__).parent / "config.toml"


def format_duration(td: timedelta) -> str:
    total = int(td.total_seconds())
    if total <= 0:
        return "expired"
    h, rem = divmod(total, 3600)
    m = rem // 60
    return f"{h}h {m:02d}m" if h else f"{m}m"


def get_status(config: dict, state: dict) -> dict:
    if state.get("session_active") and state.get("session_start"):
        start = datetime.fromisoformat(state["session_start"])
        end = start + timedelta(hours=config["session"]["session_hours"])
        remaining = end - datetime.now()
        if remaining.total_seconds() > 0:
            return {
                "active": True,
                "started": start.strftime("%I:%M %p"),
                "resets": end.strftime("%I:%M %p"),
                "remaining": format_duration(remaining),
            }
    return {"active": False}


def manual_start(config: dict) -> None:
    """Record a manually started session (user started Claude outside the daemon)."""
    now = datetime.now()
    end = now + timedelta(hours=config["session"]["session_hours"])
    save_state({
        "session_start": now.isoformat(),
        "session_active": True,
        "warned": False,
    })
    print(f"Session clock set. Resets at {end.strftime('%I:%M %p')}.")


def show_status(config: dict, state: dict) -> None:
    status = get_status(config, state)
    print("\n  Claude Session Manager")
    print("  " + "-" * 32)
    if status["active"]:
        print(f"  Session:   ACTIVE")
        print(f"  Started:   {status['started']}")
        print(f"  Resets:    {status['resets']}")
        print(f"  Remaining: {status['remaining']}")
    else:
        wake_h, wake_m = map(int, config["session"]["wake_time"].split(":"))
        offset_h = config["session"]["kickoff_offset_h"]
        now = datetime.now()
        next_fire = now.replace(
            hour=wake_h, minute=wake_m, second=0, microsecond=0
        ) - timedelta(hours=offset_h)
        if next_fire <= now:
            next_fire += timedelta(days=1)
        label = "tomorrow" if next_fire.date() > now.date() else "today"
        print(f"  Session:   INACTIVE")
        print(f"  Next kickoff: {next_fire.strftime('%I:%M %p')} ({label})")
    print()


def main() -> None:
    config = load_config(CONFIG_FILE)

    if len(sys.argv) > 1 and sys.argv[1] == "--manual-start":
        manual_start(config)
        return

    state = load_state()
    show_status(config, state)


if __name__ == "__main__":
    main()
