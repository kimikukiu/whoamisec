#!/bin/bash
# ==============================================================================
# setup_miner_vps.sh - JARVIS VPS Creation & XMRig Installation
# Extracted from whoamisecxmrbot.txt
# ==============================================================================

set -e

CONTAINER_NAME="miner-fleet-vps"
NETWORK="jarvis-net"
IP_ADDR="172.20.0.200"
IMAGE="ubuntu:22.04"
XMRIG_REPO="https://github.com/xmrig/xmrig.git"
CONFIG_FILE="/opt/xmrig/build/config.json"

# ---- Step 1: Create Docker container for mining VPS ----
echo "[*] Creating Docker container: $CONTAINER_NAME..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --network "$NETWORK" \
  --ip "$IP_ADDR" \
  --restart always \
  -p 8080:80 \
  -p 8443:443 \
  -v miner-data:/var/lib/xmrig \
  "$IMAGE" \
  sleep infinity

# ---- Step 2: Install dependencies inside the container ----
echo "[*] Installing dependencies..."
docker exec "$CONTAINER_NAME" bash -c "
apt update && apt install -y nginx certbot python3 python3-pip git build-essential cmake libuv1-dev libssl-dev libhwloc-dev
"

# ---- Step 3: Clone and build XMRig ----
echo "[*] Cloning and building XMRig..."
docker exec "$CONTAINER_NAME" bash -c "
cd /opt
git clone $XMRIG_REPO
cd xmrig
mkdir build && cd build
cmake ..
make -j\$(nproc)
"

# ---- Step 4: Deploy XMRig config ----
echo "[*] Deploying XMRig configuration..."
docker exec "$CONTAINER_NAME" bash -c "
cat > $CONFIG_FILE << 'XMRIG_EOF'
{
    \"api\": {
        \"id\": null,
        \"worker-id\": null,
        \"ipv6\": false,
        \"port\": 8081
    },
    \"http\": {
        \"enabled\": true,
        \"host\": \"0.0.0.0\",
        \"port\": 8081,
        \"access-token\": null,
        \"restricted\": true
    },
    \"autosave\": true,
    \"background\": false,
    \"colors\": true,
    \"title\": true,
    \"randomx\": {
        \"init\": -1,
        \"init-avx2\": -1,
        \"mode\": \"auto\",
        \"1gb-pages\": false,
        \"rdmsr\": true,
        \"wrmsr\": true,
        \"cache_qos\": false,
        \"numa\": true,
        \"scratchpad_prefetch_mode\": 1
    },
    \"cpu\": {
        \"enabled\": true,
        \"huge-pages\": true,
        \"huge-pages-jit\": false,
        \"hw-aes\": null,
        \"priority\": null,
        \"memory-pool\": false,
        \"yield\": true,
        \"max-threads-hint\": 100,
        \"asm\": true,
        \"argon2-impl\": null,
        \"cn/0\": false,
        \"cn-lite/0\": false
    },
    \"pools\": [
        {
            \"algo\": null,
            \"coin\": \"monero\",
            \"url\": \"pool.supportxmr.com:3333\",
            \"user\": \"8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ\",
            \"pass\": \"miner-fleet-node\",
            \"rig-id\": null,
            \"nicehash\": false,
            \"keepalive\": false,
            \"enabled\": true,
            \"tls\": false,
            \"tls-fingerprint\": null,
            \"daemon\": false,
            \"socks5\": null,
            \"self-select\": null,
            \"submit-to-origin\": false
        }
    ],
    \"print-time\": 60,
    \"health-print-time\": 60,
    \"dmi\": true,
    \"retries\": 5,
    \"retry-pause\": 5,
    \"syslog\": false,
    \"tls\": {
        \"enabled\": false,
        \"protocols\": null,
        \"cert\": null,
        \"cert_key\": null,
        \"ciphers\": null,
        \"ciphersuites\": null,
        \"dhparam\": null
    },
    \"user-agent\": null,
    \"verbose\": 0,
    \"watch\": true,
    \"pause-on-battery\": false,
    \"pause-on-active\": false
}
XMRIG_EOF
"

# ---- Step 5: Start XMRig miner in background ----
echo "[*] Starting XMRig miner..."
docker exec "$CONTAINER_NAME" bash -c "
nohup ./xmrig --config=$CONFIG_FILE > /var/log/xmrig.log 2>&1 &
"

# ---- Step 6: Enable and start nginx ----
echo "[*] Starting nginx..."
docker exec "$CONTAINER_NAME" bash -c "
systemctl enable nginx
systemctl start nginx
"

# ---- Done ----
echo ""
echo "=== MINER_FLEET VPS SETUP COMPLETE ==="
echo "Container : $CONTAINER_NAME"
echo "Network   : $NETWORK ($IP_ADDR)"
echo "HTTP      : http://localhost:8080"
echo "HTTPS     : https://localhost:8443"
echo "XMRig API : http://localhost:8081"
echo "===================================="
