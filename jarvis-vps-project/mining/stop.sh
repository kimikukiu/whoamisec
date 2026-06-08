#!/bin/bash

echo "🛑 Oprește toate serviciile..."

pkill -f "ollama serve"
pkill -f "check_payments.sh"
pkill -f "api_monero.py"

echo "✅ Toate serviciile oprite"
