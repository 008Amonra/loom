import numpy as np
import subprocess
import struct
import math
import os
from PIL import Image, ImageDraw, ImageFont

SR = 44100
BPM = 155
BEAT = 60.0 / BPM
DURATION = 30
TOTAL = int(SR * DURATION)

AMP = 0.25

def chord_freqs(root):
    return [root * 2**(i/12) for i in (0, 4, 7)]

AM_MAJ = chord_freqs(220.0)
F_MAJ  = chord_freqs(174.61)
C_MAJ  = chord_freqs(261.63)
G_MAJ  = chord_freqs(196.00)
CHORDS = [AM_MAJ, F_MAJ, C_MAJ, G_MAJ]
CHORD_NAMES = ["Am", "F", "C", "G"]

def adsr(t, a, d, s, r, gate):
    if t < 0: return 0
    if t < a: return t / a
    if t < a + d: return 1 - (1 - s) * (t - a) / d
    if t < gate: return s
    if t < gate + r: return s * (1 - (t - gate) / r)
    return 0

def piano_note(freq, duration, sr):
    n = int(sr * duration)
    t = np.arange(n) / sr
    env = np.array([adsr(ti, 0.005, 0.08, 0.25, 0.3, duration) for ti in t])
    harmonics = [1.0, 0.5, 0.33, 0.25, 0.2, 0.15, 0.1, 0.08]
    sig = np.zeros(n)
    for i, h in enumerate(harmonics):
        hf = freq * (i + 1)
        hg = 1.0 / (1 + i * 0.3)
        sig += hg * np.sin(2 * np.pi * hf * t)
    detune = np.sin(2 * np.pi * freq * 1.003 * t) * 0.15
    sig += detune
    sig = sig * env * 0.3
    return sig

def piano_chord(freqs, duration, sr):
    sig = np.zeros(int(sr * duration))
    for f in freqs:
        sig[:len(piano_note(f, duration, sr))] += piano_note(f, duration, sr)
    return sig * 0.5

def kick(sr):
    n = int(sr * 0.15)
    t = np.arange(n) / sr
    click = np.exp(-t * 2000) * 0.3 * np.sin(2 * np.pi * 3000 * t)
    body = np.exp(-t * 40) * np.sin(2 * np.pi * (150 - 100 * np.exp(-t * 30)) * t)
    return (click + body) * 0.5

def hihat_closed(sr):
    n = int(sr * 0.04)
    t = np.arange(n) / sr
    noise = np.random.randn(n)
    env = np.exp(-t * 80)
    b, a = 0.1, 0.9
    lp = np.zeros(n)
    for i in range(1, n):
        lp[i] = b * noise[i] + a * lp[i-1]
    hp = noise - lp
    return hp * env * 0.08

def bass_note(freq, duration, sr):
    n = int(sr * duration)
    t = np.arange(n) / sr
    env = np.exp(-t * 2.5)
    sig = np.sin(2 * np.pi * freq * t)
    sig += 0.3 * np.sin(2 * np.pi * freq * 2 * t)
    return sig * env * 0.25

def gen_audio():
    total_beats = int(BPM * DURATION / 60) + 1
    beats_per_chord = 8
    total = int(SR * DURATION)
    out = np.zeros(total)
    
    for b in range(total_beats):
        beat_time = b * BEAT
        beat_sample = int(beat_time * SR)
        chord_idx = (b // beats_per_chord) % len(CHORDS)
        
        if beat_time + 0.15 < DURATION:
            k = kick(SR)
            end = min(beat_sample + len(k), total)
            out[beat_sample:end] += k[:end - beat_sample]
        
        if b % 2 == 1 and beat_time + 0.04 < DURATION:
            h = hihat_closed(SR)
            end = min(beat_sample + len(h), total)
            out[beat_sample:end] += h[:end - beat_sample] * 0.5
        
        if b % 4 == 0:
            chord_dur = min(BEAT * 2, DURATION - beat_time)
            pc = piano_chord(CHORDS[chord_idx], chord_dur, SR)
            end = min(beat_sample + len(pc), total)
            out[beat_sample:end] += pc[:end - beat_sample]
        
        if b % 2 == 0:
            root = CHORDS[chord_idx][0]
            bd = min(BEAT, DURATION - beat_time)
            bn = bass_note(root / 2, bd, SR)
            end = min(beat_sample + len(bn), total)
            out[beat_sample:end] += bn[:end - beat_sample]
    
    peak = np.max(np.abs(out))
    if peak > 0:
        out = out / peak * AMP
    
    out = out * 0.7
    
    wav = np.int16(out * 32767)
    
    with open('/tmp/happy-hardcore-audio.wav', 'wb') as f:
        f.write(struct.pack('<4sI4s', b'RIFF', 36 + len(wav)*2, b'WAVE'))
        f.write(struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, SR, SR*2, 2, 16))
        f.write(struct.pack('<4sI', b'data', len(wav)*2))
        f.write(wav.tobytes())
    
    print("Audio generated!")

gen_audio()

W, H = 1920, 1080
FPS = 30
TOTAL_FRAMES = FPS * DURATION

try:
    font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
    font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
    font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
except:
    font_lg = font_md = font_sm = font_xs = ImageFont.load_default()

COLS = {
    'pink': (255, 80, 160),
    'cyan': (80, 200, 255),
    'yellow': (255, 230, 80),
    'white': (240, 240, 255),
    'dim': (160, 160, 190),
    'muted': (100, 100, 130),
    'orange': (255, 160, 40),
}

phrases = [
    (0.0,  2.5, "45dgof8", font_lg, COLS['pink'], (-1, 1, -1)),
    (2.5,  3.0, "presents", font_sm, COLS['dim'], (-1, 1, -1)),
    (4.5,  4.0, "HAPPY HARDCORE", font_lg, COLS['yellow'], (2, 1, -2)),
    (7.0,  3.5, "Piano & House", font_md, COLS['cyan'], (-2, 1, 2)),
    (9.5,  4.0, "Built on old iron", font_md, COLS['dim'], (3, -2, 1)),
    (11.5, 4.0, "No GPU needed", font_md, COLS['orange'], (-3, 1, -3)),
    (14.0, 4.0, "Just code & beats", font_md, COLS['white'], (1, -1, 1)),
    (16.5, 4.0, "Custom AI agents", font_lg, COLS['pink'], (-2, 3, -2)),
    (19.0, 4.0, "Video & Music", font_md, COLS['cyan'], (2, -2, 2)),
    (21.5, 3.5, "Automation workflows", font_md, COLS['yellow'], (-3, 2, 1)),
    (24.0, 3.0, "You describe", font_sm, COLS['white'], (0, 0, 0)),
    (26.0, 2.5, "We build", font_md, COLS['pink'], (0, 0, 0)),
    (28.0, 2.0, "45dgof8.com", font_lg, COLS['yellow'], (0, 0, 0)),
]

bars_bg = []
for _ in range(40):
    bars_bg.append({
        'x': np.random.rand() * W,
        'w': 15 + np.random.rand() * 40,
        'speed': 60 + np.random.rand() * 120,
        'h': 50 + np.random.rand() * 300,
    })

def draw_bg(draw, t):
    beat_phase = (t % BEAT) / BEAT
    pulse = 0.85 + 0.15 * (1 - beat_phase)
    
    flash = 0
    beat_idx = int(t / BEAT)
    if beat_idx % 4 == 0 and beat_phase < 0.05:
        flash = 0.15 * (1 - beat_phase / 0.05)
    
    r = int((12 + flash * 40) * pulse)
    g = int((4 + flash * 20) * pulse)
    b = int((24 + flash * 60) * pulse)
    draw.rectangle([0, 0, W, H], fill=(r, g, b))
    
    for bar in bars_bg:
        bx = (bar['x'] + bar['speed'] * t) % (W + bar['w']) - bar['w']
        bh = bar['h'] * (0.5 + 0.5 * math.sin(t * 3 + bar['x']))
        alpha = int(15 + 10 * math.sin(t * 2 + bar['x']))
        draw.rectangle([bx, H - bh, bx + bar['w'], H], fill=(80, 40, 120, alpha) if hasattr(draw, 'alpha') else (80, 40, 120))

def ease_out(t):
    return 1 - (1 - t) * (1 - t)

cmd = [
    'ffmpeg', '-y',
    '-f', 'rawvideo', '-vcodec', 'rawvideo',
    '-s', f'{W}x{H}', '-pix_fmt', 'rgb24',
    '-r', str(FPS), '-i', '-',
    '-i', '/tmp/happy-hardcore-audio.wav',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    '-c:a', 'aac', '-b:a', '192k', '-shortest',
    '/home/jace/45dgof8/45dgof8-happy-hardcore.mp4'
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

for frame in range(TOTAL_FRAMES):
    t = frame / FPS
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    draw_bg(draw, t)
    
    for start, dur, text, font, color, wobble in phrases:
        end = start + dur
        if t < start - 0.3 or t > end:
            continue
        
        y_pos = H // 2
        
        if t < start:
            continue
        elif t < start + 0.2:
            local = (t - start) / 0.2
            alpha = local
            scale = 0.6 + 0.4 * ease_out(local)
        elif t < end - 0.3:
            alpha = 1.0
            beat_idx = int(t / BEAT)
            beat_phase = (t % BEAT) / BEAT
            bounce = 1.0 + 0.03 * math.sin(beat_phase * math.pi)
            scale = bounce
        elif t < end:
            local = (t - (end - 0.3)) / 0.3
            alpha = 1.0 - local
            scale = 1.0
        else:
            continue
        
        fs = int(font.size * min(scale, 1.3))
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs)
        except:
            f = font
        
        bbox = draw.textbbox((0, 0), text, font=f)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x_pos = (W - tw) // 2
        
        wx, wy, wz = wobble
        if wx != 0:
            beat_phase = (t % BEAT) / BEAT
            x_pos += int(wx * 20 * math.sin(beat_phase * 2 * math.pi))
        if wy != 0:
            y_pos += int(wy * 15 * math.sin(t * 4))
        
        r = int(color[0] * alpha)
        g = int(color[1] * alpha)
        b = int(color[2] * alpha)
        draw.text((x_pos, y_pos - th // 2), text, fill=(r, g, b), font=f)
    
    proc.stdin.write(img.tobytes())

proc.stdin.close()
proc.wait()
print("Video generated!")
