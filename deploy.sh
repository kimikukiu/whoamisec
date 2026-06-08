#!/usr/bin/env bash
# ============================================================
# WhoamiSec — One-command deploy script
# Run on a fresh Ubuntu 22.04 VPS as root:
#   curl -sL https://raw.githubusercontent.com/kimikukiu/whoamisec/main/deploy.sh | bash
#   OR: git clone https://github.com/kimikukiu/whoamisec && cd whoamisec && bash deploy.sh
#
# Args:
#   --vps1   Deploy VPS-01 (whoamisec.com) — default
#   --vps2   Deploy VPS-02 (cicada.omni)
# ============================================================

set -euo pipefail
VPS_TYPE="${1:-}"

REPO_URL="https://github.com/kimikukiu/whoamisec"
WEB_DIR="/var/www/whoamisec"
APK_DIR="/var/apk"
CICADA_DIR="/var/www/cicada"

log() { echo -e "\e[1;36m[$(date '+%H:%M:%S')] $*\e[0m"; }
ok()  { echo -e "\e[1;32m  ✔ $*\e[0m"; }
err() { echo -e "\e[1;31m  ✗ $*\e[0m"; exit 1; }

log "WhoamiSec deploy script starting…"
[[ $EUID -ne 0 ]] && err "Run as root"

# ─── System packages ─────────────────────────────────────────
log "Installing system packages…"
apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx \
    python3 python3-pip git curl ufw fail2ban > /dev/null
ok "System packages installed"

# ─── Firewall ────────────────────────────────────────────────
log "Configuring firewall…"
ufw allow OpenSSH > /dev/null
ufw allow 'Nginx Full' > /dev/null
ufw --force enable > /dev/null
ok "UFW active (SSH + HTTP/HTTPS)"

# ─── Clone repo ──────────────────────────────────────────────
log "Cloning repository…"
if [[ -d /opt/whoamisec ]]; then
    cd /opt/whoamisec && git pull origin main
else
    git clone "$REPO_URL" /opt/whoamisec
fi
ok "Repo ready at /opt/whoamisec"

# ─── Python deps ─────────────────────────────────────────────
log "Installing Python dependencies…"
pip3 install -q flask flask-cors flask-jwt-extended flask-sqlalchemy werkzeug
ok "Python deps installed"

# ─── Ollama ──────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    log "Installing Ollama…"
    curl -fsSL https://ollama.ai/install.sh | sh
    ok "Ollama installed"
fi
log "Starting Ollama service…"
systemctl enable ollama 2>/dev/null || true
nohup ollama serve > /var/log/ollama.log 2>&1 &
sleep 3
# Pull small models in background
(
  for model in tinyllama phi:2.7b qwen2.5:0.5b llama3.2:1b deepseek-coder:1.3b granite-code:3b; do
      log "Pulling $model…"
      ollama pull "$model" 2>/dev/null || true
  done
  ok "All 6 Ollama models ready"
) &
ok "Ollama pulling models in background"

if [[ "$VPS_TYPE" == "--vps2" ]]; then
    # ── VPS-02: cicada.omni ───────────────────────────────────
    log "Deploying VPS-02 (cicada.omni)…"
    mkdir -p "$CICADA_DIR" "$APK_DIR"
    cp /opt/whoamisec/cicada.html "$CICADA_DIR/"
    cp /opt/whoamisec/nginx-vps02.conf /etc/nginx/sites-available/cicada.conf
    ln -sf /etc/nginx/sites-available/cicada.conf /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    ok "Nginx configured for cicada.omni"

    log "Starting Cicada API (port 5002)…"
    cp -r /opt/whoamisec/backend /opt/cicada-api
    cat > /etc/systemd/system/cicada-api.service <<EOF
[Unit]
Description=Cicada API
After=network.target
[Service]
WorkingDirectory=/opt/cicada-api
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5
Environment=SECRET_KEY=$(openssl rand -hex 32)
Environment=JWT_SECRET_KEY=$(openssl rand -hex 32)
Environment=PORT=5002
[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload && systemctl enable cicada-api && systemctl start cicada-api
    ok "Cicada API running on :5002"

    log "Obtaining SSL for cicada.omni…"
    log "→ Run manually: certbot --nginx -d cicada.omni -d apk.cicada.omni -d puzzle.cicada.omni"

    # APK watchdog
    if [[ -n "${GH_APK_WATCHDOG_TOKEN:-}" ]]; then
        cp /opt/whoamisec/apk-watchdog.sh /usr/local/bin/apk-watchdog
        chmod +x /usr/local/bin/apk-watchdog
        nohup APK_DIR="$APK_DIR" GH_APK_WATCHDOG_TOKEN="$GH_APK_WATCHDOG_TOKEN" \
            /usr/local/bin/apk-watchdog > /var/log/apk-watchdog.log 2>&1 &
        ok "APK watchdog running"
    else
        log "Set GH_APK_WATCHDOG_TOKEN to start APK watchdog"
    fi

else
    # ── VPS-01: whoamisec.com (default) ──────────────────────
    log "Deploying VPS-01 (whoamisec.com)…"
    mkdir -p "$WEB_DIR" "$APK_DIR"
    cp /opt/whoamisec/*.html /opt/whoamisec/*.js /opt/whoamisec/*.json \
       /opt/whoamisec/cicada-sound.mp3 "$WEB_DIR/" 2>/dev/null || true
    cp /opt/whoamisec/nginx-vps01.conf /etc/nginx/sites-available/whoamisec.conf
    ln -sf /etc/nginx/sites-available/whoamisec.conf /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    ok "Nginx configured — 8 virtual hosts"

    log "Starting WhoamiSec API (port 5001)…"
    cat > /etc/systemd/system/whoamisec-api.service <<EOF
[Unit]
Description=WhoamiSec API
After=network.target
[Service]
WorkingDirectory=/opt/whoamisec/backend
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5
Environment=SECRET_KEY=$(openssl rand -hex 32)
Environment=JWT_SECRET_KEY=$(openssl rand -hex 32)
[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload && systemctl enable whoamisec-api && systemctl start whoamisec-api
    ok "WhoamiSec API running on :5001"

    log "Obtaining SSL certificates…"
    log "→ Run manually after DNS is pointed:"
    log "   certbot --nginx -d whoamisec.com -d www.whoamisec.com \\"
    log "     -d api.whoamisec.com -d dashboard.whoamisec.com \\"
    log "     -d admin.whoamisec.com -d jarvis.whoamisec.com \\"
    log "     -d mining.whoamisec.com -d downloads.whoamisec.com \\"
    log "     -d apps.whoamisec.com"

    # APK watchdog
    if [[ -n "${GH_APK_WATCHDOG_TOKEN:-}" ]]; then
        cp /opt/whoamisec/apk-watchdog.sh /usr/local/bin/apk-watchdog
        chmod +x /usr/local/bin/apk-watchdog
        nohup APK_DIR="$APK_DIR" GH_APK_WATCHDOG_TOKEN="$GH_APK_WATCHDOG_TOKEN" \
            /usr/local/bin/apk-watchdog > /var/log/apk-watchdog.log 2>&1 &
        ok "APK watchdog running"
    fi
fi

# ─── Auto-restart watchdog ────────────────────────────────────
log "Setting up Ollama auto-restart watchdog…"
cat > /usr/local/bin/ollama-watchdog.sh <<'WATCHDOG'
#!/bin/bash
while true; do
    if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "[$(date)] Ollama down — restarting…"
        pkill ollama 2>/dev/null || true
        sleep 2
        nohup ollama serve >> /var/log/ollama.log 2>&1 &
        sleep 5
    fi
    sleep 30
done
WATCHDOG
chmod +x /usr/local/bin/ollama-watchdog.sh
cat > /etc/systemd/system/ollama-watchdog.service <<EOF
[Unit]
Description=Ollama auto-restart watchdog
After=network.target
[Service]
ExecStart=/usr/local/bin/ollama-watchdog.sh
Restart=always
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable ollama-watchdog && systemctl start ollama-watchdog
ok "Ollama watchdog active"

log ""
log "═══════════════════════════════════════════════"
ok "Deploy complete!"
log ""
log "NEXT STEPS:"
log "  1. Point DNS A records to this server's IP"
log "  2. Run certbot command shown above for SSL"
log "  3. Upload APKs to $APK_DIR/"
log "     (or set GH_APK_WATCHDOG_TOKEN for auto-download)"
log "  4. Check API: curl http://localhost:5001/api/v1/health"
log "═══════════════════════════════════════════════"
