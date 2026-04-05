# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Session Manager is a Python background daemon and CLI tool that maximizes usable Claude sessions per day. It pre-fires a kickoff API message at a scheduled time (default: 3h before wake) so each 5-hour session window starts while the user is asleep, then presents a CLI menu when the user wakes up.

## Architecture

Five components with clear boundaries:

| File | Role |
|------|------|
| `daemon.py` | Main loop — fires kickoff, tracks session clock, triggers notifications, manages queue execution |
| `cli_menu.py` | Interactive terminal menu — renders session status, handles user menu selections |
| `queue_parser.py` | Reads/writes `active-projects.md`; parses project markdown schema |
| `notifier.py` | Mac native notifications via `osascript` |
| `config.toml` | User config (wake time, kickoff offset, vault path, model, etc.) |

**State file**: `~/.claude-session/state.json` — persists `session_start` timestamp across restarts.

**Session clock logic**: `time_remaining = (session_start + 5h) - now()`. The daemon cannot read the Claude session clock directly; it infers reset time from the local state file. Rate-limit response headers are used as a cross-check.

**Queue file**: `~/Documents/Obsidian/active-projects.md` (configurable). Projects have `status`, `next-step`, `context-file` (Obsidian `[[wikilink]]`), and `priority` fields. Daemon processes `high` priority first, sends `next-step` as the continuation prompt, optionally prepending resolved wikilink content.

**Kickoff command**: `claude -p "k"` via subprocess — uses the existing Claude Code CLI session (no API key required). Response is discarded. This is the cheapest way to start the session clock.

**Idle detection**: The daemon never auto-runs the queue. Queue execution only starts when the user selects option [2] from the CLI menu.

## Commands

```bash
# Create venv and install dependencies
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Run tests
.venv/bin/pytest tests/ -v

# Run a single test
.venv/bin/pytest tests/test_daemon.py::test_name -v

# Run the daemon
.venv/bin/python daemon.py

# Check session status
.venv/bin/python cli_menu.py

# Resync clock after a manual session start
.venv/bin/python cli_menu.py --manual-start
```

## Configuration

`config.toml` at repo root (copied to `~/.claude-session/config.toml` on first run):

```toml
[session]
wake_time        = "08:00"
kickoff_offset_h = 3
session_hours    = 5

[queue]
vault_path       = "~/Documents/Obsidian"
queue_file       = "active-projects.md"

[api]
model            = "claude-haiku-4-5-20251001"
kickoff_message  = "hey"

[notifications]
enabled          = true
warn_at_minutes  = 30
```

## Key Constraints

- macOS only (uses `osascript` for notifications, `launchd` for auto-launch).
- API key must be set in env: `ANTHROPIC_API_KEY`.
- The daemon must **not** auto-fire queue execution — only on explicit user selection.
- Clock resets when the user manually reports a session start via CLI (resyncs `state.json`).

## Build Phases

1. Core daemon: config loading, kickoff API call, clock tracking, notification, basic status display.
2. CLI menu: options 1–4 with daemon backoff on option 1.
3. Project queue: `queue_parser.py`, option 2 send/loop, completion notifications.
4. Obsidian context: resolve `[[wikilink]]` to absolute path, inject content into prompt.
5. Polish: launchd plist, 30-min warning, manual clock resync, API-vs-web session sharing test.
