import numpy as np
import subprocess
import struct
import math
import os

SR = 44100
BPM = 155
BEAT = 60.0 / BPM
DURATION = 30
TOTAL = int(SR * DURATION)
AMP = 0.2

def adsr(t, a, d, s, r, gate):
    if t < 0: return 0
    if t < a: return t / a
    if t < a + d: return 1 - (1 - s) * (t - a) / d
    if t < gate: return s
    if t < gate + r: return s * (1 - (t - gate) / r)
    return 0

def chord_freqs(root):
    return [root * 2**(i/12) for i in (0, 4, 7)]

# Chord progression
CHORDS_MAJ = [
    chord_freqs(220.0),   # Am
    chord_freqs(174.61),  # F
    chord_freqs(261.63),  # C
    chord_freqs(196.00),  # G
]
CHORDS_MIN = [
    chord_freqs(220.0),   # Am
    chord_freqs(207.65),  # Bdim
    chord_freqs(261.63),  # C
    chord_freqs(196.00),  # G
]

def piano_chord(freqs, duration, sr, vel=1.0):
    n = int(sr * duration)
    if n <= 0: return np.array([])
    t = np.arange(n) / sr
    env = np.array([adsr(ti, 0.003, 0.06, 0.2, 0.3, duration) for ti in t])
    sig = np.zeros(n)
    for f in freqs:
        hs = [1.0, 0.5, 0.33, 0.25, 0.18, 0.12, 0.08, 0.06]
        for i, h in enumerate(hs):
            hf = f * (i + 1)
            hg = 1.0 / (1 + i * 0.35)
            sig += hg * np.sin(2 * np.pi * hf * t)
        det = np.sin(2 * np.pi * f * 1.004 * t) * 0.12
        sig += det
    sig = sig * env * 0.15 * vel
    return sig

def piano_stab(freqs, sr, dur=0.3):
    return piano_chord(freqs, dur, sr, 1.2)

def kick(sr):
    n = int(sr * 0.18)
    t = np.arange(n) / sr
    click = np.exp(-t * 3000) * 0.4 * np.sin(2 * np.pi * 4000 * t)
    tick = np.exp(-t * 1500) * 0.3 * np.sin(2 * np.pi * 2000 * t)
    body = np.exp(-t * 35) * np.sin(2 * np.pi * (150 - 100 * np.exp(-t * 25)) * t)
    sub = np.exp(-t * 25) * np.sin(2 * np.pi * 60 * t) * 0.3
    return click + tick + body + sub

def kick_thump(sr):
    n = int(sr * 0.25)
    t = np.arange(n) / sr
    click = np.exp(-t * 4000) * 0.3 * np.sin(2 * np.pi * 5000 * t)
    body = np.exp(-t * 30) * np.sin(2 * np.pi * (140 - 100 * np.exp(-t * 20)) * t)
    sub = np.exp(-t * 20) * np.sin(2 * np.pi * 55 * t) * 0.5
    noise = np.random.randn(n) * np.exp(-t * 100) * 0.05
    return click + body + sub + noise

def hihat(sr, open_pct=0):
    d = 0.04 if open_pct < 0.5 else 0.15
    n = int(sr * d)
    t = np.arange(n) / sr
    noise = np.random.randn(n)
    env = np.exp(-t * (60 if open_pct < 0.5 else 15))
    signal = noise * env
    for _ in range(8):
        delayed = np.roll(noise, int(sr * 0.0001 * (_ + 1)))
        delayed[:int(sr * 0.0001 * (_ + 1))] = 0
        signal += delayed * 0.3 * np.exp(-_ * 0.5)
    signal = signal * 0.06
    return signal

def clap(sr):
    n = int(sr * 0.12)
    t = np.arange(n) / sr
    noise = np.random.randn(n)
    env = np.exp(-t * 25)
    sig = noise * env * 0.12
    noise2 = np.random.randn(n)
    env2 = np.exp(-t * 60) * np.exp(-((t - 0.01) * 200)**2)
    sig += noise2 * env2 * 0.08
    sig = sig * 0.5
    return sig

def crash(sr):
    n = int(sr * 0.5)
    t = np.arange(n) / sr
    noise = np.random.randn(n)
    env = np.exp(-t * 6)
    sig = noise * env * 0.04
    return sig

def snare(sr):
    n = int(sr * 0.15)
    t = np.arange(n) / sr
    tone = np.exp(-t * 40) * np.sin(2 * np.pi * 200 * t) * 0.3
    noise = np.random.randn(n) * np.exp(-t * 30) * 0.08
    return tone + noise

def synth_lead(freq, duration, sr, gate=0.5):
    n = int(sr * duration)
    t = np.arange(n) / sr
    env = np.array([adsr(ti, 0.01, 0.05, 0.4, 0.1, gate) for ti in t])
    saw = 2 * (freq * t - np.floor(0.5 + freq * t))
    sq = np.sign(np.sin(2 * np.pi * freq * t))
    sig = saw * 0.3 + sq * 0.15
    sig += 0.15 * np.sin(2 * np.pi * freq * 2 * t)
    sig = sig * env * 0.12
    return sig

def synth_pad(freqs, duration, sr):
    n = int(sr * duration)
    t = np.arange(n) / sr
    env = np.exp(-t * 1.5)
    sig = np.zeros(n)
    for f in freqs:
        sig += 0.5 * np.sin(2 * np.pi * f * t)
        sig += 0.25 * np.sin(2 * np.pi * f * 2 * t)
        sig += 0.12 * np.sin(2 * np.pi * f * 3 * t)
    sig = sig * env * 0.03
    return sig

def bassline(freq, duration, sr):
    n = int(sr * duration)
    t = np.arange(n) / sr
    env = np.exp(-t * 3)
    sig = np.sin(2 * np.pi * freq * t) * 0.5
    sig += 0.3 * np.sin(2 * np.pi * freq * 2 * t) * 0.3
    sig = sig * env * 0.2
    return sig

# Melody notes for synth lead (Am pentatonic-ish)
melody = [
    (0, 440.00), (0.5, 523.25), (1.0, 659.25), (1.5, 523.25),
    (2, 440.00), (2.5, 659.25), (3, 783.99), (3.5, 659.25),
    (4, 523.25), (4.5, 440.00), (5, 523.25), (5.5, 659.25),
    (6, 783.99), (6.5, 880.00), (7, 783.99), (7.5, 659.25),
]

def gen_audio():
    total_beats = int(BPM * DURATION / 60) + 1
    out = np.zeros(TOTAL)
    
    # Pad track (slowly evolving)
    for i in range(4):
        start_t = i * 8
        dur = 10
        si = int(start_t * SR)
        ei = min(si + int(dur * SR), TOTAL)
        ch = CHORDS_MAJ[i % 4]
        pad = synth_pad(ch, dur, SR)
        actual = min(len(pad), ei - si)
        out[si:si+actual] += pad[:actual]
    
    for b in range(total_beats):
        bt = b * BEAT
        bs = int(bt * SR)
        if bs >= TOTAL:
            break
        
        ci = (b // 8) % 4
        
        # Kick on every beat
        if bt + 0.18 < DURATION:
            k = kick(SR) if b % 4 != 0 else kick_thump(SR)
            end = min(bs + len(k), TOTAL)
            out[bs:end] += k[:end-bs] * 0.8
        
        # Snare/clap on beats 2 and 4
        if b % 4 in (1, 3):
            if bt + 0.12 < DURATION:
                c = clap(SR)
                end = min(bs + len(c), TOTAL)
                out[bs:end] += c[:end-bs]
                if b % 8 == 3:
                    s = snare(SR)
                    end = min(bs + len(s), TOTAL)
                    out[bs:end] += s[:end-bs]
        
        # Closed hi-hat on off-beats (8th notes)
        for o in [0.5]:
            hbt = bt + o * BEAT
            hbs = int(hbt * SR)
            if hbt + 0.04 < DURATION:
                h = hihat(SR)
                end = min(hbs + len(h), TOTAL)
                out[hbs:end] += h[:end-hbs]
        
        # Open hi-hat every 4 beats
        if b % 8 == 0 and b > 0:
            hbt = bt + 0.3
            hbs = int(hbt * SR)
            if hbt + 0.1 < DURATION:
                h = hihat(SR, open_pct=1)
                end = min(hbs + len(h), TOTAL)
                out[hbs:end] += h[:end-hbs]
        
        # Crash cymbal every 16 beats
        if b % 16 == 0:
            if bt + 0.3 < DURATION:
                cr = crash(SR)
                end = min(bs + len(cr), TOTAL)
                out[bs:end] += cr[:end-bs]
        
        # Piano stabs - varied pattern
        if b % 4 == 0:
            pd = BEAT * 1.8
            if bt + pd < DURATION:
                ch = CHORDS_MAJ[ci]
                if b % 16 == 8:
                    acc = piano_chord(ch, pd, SR, 0.7)
                elif b % 32 == 0:
                    acc = piano_chord(CHORDS_MAJ[(ci+1)%4], pd, SR, 0.9)
                else:
                    acc = piano_chord(ch, pd, SR, 0.6)
                end = min(bs + len(acc), TOTAL)
                out[bs:end] += acc[:end-bs]
        
        # Additional piano stabs on off-beats for happy feel
        if b % 2 == 1 and b % 4 != 3:
            pd = BEAT * 0.5
            hbt = bt
            hbs = int(hbt * SR)
            if hbt + pd < DURATION:
                ch = CHORDS_MAJ[ci]
                acc = piano_chord(ch, pd, SR, 0.3)
                end = min(hbs + len(acc), TOTAL)
                out[hbs:end] += acc[:end-hbs]
        
        # Synth lead melody
        for m_start, m_freq in melody:
            if abs(bt - m_start) < 0.05:
                sd = BEAT * 0.9
                if bt + sd < DURATION:
                    sl = synth_lead(m_freq, sd, SR)
                    end = min(bs + len(sl), TOTAL)
                    out[bs:end] += sl[:end-bs]
        
        # Bass
        root = CHORDS_MAJ[ci][0] / 2
        bd = BEAT * 1.9
        if bt + bd < DURATION:
            bn = bassline(root, bd, SR)
            end = min(bs + len(bn), TOTAL)
            out[bs:end] += bn[:end-bs]
        
        # Extra percussion - shaker feel on 16th notes
        if b % 2 == 0:
            for sixteenth in [0.25, 0.75]:
                sbt = bt + sixteenth * BEAT
                sbs = int(sbt * SR)
                if sbt + 0.02 < DURATION:
                    nz = np.random.randn(int(SR * 0.02)) * 0.008
                    nz_env = np.exp(-np.arange(len(nz)) * 80)
                    end = min(sbs + len(nz), TOTAL)
                    out[sbs:end] += nz[:end-sbs] * nz_env[:end-sbs]

    # Kick fill / buildup before drop
    for b in range(28, 32):
        bt = b * BEAT
        bs = int(bt * SR)
        if bt + 0.18 < DURATION:
            k = kick(SR)
            end = min(bs + len(k), TOTAL)
            out[bs:end] += k[:end-bs] * 0.7
    
    # Outro - fade out last 4 beats
    fade_start = TOTAL - int(4 * BEAT * SR)
    fade_env = np.linspace(1, 0, TOTAL - fade_start)
    out[fade_start:] *= fade_env
    
    peak = np.max(np.abs(out))
    if peak > 0:
        out = out / peak * AMP
    
    out = out * 0.8
    wav = np.int16(out * 32767)
    
    with open('/tmp/intermix-audio.wav', 'wb') as f:
        f.write(struct.pack('<4sI4s', b'RIFF', 36 + len(wav)*2, b'WAVE'))
        f.write(struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, SR, SR*2, 2, 16))
        f.write(struct.pack('<4sI', b'data', len(wav)*2))
        f.write(wav.tobytes())
    print("Audio generated!")

gen_audio()

# Video intercut segments: [video_index, start, end]
# video 0 = typo-audio, video 1 = happy-hardcore
cuts = [
    (0, 0, 5),
    (1, 0, 5),
    (0, 5, 10),
    (1, 5, 10),
    (0, 10, 16),
    (1, 10, 16),
    (0, 16, 22),
    (1, 16, 22),
    (0, 22, 26),
    (1, 22, 26),
    (0, 26, 30),
    (1, 26, 30),
]

cmd = [
    'ffmpeg', '-y',
    '-i', '/home/jace/45dgof8/45dgof8-typo-audio.mp4',
    '-i', '/home/jace/45dgof8/45dgof8-happy-hardcore.mp4',
    '-i', '/tmp/intermix-audio.wav',
    '-filter_complex',
]

concat = ''
map_parts = []
for i, (vi, s, e) in enumerate(cuts):
    concat += f'[{vi}:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}];'
    map_parts.append(f'[v{i}]')

concat += ''.join(map_parts) + f'concat=n={len(cuts)}:v=1:a=0[outv]'

cmd += [concat, '-map', '[outv]', '-map', '2:a']
cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p']
cmd += ['-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart']
cmd += ['/home/jace/45dgof8/45dgof8-intermix.mp4']

print("Running FFmpeg intercut...")
subprocess.run(cmd, check=True)
print("Done! /home/jace/45dgof8/45dgof8-intermix.mp4")
