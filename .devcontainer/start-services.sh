#!/bin/bash
set -e
echo "[+] Starting WhoamiSec services..."

# ── Nginx ────────────────────────────────────────────────────
echo "[+] Nginx on :8080..."
sudo service nginx restart > /dev/null 2>&1 || true

# ── Flask API ────────────────────────────────────────────────
pkill -f "python app.py" 2>/dev/null || true
sleep 1
echo "[+] Flask API on :5001..."
cd /workspace/backend
nohup python app.py > /tmp/flask.log 2>&1 &
sleep 2

# ── Ollama (AI models — auto-restart watchdog) ───────────────
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

# ── Make ports PUBLIC (no GitHub auth required) ──────────────
sleep 2
if command -v gh &>/dev/null && [ -n "${CODESPACE_NAME:-}" ]; then
    gh codespace ports visibility 8080:public 5001:public 5004:public 5005:public \
        -c "$CODESPACE_NAME" 2>/dev/null && echo "[+] Ports set to PUBLIC" || true
fi

echo ""
echo "══════════════════════════════════════════════"
echo " WhoamiSec — ONLINE"
echo " Web : https://${CODESPACE_NAME:-localhost}-8080.app.github.dev"
echo " API : https://${CODESPACE_NAME:-localhost}-5001.app.github.dev"
echo "══════════════════════════════════════════════"
