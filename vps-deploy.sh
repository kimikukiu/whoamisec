#!/usr/bin/env bash
# WhoamiSec — Full VPS Deploy (Ubuntu from scratch)
# 256GB disk + 64GB RAM — Docker + MinIO S3 + Nginx + SSL
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${CYAN}[$(date '+%H:%M:%S')] $*${NC}"; }
ok()   { echo -e "${GREEN}  ✔ $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ $*${NC}"; }
err()  { echo -e "${RED}  ✖ $*${NC}"; }

VPS_IP=$(curl -fsSL https://ipv4.icanhazip.com 2>/dev/null || hostname -I | awk '{print $1}')
MINIO_DATA="/opt/minio-data"
MINIO_PASS="$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)Xmr!"
MINIO_USER="whoamisecadmin"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     WhoamiSec — Full VPS Deploy (Ubuntu)                 ║"
echo "║     Docker + MinIO S3 + Nginx + SSL + Fail2Ban          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log "VPS IP: $VPS_IP"

# Step 1: System
log "Step 1: System update..."
apt-get update -qq && apt-get upgrade -y -qq
apt-get install -y -qq curl wget gnupg lsb-release ca-certificates ufw fail2ban \
    certbot python3-certbot-nginx git htop tmux build-essential software-properties-common
ok "System updated"

# Step 2: Docker
if ! command -v docker &>/dev/null; then
    log "Step 2: Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker && systemctl start docker
    usermod -aG docker "$SUDO_USER" 2>/dev/null || true
    ok "Docker installed"
else ok "Step 2: Docker already installed: $(docker --version | head -1)"; fi

if ! docker compose version &>/dev/null 2>&1; then
    apt-get install -y -qq docker-compose-plugin; fi
ok "Docker Compose ready"

# Step 3: MinIO data dirs
log "Step 3: MinIO storage directories..."
mkdir -p "$MINIO_DATA"/data{1,2,3,4}
chown -R 1000:1000 "$MINIO_DATA"
ok "MinIO storage: $MINIO_DATA (4 volumes)"

# Step 4: Clone repo
DEPLOY_DIR="/opt/whoamisec"
if [ -d "$DEPLOY_DIR/.git" ]; then
    cd "$DEPLOY_DIR" && git pull origin main && ok "Repo updated"
elif [ -f "$(dirname "$0")/docker-compose.yml" ]; then
    DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)" && cd "$DEPLOY_DIR" && ok "Using local: $DEPLOY_DIR"
else
    git clone https://github.com/kimikukiu/whoamisec.git "$DEPLOY_DIR" && cd "$DEPLOY_DIR" && ok "Repo cloned"
fi

# Step 5: Environment
if [ ! -f ".env" ]; then
    cat > .env << ENVEOF
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
MINIO_ROOT_USER=$MINIO_USER
MINIO_ROOT_PASSWORD=$MINIO_PASS
GH_APK_WATCHDOG_TOKEN=
CF_TUNNEL_TOKEN=
ENVEOF
    ok ".env created (MinIO password: $MINIO_PASS)"
else ok "Step 5: .env exists"; fi

# Step 6: Firewall
log "Step 6: Firewall..."
ufw --force enable
ufw default deny incoming && ufw default allow outgoing
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw allow 9000/tcp && ufw allow 9001/tcp
ok "Firewall configured"

# Step 7: Fail2Ban
cat > /etc/fail2ban/jail.local << 'FBEOF'
[DEFAULT]
bantime=3600; findtime=600; maxretry=5
[sshd]
enabled=true; port=22; logpath=/var/log/auth.log; maxretry=3; bantime=86400
FBEOF
systemctl enable fail2ban && systemctl restart fail2ban
ok "Fail2Ban active"

# Step 8: Nginx
if ! command -v nginx &>/dev/null; then
    apt-get install -y -qq nginx && systemctl enable nginx; ok "Nginx installed"
else ok "Step 8: Nginx exists"; fi
if [ -f nginx-vps01.conf ]; then
    cp nginx-vps01.conf /etc/nginx/sites-available/whoamisec.conf
    ln -sf /etc/nginx/sites-available/whoamisec.conf /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && ok "Nginx config valid"
fi

# Step 9: Docker stack
log "Step 9: Starting Docker stack..."
docker compose down 2>/dev/null || true
docker compose build --no-cache
docker compose up -d web api minio
for i in $(seq 1 30); do
    docker compose exec -T minio mc ready local 2>/dev/null && { ok "MinIO healthy!"; break; }
    sleep 2
done

# Step 10: MinIO buckets
log "Step 10: Creating buckets..."
MC_BIN="/usr/local/bin/mc"
[ ! -f "$MC_BIN" ] && curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o "$MC_BIN" && chmod +x "$MC_BIN"
set -a; source .env; set +a
$MC_BIN alias set whoamisec http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
for B in apk-releases ipa-releases app-icons cicada-puzzles cicada-backups media backups logs databases user-uploads; do
    $MC_BIN mb "whoamisec/$B" --ignore-existing 2>/dev/null
    $MC_BIN version enable "whoamisec/$B" 2>/dev/null || true
done
for B in apk-releases ipa-releases app-icons cicada-puzzles media user-uploads; do
    $MC_BIN anonymous set download "whoamisec/$B" 2>/dev/null
done
ok "10 buckets created"

# Step 11: SSL
log "Step 11: SSL..."
if dig +short whoamisec.com 2>/dev/null | grep -q "$VPS_IP"; then
    certbot --nginx -d whoamisec.com -d www.whoamisec.com -d api.whoamisec.com \
        -d dashboard.whoamisec.com -d admin.whoamisec.com -d jarvis.whoamisec.com \
        -d mining.whoamisec.com -d downloads.whoamisec.com -d apps.whoamisec.com \
        -d s3.whoamisec.com -d storage.whoamisec.com \
        --non-interactive --agree-tos --email admin@whoamisec.com 2>/dev/null && ok "SSL installed!" || warn "SSL failed — run certbot --nginx manually"
else warn "whoamisec.com does not point to $VPS_IP — skip SSL"; fi

# Done
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
ok "WhoamiSec FULL VPS is LIVE!"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Website:       http://$VPS_IP:8080"
echo "  API:           http://$VPS_IP:5001"
echo "  MinIO S3:      http://$VPS_IP:9000"
echo "  MinIO Console: http://$VPS_IP:9001"
echo "  MinIO User:    $MINIO_USER"
echo "  MinIO Pass:    $MINIO_PASS"
echo ""
echo "  docker compose ps / docker compose logs -f / docker compose down"
