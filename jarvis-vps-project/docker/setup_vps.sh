#!/bin/bash
# ============================================
# JARVIS VPS - FULL SETUP FROM SCRATCH
# 2700 Agents | Docker | XMR Mining | Cicada 3301
# ============================================

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🚀 JARVIS VPS - FULL DEPLOYMENT FROM SCRATCH              ║"
echo "║   2,700 ABLITERATED AGENTS | DOCKER | XMR MINING           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ---- Step 1: System Update ----
echo "📦 Step 1: System update..."
sudo apt-get update && sudo apt-get upgrade -y

# ---- Step 2: Install Docker ----
echo "🐳 Step 2: Install Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# ---- Step 3: Install Docker Compose ----
echo "📋 Step 3: Install Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt-get install -y docker-compose-plugin
fi

# ---- Step 4: Install Python Dependencies ----
echo "🐍 Step 4: Install Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# ---- Step 5: Install Build Tools (for XMRig) ----
echo "🔧 Step 5: Install build tools..."
sudo apt-get install -y git build-essential cmake libuv1-dev libssl-dev libhwloc-dev nginx certbot

# ---- Step 6: Create Network ----
echo "🌐 Step 6: Create Docker network..."
docker network create jarvis-net --subnet=172.20.0.0/16 2>/dev/null || true

# ---- Step 7: Install Ollama ----
echo "🤖 Step 7: Install Ollama AI..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi
nohup ollama serve > ollama.log 2>&1 &
sleep 5

# Pull AI models
echo "📥 Pulling AI models..."
ollama pull llama2 2>/dev/null || true
ollama pull llama3 2>/dev/null || true
ollama pull codellama 2>/dev/null || true
ollama pull mistral 2>/dev/null || true
ollama pull dolphin-mixtral 2>/dev/null || true
ollama pull glm4 2>/dev/null || true

# ---- Step 8: Setup Python Virtual Environment ----
echo "📦 Step 8: Setup Python venv..."
cd "$(dirname "$0")/.."
python3 -m venv venv
source venv/bin/activate

pip install flask flask-cors flask-limiter flask-socketio flask-jwt-extended
pip install python-dotenv prometheus-client requests redis PyJWT
pip install pillow numpy qrcode

# ---- Step 9: Create Data Directories ----
echo "📁 Step 9: Create directories..."
mkdir -p logs backups data ssl

# ---- Step 10: Setup .env ----
echo "⚙️ Step 10: Setup environment..."
if [ ! -f mining/.env ]; then
    cat > mining/.env << 'ENVEOF'
# MONERO CONFIG
XMR_ADDRESS="8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ"
XMR_PRICE=0.05
WALLET_NAME="boss_wallet"
WALLET_PASS="BossSuperParola123!"

# OLLAMA CONFIG
OLLAMA_HOST="localhost"
OLLAMA_PORT=11434
OLLAMA_MODEL="llama2"

# API CONFIG
API_PORT=5000
API_HOST="0.0.0.0"
API_SECRET_KEY="SuperSecretKeyChangeMe123!"
ADMIN_USERNAME="boss"
ADMIN_PASSWORD="WhoamiSecBoss2026!"

# RATE LIMITING
RATE_LIMIT_PER_IP="100 per minute"
RATE_LIMIT_PER_TXID="1000 per hour"

# AUTO-BAN CONFIG
MAX_FAILED_ATTEMPTS=10
BAN_DURATION_MINUTES=60

# MONITORING
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# LOGGING
LOG_LEVEL="INFO"
LOG_RETENTION_DAYS=7
ENABLE_AUDIT_LOG=true

# ANTI-DDOS
MAX_CONNECTIONS_PER_IP=10
REQUEST_TIMEOUT_SECONDS=30
MAX_BODY_SIZE_MB=10

# BACKUP
BACKUP_ENABLED=true
BACKUP_INTERVAL_HOURS=6
BACKUP_RETENTION_DAYS=30
ENVEOF
    chmod 600 mining/.env
fi

# ---- Step 11: Start Everything ----
echo "🚀 Step 11: Starting all services..."
docker-compose -f docker/docker-compose.yml up -d --build

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ✅ JARVIS VPS - ALL SERVICES ONLINE!                       ║"
echo "║                                                               ║"
echo "║   🌐 Websites:  http://localhost (Nginx)                     ║"
echo "║   🧠 Ollama:    http://localhost:11434                       ║"
echo "║   🔐 JARVIS:    http://localhost:5004                        ║"
echo "║   💰 Monero:    http://localhost:5000                        ║"
echo "║   📊 Subscribe: http://localhost:5005                        ║"
echo "║   🧩 Cicada:    http://localhost:5050                        ║"
echo "║   ⛏️ Mining:    http://localhost:8080                        ║"
echo "║   🤖 API:       http://localhost:5001                        ║"
echo "║   🖥️ WebUI:     http://localhost:8080                        ║"
echo "║                                                               ║"
echo "║   🔐 Admin: boss / WhoamiSecBoss2026!                        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
