#!/usr/bin/env python3
"""Convert existing PNG icon to macOS .icns format.

Requires: pip install pillow

Takes assets/icon.png and generates assets/icon.icns
"""

import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Installing pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image


def save_iconset(img: Image.Image, output_dir: Path):
    """Save image as macOS iconset."""
    iconset_dir = output_dir / "VoxDrop.iconset"
    iconset_dir.mkdir(parents=True, exist_ok=True)

    # Required sizes for macOS icons
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    for size in sizes:
        # Regular resolution
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(iconset_dir / f"icon_{size}x{size}.png")

        # Retina (@2x) - stored as larger size with smaller name
        if size <= 512:
            resized_2x = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            resized_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")

    return iconset_dir


def create_icns(iconset_dir: Path, output_path: Path):
    """Convert iconset to icns using iconutil."""
    try:
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_path)],
            check=True,
        )
        print(f"Created: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating icns: {e}")
        print("iconset saved at:", iconset_dir)


def main():
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets"

    png_path = assets_dir / "icon.png"

    if not png_path.exists():
        print(f"Error: {png_path} not found")
        print("Please place your icon.png in the assets/ folder first.")
        sys.exit(1)

    print(f"Loading icon from {png_path}...")

    # Load the existing PNG
    icon = Image.open(png_path).convert('RGBA')

    # Resize to 1024 if needed (standard macOS icon size)
    if icon.size != (1024, 1024):
        print(f"Resizing from {icon.size} to 1024x1024...")
        icon = icon.resize((1024, 1024), Image.Resampling.LANCZOS)

    # Create iconset and convert to icns
    iconset_dir = save_iconset(icon, assets_dir)
    icns_path = assets_dir / "icon.icns"
    create_icns(iconset_dir, icns_path)

    # Clean up iconset directory
    import shutil
    shutil.rmtree(iconset_dir)

    print("\nDone! icon.icns created in assets/")


if __name__ == "__main__":
    main()
