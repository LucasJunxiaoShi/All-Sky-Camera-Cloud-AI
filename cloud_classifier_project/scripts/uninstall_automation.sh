#!/usr/bin/env bash
set -euo pipefail

LABEL="com.cloudai.classifier-sync"
PLIST_DEST="${HOME}/Library/LaunchAgents/${LABEL}.plist"

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl unload "${PLIST_DEST}" 2>/dev/null || true
rm -f "${PLIST_DEST}"

tmp="$(mktemp)"
crontab -l 2>/dev/null | awk '!/cloudai_classifier_sync/' > "${tmp}" || true
crontab "${tmp}" || true
rm -f "${tmp}"

echo "Removed launchd + cron automation for classifier sync."
