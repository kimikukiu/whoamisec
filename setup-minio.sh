#!/usr/bin/env bash
# WhoamiSec — MinIO S3 Setup (standalone)
set -euo pipefail
CYAN='\033[0;36m'; GREEN='\033[0;32m'; NC='\033[0m'
log() { echo -e "${CYAN}[$(date '+%H:%M:%S')] $*${NC}"; }
ok()  { echo -e "${GREEN}  ✔ $*${NC}"; }

MINIO_USER="whoamisecadmin"
MINIO_PASS="$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)Xmr!"
MINIO_DATA="/opt/minio-data"
BUCKETS="apk-releases ipa-releases app-icons cicada-puzzles cicada-backups media backups logs databases user-uploads"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     MinIO S3 Storage Setup                                ║"
echo "╚══════════════════════════════════════════════════════════╝"

mkdir -p "$MINIO_DATA"/data{1,2,3,4}
chown -R 1000:1000 "$MINIO_DATA"
ok "Storage dirs: $MINIO_DATA"

if [ ! -f ".env" ]; then
    cat > .env << ENVEOF
MINIO_ROOT_USER=$MINIO_USER
MINIO_ROOT_PASSWORD=$MINIO_PASS
ENVEOF
    ok ".env created"
fi

docker compose up -d minio 2>&1
log "Waiting for MinIO..."
for i in $(seq 1 30); do
    docker compose exec -T minio mc ready local 2>/dev/null && { ok "MinIO healthy!"; break; }
    sleep 2
done

MC="/usr/local/bin/mc"
[ ! -f "$MC" ] && curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o "$MC" && chmod +x "$MC"
mc alias set whoamisec http://localhost:9000 "$MINIO_USER" "$MINIO_PASS"

for B in $BUCKETS; do
    mc mb "whoamisec/$B" --ignore-existing 2>/dev/null
    mc version enable "whoamisec/$B" 2>/dev/null || true
    ok "Bucket: $B"
done
for B in apk-releases ipa-releases app-icons cicada-puzzles media user-uploads; do
    mc anonymous set download "whoamisec/$B" 2>/dev/null
done
ok "Public download enabled"

echo ""
echo "  S3 API:  http://localhost:9000"
echo "  Console: http://localhost:9001"
echo "  User:    $MINIO_USER"
echo "  Pass:    $MINIO_PASS"
