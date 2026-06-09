#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WHOAMISecAI JARVIS — Android APK Build Script
# ═══════════════════════════════════════════════════════════════
#
# Prerequisites:
#   1. JDK 17+ (recommended: Eclipse Temurin JDK 21)
#   2. Android SDK with:
#      - platforms;android-34
#      - build-tools;34.0.0
#      - platform-tools
#
# Quick setup (Ubuntu/Debian):
#   sudo apt install openjdk-21-jdk-headless unzip
#   wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
#   unzip commandlinetools-linux-11076708_latest.zip -d $HOME/android-sdk/cmdline-tools
#   yes | $HOME/android-sdk/cmdline-tools/latest/bin/sdkmanager "platforms;android-34" "build-tools;34.0.0"
#
# Usage:
#   chmod +x build-apk.sh
#   ./build-apk.sh          # Build release APKs
#   ./build-apk.sh debug    # Build debug APKs
#
# Output: app/build/outputs/apk/release/ (or debug/)
#   - app-arm64-v8a-release.apk    (ARM 64-bit — modern phones)
#   - app-armeabi-v7a-release.apk  (ARM 32-bit — older phones)
#   - app-armeabi-release.apk      (ARM legacy — very old phones)
#   - app-universal-release.apk    (Universal FAT — all architectures)
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Environment ──
if [ -z "$JAVA_HOME" ]; then
    if [ -d "/usr/lib/jvm/java-21-openjdk-amd64" ]; then
        export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
    elif [ -d "$HOME/jdk21" ]; then
        export JAVA_HOME=$HOME/jdk21
    else
        echo "ERROR: JAVA_HOME not set. Install JDK 21 first."
        exit 1
    fi
fi

if [ -z "$ANDROID_HOME" ]; then
    if [ -d "$HOME/Android/Sdk" ]; then
        export ANDROID_HOME=$HOME/Android/Sdk
    elif [ -d "$HOME/android-sdk" ]; then
        export ANDROID_HOME=$HOME/android-sdk
    else
        echo "ERROR: ANDROID_HOME not set. Install Android SDK first."
        exit 1
    fi
fi

export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/build-tools/34.0.0:$PATH"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  WHOAMISecAI JARVIS — Android APK Builder           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "JAVA_HOME: $JAVA_HOME"
echo "ANDROID_HOME: $ANDROID_HOME"
echo "Java: $(java -version 2>&1 | head -1)"
echo "Build variant: ${1:-release}"
echo ""

# ── Verify ──
command -v javac >/dev/null 2>&1 || { echo "ERROR: javac not found. Need full JDK, not JRE."; exit 1; }
[ -f "$ANDROID_HOME/platforms/android-34/android.jar" ] || { echo "ERROR: platforms;android-34 not found."; exit 1; }
[ -f "$ANDROID_HOME/build-tools/34.0.0/aapt2" ] || { echo "ERROR: build-tools;34.0.0 not found."; exit 1; }

cd "$SCRIPT_DIR"

# ── Build ──
echo "► Downloading dependencies & building..."
if [ "$1" = "debug" ]; then
    ./gradlew assembleDebug --no-daemon --stacktrace
    echo ""
    echo "✅ Debug APKs built!"
    echo "Output: app/build/outputs/apk/debug/"
    ls -lh app/build/outputs/apk/debug/*.apk 2>/dev/null
else
    ./gradlew assembleRelease --no-daemon --stacktrace
    echo ""
    echo "✅ Release APKs built!"
    echo "Output: app/build/outputs/apk/release/"
    ls -lh app/build/outputs/apk/release/*.apk 2>/dev/null
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Build complete! APKs ready for distribution.        ║"
echo "║  Copy to download/ for web serving.                  ║"
echo "╚══════════════════════════════════════════════════════╝"
