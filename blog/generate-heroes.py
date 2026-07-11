#!/usr/bin/env python3
"""Generate hero images for blog posts."""

import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT_DIR = Path(__file__).parent / "images"
OUT_DIR.mkdir(exist_ok=True)

W, H = 1200, 630  # OG image size


def gradient_bg(w, h, colors, direction="diagonal"):
    """Create a smooth gradient background."""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    c1, c2 = colors
    for y in range(h):
        for x in range(w):
            if direction == "diagonal":
                t = (x / w * 0.6 + y / h * 0.4)
            elif direction == "radial":
                cx, cy = w * 0.7, h * 0.4
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                max_dist = math.sqrt(w ** 2 + h ** 2)
                t = min(dist / max_dist * 1.5, 1.0)
            else:
                t = y / h

            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            draw.point((x, y), fill=(r, g, b))

    return img


def add_glow(img, cx, cy, radius, color, intensity=0.3):
    """Add a soft glow effect."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for r in range(radius, 0, -2):
        alpha = int(255 * intensity * (1 - r / radius) ** 2)
        alpha = min(alpha, 255)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(*color, alpha)
        )

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    return result.convert("RGB")


def add_particles(img, count=30, color=(212, 175, 55)):
    """Add scattered dot particles."""
    draw = ImageDraw.Draw(img)
    random.seed(42)  # Reproducible

    for _ in range(count):
        x = random.randint(0, img.width)
        y = random.randint(0, img.height)
        size = random.randint(1, 4)
        alpha = random.randint(40, 120)
        draw.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=(*color, alpha) if img.mode == "RGBA" else color
        )

    return img


def draw_text_with_shadow(draw, pos, text, font, fill, shadow_color=(0, 0, 0), shadow_offset=3):
    """Draw text with drop shadow."""
    x, y = pos
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def create_hero(title, subtitle, filename, scheme="gold"):
    """Create a hero image with gradient, glow, and text."""
    if scheme == "gold":
        c1 = (15, 12, 8)    # Dark brown-black
        c2 = (35, 28, 15)   # Warm dark
        glow_color = (212, 175, 55)  # Gold
        text_color = (255, 255, 255)
        accent_color = (212, 175, 55)
    elif scheme == "blue":
        c1 = (8, 12, 25)    # Dark navy
        c2 = (15, 25, 45)   # Mid navy
        glow_color = (100, 160, 255)  # Blue
        text_color = (255, 255, 255)
        accent_color = (100, 160, 255)
    elif scheme == "purple":
        c1 = (15, 8, 25)    # Dark purple
        c2 = (30, 15, 50)   # Mid purple
        glow_color = (180, 120, 255)  # Purple
        text_color = (255, 255, 255)
        accent_color = (180, 120, 255)

    # Create gradient background
    img = gradient_bg(W, H, [c1, c2], "diagonal")

    # Add glow effects
    img = add_glow(img, int(W * 0.75), int(H * 0.35), 250, glow_color, 0.25)
    img = add_glow(img, int(W * 0.2), int(H * 0.7), 180, glow_color, 0.15)

    # Add particles
    img_rgba = img.convert("RGBA")
    img_rgba = add_particles(img_rgba, 40, glow_color)
    img = img_rgba.convert("RGB")

    # Add subtle noise/texture
    draw = ImageDraw.Draw(img)
    random.seed(123)
    for _ in range(200):
        x = random.randint(0, W - 1)
        y = random.randint(0, H - 1)
        brightness = random.randint(0, 15)
        draw.point((x, y), fill=(brightness, brightness, brightness))

    # Load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        badge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # Draw badge
    badge_text = "45DGOFCOM BLOG"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = badge_bbox[2] - badge_bbox[0] + 24
    badge_h = badge_bbox[3] - badge_bbox[1] + 12
    badge_x, badge_y = 60, 50
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=4,
        fill=(*accent_color, 40),
        outline=(*accent_color, 100)
    )
    draw.text((badge_x + 12, badge_y + 5), badge_text, font=badge_font, fill=accent_color)

    # Draw title (wrapped)
    max_text_width = W - 160  # 80px margins
    lines = wrap_text(title, title_font, max_text_width, draw)

    y_start = H // 2 - len(lines) * 35
    for i, line in enumerate(lines):
        draw_text_with_shadow(
            draw, (80, y_start + i * 65), line, title_font,
            fill=text_color, shadow_color=(0, 0, 0), shadow_offset=4
        )

    # Draw subtitle
    sub_y = y_start + len(lines) * 65 + 20
    draw.text((80, sub_y), subtitle, font=subtitle_font, fill=(*accent_color, 200))

    # Draw decorative line
    line_y = sub_y + 40
    draw.line([(80, line_y), (280, line_y)], fill=accent_color, width=2)

    # Save
    out_path = OUT_DIR / filename
    img.save(out_path, "PNG", quality=95)
    print(f"  ✓ {out_path.name} ({W}x{H})")
    return out_path


def create_index_hero():
    """Create the blog index hero image."""
    img = gradient_bg(W, H, [(10, 8, 15), (25, 18, 35)], "radial")
    img = add_glow(img, W // 2, H // 2, 300, (212, 175, 55), 0.2)

    img_rgba = img.convert("RGBA")
    img_rgba = add_particles(img_rgba, 50, (212, 175, 55))
    img = img_rgba.convert("RGB")

    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    # Center "BLOG" text
    title = "BLOG"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw_text_with_shadow(
        draw, ((W - tw) // 2, H // 2 - 60), title, title_font,
        fill=(212, 175, 55), shadow_color=(0, 0, 0), shadow_offset=4
    )

    subtitle = "AI tools, YouTube creation, and building in public"
    bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, H // 2 + 30), subtitle, font=sub_font, fill=(150, 150, 160))

    # Decorative lines
    line_w = 120
    line_y = H // 2 + 80
    draw.line([(W // 2 - line_w, line_y), (W // 2 + line_w, line_y)], fill=(212, 175, 55), width=2)

    out_path = OUT_DIR / "blog-hero.png"
    img.save(out_path, "PNG", quality=95)
    print(f"  ✓ {out_path.name} ({W}x{H})")
    return out_path


if __name__ == "__main__":
    print("🎨 Generating hero images...")

    # Post 1: AI Tools
    create_hero(
        "10 AI Tools That Turn Your Photos Into YouTube Shorts",
        "From images to finished Shorts — no editing skills needed",
        "hero-ai-tools.png",
        scheme="gold"
    )

    # Post 2: Faceless YouTube
    create_hero(
        "10 Faceless YouTube Tools You Can Use Today",
        "Build a channel without showing your face",
        "hero-faceless.png",
        scheme="blue"
    )

    # Post 3: No Camera
    create_hero(
        "How to Create YouTube Shorts Without a Camera",
        "Images + text + AI voiceover = finished Short",
        "hero-no-camera.png",
        scheme="purple"
    )

    # Blog index hero
    create_index_hero()

    print(f"\n✅ Generated 4 images in {OUT_DIR}")
