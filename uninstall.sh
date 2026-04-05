#!/bin/bash
PLIST="$HOME/Library/LaunchAgents/com.rishirajfs.claude-session-manager.plist"

if [ -f "$PLIST" ]; then
    launchctl unload "$PLIST"
    rm "$PLIST"
    echo "Uninstalled."
else
    echo "Not installed."
fi
