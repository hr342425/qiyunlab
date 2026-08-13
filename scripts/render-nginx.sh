#!/usr/bin/env bash
# 根据 .env 渲染 deploy/nginx.conf（http 或 https 模板）
# 用法: scripts/render-nginx.sh [http|https]   (缺省按 .env 的 MAIL_HTTPS 自动选择)
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"
[ -f .env ] || { echo "render-nginx: .env not found in $APP_DIR" >&2; exit 1; }

set -a
# shellcheck disable=SC1091
source .env
set +a

MAIL_API_KEY="${MAIL_API_KEY:-}"
PRIMARY="${MAIL_PRIMARY_DOMAIN:-}"
DOMAINS="${MAIL_DOMAINS:-}"

[ -n "$MAIL_API_KEY" ] || { echo "render-nginx: MAIL_API_KEY is required" >&2; exit 1; }

MODE="${1:-}"
if [ -z "$MODE" ]; then
  if [ "${MAIL_HTTPS:-0}" = "1" ]; then MODE=https; else MODE=http; fi
fi

case "$MODE" in
  http)
    TEMPLATE="$APP_DIR/deploy/nginx.http.template"
    ;;
  https)
    [ -n "$PRIMARY" ] || { echo "render-nginx: MAIL_PRIMARY_DOMAIN required for https" >&2; exit 1; }
    TEMPLATE="$APP_DIR/deploy/nginx.https.template"
    ;;
  *)
    echo "render-nginx: mode must be http or https" >&2
    exit 1
    ;;
esac

# MAIL_DOMAINS 用逗号分隔，转为 nginx 的空格分隔 server_name；为空则用 _（catch-all）
SERVER_NAMES="$(printf '%s' "$DOMAINS" | tr ',' ' ')"
[ -n "$SERVER_NAMES" ] || SERVER_NAMES="_"

sed \
  -e "s|__MAIL_API_KEY__|$MAIL_API_KEY|g" \
  -e "s|__SERVER_NAMES__|$SERVER_NAMES|g" \
  -e "s|__PRIMARY_DOMAIN__|$PRIMARY|g" \
  "$TEMPLATE" > "$APP_DIR/deploy/nginx.conf"

echo "render-nginx: wrote deploy/nginx.conf (mode=$MODE, domains=$SERVER_NAMES)"
