<p align="center">
  <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iMTAwIj48dGV4dCB4PSIxMCIgeT0iNzAiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iNjAiIGZpbGw9IiMwMGZmNDEiPldIT0FNSS5TRUM8L3RleHQ+PHRleHQgeD0iMTAiIHk9IjkwIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjEyIiBmaWxsPSIjMzM5OTU1Ij5KQVJWSVMgT01OSSBBQkxJVEVSQVRFRAwKPC90ZXh0Pjwvc3ZnPg==" alt="WHOAMI.SEC">
</p>

<h1 align="center">WHOAMI<span style="color:#ff0040">.SEC</span></h1>

<p align="center">
  <strong>Next-Gen AI Security Platform</strong><br>
  <em>JARVIS OMNI ABLITERATED</em>
</p>

<p align="center">
  <a href="#features">Features</a> &bull;
  <a href="#setup">Setup</a> &bull;
  <a href="#api">API</a> &bull;
  <a href="#monero">Monero</a>
</p>

---

## Features

| Feature | Description |
|---------|-------------|
| **VPS Creation** | Ephemeral VPS instances, Tor-routable, auto-burned |
| **Monero Payments** | Zero-KYC XMR payments, automated verification |
| **AI Agents** | Local LLMs: Llama 3.2, Phi, TinyLlama, DeepSeek-Coder |
| **Auto-Scale** | Dynamic resource allocation, GPU passthrough |
| **Zero-KYC** | No identity verification, anonymous JWT sessions |
| **JARVIS Core** | Multi-model AI orchestrator, self-healing infra |

## Setup

### Quick Start (Docker)

```bash
git clone https://github.com/kimikukiu/whoamisec.git
cd whoamisec
docker-compose up -d
```

### Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python app.py
# Server runs on http://0.0.0.0:5001
```

**Frontend:**
Serve the HTML files with any static server, or open `index.html` directly.

### Ollama (AI Backend)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama3.2:1b
ollama pull phi:2.7b
ollama pull tinyllama
ollama pull deepseek-coder:6.7b
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///whoamisec.db` | Database connection string |
| `SECRET_KEY` | `whoamisec-super-secret-2026` | Flask secret key |
| `JWT_SECRET_KEY` | `jwt-whoamisec-secret` | JWT signing key |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API URL |
| `XMR_WALLET_RPC` | `http://127.0.0.1:18083/json_rpc` | Monero wallet RPC |
| `XMR_WALLET_ADDRESS` | *(see env)* | Platform XMR deposit address |
| `XMR_CREDITS_PER_XMR` | `1000` | Credits awarded per XMR |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login, get JWT token |
| `GET` | `/api/auth/me` | Get current user info |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ai/chat` | Send message to AI model |
| `GET` | `/api/models` | List available models |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/payments/monero` | Get XMR deposit address |
| `GET` | `/api/payments/check` | Check for new payments |

### Admin (Requires admin JWT)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/users` | List all users |
| `PUT` | `/api/admin/user/<id>/credits` | Update user credits |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service health check |

## Example API Usage

```bash
# Register
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"secure123"}'

# Login
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"secure123"}'

# Chat with AI
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"message":"Write a Python hello world","model":"deepseek-coder:6.7b"}'
```

## Default Admin

- **Username:** `admin`
- **Password:** `WhoamiSecAdmin2026!`
- Auto-created on first startup

## Monero

Send XMR to fund your account:
```
46BeJeHmQQ6czjXH2vKSe8V7PbaEtfM3ekuJMFc9BBYhMZym43VWLqPhKYsVfkBB1Jc3RYpUK1jhCcxvFKMn3uTDQzmzDfk
```
- 1 XMR = 1,000 credits
- Payments are verified on-chain
- Zero-KYC, anonymous

## Tech Stack

- **Backend:** Python / Flask / SQLAlchemy / SQLite
- **Frontend:** HTML / CSS / Vanilla JS
- **AI:** Ollama (local LLM inference)
- **Auth:** JWT (flask-jwt-extended)
- **Payments:** Monero (XMR)
- **Deploy:** Docker / Nginx / GitHub Pages

## Credits

Powered by **JARVIS OMNI** — ABLITERATED MODE: ACTIVE

---

<p align="center">
  <code style="color:#ff0040">ABLITERATED MODE: ACTIVE</code>
</p>
