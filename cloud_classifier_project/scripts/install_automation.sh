#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.cloudai.classifier-sync"
PLIST_TEMPLATE="${ROOT}/launchd/${LABEL}.plist.template"
PLIST_DEST="${HOME}/Library/LaunchAgents/${LABEL}.plist"
CRON_CMD="cd ${ROOT} && /bin/bash scripts/sync_raw_not_classified.sh >> /tmp/cloudai_classifier_sync.log 2>&1"

chmod +x "${ROOT}/scripts/sync_raw_not_classified.sh"

mkdir -p "${HOME}/Library/LaunchAgents"
sed "s|__PROJECT_ROOT__|${ROOT}|g" "${PLIST_TEMPLATE}" > "${PLIST_DEST}"

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl unload "${PLIST_DEST}" 2>/dev/null || true
launchctl load -w "${PLIST_DEST}"

# Keep 30-minute cron schedule
tmp="$(mktemp)"
{
  crontab -l 2>/dev/null | awk '!/cloudai_classifier_sync/'
  echo "*/30 * * * * ${CRON_CMD} # cloudai_classifier_sync"
} > "${tmp}"
crontab "${tmp}"
rm -f "${tmp}"

echo "Installed automation:"
echo "- launchd RunAtLoad (immediate run after login/start session)"
echo "- cron every 30 minutes"
echo "Log file: /tmp/cloudai_classifier_sync.log"
