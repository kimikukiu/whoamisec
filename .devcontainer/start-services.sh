#!/bin/bash
set -e
echo "[+] Restarting all WhoamiSec services..."

# Restart nginx
echo "[+] Restarting nginx..."
sudo service nginx restart > /dev/null 2>&1 || true

# Kill any existing Flask processes
pkill -f "python app.py" 2>/dev/null || true
sleep 1

# Start Flask backend
echo "[+] Starting Flask backend..."
cd /workspace/backend
nohup python app.py > /tmp/flask.log 2>&1 &
sleep 2

echo "[+] All services restarted successfully"
echo "[+] Nginx: http://localhost:8080"
echo "[+] Flask API: http://localhost:5001"
