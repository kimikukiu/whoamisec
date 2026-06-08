# WhoamiSec

**Privacy-first AI Infrastructure.** Run powerful open-source models through a scalable API. Zero KYC. Pay with Monero.

**Live at:** [whoamisec.com](https://whoamisec.com)

---

## Features

- **6 AI Models** — LLaMA, Phi, Qwen, DeepSeek, Granite — all running on isolated infrastructure
- **Zero-KYC Payments** — Monero (XMR) only. No identity verification required
- **OpenAI-Compatible API** — Drop-in replacement for OpenAI endpoints
- **Open WebUI** — Built-in ChatGPT-like interface
- **Self-Healing Infrastructure** — Watchdog monitoring, auto-restart, 99.9% uptime
- **Enterprise Security** — Rate limiting, auto-ban, audit logging, anti-DDoS

## Quick Start

### 1. Create Account

```bash
curl -X POST https://whoamisec.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","email":"my@email.com","password":"securepass123"}'
```

### 2. Query AI Models

```bash
curl -X POST https://whoamisec.com/api/v1/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:1b","messages":[{"role":"user","content":"Hello!"}]}'
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Get user info |
| POST | `/api/v1/chat` | Chat with AI |
| GET | `/api/v1/models` | List models |
| GET | `/api/v1/payments/info` | Payment info |
| POST | `/api/v1/payments/verify` | Verify XMR payment |
| GET | `/api/v1/health` | System health |

## Available Models

| Model | Size | Speed |
|-------|------|-------|
| TinyLlama 1.1B | 650MB | Fast |
| Phi-2.7B | 1.6GB | Medium |
| Qwen 2.5 0.5B | 350MB | Fast |
| Llama 3.2 1B | 1.3GB | Medium |
| DeepSeek Coder 1.3B | 750MB | Medium |
| Granite Code 3B | 2.0GB | Slow |

## Pricing

| Plan | Price | Requests/Day | Models |
|------|-------|-------------|--------|
| Starter | Free | 100 | 1 |
| Pro | 0.05 XMR/month | 10,000 | All 6 |
| Enterprise | 0.15 XMR/month | Unlimited | All + Custom |

## Monero Payment

Send XMR to:
```
8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ
```

Then verify your payment via the API with your transaction ID.

## Deploy with Docker

```bash
docker compose up -d
```

## Tech Stack

- **Backend:** Flask + SQLAlchemy + JWT
- **AI:** Ollama (6 models)
- **Payments:** Monero (XMR)
- **Frontend:** HTML/CSS/JS
- **Proxy:** Nginx
- **Infrastructure:** Docker

---

*WhoamiSec.com — Privacy-first AI infrastructure. Built by JARVIS OMNI.*
