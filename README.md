# Claude Session Manager

Claude Pro/Max gives you a 5-hour usage window that starts from your **first message of the day**. If you open Claude at 9 AM, your window runs 9 AM–2 PM, then resets, giving you maybe 3 usable sessions in a waking day.

This tool runs silently in the background and sends a single throwaway message the moment each session window opens — including while you're asleep — so by the time you wake up, your first window is already running and you haven't wasted any time.

**Before (no tool):** wake up at 8 AM, start Claude, get sessions from 8 AM → 1 PM → 6 PM. That's 3 sessions covering ~15 hours of your day.

**After (with tool):** watcher fires at 5 AM while you're asleep, sessions chain from 5 AM → 10 AM → 3 PM → 8 PM → 1 AM. You wake up to a session already in progress, and get 4+ full sessions covering your entire waking day.

---

## What you need

- macOS
- Python 3.11 or later (`python3 --version` to check)
- [Claude Code](https://claude.ai/code) installed and logged in (`claude --version` to check)

That's it. No API key, no separate account. It uses the same Claude login you already have.

---

## Setup (one time)

```bash
git clone https://github.com/rishirajFS/claude-session-manager
cd claude-session-manager
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## Starting the watcher

```bash
.venv/bin/python watcher.py --start
```

That's all. It forks into the background and starts watching. You'll see:

```
Started (PID 12345). Logs: /Users/you/.claude-session/watcher.log
```

From here, it runs silently. Every 15–20 minutes it checks whether your 5-hour window has expired. When it has, it fires `claude -p "k"` — a single one-character message that starts the next window — and goes back to sleep.

---

## Day-to-day use

**Check if it's running and how much time is left in your current session:**

```bash
.venv/bin/python watcher.py --status
```

```
Watcher:  RUNNING
Session:  ACTIVE — 3h 42m remaining (resets 14:30)
```

**If you opened Claude yourself before the watcher fired** (e.g. you couldn't wait), tell it so the clock is accurate:

```bash
.venv/bin/python watcher.py --reset
```

This sets the session start to right now. Without this, the watcher might fire an extra kickoff thinking the previous session expired when it hadn't.

**Stop the watcher:**

```bash
.venv/bin/python watcher.py --stop
```

---

## Run on login automatically

So you never have to remember to start it:

```bash
./install.sh
```

This installs a launchd agent that starts the watcher every time you log in to your Mac. To remove it:

```bash
./uninstall.sh
```

---

## Checking the logs

```bash
tail -f ~/.claude-session/watcher.log
```

You'll see a line each time a session fires, and when the next check is scheduled:

```
Claude session watcher running. Ctrl+C to stop.
[05:00] Session started. Resets at 10:00.
  Next check at 05:17.
[10:02] Session started. Resets at 15:02.
  Next check at 10:19.
```

---

## Verifying it works

The watcher assumes that `claude -p "k"` (Claude Code CLI) shares the same 5-hour session pool as claude.ai. To confirm this on your account:

```bash
.venv/bin/python cli_menu.py --verify
```

This walks you through the test: check your reset time on claude.ai, send the kickoff, check again. If the reset time updated, you're good.

---

## One important edge case

The watcher tracks session start time **locally** in `~/.claude-session/state.json`. It has no way to see your actual usage on claude.ai. This means:

- If you use Claude heavily and hit your limit early, the watcher doesn't know — it will still fire at the calculated reset time, which is fine.
- If you start a Claude session manually without telling the watcher, run `--reset` so the clocks stay in sync.
- The state file is just JSON, so you can inspect or edit it directly if anything looks off.

---

## Commands

| Command | What it does |
|---------|-------------|
| `python watcher.py --start` | Start in background |
| `python watcher.py --stop` | Stop background process |
| `python watcher.py --status` | Show watcher state and time remaining |
| `python watcher.py --reset` | Resync clock to now (use after a manual session start) |
| `python watcher.py` | Run in foreground — useful for testing |
| `python cli_menu.py --verify` | Walk through the session clock verification test |
