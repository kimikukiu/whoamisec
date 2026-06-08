# ============================================
# JARVIS VPS PROJECT - MASTER README
# WHOAMISEC | JARVIS OMNI ABLITERATED
# 2,700 Agents | Docker | XMR Mining | Cicada 3301
# ============================================

## 🏗️ PROJECT STRUCTURE

```
jarvis-vps-project/
├── docker/
│   ├── docker-compose.yml          # Main Docker Compose (all services)
│   ├── Dockerfile.nginx            # Nginx reverse proxy
│   ├── setup_vps.sh                # Full VPS setup from scratch
│   ├── deploy_100_nodes.sh         # Deploy 100 XMR mining nodes
│   ├── setup_miner_vps.sh          # Miner VPS setup
│   └── nginx/
│       └── jarvis.conf             # Nginx vhost config
│
├── backend/
│   ├── Dockerfile                  # Python backend Dockerfile
│   ├── app.py                      # Main Flask API (JWT auth, XMR wallet)
│   ├── jarvis_mind_secure.py       # JARVIS MIND - Admin VPS Control (Port 5004)
│   ├── jarvis_subscription_system.py # Subscription/monetization system (Port 5005)
│   └── requirements.txt
│
├── mining/
│   ├── Dockerfile                  # Mining Dockerfile
│   ├── Dockerfile.miner            # XMRig miner Dockerfile
│   ├── xmrig_config.json           # XMRig miner configuration
│   ├── api_monero.py               # Basic Monero payment API
│   ├── api_enterprise.py           # Enterprise API (rate limit, anti-DDoS, auto-ban)
│   ├── check_payments.sh           # Monero payment watchdog
│   ├── start.sh                    # Start all mining services
│   ├── stop.sh                     # Stop all mining services
│   ├── backup.sh                   # Backup whitelist + .env
│   ├── satgate.yaml                # Satgate pricing config
│   ├── miner_index.html            # Mining fleet frontend (100 nodes)
│   ├── miner_admin_panel.html      # Mining admin panel
│   ├── telegram_miner_bot.py       # Telegram bot for mining notifications
│   └── requirements.txt
│
├── cicada3301/
│   ├── Dockerfile                  # Cicada Dockerfile
│   ├── cicada_puzzle_system.py     # Basic puzzle platform (6 levels)
│   ├── cicada_ultimate.py          # Ultimate system (8 levels, leaderboard, NFTs)
│   └── requirements.txt
│
├── agents/                         # Agent configuration (2,700 agents)
├── frontend/                       # Static HTML files (served by Nginx)
│   ├── index.html                  # Landing page
│   ├── login.html                  # SaaS login
│   ├── dashboard.html              # AI chat dashboard
│   ├── admin.html                  # Admin panel
│   ├── jarvis.html                 # JARVIS MIND VPS control
│   ├── mining.html                 # Mining fleet page
│   └── cicada.html                 # Cicada 3301 page
│
├── nginx/
├── ssl/
├── logs/
├── backups/
├── data/
│
├── DEPLOY.md                       # Deployment instructions
└── README.md                       # This file
```

## 🚀 QUICK START

### Option 1: Full VPS Setup (Recommended)
```bash
cd docker
chmod +x setup_vps.sh
sudo ./setup_vps.sh
```

### Option 2: Docker Compose Only
```bash
cd docker
docker-compose up -d --build
```

### Option 3: Manual Services
```bash
# Ollama (AI Models)
nohup ollama serve > ollama.log 2>&1 &
ollama pull llama2 && ollama pull llama3

# JARVIS MIND (Admin VPS Control)
python3 backend/jarvis_mind_secure.py

# Monero Enterprise API
python3 mining/api_enterprise.py

# Cicada 3301 Puzzle System
python3 cicada3301/cicada_ultimate.py

# Subscription System
python3 backend/jarvis_subscription_system.py
```

## 🔗 SERVICE PORTS

| Service | Port | Description |
|---------|------|-------------|
| Nginx | 80/443 | Reverse proxy + static files |
| Ollama | 11434 | AI models API |
| JARVIS MIND | 5004 | Admin VPS control |
| Monero API | 5000 | Enterprise payment API |
| Subscription | 5005 | User subscription system |
| Cicada 3301 | 5050 | Puzzle platform |
| Backend API | 5001 | Main Flask API |
| Mining Fleet | 8080 | XMR mining dashboard |
| XMRig API | 8081 | Miner statistics |
| Redis | 6379 | Rate limiting cache |

## 🔐 CREDENTIALS

- **Admin**: boss / WhoamiSecBoss2026!
- **Monero Address**: 8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ
- **Telegram**: @proplanwh

## ⛏️ MINING

- **Pool**: pool.supportxmr.com:3333
- **Nodes**: 100 Docker containers
- **Platform Fee**: 35%
- **XMRig Config**: mining/xmrig_config.json

## 🧩 CICADA 3301

- **8 Puzzle Levels**: Beginner → Mythic
- **Rewards**: 0.01 - 2.50 XMR
- **Features**: Leaderboard, NFTs, Achievements, Tournaments

## 💰 MONETIZATION

- 6 Subscription Plans (Free → Supreme)
- Credit-based system
- Monero payments only
- Rate limiting + auto-ban protection

## 📱 APK

- WHOAMISEC-Business-v16.apk (5 tabs)
- JARVIS-MIND-v3.apk (6 tabs)
- Download: https://github.com/kimikukiu/whoamisec/releases/tag/v16.0

## 🤖 AI MODELS (Ollama)

- llama2, llama3, codellama, mistral, dolphin-mixtral, glm4

---
Created by JARVIS OMNI ABLITERATED | WHOAMISEC
