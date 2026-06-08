#!/bin/bash
set -e
echo "=========================================="
echo "[+] WhoamiSec VPS Setup Script"
echo "=========================================="

# Install nginx
echo "[+] Installing nginx..."
sudo apt-get update -qq
sudo apt-get install -y -qq nginx > /dev/null 2>&1

# Install Python dependencies
echo "[+] Installing Python dependencies..."
cd /workspace/backend
pip install -r requirements.txt > /dev/null 2>&1

# Copy nginx config
echo "[+] Configuring nginx..."
sudo cp /workspace/nginx.conf /etc/nginx/sites-available/whoamisec
sudo ln -sf /etc/nginx/sites-available/whoamisec /etc/nginx/sites-enabled/whoamisec
sudo rm -f /etc/nginx/sites-enabled/default

# Install SSH key
echo "[+] Installing SSH authorized key..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINRX1gVu9BdTeTOYmJq+FRgGtvQys6RS29rG7D57OYBq" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Start services
echo "[+] Starting nginx..."
sudo nginx -t > /dev/null 2>&1
sudo service nginx restart > /dev/null 2>&1

echo "[+] Starting Flask backend..."
cd /workspace/backend
nohup python app.py > /tmp/flask.log 2>&1 &
sleep 2

echo "=========================================="
echo "[+] Setup complete!"
echo "[+] Nginx: http://localhost:8080"
echo "[+] Flask API: http://localhost:5001"
echo "[+] SSH: port 22"
echo "[+] Pages: /index.html, /mining.html, /jarvis.html, /login.html, /dashboard.html, /admin.html"
echo "=========================================="
