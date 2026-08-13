#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/qiyunlab/app}"
BRANCH="${BRANCH:-main}"
FORCE_SYNC="${FORCE_SYNC:-0}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8080/health}"

log() {
  printf '[deploy] %s\n' "$*"
}

if [ "$FORCE_SYNC" != "0" ] && [ "$FORCE_SYNC" != "1" ]; then
  echo "Unsupported FORCE_SYNC: $FORCE_SYNC" >&2
  echo "Use FORCE_SYNC=0 or FORCE_SYNC=1." >&2
  exit 1
fi

cd "$APP_DIR"

log "syncing code from origin/$BRANCH"
git fetch origin "$BRANCH"
if [ "$FORCE_SYNC" = "1" ]; then
  git checkout -B "$BRANCH" "origin/$BRANCH"
  git reset --hard "origin/$BRANCH"
else
  if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
    git checkout "$BRANCH"
  else
    git checkout -b "$BRANCH" "origin/$BRANCH"
  fi
  git pull --ff-only origin "$BRANCH"
fi

log "building mail image"
docker compose build mail

log "starting containers"
docker compose up -d --remove-orphans

log "checking health: $HEALTH_URL"
for attempt in $(seq 1 20); do
  if curl -fsS "$HEALTH_URL" >/dev/null; then
    log "deploy complete. branch=$BRANCH force_sync=$FORCE_SYNC"
    exit 0
  fi
  sleep 1
  log "health check retry $attempt/20"
done

echo "Health check failed: $HEALTH_URL" >&2
docker compose ps >&2 || true
docker compose logs --tail=80 mail >&2 || true
exit 1
