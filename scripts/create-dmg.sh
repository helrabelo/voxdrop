#!/bin/bash
# Create DMG for DropVox distribution
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

APP_NAME="DropVox"
VERSION=$(grep 'version = ' pyproject.toml | head -1 | cut -d'"' -f2)
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
VOL_NAME="$APP_NAME"

# Window and icon settings
WINDOW_WIDTH=500
WINDOW_HEIGHT=350
ICON_SIZE=100
APP_X=130
APP_Y=150
APPS_X=370
APPS_Y=150

echo "=============================================="
echo "Creating DMG for $APP_NAME v$VERSION"
echo "=============================================="

# Check prerequisites
if [ ! -d "dist/DropVox.app" ]; then
    echo "Error: dist/DropVox.app not found."
    echo "Run ./scripts/build.sh first."
    exit 1
fi

# Clean up any previous attempts
echo "==> Cleaning up..."
rm -f "dist/$DMG_NAME" "dist/${APP_NAME}_temp.dmg"

# Unmount any existing volume with same name
if [ -d "/Volumes/$VOL_NAME" ]; then
    hdiutil detach "/Volumes/$VOL_NAME" -force 2>/dev/null || true
    sleep 1
fi

# Create temporary directory for DMG contents
DMG_TEMP="dist/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

echo "==> Copying app bundle..."
cp -R "dist/DropVox.app" "$DMG_TEMP/"

echo "==> Creating Applications symlink..."
ln -s /Applications "$DMG_TEMP/Applications"

# Calculate DMG size (app size + 50MB buffer)
APP_SIZE=$(du -sm "dist/DropVox.app" | cut -f1)
DMG_SIZE=$((APP_SIZE + 50))

echo "==> Creating writable DMG (${DMG_SIZE}MB)..."
hdiutil create -srcfolder "$DMG_TEMP" -volname "$VOL_NAME" -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${DMG_SIZE}m \
    "dist/${APP_NAME}_temp.dmg"

rm -rf "$DMG_TEMP"

# Mount the DMG
echo "==> Mounting DMG..."
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "dist/${APP_NAME}_temp.dmg" | \
    egrep '^/dev/' | sed 1q | awk '{print $1}')
MOUNT_POINT="/Volumes/$VOL_NAME"

if [ ! -d "$MOUNT_POINT" ]; then
    echo "Error: Failed to mount DMG"
    exit 1
fi

sleep 2

# Configure DMG appearance
echo "==> Configuring appearance..."
osascript <<EOF
tell application "Finder"
    tell disk "$VOL_NAME"
        open
        delay 1
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {100, 100, $((100 + WINDOW_WIDTH)), $((100 + WINDOW_HEIGHT))}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to $ICON_SIZE
        set position of item "DropVox.app" of container window to {$APP_X, $APP_Y}
        set position of item "Applications" of container window to {$APPS_X, $APPS_Y}
        close
        open
        update without registering applications
        delay 1
        close
    end tell
end tell
EOF

# Delete system folders
echo "==> Cleaning system folders..."
rm -rf "$MOUNT_POINT/.fseventsd" 2>/dev/null || true
rm -rf "$MOUNT_POINT/.Spotlight-V100" 2>/dev/null || true
rm -rf "$MOUNT_POINT/.Trashes" 2>/dev/null || true

sync
sleep 1

# Unmount
echo "==> Unmounting..."
hdiutil detach "$DEVICE" -quiet 2>/dev/null || hdiutil detach "$DEVICE" -force

# Compress
echo "==> Compressing..."
hdiutil convert "dist/${APP_NAME}_temp.dmg" -format UDZO -imagekey zlib-level=9 \
    -o "dist/$DMG_NAME"

rm -f "dist/${APP_NAME}_temp.dmg"

FINAL_SIZE=$(du -h "dist/$DMG_NAME" | cut -f1)

echo ""
echo "=============================================="
echo "Done! dist/$DMG_NAME ($FINAL_SIZE)"
echo "=============================================="
