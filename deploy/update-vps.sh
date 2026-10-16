#!/usr/bin/env bash
# Run from the VPS: bash /home/nasser/apps/reguide/source/deploy/update-vps.sh
set -Eeuo pipefail
umask 022

APP=/home/nasser/apps/reguide
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ "$SOURCE" == "$APP/source" ]] || { echo 'Run this script from the VPS source checkout.'; exit 1; }
[[ -f "$APP/backend/.env" && -d "$APP/data" ]] || { echo 'Production environment is not initialized.'; exit 1; }
exec 9>"$APP/deploy/update.lock"
flock -n 9 || { echo 'Another deployment is running.'; exit 1; }

cd "$SOURCE"
git diff --quiet && git diff --cached --quiet || { echo 'Commit or stash tracked source changes before deploying.'; exit 1; }
[[ "$(git branch --show-current)" == main ]] || { echo 'Expected the main branch.'; exit 1; }
git pull --ff-only origin main
REVISION="$(git rev-parse HEAD)"

echo 'Building frontend for /reguide/ ...'
cd "$SOURCE/frontend"
npm ci --no-audit --no-fund
VITE_BASE_PATH=/reguide/ VITE_API_BASE=/reguide/api npm run build
node --test .verification/paper-analysis.test.cjs .verification/source-anchors.test.cjs

STAMP="$(date -u +%Y%m%d-%H%M%S)-${REVISION:0:8}"
BACKUP="$APP/deploy/backups/$STAMP"
mkdir -p "$BACKUP"
chmod 700 "$APP/deploy/backups" "$BACKUP"
cp -a "$APP/backend/app" "$BACKUP/backend-app"
cp -a "$APP/frontend/dist" "$BACKUP/frontend-dist"
"$APP/backend/.venv/bin/python" - "$APP/data/researchguide.db" "$BACKUP/researchguide.db" <<'PY'
import sqlite3
import sys
with sqlite3.connect(sys.argv[1]) as source, sqlite3.connect(sys.argv[2]) as target:
    source.backup(target)
PY
chmod 600 "$BACKUP/researchguide.db"

echo 'Installing backend dependencies ...'
"$APP/backend/.venv/bin/python" -m pip install --disable-pip-version-check -r "$SOURCE/backend/requirements.txt"
"$APP/backend/.venv/bin/python" -m pip check

CHANGED=0
rollback() {
    result=$?
    trap - ERR
    if [[ "$CHANGED" == 1 ]]; then
        echo 'Deployment failed. Restoring the previous application code.' >&2
        rsync -a --delete "$BACKUP/backend-app/" "$APP/backend/app/"
        rsync -a --delete "$BACKUP/frontend-dist/" "$APP/frontend/dist/"
        systemctl --user restart reguide.service
    fi
    echo "Deployment backup: $BACKUP" >&2
    exit "$result"
}
trap rollback ERR
CHANGED=1
rsync -a --delete --exclude=__pycache__ "$SOURCE/backend/app/" "$APP/backend/app/"
rsync -a --delete "$SOURCE/frontend/dist/" "$APP/frontend/dist/"
systemctl --user restart reguide.service

HEALTHY=0
for attempt in {1..20}; do
    if curl --fail --silent --max-time 3 http://127.0.0.1:8125/api/health >"$BACKUP/health.json"; then
        HEALTHY=1
        break
    fi
    sleep 1
done
[[ "$HEALTHY" == 1 ]]
systemctl --user is-active --quiet reguide.service
curl --fail --silent --max-time 15 https://nasserdiary.com/reguide/api/health
curl --fail --silent --max-time 15 --output /dev/null https://nasserdiary.com/reguide/auth
printf '%s\n' "$REVISION" >"$APP/deploy/deployed-revision"
trap - ERR
printf '\nDeployed commit: %s\nApplication: https://nasserdiary.com/reguide/\nBackup: %s\n' "$REVISION" "$BACKUP"
