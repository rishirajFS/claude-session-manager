#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$REPO_DIR/.venv/bin/python"
DAEMON="$REPO_DIR/daemon.py"
PLIST_LABEL="com.rishirajfs.claude-session-manager"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"
LOG_DIR="$HOME/.claude-session"

# Checks
if [ ! -f "$PYTHON" ]; then
    echo "Error: .venv not found."
    echo "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

CLAUDE_BIN="$(which claude 2>/dev/null || true)"
if [ -z "$CLAUDE_BIN" ]; then
    echo "Error: claude CLI not found in PATH. Install Claude Code first."
    exit 1
fi

CLAUDE_DIR="$(dirname "$CLAUDE_BIN")"

mkdir -p "$LOG_DIR"
mkdir -p "$HOME/Library/LaunchAgents"

# Write plist
cat > "$PLIST_DEST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$DAEMON</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$REPO_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$CLAUDE_DIR:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/daemon.error.log</string>
</dict>
</plist>
EOF

# Reload
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Installed and started."
echo "Logs:   $LOG_DIR/daemon.log"
echo "Errors: $LOG_DIR/daemon.error.log"
echo ""
echo "Check status:   launchctl list | grep claude-session"
echo "View logs:      tail -f $LOG_DIR/daemon.log"
echo "Uninstall:      ./uninstall.sh"
