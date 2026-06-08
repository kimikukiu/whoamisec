#!/usr/bin/env bash
# ============================================================
# WhoamiSec — Start everything in Codespace
# Just run:  bash start.sh
# ============================================================

set -euo pipefail
cd "$(dirname "$0")"

log() { echo -e "\e[1;36m[$(date '+%H:%M:%S')] $*\e[0m"; }
ok()  { echo -e "\e[1;32m  ✔ $*\e[0m"; }
warn(){ echo -e "\e[1;33m  ⚠ $*\e[0m"; }

log "Starting WhoamiSec stack…"

# ── Ollama (AI models) ───────────────────────────────────────
if ! pgrep -x ollama > /dev/null; then
    log "Starting Ollama…"
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
    ok "Ollama running (port 11434)"
else
    ok "Ollama already running"
fi

# Pull models silently if missing
for model in tinyllama phi:2.7b qwen2.5:0.5b llama3.2:1b deepseek-coder:1.3b granite-code:3b; do
    ollama list 2>/dev/null | grep -q "${model%%:*}" || {
        log "Pulling $model (background)…"
        nohup ollama pull "$model" >> /tmp/ollama.log 2>&1 &
    }
done

# ── Docker stack ─────────────────────────────────────────────
if command -v docker &>/dev/null; then
    log "Starting Docker stack (web + api)…"
    docker compose up -d web api

    # Start tunnel if token is set
    if [[ -n "${CF_TUNNEL_TOKEN:-}" ]]; then
        log "Starting Cloudflare Tunnel…"
        docker compose --profile tunnel up -d tunnel
        ok "Tunnel active → whoamisec.com + cicada.omni are LIVE"
    else
        warn "CF_TUNNEL_TOKEN not set — tunnel not started"
        warn "Run: bash tunnel-setup.sh  to get your free tunnel token"
    fi

    # Start APK watchdog if token is set
    if [[ -n "${GH_APK_WATCHDOG_TOKEN:-}" ]]; then
        docker compose --profile apk up -d apk-watchdog
        ok "APK watchdog running"
    fi

    log ""
    log "Stack status:"
    docker compose ps
else
    # No Docker — run Flask directly
    warn "Docker not found, running Flask directly…"
    cd backend
    pip install -q flask flask-cors flask-jwt-extended flask-sqlalchemy werkzeug 2>/dev/null
    nohup python3 app.py > /tmp/flask.log 2>&1 &
    ok "Flask API running on :5001"
    cd ..

    # Expose via Codespace port forwarding
    log "Open in Codespace: Ports tab → Forward port 5001 → Set to Public"
fi

# ── Watchdog (auto-restart dead services) ──────────────────────
if ! pgrep -f "watchdog.sh" > /dev/null; then
    log "Starting watchdog…"
    nohup bash "$(dirname "$0")/watchdog.sh" > /tmp/watchdog.log 2>&1 &
    ok "Watchdog running (auto-restarts dead services every 60s)"
fi

echo ""
echo "════════════════════════════════════════════════════════"
ok "WhoamiSec is running!"
echo ""
echo "  Local:        http://localhost:8080"
echo "  API:          http://localhost:5001/api/v1/health"
echo "  Ollama:       http://localhost:11434"
echo "  Watchdog:     /tmp/watchdog.log"
[[ -n "${CF_TUNNEL_TOKEN:-}" ]] && echo "  Public:       https://whoamisec.com  (via Cloudflare)"
echo ""
echo "  Logs:  docker compose logs -f"
echo "  Stop:  docker compose down"
echo "════════════════════════════════════════════════════════"
