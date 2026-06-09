#!/usr/bin/env bash
# ============================================================
# WhoamiSec — VPS Deploy Script
# Works WITHOUT any DNS / domain name — just VPS IP
#
# Run on a fresh Ubuntu/Debian VPS:
#   curl -fsSL https://raw.githubusercontent.com/kimikukiu/whoamisec/main/vps-deploy.sh | bash
#
# Or after git clone:
#   bash vps-deploy.sh
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${CYAN}[$(date '+%H:%M:%S')] $*${NC}"; }
ok()   { echo -e "${GREEN}  ✔ $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ $*${NC}"; }
err()  { echo -e "${RED}  ✖ $*${NC}"; }

# ── Detect public IP ─────────────────────────────────────────
VPS_IP=$(curl -fsSL https://ipv4.icanhazip.com 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          WhoamiSec — VPS Deploy                          ║"
echo "║          admin / WhoamiSecAdmin2026!                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log "VPS IP: $VPS_IP"

# ── Step 1: Install Docker ───────────────────────────────────
if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    ok "Docker installed"
else
    ok "Docker already installed ($(docker --version | head -1))"
fi

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
    log "Installing Docker Compose..."
    apt-get install -y docker-compose-plugin 2>/dev/null || \
    curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose
    ok "Docker Compose installed"
fi

# ── Step 2: Clone or update repo ────────────────────────────
DEPLOY_DIR="/opt/whoamisec"
if [ -d "$DEPLOY_DIR/.git" ]; then
    log "Updating existing repo at $DEPLOY_DIR..."
    cd "$DEPLOY_DIR"
    git pull origin main
    ok "Repo updated"
elif [ -f "$(dirname "$0")/docker-compose.yml" ]; then
    DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
    cd "$DEPLOY_DIR"
    ok "Using existing repo at $DEPLOY_DIR"
else
    log "Cloning repo to $DEPLOY_DIR..."
    git clone https://github.com/kimikukiu/whoamisec.git "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
    ok "Repo cloned"
fi

# ── Step 3: Configure environment ───────────────────────────
if [ ! -f ".env" ]; then
    log "Creating .env..."
    cat > .env << EOF
# WhoamiSec — auto-generated $(date)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# GitHub token for auto-downloading APK releases
# Get from: github.com → Settings → Developer settings → Personal access tokens → Fine-grained
# Permissions needed: Contents: Read (for public repos, no token needed — set to 'public')
GH_APK_WATCHDOG_TOKEN=

# Cloudflare Tunnel token (optional — for custom domain without DNS)
# Setup: bash tunnel-setup.sh
CF_TUNNEL_TOKEN=
EOF
    ok ".env created with random secrets"
fi

# ── Step 4: Open firewall ────────────────────────────────────
if command -v ufw &>/dev/null; then
    ufw allow 80/tcp 2>/dev/null && ok "Firewall: port 80 opened" || true
    ufw allow 443/tcp 2>/dev/null && ok "Firewall: port 443 opened" || true
fi

# ── Step 5: Build and start ──────────────────────────────────
log "Building and starting services..."
docker compose down 2>/dev/null || true
docker compose pull 2>/dev/null || true
docker compose build --no-cache

# Check if GH token is set — start APK watchdog if so
if grep -q "GH_APK_WATCHDOG_TOKEN=." .env 2>/dev/null; then
    log "Starting all services including APK watchdog..."
    docker compose up -d
else
    log "Starting web + api (no APK watchdog token set)..."
    docker compose up -d web api apk-watchdog
fi

# Wait for health
log "Waiting for services to start..."
for i in $(seq 1 20); do
    if curl -fsSL "http://localhost:8080/health" &>/dev/null; then
        break
    fi
    sleep 2
done

# ── Step 6: Status ───────────────────────────────────────────
docker compose ps

echo ""
echo "══════════════════════════════════════════════════════════"
ok "WhoamiSec is LIVE!"
echo ""
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │  Website:      http://$VPS_IP/                      "
echo "  │  Downloads:    http://$VPS_IP/downloads             "
echo "  │  APK files:    http://$VPS_IP/apk/                  "
echo "  │  JARVIS MIND:  http://$VPS_IP/apps/jarvis-mind      "
echo "  │  Business:     http://$VPS_IP/apps/business         "
echo "  │  CICADA 3301:  http://$VPS_IP/apps/cicada           "
echo "  │  Admin panel:  http://$VPS_IP/admin                 "
echo "  │  API health:   http://$VPS_IP/health                "
echo "  │                                                      "
echo "  │  Admin login:  admin / WhoamiSecAdmin2026!          "
echo "  └─────────────────────────────────────────────────────┘"
echo ""
echo "  APK auto-download: edit .env → set GH_APK_WATCHDOG_TOKEN"
echo "  Custom domain:     bash tunnel-setup.sh (Cloudflare, free)"
echo ""
echo "  Logs:   docker compose logs -f"
echo "  Stop:   docker compose down"
echo "══════════════════════════════════════════════════════════"
