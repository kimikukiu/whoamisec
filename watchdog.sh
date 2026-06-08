#!/bin/bash
# ════════════════════════════════════════════════════════════
# WhoamiSec VPS — Service Watchdog
# Runs every 60s, auto-restarts any dead service
# Install:  nohup bash watchdog.sh &> /tmp/watchdog.log &
# ════════════════════════════════════════════════════════════

INTERVAL=60
REPO_DIR="/workspaces/whoamisec"
# Fall back to script location if REPO_DIR doesn't exist
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
[ -d "$REPO_DIR" ] || REPO_DIR="$SCRIPT_DIR/.."

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

restart_docker_stack() {
    log "Starting Docker stack…"
    cd "$REPO_DIR"
    docker compose up -d web api 2>&1
    log "Docker stack restarted"
}

restart_flask_direct() {
    log "Starting Flask (no Docker)…"
    cd "$REPO_DIR/backend"
    pip install -q flask flask-cors flask-jwt-extended flask-sqlalchemy werkzeug 2>/dev/null
    nohup python3 app.py > /tmp/flask.log 2>&1 &
    log "Flask started on :5001"
}

restart_ollama() {
    log "Starting Ollama…"
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
    log "Ollama started on :11434"
}

check_and_restart_nginx() {
    # If Docker nginx is not running, try to restart
    if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'web'; then
        if command -v docker &>/dev/null; then
            log "Nginx container DOWN — restarting Docker stack"
            restart_docker_stack
        else
            log "Nginx DOWN — no Docker, trying direct Flask"
            restart_flask_direct
        fi
    fi
}

check_and_restart_flask() {
    # Check if Flask is responding
    if command -v docker &>/dev/null && docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'api'; then
        # Docker Flask — check via docker
        if ! docker exec api curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1; then
            log "Flask API container unhealthy — restarting"
            cd "$REPO_DIR"
            docker compose restart api 2>&1
        fi
    elif ! curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1; then
        log "Flask API DOWN — restarting"
        restart_flask_direct
    fi
}

check_and_restart_ollama() {
    if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        if command -v ollama &>/dev/null; then
            log "Ollama DOWN — restarting"
            restart_ollama
        fi
    fi
}

# ════════════════════════════════════════════════════════════
# Main loop
# ════════════════════════════════════════════════════════════
log "=== WhoamiSec Watchdog Started ==="
log "Repo dir: $REPO_DIR"
log "Interval: ${INTERVAL}s"

while true; do
    check_and_restart_nginx
    check_and_restart_flask
    check_and_restart_ollama
    sleep $INTERVAL
done
