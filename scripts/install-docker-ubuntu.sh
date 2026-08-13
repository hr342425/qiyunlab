#!/usr/bin/env bash
# Install Docker Engine + Compose plugin on Ubuntu (Tencent Cloud).
set -euo pipefail

DOCKER_MIRROR="${DOCKER_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/docker-ce}"
REGISTRY_MIRROR="${REGISTRY_MIRROR:-}"

log() { printf '[docker-install] %s\n' "$*"; }

if [ "$(id -u)" -eq 0 ]; then
  SUDO=()
else
  SUDO=(sudo)
fi

log "removing old docker packages if present"
"${SUDO[@]}" apt-get remove -y docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc || true

log "installing prerequisites"
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y ca-certificates curl gnupg lsb-release git ufw

log "adding Docker CE apt key from $DOCKER_MIRROR"
"${SUDO[@]}" install -m 0755 -d /etc/apt/keyrings
"${SUDO[@]}" rm -f /etc/apt/keyrings/docker.gpg
curl -fsSL "$DOCKER_MIRROR/linux/ubuntu/gpg" | "${SUDO[@]}" gpg --dearmor -o /etc/apt/keyrings/docker.gpg
"${SUDO[@]}" chmod a+r /etc/apt/keyrings/docker.gpg

log "adding Docker CE apt repository"
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] $DOCKER_MIRROR/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  "${SUDO[@]}" tee /etc/apt/sources.list.d/docker.list >/dev/null

log "installing Docker Engine and Compose plugin"
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

if [ -n "$REGISTRY_MIRROR" ]; then
  log "configuring registry mirror: $REGISTRY_MIRROR"
  "${SUDO[@]}" mkdir -p /etc/docker
  "${SUDO[@]}" tee /etc/docker/daemon.json >/dev/null <<JSON
{"registry-mirrors": ["$REGISTRY_MIRROR"]}
JSON
fi

log "enabling Docker service"
"${SUDO[@]}" systemctl enable --now docker

log "Docker installed"
docker --version
docker compose version
