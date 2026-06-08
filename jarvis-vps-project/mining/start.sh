#!/bin/bash

cd ~/ollama-monero-biz

echo "🚀 Pornesc OLLAMA..."
nohup ollama serve > ollama.log 2>&1 &
sleep 3

echo "🤖 Pornesc MONERO WATCHDOG..."
nohup ./check_payments.sh > watchdog.log 2>&1 &

echo "💰 Pornesc API MONETIZARE..."
nohup python3 api_monero.py > api.log 2>&1 &

echo "✅ TOATE SERVICIILE SUNT ONLINE!"
echo ""
echo "📊 Verifică serviciile:"
echo "   ps aux | grep -E 'ollama|check_payments|api_monero'"
echo ""
echo "🔗 Endpoint-uri:"
echo "   GET  /price  - preț și adresă plată"
echo "   POST /ask    - întreabă AI-ul (necesită txid)"
echo "   GET  /health - health check"
echo "   GET  /stats  - statistici"
echo ""
echo "🏦 Adresa XMR: $(grep XMR_ADDRESS .env | cut -d'=' -f2)"
