import subprocess
import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
DURATION = 30
TOTAL = FPS * DURATION

ACCENT = (100, 200, 255)
WHITE = (240, 240, 255)
DIM = (140, 140, 170)
MUTED = (100, 100, 130)

def bg(t):
    i = int(t * 60) % 360
    phase = 0.5 + 0.5 * math.sin(math.radians(i))
    r = int(8 + 12 * phase)
    g = int(4 + 8 * (1 - phase))
    b = int(22 + 18 * phase)
    return (r, g, b)

try:
    font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 82)
    font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
    font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
except:
    font_lg = ImageFont.load_default()
    font_md = font_lg
    font_sm = font_lg
    font_xs = font_lg

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def ease_out(t):
    return 1 - (1 - t) * (1 - t)

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

phrases = [
    (0.0, 4.0, "45dgof8", 82, ACCENT, font_lg, 'center', 0.35),
    (3.5, 4.0, "AI Agents", 50, WHITE, font_md, 'center', 0.48),
    (5.0, 5.0, "for Solo Creators", 50, DIM, font_md, 'center', 0.56),
    (8.0, 4.0, "No GPU. No cloud. Just code.", 30, MUTED, font_sm, 'center', 0.66),
    (11.0, 5.0, "Built with support by jace + opencode", 24, MUTED, font_xs, 'center', 0.76),
    (16.5, 4.0, "45dgof8.com", 36, ACCENT, font_sm, 'center', 0.88),
]

particles = []
for _ in range(60):
    angle = 2 * math.pi * (os.urandom(1)[0] / 255)
    speed = 20 + 30 * (os.urandom(1)[0] / 255)
    particles.append({
        'x': W * (os.urandom(1)[0] / 255),
        'y': H * (os.urandom(1)[0] / 255),
        'vx': speed * math.cos(angle),
        'vy': speed * math.sin(angle),
        'size': 1.5 + 2 * (os.urandom(1)[0] / 255),
        'phase': 2 * math.pi * (os.urandom(1)[0] / 255),
    })

def draw_particles(draw, t):
    for p in particles:
        x = (p['x'] + p['vx'] * t) % W
        y = (p['y'] + p['vy'] * t) % H
        alpha = int(40 + 30 * math.sin(t * 2 + p['phase']))
        draw.ellipse([x-p['size'], y-p['size'], x+p['size'], y+p['size']],
                     fill=(ACCENT[0], ACCENT[1], ACCENT[2], alpha) if hasattr(draw, 'alpha') else ACCENT)
        try:
            draw.ellipse([x-p['size'], y-p['size'], x+p['size'], y+p['size']],
                         fill=(ACCENT[0], ACCENT[1], ACCENT[2], min(70, alpha)))
        except:
            pass

cmd = [
    'ffmpeg', '-y',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-s', f'{W}x{H}',
    '-pix_fmt', 'rgb24',
    '-r', str(FPS),
    '-i', '-',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-r', str(FPS),
    '/home/jace/45dgof8/45dgof8-typo.mp4'
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

for frame in range(TOTAL):
    t = frame / FPS

    bgc = bg(t)
    img = Image.new('RGB', (W, H), bgc)
    draw = ImageDraw.Draw(img)

    draw_particles(draw, t)

    for start, duration, text, size, color, font, align, y_norm in phrases:
        end = start + duration
        if t < start - 0.5 or t > end:
            continue

        y_pos = int(H * y_norm)

        if t < start:
            continue
        elif t < start + 0.3:
            local = (t - start) / 0.3
            alpha = local
            scale = 0.5 + 0.5 * ease_out(local)
        elif t < end - 0.5:
            alpha = 1.0
            scale = 1.0
        elif t < end:
            local = (t - (end - 0.5)) / 0.5
            alpha = 1.0 - ease_in_out(local)
            scale = 1.0
        else:
            continue

        fs = int(size * scale)
        try:
            f = ImageFont.truetype(font.path if hasattr(font, 'path') else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs)
        except:
            f = font

        bbox = draw.textbbox((0, 0), text, font=f)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        x_pos = (W - tw) // 2

        offset_x = 0
        if t < start + 0.5 and start > 0:
            local_slide = (t - start) / 0.5
            slide = 1.0 - ease_out(local_slide)
            if frame % 2 == 0:
                offset_x = int(-80 * slide)
            else:
                offset_x = int(80 * slide)

        x = x_pos + offset_x

        r = int(lerp(0, color[0], alpha))
        g = int(lerp(0, color[1], alpha))
        b = int(lerp(0, color[2], alpha))
        draw.text((x, y_pos - th // 2), text, fill=(r, g, b), font=f)

    proc.stdin.write(img.tobytes())

proc.stdin.close()
proc.wait()
print("Video generated!")
