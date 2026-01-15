#!/bin/bash
# Create DMG for DropVox distribution
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

APP_NAME="DropVox"
VERSION=$(grep 'version = ' pyproject.toml | head -1 | cut -d'"' -f2)
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
DMG_DIR="dist/dmg"

echo "==> Creating DMG for $APP_NAME v$VERSION..."

# Check if app exists
if [ ! -d "dist/DropVox.app" ]; then
    echo "Error: dist/DropVox.app not found. Run ./scripts/build.sh first."
    exit 1
fi

# Clean previous DMG build
rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"

# Copy app to DMG staging
cp -R "dist/DropVox.app" "$DMG_DIR/"

# Create symlink to Applications folder
ln -s /Applications "$DMG_DIR/Applications"

# Create DMG
echo "==> Packaging DMG..."
hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_DIR" -ov -format UDZO "dist/$DMG_NAME"

# Clean up staging
rm -rf "$DMG_DIR"

echo "==> DMG created: dist/$DMG_NAME"
echo ""
echo "Upload this file to GitHub Releases for distribution."
