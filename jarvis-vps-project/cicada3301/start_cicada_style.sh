#!/bin/bash
# CICADA 3301 Style - Startup Script
pkill -f cicada_3301_style 2>/dev/null
cd /opt
mkdir -p /var/lib/jarvis
nohup python3 /opt/cicada_3301_style.py > /var/log/cicada_3301.log 2>&1 &
echo "CICADA 3301 started on port 5060"
