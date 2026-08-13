#!/usr/bin/env bash
# 为 qiyunlab 配置 Let's Encrypt HTTPS 并启用自动续期（webroot HTTP-01）
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
CERTBOT_WEBROOT="${CERTBOT_WEBROOT:-/var/www/certbot}"
LETSENCRYPT_DIR="${LETSENCRYPT_DIR:-/etc/letsencrypt}"
EMAIL="${MAIL_LE_EMAIL:-}"
DOMAINS=()
STAGING=0

log() { printf '[https-setup] %s\n' "$*"; }
die()  { printf '[https-setup] ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USG'
Usage:
  sudo bash scripts/setup-letsencrypt-https.sh \
      -d qiyunlab.cc.cd -d www.qiyunlab.cc.cd -m you@example.com [--staging]
Options:
  -d, --domain DOMAIN   证书包含的域名（可重复）
  -m, --email EMAIL     Let's Encrypt 通知邮箱
      --staging         使用 staging 环境测试
  -h, --help            帮助
环境变量:
  LETSENCRYPT_DIR, CERTBOT_WEBROOT, MAIL_LE_EMAIL 可在 .env 中设置
USG
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    -d|--domain) [ "${2:-}" ] || die "missing value for $1"; DOMAINS+=("$2"); shift 2 ;;
    -m|--email)  EMAIL="$2"; shift 2 ;;
    --staging)   STAGING=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ "${#DOMAINS[@]}" -gt 0 ] || die "at least one -d domain is required"
[ -n "$EMAIL" ] || die "email is required (-m) or MAIL_LE_EMAIL"
[ -d "$APP_DIR" ] || die "APP_DIR not found: $APP_DIR"
[ -f "$APP_DIR/docker-compose.yml" ] || die "docker-compose.yml not found"

if [ "$(id -u)" -eq 0 ]; then SUDO=(); else SUDO=(sudo); fi

PRIMARY_DOMAIN="${DOMAINS[0]}"
SERVER_NAMES="${DOMAINS[*]}"

require_command() { command -v "$1" >/dev/null 2>&1 || die "missing command: $1"; }
require_command docker
require_command curl
require_command sed

upsert_env() {
  local key="$1" value="$2" env_file="$APP_DIR/.env" tmp
  touch "$env_file"
  tmp="$(mktemp)"
  awk -v k="$key" -v v="$value" '
    BEGIN{done=0}
    $0 ~ "^" k "=" { print k "=" v; done=1; next }
    { print }
    END{ if(!done) print k "=" v }
  ' "$env_file" > "$tmp"
  mv "$tmp" "$env_file"
}

upsert_env LETSENCRYPT_DIR "$LETSENCRYPT_DIR"
upsert_env CERTBOT_WEBROOT "$CERTBOT_WEBROOT"
upsert_env MAIL_LE_EMAIL "$EMAIL"
upsert_env MAIL_PRIMARY_DOMAIN "$PRIMARY_DOMAIN"
upsert_env MAIL_DOMAINS "$(IFS=,; echo "${DOMAINS[*]}")"

"${SUDO[@]}" mkdir -p "$CERTBOT_WEBROOT" "$LETSENCRYPT_DIR"

if ! command -v certbot >/dev/null 2>&1; then
  log "installing certbot (snap)"
  "${SUDO[@]}" apt-get update
  "${SUDO[@]}" apt-get install -y snapd
  "${SUDO[@]}" systemctl enable --now snapd.socket || true
  "${SUDO[@]}" snap install core || true
  "${SUDO[@]}" snap refresh core || true
  "${SUDO[@]}" snap install --classic certbot
  "${SUDO[@]}" ln -sf /snap/bin/certbot /usr/bin/certbot
fi

compose() { docker compose -f "$APP_DIR/docker-compose.yml" "$@"; }

log "rendering HTTP (ACME) nginx config"
"$APP_DIR/scripts/render-nginx.sh" http
log "starting containers (HTTP phase)"
compose up -d --remove-orphans
compose exec -T nginx nginx -t || die "nginx config test failed"
curl -fsS --max-time 10 http://127.0.0.1/healthz >/dev/null || die "local health check failed"

check_challenge() {
  local token="qy-acme-check-$(date +%s)"
  local dir="$CERTBOT_WEBROOT/.well-known/acme-challenge"
  "${SUDO[@]}" mkdir -p "$dir"
  printf 'ok\n' | "${SUDO[@]}" tee "$dir/$token" >/dev/null
  for d in "${DOMAINS[@]}"; do
    log "checking http://$d/.well-known/acme-challenge/$token"
    curl -fsS --max-time 15 "http://$d/.well-known/acme-challenge/$token" >/dev/null \
      || die "cannot reach ACME path via $d. Check DNS, security group (port 80), firewall, and ICP/unblock status."
  done
  "${SUDO[@]}" rm -f "$dir/$token"
}
check_challenge

args=(certonly --webroot -w "$CERTBOT_WEBROOT" --agree-tos --non-interactive --email "$EMAIL" --keep-until-expiring --expand)
[ "$STAGING" = "1" ] && args+=(--staging)
for d in "${DOMAINS[@]}"; do args+=(-d "$d"); done
log "requesting certificate from Let's Encrypt"
"${SUDO[@]}" certbot "${args[@]}"

log "rendering HTTPS nginx config"
"$APP_DIR/scripts/render-nginx.sh" https
upsert_env MAIL_HTTPS 1
log "restarting containers (HTTPS phase)"
compose up -d --remove-orphans
compose exec -T nginx nginx -t || die "nginx https config test failed"
compose exec -T nginx nginx -s reload

hook_dir="/etc/letsencrypt/renewal-hooks/deploy"
hook_path="$hook_dir/reload-qiyunlab-nginx.sh"
log "writing renewal deploy hook: $hook_path"
"${SUDO[@]}" mkdir -p "$hook_dir"
"${SUDO[@]}" tee "$hook_path" >/dev/null <<SH
#!/usr/bin/env bash
set -euo pipefail
docker compose -f "$APP_DIR/docker-compose.yml" exec -T nginx nginx -s reload
SH
"${SUDO[@]}" chmod +x "$hook_path"

log "testing renewal (dry-run)"
"${SUDO[@]}" certbot renew --dry-run

log "checking HTTPS endpoint"
curl -fsS --max-time 15 "https://$PRIMARY_DOMAIN/healthz" >/dev/null \
  || die "HTTPS check failed for https://$PRIMARY_DOMAIN/healthz"

log "HTTPS setup complete. Auto-renewal managed by certbot (systemd timer)."
