#!/usr/bin/env bash
# =============================================================================
# qiyunlab 前端同步 + 自动部署脚本
#
# 流程：
#   1. 从内网 GitLab (qyweb / develop) 拉取最新前端源码
#   2. 同步到本仓库 frontend/，并做 Plan A 脱敏（去掉硬编码密钥/公网直连）
#   3. 提交并推送到 GitHub (hr342425/qiyunlab)
#   4. SSH 到云服务器执行 ./deploy/deploy.sh 触发一键部署
#
# 说明：
#   - 本脚本不包含任何真实密钥；密钥从环境变量或本地配置文件读取
#   - 配置文件名：${QYUNLAB_SYNC_CONFIG:-~/.config/qiyunlab/sync.env}
#   - 用法：./scripts/sync-deploy.sh [--dry-run] [--skip-deploy]
# =============================================================================
set -euo pipefail

# ---------- 配置（可用环境变量覆盖） ----------
GITLAB_URL="${GITLAB_URL:-ssh://git@gitlab.indac.biz:2222/frontend/qyweb.git}"
GITLAB_BRANCH="${GITLAB_BRANCH:-develop}"
GITLAB_SSH_KEY="${GITLAB_SSH_KEY:-$HOME/id_ed25519}"
SYNC_CACHE="${SYNC_CACHE:-$HOME/.cache/qyweb-sync}"

QYUNLAB_DIR="${QYUNLAB_DIR:-/Users/hongrui/work/qiyunlab}"
FRONTEND_DIR="frontend"

SERVER_HOST="${SERVER_HOST:-101.133.159.247}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_APP_DIR="${SERVER_APP_DIR:-/opt/qiyunlab/app}"

CONFIG_FILE="${QYUNLAB_SYNC_CONFIG:-$HOME/.config/qiyunlab/sync.env}"

DRY_RUN=0
SKIP_DEPLOY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --skip-deploy) SKIP_DEPLOY=1 ;;
    *) echo "未知参数: $arg" >&2; echo "用法: $0 [--dry-run] [--skip-deploy]" >&2; exit 1 ;;
  esac
done

log() { printf '[sync] %s\n' "$*"; }
die() { echo "[sync] 错误: $*" >&2; exit 1; }

# ---------- 读取密钥配置 ----------
if [ -f "$CONFIG_FILE" ]; then
  log "加载配置: ${CONFIG_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
  set +a
else
  log "提示: 未找到 ${CONFIG_FILE}，将只使用环境变量（可参考 scripts/sync.env.example）"
fi

require_var() { [ -n "${!1:-}" ] || die "缺少配置 ${1}（在 ${CONFIG_FILE} 或环境变量中设置）"; }
require_var GITHUB_TOKEN
GITHUB_USER="${GITHUB_USER:-hr342425}"
if [ -z "${SERVER_SSH_PASSWORD:-}" ] && [ -z "${SERVER_SSH_KEY:-}" ]; then
  die "缺少 SERVER_SSH_PASSWORD 或 SERVER_SSH_KEY"
fi
command -v sshpass >/dev/null 2>&1 || die "需要 sshpass（brew install sshpass）"

# ---------- 1. 从内网 GitLab 同步前端 ----------
log "1/5 从 GitLab(${GITLAB_BRANCH}) 同步前端..."
if [ ! -d "$SYNC_CACHE/.git" ]; then
  mkdir -p "$(dirname "$SYNC_CACHE")"
  GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -i $GITLAB_SSH_KEY" \
    git clone --depth 1 -b "$GITLAB_BRANCH" "$GITLAB_URL" "$SYNC_CACHE"
else
  ( cd "$SYNC_CACHE" \
      && GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -i $GITLAB_SSH_KEY" \
         git fetch --depth 1 origin "$GITLAB_BRANCH" \
      && git checkout -f "origin/$GITLAB_BRANCH" )
fi
log "前端版本: $(cd "$SYNC_CACHE" && git log -1 --format='%h %s')"

# ---------- 2. 复制到 qiyunlab/frontend（去掉部署相关文件） ----------
log "2/5 同步到 ${QYUNLAB_DIR}/${FRONTEND_DIR}"
cd "$QYUNLAB_DIR"
[ -d .git ] || die "${QYUNLAB_DIR} 不是 git 仓库"
mkdir -p "$FRONTEND_DIR"
rsync -a --delete \
  --exclude='.git' --exclude='node_modules' --exclude='dist' \
  --exclude='container' --exclude='CI' --exclude='.gitlab-ci.yml' \
  --exclude='qyweb' \
  "$SYNC_CACHE/" "$FRONTEND_DIR/"

# ---------- 3. Plan A 脱敏：去掉前端硬编码密钥/公网直连 ----------
log "3/5 脱敏（同源 /appointment + 移除密钥头）"
CONTACT="$FRONTEND_DIR/src/views/ContactView.vue"
[ -f "$CONTACT" ] && {
  perl -0pi -e "s#http://[0-9.]+/appointment#/appointment#g" "$CONTACT"
  perl -0pi -e "s/'X-API-Key'\s*:\s*'[^']*'[,\s]*\n//g" "$CONTACT"
}
# 脱敏结果校验：不允许残留公网直连或真实密钥
if grep -rEq "http://[0-9.]+/appointment|wKW5UMYnh2ZImhJh5pta7rAJJvV4cm1h|NQQqwirkwEMZQALM" "$FRONTEND_DIR" 2>/dev/null; then
  die "脱敏校验未通过：前端仍残留公网直连或真实密钥，已中止提交"
fi

# ---------- 4. 提交并推送 GitHub ----------
log "4/5 提交并推送 GitHub"
git pull --ff-only origin main
git add "$FRONTEND_DIR"
if git diff --cached --quiet; then
  log "前端无变化，跳过提交"
else
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] 将提交 frontend 变更（未实际提交）"
    git status --short "$FRONTEND_DIR" | head -40
  else
    git commit -m "Sync frontend from internal GitLab (${GITLAB_BRANCH})"
    git -c credential.helper="!f() { echo username=$GITHUB_USER; echo password=$GITHUB_TOKEN; }; f" \
      push origin main
  fi
fi

# ---------- 5. SSH 到服务器自动部署 ----------
if [ "$SKIP_DEPLOY" = "1" ] || [ "$DRY_RUN" = "1" ]; then
  log "5/5 跳过服务器部署（--skip-deploy 或 --dry-run）"
else
  log "5/5 SSH 部署到 ${SERVER_HOST}:${SERVER_APP_DIR}"
  if [ -n "${SERVER_SSH_PASSWORD:-}" ]; then
    sshpass -p "$SERVER_SSH_PASSWORD" \
      ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" \
      "cd $SERVER_APP_DIR && ./deploy/deploy.sh"
  else
    ssh -i "$SERVER_SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" \
      "cd $SERVER_APP_DIR && ./deploy/deploy.sh"
  fi
fi

log "完成。"
