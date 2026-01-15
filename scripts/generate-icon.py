#!/usr/bin/env python3
"""Generate a simple app icon for VoxDrop.

Requires: pip install pillow

Creates a basic icon with a microphone/waveform motif.
For production, replace with a professionally designed icon.
"""

import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image, ImageDraw, ImageFont


def create_icon(size: int = 1024) -> Image.Image:
    """Create a simple VoxDrop icon."""
    # Create image with rounded corners background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background - gradient-like purple/blue
    padding = int(size * 0.05)
    corner_radius = int(size * 0.2)

    # Draw rounded rectangle background
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=corner_radius,
        fill=(88, 86, 214),  # Purple
    )

    # Draw a simple waveform/audio icon
    center_x = size // 2
    center_y = size // 2
    bar_width = int(size * 0.08)
    gap = int(size * 0.04)

    # Audio bars (waveform visualization)
    bar_heights = [0.25, 0.45, 0.65, 0.45, 0.25]
    num_bars = len(bar_heights)
    total_width = num_bars * bar_width + (num_bars - 1) * gap
    start_x = center_x - total_width // 2

    for i, height_ratio in enumerate(bar_heights):
        bar_height = int(size * height_ratio)
        x = start_x + i * (bar_width + gap)
        y1 = center_y - bar_height // 2
        y2 = center_y + bar_height // 2

        draw.rounded_rectangle(
            [x, y1, x + bar_width, y2],
            radius=bar_width // 2,
            fill=(255, 255, 255),
        )

    return img


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
    assets_dir.mkdir(exist_ok=True)

    print("Generating VoxDrop icon...")

    # Create the icon
    icon = create_icon(1024)

    # Save as PNG
    png_path = assets_dir / "icon.png"
    icon.save(png_path)
    print(f"Created: {png_path}")

    # Create iconset and convert to icns
    iconset_dir = save_iconset(icon, assets_dir)
    icns_path = assets_dir / "icon.icns"
    create_icns(iconset_dir, icns_path)

    # Clean up iconset directory
    import shutil
    shutil.rmtree(iconset_dir)

    print("\nDone! Icon files created in assets/")


if __name__ == "__main__":
    main()
