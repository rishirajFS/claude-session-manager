# Claude Session Manager

A macOS background daemon and CLI tool that maximizes usable Claude sessions per day by automatically starting each 5-hour session window at the optimal time.

## The Problem

Claude Pro/Max resets every 5 hours from first use. Starting your first session at 8 AM gives you 3 sessions in a waking day. Pre-starting a session at 5 AM (while asleep) gives you 5 — a 67% throughput increase with zero extra effort.

| Session | Start | End | Status |
|---------|-------|-----|--------|
| 1 | 5:00 AM | 10:00 AM | Asleep — daemon fires kickoff |
| 2 | 10:00 AM | 3:00 PM | Awake — 5 full hours |
| 3 | 3:00 PM | 8:00 PM | Awake — 5 full hours |
| 4 | 8:00 PM | 1:00 AM | Awake — 5 full hours |
| 5 | 1:00 AM | 6:00 AM | Asleep — daemon fires kickoff |

## How It Works

The daemon fires `claude -p "k"` at the scheduled kickoff time. This uses your existing Claude Code session (no API key required) and costs ~2 tokens — just enough to start the session clock. Sessions then chain automatically: when one expires, the daemon immediately fires the next kickoff.

## Setup

**Requirements:** macOS, Python 3.11+, [Claude Code CLI](https://claude.ai/code) installed and logged in.

```bash
git clone https://github.com/FettesSchwein/claude-session-manager
cd claude-session-manager

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Edit `config.toml` to match your schedule:

```toml
[session]
wake_time        = "08:00"   # your typical wake time
kickoff_offset_h = 3         # hours before wake to fire first kickoff
```

## Usage

**Start the daemon** (keep this running in the background):

```bash
python daemon.py
```

**Check session status / open the menu:**

```bash
python cli_menu.py
```

```
  Claude Session Manager
  ----------------------------------------
  Session: ACTIVE  |  4h 58m remaining
  Queue:   2 projects

  [1] Use this session myself
  [2] Run project queue
  [3] View / edit queue
  [4] Skip this session
```

**If you started a Claude session manually** (outside the daemon), resync the clock:

```bash
python cli_menu.py --manual-start
```

## Menu Options

| Option | What it does |
|--------|-------------|
| **[1] Use this session myself** | Daemon backs off. You use Claude normally. Resumes automatically on next session reset. |
| **[2] Run project queue** | Daemon sends continuation prompts from your queue file. *(Phase 3)* |
| **[3] View / edit queue** | Opens `active-projects.md` in `$EDITOR`. Creates the file with a template if it doesn't exist. |
| **[4] Skip this session** | Daemon idles. Session expires unused. Kickoff fires automatically for the next one. |

## Project Queue Format

The queue lives at `~/Documents/Obsidian/active-projects.md` (configurable in `config.toml`):

```markdown
## active-projects

### 1. KV Cache Benchmarks
status: in-progress
next-step: Run prefetch experiments on V100, log throughput delta vs baseline
context-file: [[kv-cache/experiment-log]]
priority: high

### 2. HARBOR LoRA Fine-tuning
status: blocked-on-session
next-step: Resume SFT on College Experience dataset, epoch 3
priority: medium
```

Fields: `status` (in-progress | blocked-on-session | done), `next-step` (sent to Claude as the continuation prompt), `context-file` (optional Obsidian wikilink injected before the prompt), `priority` (high | medium | low).

## State

Session state is stored at `~/.claude-session/state.json`. Never committed.

## Configuration

Full `config.toml` reference:

```toml
[session]
wake_time        = "08:00"   # 24h format
kickoff_offset_h = 3         # hours before wake_time to fire kickoff
session_hours    = 5         # Claude session window length

[queue]
vault_path       = "~/Documents/Obsidian"
queue_file       = "active-projects.md"

[api]
kickoff_message  = "k"       # message sent to start the session clock

[notifications]
enabled          = true
warn_at_minutes  = 30        # Mac notification when this many minutes remain
```

## Running Tests

```bash
.venv/bin/pytest tests/ -v
```

## Build Status

- [x] Phase 1 — Core daemon, session clock, notifications, basic status display
- [x] Phase 2 — Interactive CLI menu, daemon backoff, queue file editor
- [ ] Phase 3 — Project queue execution (option 2)
- [ ] Phase 4 — Obsidian wikilink context injection
- [ ] Phase 5 — launchd auto-launch, manual clock resync polish
