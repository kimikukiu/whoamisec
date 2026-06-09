#!/usr/bin/env bash
# WhoamiSec — S3 Storage Helper (uses curl, no Docker needed)
set -euo pipefail
CYAN='\033[0;36m'; GREEN='\033[0;32m'; NC='\033[0m'
log() { echo -e "${CYAN}[$(date '+%H:%M:%S')] $*${NC}"; }
ok()  { echo -e "${GREEN}  ✔ $*${NC}"; }

S3="${S3_ENDPOINT:-http://localhost:9000}"
BUCKETS=(apk-releases ipa-releases app-icons cicada-puzzles cicada-backups media backups logs databases user-uploads)

cmd_upload() {
    local BUCKET="$1" FILE="$2" FNAME=$(basename "$2")
    [ ! -f "$FILE" ] && echo "File not found: $FILE" && exit 1
    local SIZE=$(wc -c < "$FILE")
    log "Uploading $FNAME ($SIZE bytes) → s3://$BUCKET/"
    curl -s -X PUT --data-binary @"$FILE" "$S3/$BUCKET/$FNAME" -o /dev/null -w "  HTTP %{http_code}\n"
    ok "s3://$BUCKET/$FNAME"
}

cmd_download() {
    local BUCKET="$1" NAME="$2" DEST="${3:-./$2}"
    log "Downloading s3://$BUCKET/$NAME → $DEST"
    curl -s "$S3/$BUCKET/$NAME" -o "$DEST" -w "  HTTP %{http_code}, %{size_download} bytes\n"
}

cmd_list() {
    local BUCKET="${1:-}"
    if [ -z "$BUCKET" ]; then
        log "All buckets:"
        for B in "${BUCKETS[@]}"; do echo "  📦 $B"; done
    else
        log "Bucket: $BUCKET"
        curl -s "$S3/$BUCKET/" | head -20
    fi
}

cmd_status() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "  WhoamiSec S3 Storage"
    echo "╚════════════════════════════════════════╝"
    echo "  Endpoint: $S3"
    echo "  Health:   $(curl -s "$S3/minio/health/live" 2>/dev/null || echo 'offline')"
    echo ""
}

case "${1:-help}" in
    upload)   cmd_upload "$2" "$3" ;;
    download) cmd_download "$2" "$3" "${4:-}" ;;
    list)     cmd_list "${2:-}" ;;
    status)   cmd_status ;;
    help|*)   echo "Usage: $0 {upload|download|list|status} [args...]"; echo "  upload <bucket> <file>"; echo "  download <bucket> <name> [dest]"; echo "  list [bucket]"; echo "  status" ;;
esac
