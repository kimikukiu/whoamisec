#!/usr/bin/env bash
# ============================================================
# Cloudflare Tunnel setup — whoamisec.com → Codespace FREE
#
# Zero cost. No VPS. No server. Runs entirely in Codespace.
#
# Requirements:
#   - Cloudflare account (free)
#   - whoamisec.com / cicada.omni nameservers → Cloudflare
#
# Run ONCE to create the tunnel, then copy token to Codespace secrets.
# ============================================================

set -euo pipefail

log() { echo -e "\e[1;36m[$(date '+%H:%M:%S')] $*\e[0m"; }
ok()  { echo -e "\e[1;32m  ✔ $*\e[0m"; }

# ── Step 1: Install cloudflared ──────────────────────────────
if ! command -v cloudflared &>/dev/null; then
    log "Installing cloudflared…"
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
        -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
    ok "cloudflared installed"
fi

cloudflared --version

# ── Step 2: Login to Cloudflare ──────────────────────────────
log "Opening Cloudflare login… (browser will open)"
cloudflared tunnel login
ok "Logged in"

# ── Step 3: Create tunnels ───────────────────────────────────
log "Creating tunnel: whoamisec-main"
cloudflared tunnel create whoamisec-main
TUNNEL_ID=$(cloudflared tunnel list | grep whoamisec-main | awk '{print $1}')
log "Tunnel ID: $TUNNEL_ID"

# ── Step 4: Configure DNS routes ────────────────────────────
log "Adding DNS routes…"
cloudflared tunnel route dns whoamisec-main whoamisec.com
cloudflared tunnel route dns whoamisec-main www.whoamisec.com
cloudflared tunnel route dns whoamisec-main api.whoamisec.com
cloudflared tunnel route dns whoamisec-main dashboard.whoamisec.com
cloudflared tunnel route dns whoamisec-main admin.whoamisec.com
cloudflared tunnel route dns whoamisec-main jarvis.whoamisec.com
cloudflared tunnel route dns whoamisec-main mining.whoamisec.com
cloudflared tunnel route dns whoamisec-main downloads.whoamisec.com
cloudflared tunnel route dns whoamisec-main apps.whoamisec.com
cloudflared tunnel route dns whoamisec-main cicada.omni
cloudflared tunnel route dns whoamisec-main apk.cicada.omni
ok "All DNS routes added"

# ── Step 5: Create tunnel config ────────────────────────────
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<EOF
tunnel: $TUNNEL_ID
credentials-file: /root/.cloudflared/${TUNNEL_ID}.json

ingress:
  # API subdomain → Flask
  - hostname: api.whoamisec.com
    service: http://localhost:5001

  # All other whoamisec.com subdomains + cicada → nginx
  - hostname: whoamisec.com
    service: http://localhost:8080
  - hostname: www.whoamisec.com
    service: http://localhost:8080
  - hostname: dashboard.whoamisec.com
    service: http://localhost:8080
  - hostname: admin.whoamisec.com
    service: http://localhost:8080
  - hostname: jarvis.whoamisec.com
    service: http://localhost:8080
  - hostname: mining.whoamisec.com
    service: http://localhost:8080
  - hostname: downloads.whoamisec.com
    service: http://localhost:8080
  - hostname: apps.whoamisec.com
    service: http://localhost:8080
  - hostname: cicada.omni
    service: http://localhost:8080
  - hostname: apk.cicada.omni
    service: http://localhost:8080/apk/

  # Catch-all
  - service: http_status:404
EOF
ok "Tunnel config written"

# ── Step 6: Get tunnel token for Docker ─────────────────────
log "Getting tunnel token for docker-compose…"
TOKEN=$(cloudflared tunnel token whoamisec-main)
echo ""
echo "════════════════════════════════════════════════════════"
ok "TUNNEL TOKEN (save this as Codespace secret CF_TUNNEL_TOKEN):"
echo ""
echo "$TOKEN"
echo ""
echo "  github.com → Your Codespace → Settings → Secrets"
echo "  Name:  CF_TUNNEL_TOKEN"
echo "  Value: (paste token above)"
echo "════════════════════════════════════════════════════════"
echo ""
log "Start everything:"
echo "  docker compose up -d                          # web + api"
echo "  docker compose --profile tunnel up -d tunnel  # + CF tunnel"
echo "  docker compose --profile apk up -d apk-watchdog  # + APK sync"
