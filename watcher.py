#!/usr/bin/env python3
"""
Runs in the background. Checks every 15-20 minutes whether the 5-hour
Claude session has reset, and fires a kickoff message when it has.

Usage:
    python watcher.py --start     # start in background
    python watcher.py --stop      # stop background process
    python watcher.py --status    # show current session status
    python watcher.py --reset     # tell watcher you started a session manually
    python watcher.py             # run in foreground (for testing)
"""

import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

STATE_DIR = Path.home() / ".claude-session"
STATE_FILE = STATE_DIR / "state.json"
PID_FILE = STATE_DIR / "watcher.pid"
LOG_FILE = STATE_DIR / "watcher.log"

SESSION_HOURS = 5
MIN_INTERVAL = 15 * 60  # 15 minutes
MAX_INTERVAL = 20 * 60  # 20 minutes


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def session_expired(state: dict) -> bool:
    if not state.get("session_start"):
        return True
    start = datetime.fromisoformat(state["session_start"])
    return datetime.now() >= start + timedelta(hours=SESSION_HOURS)


def time_until_reset(state: dict) -> timedelta | None:
    if not state.get("session_start"):
        return None
    start = datetime.fromisoformat(state["session_start"])
    remaining = (start + timedelta(hours=SESSION_HOURS)) - datetime.now()
    return remaining if remaining.total_seconds() > 0 else None


def fire_kickoff() -> bool:
    result = subprocess.run(
        ["claude", "-p", "k"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        log(f"[ERROR] Kickoff failed: {result.stderr.strip()}")
        return False

    now = datetime.now()
    reset_at = now + timedelta(hours=SESSION_HOURS)
    save_state({"session_start": now.isoformat()})
    log(f"[{now.strftime('%H:%M')}] Session started. Resets at {reset_at.strftime('%H:%M')}.")
    return True


def log(message: str) -> None:
    print(message, flush=True)


def run_loop() -> None:
    log("Claude session watcher running. Ctrl+C to stop.")
    while True:
        state = load_state()
        if session_expired(state):
            fire_kickoff()
        interval = random.randint(MIN_INTERVAL, MAX_INTERVAL)
        next_check = datetime.now() + timedelta(seconds=interval)
        log(f"  Next check at {next_check.strftime('%H:%M')}.")
        time.sleep(interval)


def cmd_start() -> None:
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        try:
            os.kill(pid, 0)
            print(f"Already running (PID {pid}).")
            return
        except ProcessLookupError:
            pass

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    pid = os.fork()
    if pid > 0:
        PID_FILE.write_text(str(pid))
        print(f"Started (PID {pid}). Logs: {LOG_FILE}")
        return

    # Child: redirect output to log and run loop
    with open(LOG_FILE, "a") as log_fd:
        os.dup2(log_fd.fileno(), sys.stdout.fileno())
        os.dup2(log_fd.fileno(), sys.stderr.fileno())
    run_loop()


def cmd_stop() -> None:
    if not PID_FILE.exists():
        print("Not running.")
        return
    pid = int(PID_FILE.read_text())
    try:
        os.kill(pid, 15)  # SIGTERM
        PID_FILE.unlink()
        print(f"Stopped (PID {pid}).")
    except ProcessLookupError:
        PID_FILE.unlink()
        print("Process not found. Cleaned up PID file.")


def cmd_status() -> None:
    running = False
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        try:
            os.kill(pid, 0)
            running = True
        except ProcessLookupError:
            pass

    state = load_state()
    remaining = time_until_reset(state)

    print(f"Watcher:  {'RUNNING' if running else 'STOPPED'}")
    if remaining:
        h, rem = divmod(int(remaining.total_seconds()), 3600)
        m = rem // 60
        duration = f"{h}h {m:02d}m" if h else f"{m}m"
        reset_at = datetime.fromisoformat(state["session_start"]) + timedelta(hours=SESSION_HOURS)
        print(f"Session:  ACTIVE — {duration} remaining (resets {reset_at.strftime('%H:%M')})")
    else:
        print(f"Session:  {'INACTIVE — kickoff will fire on next check' if running else 'INACTIVE'}")


def cmd_reset() -> None:
    now = datetime.now()
    reset_at = now + timedelta(hours=SESSION_HOURS)
    save_state({"session_start": now.isoformat()})
    print(f"Clock set to now. Session resets at {reset_at.strftime('%H:%M')}.")


COMMANDS = {
    "--start": cmd_start,
    "--stop": cmd_stop,
    "--status": cmd_status,
    "--reset": cmd_reset,
}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg in COMMANDS:
        COMMANDS[arg]()
    else:
        run_loop()
