#!/usr/bin/env python3
"""Generate a menu bar icon by drawing the waveform directly.

Creates dark gray waveform bars on transparent background for macOS template mode.
"""

from PIL import Image, ImageDraw


def draw_rounded_rect(draw, xy, radius, fill):
    """Draw a rectangle with rounded corners (pill shape)."""
    x1, y1, x2, y2 = xy
    # Draw the main rectangle
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    # Draw the four corners
    draw.ellipse([x1, y1, x1 + 2 * radius, y1 + 2 * radius], fill=fill)
    draw.ellipse([x2 - 2 * radius, y1, x2, y1 + 2 * radius], fill=fill)
    draw.ellipse([x1, y2 - 2 * radius, x1 + 2 * radius, y2], fill=fill)
    draw.ellipse([x2 - 2 * radius, y2 - 2 * radius, x2, y2], fill=fill)


def create_menubar_icon():
    # Create at 2x resolution for quality, then scale down
    # Menu bar icons are typically 18-22px, we'll use 18px as base
    scale = 4  # Work at 4x for smooth edges
    size = 18 * scale  # 72px working size

    # Create transparent image
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark gray color for template icon
    color = (50, 50, 50, 255)

    # Bar properties (at 4x scale)
    bar_width = 3 * scale  # 12px
    bar_gap = 2 * scale    # 8px between bars
    radius = bar_width // 2  # Fully rounded ends

    # Bar heights (symmetrical waveform pattern) - relative to size
    # Pattern: short, medium, tall, medium, short
    heights = [0.35, 0.55, 0.85, 0.55, 0.35]

    # Calculate total width of all bars
    num_bars = len(heights)
    total_width = num_bars * bar_width + (num_bars - 1) * bar_gap

    # Starting x position (centered)
    start_x = (size - total_width) // 2

    # Draw each bar
    for i, height_ratio in enumerate(heights):
        bar_height = int(size * height_ratio)
        x = start_x + i * (bar_width + bar_gap)
        # Center vertically
        y_top = (size - bar_height) // 2
        y_bottom = y_top + bar_height

        draw_rounded_rect(draw, (x, y_top, x + bar_width, y_bottom), radius, color)

    # Resize to final sizes
    # @1x: 18px
    img_1x = img.resize((18, 18), Image.LANCZOS)
    # @2x: 36px
    img_2x = img.resize((36, 36), Image.LANCZOS)

    # Save
    output_1x = "/Users/helrabelo/code/personal/voxdrop/assets/menubar_icon.png"
    output_2x = "/Users/helrabelo/code/personal/voxdrop/assets/menubar_icon@2x.png"

    img_1x.save(output_1x)
    img_2x.save(output_2x)

    print(f"Created {output_1x} ({img_1x.size})")
    print(f"Created {output_2x} ({img_2x.size})")


if __name__ == "__main__":
    create_menubar_icon()
