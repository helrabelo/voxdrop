#!/bin/bash
# Build VoxDrop macOS app bundle
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "==> Cleaning previous builds..."
rm -rf build dist

echo "==> Installing dependencies..."
pip install -e ".[dev]"

echo "==> Building VoxDrop.app..."
python -m PyInstaller VoxDrop.spec --noconfirm

echo "==> Build complete!"
echo "    App location: dist/VoxDrop.app"
echo ""
echo "To create a DMG for distribution:"
echo "    ./scripts/create-dmg.sh"
