#!/usr/bin/env python3
"""QC + assemble a movie-director kit into a final vertical MP4.

  python3 assemble.py <slug>
  python3 assemble.py <slug> --duration 45 --output /custom/path.mp4

Reads kits/<slug>/shotlist.json, verifies every frame file exists and plays,
then drives make_short.py: Ken Burns on images, direct cut on animated
(NightCafe/Qwen) video clips, Piper TTS per shot text, optional bg-music bed. Final MP4 → kits/<slug>/out/.
"""
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KITS = ROOT / "kits"
AGENT = ROOT.parent / "youtube-agent"
sys.path.insert(0, str(AGENT))
import make_short  # reuse the render pipeline + Piper TTS

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv"}
TARGET_RATIO = 9 / 16


def probe_video(path: Path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        w, h = (int(x) for x in r.stdout.strip().split(",")[:2])
    except ValueError:
        return None
    r2 = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        dur = float(r2.stdout.strip())
    except ValueError:
        dur = None
    return dur, w, h


def qc(shots: list, kit: Path) -> list:
    errors, warns = [], []
    for s in shots:
        p = kit / s["frame"]
        if not p.exists():
            errors.append(f"missing frame: {s['frame']}")
            continue
        info = probe_video(p)
        if info is None:
            errors.append(f"not a playable media file: {s['frame']}")
            continue
        dur, w, h = info
        ratio = w / h if h else 0
        if abs(ratio - TARGET_RATIO) > 0.05:
            warns.append(
                f"{s['frame']} is {w}x{h} (not 9:16 portrait) — will be scaled/cropped")
        if p.suffix.lower() in VIDEO_EXTS:
            if dur is not None and dur < 1.0:
                warns.append(f"{s['frame']} video is only {dur:.1f}s")
            label = f"video   {dur:.1f}s" if dur else "video   dur?"
        else:
            label = "image"
        print(f"  ok: {s['frame']:<34} {w}x{h}  {label}")
    if warns:
        print("  -- (continued below)" + ("" if not errors else " errors:"))
        for wmsg in warns:
            print(f"  warn: {wmsg}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug", nargs="?", help="kit slug under kits/, or use --kit")
    ap.add_argument("--kit", default=None, help="direct path to a kit dir (overrides slug)")
    ap.add_argument("--output", default=None, help="output MP4 path")
    ap.add_argument("--duration", type=int, default=0, help="target runtime in seconds")
    args = ap.parse_args()

    kit = Path(args.kit) if args.kit else (KITS / args.slug) if args.slug else None
    if kit is None or not kit.is_dir():
        sys.exit("provide a kit slug or --kit <dir>")

    shot_path = kit / "shotlist.json"
    if not shot_path.exists():
        sys.exit(f"missing {shot_path}")
    shotlist = json.loads(shot_path.read_text())
    shots = shotlist.get("shots", [])
    if not shots:
        sys.exit("shotlist.json has no shots")

    print(f"kit: {kit}")
    print("QC:")
    errors = qc(shots, kit)
    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        sys.exit(1)
    print("QC passed.")

    images, videos, texts = [], [], []
    has_video = False
    for s in shots:
        f = kit / s["frame"]
        texts.append(s.get("text", []))
        if f.suffix.lower() in VIDEO_EXTS:
            videos.append(str(f))
            images.append(None)
            has_video = True
        else:
            videos.append(None)
            images.append(str(f))

    # make_short only supports mixed image+video in the "standard" layout
    layout = "standard" if has_video else shotlist.get("layout", "fullbleed")
    if has_video and shotlist.get("layout", "fullbleed") in ("fullbleed", "commentary"):
        print("  note: layout is image-only in make_short; using 'standard' for mixed image+video")

    out = Path(args.output) if args.output else kit / "out" / f"{kit.name}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = args.duration or shotlist.get("runtime", 60)

    print(f"\nassembling {len(shots)} shots -> {out}")
    make_short.run(
        images=images, texts=texts, videos=videos,
        duration=duration,
        voice="same" if shotlist.get("voice") else None,
        lang=shotlist.get("lang", "en"),
        layout=layout,
        text_bg=shotlist.get("text_bg"),
        tts_speed=shotlist.get("tts_speed", 0.85),
        bg_music=shotlist.get("bg_music"),
        output=str(out),
    )
    print(f"\ndone: {out} ({out.stat().st_size / 1e6:.1f} MB)" if out.exists() else "\nfailed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())