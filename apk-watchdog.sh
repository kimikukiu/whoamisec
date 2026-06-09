#!/usr/bin/env bash
# APK Watchdog — monitors GitHub repo for new APK releases and deploys them
# Requires env var: GH_APK_WATCHDOG_TOKEN
# Usage: ./apk-watchdog.sh [--once]
# To run continuously in Codespace: nohup ./apk-watchdog.sh > apk-watchdog.log 2>&1 &

set -euo pipefail

REPO="whoamisecai/whoamisec"
APK_DIR="${APK_DIR:-/var/www/apk}"
CHECK_INTERVAL=300   # seconds between polls (5 min)
STATE_FILE="/tmp/.apk_watchdog_state"
TOKEN="${GH_APK_WATCHDOG_TOKEN:-}"

# ─── Validation ─────────────────────────────────────────────────────────────
if [[ -z "$TOKEN" ]]; then
    echo "[ERROR] GH_APK_WATCHDOG_TOKEN is not set."
    echo "  → Add it as a Codespace secret:"
    echo "     github.com → Settings → Codespaces → Secrets → New"
    echo "     Name: GH_APK_WATCHDOG_TOKEN"
    exit 1
fi

mkdir -p "$APK_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ─── GitHub API helpers ──────────────────────────────────────────────────────
gh_api() {
    curl -fsSL \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "https://api.github.com/$1"
}

get_latest_release_tag() {
    gh_api "repos/$REPO/releases/latest" 2>/dev/null \
        | grep '"tag_name"' | head -1 \
        | sed 's/.*"tag_name": *"\([^"]*\)".*/\1/'
}

get_release_assets() {
    local tag="$1"
    gh_api "repos/$REPO/releases/tags/$tag" 2>/dev/null \
        | grep '"browser_download_url"' \
        | sed 's/.*"browser_download_url": *"\([^"]*\)".*/\1/'
}

download_asset() {
    local url="$1"
    local dest="$APK_DIR/$(basename "$url")"
    log "Downloading $(basename "$url") …"
    curl -fsSL \
        -H "Authorization: Bearer $TOKEN" \
        -L "$url" -o "$dest"
    log "Saved → $dest"
}

check_commits_for_apk() {
    # Fallback: scan latest commit messages for APK build triggers
    gh_api "repos/$REPO/commits?per_page=5" 2>/dev/null \
        | grep '"message"' | head -5 \
        | grep -i '\(apk\|release\|build\|v[0-9]\)' || true
}

# ─── Main watch loop ─────────────────────────────────────────────────────────
log "APK Watchdog started — repo: $REPO"
log "APK output dir: $APK_DIR"
log "Poll interval: ${CHECK_INTERVAL}s"
log "Token: ${TOKEN:0:8}… (truncated)"

ONE_SHOT="${1:-}"

while true; do
    log "Checking for new APK release…"

    latest_tag=$(get_latest_release_tag)

    if [[ -z "$latest_tag" ]]; then
        log "No releases found — checking commits for APK build signals…"
        check_commits_for_apk | while read -r msg; do
            log "  commit: $msg"
        done
    else
        prev_tag=$(cat "$STATE_FILE" 2>/dev/null || echo "")

        if [[ "$latest_tag" != "$prev_tag" ]]; then
            log "New release detected: $latest_tag (was: ${prev_tag:-none})"

            assets=$(get_release_assets "$latest_tag")
            if [[ -z "$assets" ]]; then
                log "  No downloadable assets in this release."
            else
                echo "$assets" | while read -r url; do
                    case "$url" in
                        *.apk|*.APK)
                            download_asset "$url"
                            ;;
                        *.sha256|*.md5)
                            download_asset "$url"
                            ;;
                        *)
                            log "  Skipping non-APK asset: $(basename "$url")"
                            ;;
                    esac
                done
                log "Release $latest_tag deployed to $APK_DIR"
            fi

            echo "$latest_tag" > "$STATE_FILE"
        else
            log "No new release. Current: $latest_tag"
        fi
    fi

    # Show what's currently in APK_DIR
    if [[ -d "$APK_DIR" ]] && ls "$APK_DIR"/*.apk "$APK_DIR"/*.APK 2>/dev/null | head -1; then
        log "APKs available:"
        ls -lh "$APK_DIR"/*.apk "$APK_DIR"/*.APK 2>/dev/null | awk '{print "  "$NF" ("$5")"}'
    fi

    [[ "$ONE_SHOT" == "--once" ]] && break

    log "Next check in ${CHECK_INTERVAL}s (Ctrl+C to stop)"
    sleep "$CHECK_INTERVAL"
done
