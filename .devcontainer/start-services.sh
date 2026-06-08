#!/bin/bash
set -e
echo "[+] Starting WhoamiSec services..."

REPO_DIR="/workspaces/whoamisec"
[ -d "$REPO_DIR" ] || REPO_DIR="/workspace"

# ── Docker stack (preferred) ──────────────────────────────────
if command -v docker &>/dev/null && [ -f "$REPO_DIR/docker-compose.yml" ]; then
    echo "[+] Starting Docker stack (web + api)..."
    cd "$REPO_DIR"
    docker compose up -d web api 2>&1
    sleep 5

    # Verify containers are running
    if docker ps --format '{{.Names}}' | grep -q 'web'; then
        echo "[+] Nginx container running on :8080"
    else
        echo "[!] Nginx container failed — falling back to direct start"
        docker compose logs web 2>&1 | tail -10
    fi

    if docker ps --format '{{.Names}}' | grep -q 'api'; then
        echo "[+] Flask API container running on :5001"
    else
        echo "[!] API container failed — falling back to direct Flask"
    fi

    # Start tunnel if token is set
    if [[ -n "${CF_TUNNEL_TOKEN:-}" ]]; then
        echo "[+] Starting Cloudflare Tunnel..."
        docker compose --profile tunnel up -d tunnel 2>&1
        echo "[+] Tunnel active"
    fi

    # Start APK watchdog if token is set
    if [[ -n "${GH_APK_WATCHDOG_TOKEN:-}" ]]; then
        docker compose --profile apk up -d apk-watchdog 2>&1
        echo "[+] APK watchdog running"
    fi
else
    # ── Direct start (no Docker) ───────────────────────────────
    echo "[+] No Docker — running services directly..."

    # Nginx
    if command -v nginx &>/dev/null; then
        echo "[+] Nginx on :8080..."
        sudo service nginx restart > /dev/null 2>&1 || true
    fi

    # Flask API
    pkill -f "python.*app.py" 2>/dev/null || true
    sleep 1
    echo "[+] Flask API on :5001..."
    cd "$REPO_DIR/backend"
    pip install -q flask flask-cors flask-jwt-extended flask-sqlalchemy werkzeug 2>/dev/null
    nohup python3 app.py > /tmp/flask.log 2>&1 &
    sleep 2
fi

# ── Ollama (AI models) ─────────────────────────────────────────
if command -v ollama &>/dev/null; then
    if ! pgrep -x ollama > /dev/null; then
        echo "[+] Ollama on :11434..."
        nohup ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
    fi
    # Pull missing models in background
    (for m in tinyllama phi:2.7b qwen2.5:0.5b llama3.2:1b deepseek-coder:1.3b granite-code:3b; do
        ollama list 2>/dev/null | grep -q "${m%%:*}" || ollama pull "$m" >> /tmp/ollama.log 2>&1 || true
    done; echo "[+] Ollama models ready") &
fi

# ── Watchdog (auto-restart dead services) ───────────────────────
if ! pgrep -f "watchdog.sh" > /dev/null && [ -f "$REPO_DIR/watchdog.sh" ]; then
    echo "[+] Starting watchdog..."
    nohup bash "$REPO_DIR/watchdog.sh" > /tmp/watchdog.log 2>&1 &
fi

# ── Make ports PUBLIC ──────────────────────────────────────────
sleep 2
if command -v gh &>/dev/null && [ -n "${CODESPACE_NAME:-}" ]; then
    gh codespace ports visibility 8080:public 5001:public 5004:public 5005:public 11434:public \
        -c "$CODESPACE_NAME" 2>/dev/null && echo "[+] All ports set to PUBLIC" || true
fi

echo ""
echo "══════════════════════════════════════════════════"
echo " WhoamiSec — ONLINE"
echo " Web : https://${CODESPACE_NAME:-localhost}-8080.app.github.dev"
echo " API : https://${CODESPACE_NAME:-localhost}-5001.app.github.dev"
echo " Ollama: http://localhost:11434"
echo " Watchdog: /tmp/watchdog.log"
echo "══════════════════════════════════════════════════"
