import os
import subprocess
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


def queue_file_path(config: dict) -> Path:
    vault = Path(config["queue"]["vault_path"]).expanduser()
    return vault / config["queue"]["queue_file"]


def get_queue_count(config: dict) -> int:
    path = queue_file_path(config)
    if not path.exists():
        return 0
    text = path.read_text()
    return sum(
        1 for line in text.splitlines()
        if line.startswith("### ") and "status: done" not in text.split(line)[1].split("###")[0]
    )


def manual_start(config: dict) -> None:
    now = datetime.now()
    end = now + timedelta(hours=config["session"]["session_hours"])
    save_state({
        "session_start": now.isoformat(),
        "session_active": True,
        "warned": False,
        "user_active": False,
        "skipped": False,
    })
    print(f"Session clock set. Resets at {end.strftime('%I:%M %p')}.")


def verify_session_clock(config: dict) -> None:
    print("\n  Session Clock Verification")
    print("  " + "-" * 40)
    print("  This checks whether `claude -p \"k\"` starts the claude.ai")
    print("  5-hour session window.\n")
    print("  Step 1: Open https://claude.ai/settings/limits in your browser.")
    print("          Note the current reset time (or confirm no session is active).")
    print()

    try:
        input("  Press Enter when ready to send the kickoff... ")
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return

    message = config["api"]["kickoff_message"]
    print(f"\n  Sending: claude -p \"{message}\"")
    result = subprocess.run(
        ["claude", "-p", message],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        print(f"  Error: {result.stderr.strip()}")
        return

    now = datetime.now()
    expected_reset = now + timedelta(hours=config["session"]["session_hours"])
    print(f"  Sent at {now.strftime('%I:%M:%S %p')}.")
    print(f"  Expected reset time: {expected_reset.strftime('%I:%M %p')}\n")
    print("  Step 2: Refresh https://claude.ai/settings/limits.")
    print(f"          If the reset time is now ~{expected_reset.strftime('%I:%M %p')},")
    print("          verification passed — the CLI starts the session clock.")
    print("          If nothing changed, the CLI does not share the web session pool.\n")


def _print_header(status: dict, queue_count: int) -> None:
    print("\n  Claude Session Manager")
    print("  " + "-" * 40)
    if status["active"]:
        print(f"  Session: ACTIVE  |  {status['remaining']} remaining")
    else:
        print(f"  Session: INACTIVE")
    print(f"  Queue:   {queue_count} project{'s' if queue_count != 1 else ''}")
    print()


def _handle_option_1(state: dict) -> None:
    save_state({**state, "user_active": True, "skipped": False})
    print("\n  Session is yours. Daemon has backed off.")
    print("  It will resume automatically when this session expires.\n")


def _handle_option_2() -> None:
    print("\n  Queue execution coming in Phase 3.\n")


def _handle_option_3(config: dict) -> None:
    path = queue_file_path(config)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "## active-projects\n\n"
            "### 1. Example Project\n"
            "status: in-progress\n"
            "next-step: Describe what Claude should do next\n"
            "priority: high\n"
        )
        print(f"\n  Created queue file at {path}")

    editor = os.environ.get("EDITOR")
    if editor:
        subprocess.run([editor, str(path)])
    else:
        subprocess.run(["open", "-t", str(path)])


def _handle_option_4(state: dict) -> None:
    save_state({**state, "skipped": True, "user_active": False})
    print("\n  Session skipped. Daemon will idle until this session expires.\n")


def _handle_option_5(config: dict) -> None:
    manual_start(config)
    print("  Daemon clock resynced.\n")


def show_menu(config: dict, state: dict) -> None:
    while True:
        status = get_status(config, state)
        queue_count = get_queue_count(config)
        _print_header(status, queue_count)

        print("  [1] Use this session myself")
        print("  [2] Run project queue")
        print("  [3] View / edit queue")
        print("  [4] Skip this session")
        print("  [5] Record manual session start")
        print()

        try:
            choice = input("  Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if choice == "1":
            _handle_option_1(state)
            return
        elif choice == "2":
            _handle_option_2()
            return
        elif choice == "3":
            _handle_option_3(config)
            state = load_state()
        elif choice == "4":
            _handle_option_4(state)
            return
        elif choice == "5":
            _handle_option_5(config)
            state = load_state()
        else:
            print("  Invalid choice. Enter 1–5.\n")


def main() -> None:
    config = load_config(CONFIG_FILE)

    if len(sys.argv) > 1:
        flag = sys.argv[1]
        if flag == "--manual-start":
            manual_start(config)
            return
        if flag == "--verify":
            verify_session_clock(config)
            return

    state = load_state()
    show_menu(config, state)


if __name__ == "__main__":
    main()
