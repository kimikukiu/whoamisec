#!/usr/bin/env bash
# ============================================================
# APK Builder — wraps the web apps as native Android APKs
# Uses Capacitor (https://capacitorjs.com) — official Ionic tool
#
# Requirements (run once):
#   npm install -g @capacitor/cli
#   Install Android Studio + set ANDROID_HOME
#   Install JDK 17: apt install openjdk-17-jdk
#
# Usage:
#   bash build-apk.sh business   → WHOAMISEC-Business-v16.apk
#   bash build-apk.sh jarvis     → JARVIS-MIND-v3.apk
#   bash build-apk.sh all        → both APKs
# ============================================================

set -euo pipefail

TARGET="${1:-all}"
DIST_DIR="$(pwd)/apk-dist"
mkdir -p "$DIST_DIR"

log() { echo -e "\e[1;36m[$(date '+%H:%M:%S')] $*\e[0m"; }
ok()  { echo -e "\e[1;32m  ✔ $*\e[0m"; }
err() { echo -e "\e[1;31m  ✗ $*\e[0m"; exit 1; }

check_deps() {
    command -v node   &>/dev/null || err "node not found — install Node.js 18+"
    command -v npm    &>/dev/null || err "npm not found"
    command -v npx    &>/dev/null || err "npx not found"
    [[ -n "${ANDROID_HOME:-}" ]] || err "ANDROID_HOME not set — install Android Studio"
    ok "All dependencies found"
}

build_apk() {
    local name="$1"       # business | jarvis
    local html_src="$2"   # path to the HTML file
    local app_id="$3"     # com.whoamisec.business
    local app_name="$4"   # WHOAMISEC Business
    local version="$5"    # 16 | 3
    local out_apk="${DIST_DIR}/${app_name// /-}-v${version}.apk"

    local build_dir="/tmp/apk-build-${name}"
    rm -rf "$build_dir" && mkdir -p "$build_dir/www"

    log "Building $app_name (v$version)…"

    # Copy the web app HTML as the entry point
    cp "$html_src" "$build_dir/www/index.html"

    # Copy shared assets if they exist
    for f in manifest.json sw.js cicada-sound.mp3; do
        [[ -f "$(pwd)/$f" ]] && cp "$(pwd)/$f" "$build_dir/www/" || true
    done

    cd "$build_dir"

    # Create minimal package.json
    cat > package.json <<JSON
{
  "name": "$(echo "$app_name" | tr '[:upper:] ' '[:lower:]-')",
  "version": "1.${version}.0",
  "private": true,
  "dependencies": {
    "@capacitor/android": "^6.0.0",
    "@capacitor/core": "^6.0.0",
    "@capacitor/app": "^6.0.0",
    "@capacitor/status-bar": "^6.0.0"
  }
}
JSON

    npm install --silent

    # Init Capacitor
    npx cap init "$app_name" "$app_id" --web-dir www

    # capacitor.config.json
    cat > capacitor.config.json <<JSON
{
  "appId": "$app_id",
  "appName": "$app_name",
  "webDir": "www",
  "server": { "androidScheme": "https" },
  "android": {
    "allowMixedContent": true,
    "captureInput": true,
    "webContentsDebuggingEnabled": false
  }
}
JSON

    # Add Android platform
    npx cap add android

    # Add full Android permissions to manifest
    local manifest="android/app/src/main/AndroidManifest.xml"
    if [[ -f "$manifest" ]]; then
        sed -i 's|<uses-permission android:name="android.permission.INTERNET" />|<uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />\n    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n    <uses-permission android:name="android.permission.CAMERA" />\n    <uses-permission android:name="android.permission.READ_CONTACTS" />\n    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />\n    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />\n    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />\n    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29" />|' "$manifest"
    fi

    npx cap sync android

    # Set version in build.gradle
    local gradle="android/app/build.gradle"
    if [[ -f "$gradle" ]]; then
        sed -i "s/versionCode 1/versionCode $version/" "$gradle"
        sed -i "s/versionName \"1.0\"/versionName \"${version}.0\"/" "$gradle"
    fi

    # Build release APK
    cd android
    chmod +x gradlew
    ./gradlew assembleRelease --quiet 2>&1 | tail -5

    local built_apk
    built_apk=$(find . -name "*.apk" -path "*/release/*" | head -1)

    if [[ -z "$built_apk" ]]; then
        # Fallback: debug build
        ./gradlew assembleDebug --quiet 2>&1 | tail -5
        built_apk=$(find . -name "*.apk" | head -1)
    fi

    [[ -z "$built_apk" ]] && err "APK build failed for $app_name"
    cp "$built_apk" "$out_apk"
    ok "APK ready → $out_apk ($(du -sh "$out_apk" | cut -f1))"

    # Generate SHA256 checksum
    sha256sum "$out_apk" > "${out_apk}.sha256"
    ok "Checksum → ${out_apk}.sha256"

    cd "$OLDPWD"
}

check_deps

case "$TARGET" in
    business)
        build_apk "business" \
            "$(pwd)/whoamisec-business-app.html" \
            "com.whoamisec.business" \
            "WHOAMISEC Business" \
            "16"
        ;;
    jarvis)
        build_apk "jarvis" \
            "$(pwd)/jarvis-mind-app.html" \
            "com.whoamisec.jarvis" \
            "JARVIS MIND" \
            "31"
        ;;
    all)
        build_apk "business" \
            "$(pwd)/whoamisec-business-app.html" \
            "com.whoamisec.business" \
            "WHOAMISEC Business" \
            "16"
        build_apk "jarvis" \
            "$(pwd)/jarvis-mind-app.html" \
            "com.whoamisec.jarvis" \
            "JARVIS MIND" \
            "31"
        ;;
    *)
        err "Usage: $0 [business|jarvis|all]"
        ;;
esac

log ""
log "═══════════════════════════════════════════════"
ok "APK build complete!"
log "Output: $DIST_DIR"
ls -lh "$DIST_DIR"/*.apk 2>/dev/null || true
log ""
log "Upload to VPS-01:"
log "  scp $DIST_DIR/*.apk root@VPS-01-IP:/var/apk/"
log "Upload to VPS-02 (APK mirror):"
log "  scp $DIST_DIR/*.apk root@VPS-02-IP:/var/apk/"
log "═══════════════════════════════════════════════"
