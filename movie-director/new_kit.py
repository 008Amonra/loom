#!/usr/bin/env python3
"""Scaffold a movie-director kit workspace.

  python3 new_kit.py "a 60s music video about a lighthouse keeper"

Creates kits/<slug>/ with kit.md + shotlist.json ready to fill in.
The agent fills concept/characters/prompts; Jace pastes prompts into
Qwen Chat (free path, default) or NightCafe (paid upgrade) and drops
outputs into frames/; assemble.py QC + renders.
"""
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KITS = ROOT / "kits"

KIT_MD_TEMPLATE = """\
# {title}

## 1. Concept brief
- Hook / logline:
- Story beats (3-5):
- Tone / palette:
- Runtime: 60s, 9:16, 24-30fps

## 2. Character bibles
### {slug} — main
- Locked look (face, hair, wardrobe):
- Image reference prompt (paste into Qwen Chat / NightCafe, 9:16):

## 3. Qwen-Image 3.0 prompts — IMAGE phase (character sheets + world plates)
Target: chat.qwen.ai → Qwen-Image 3.0 (free, ~a few gens/day)
### IMG 01 — character sheet
- Prompt:
- Aspect: 9:16
-- style hint --

## 4. Wan image→video prompts — VIDEO phase (per shot, animate the saved still)
Target: chat.qwen.ai → video tool → upload the IMG still → motion prompt (free)
### VID 01 — shot 1
- Still: IMG 01 (saved output)
- Motion prompt (what happens + camera move + optional ambient sound):
- Duration: 5-8s | Aspect: 9:16 (adaptive matches the still)
-- style hint --

## 4b. Paid upgrade (optional)
Same shot list → NightCafe Seedance/Kling for 1080p long-form + stricter character lock.
Keep movie-director's shotlist.json unchanged; only the frames/ swap out.

## 5. Shot list (mirrors shotlist.json)
| #  | frame file        | text / TTS line   | tones |
| -- | ----------------- | ----------------- | ----- |
| 1  | frames/01_open... |                   | 6     |

## 6. QC checklist
- all frame files present under frames/ and named per shot list
- every video clip plays (no corrupt file)
- free-tier frames: 480-720p allowed (assemble upscales); NightCafe 1080p=cleanest
- frames are vertical 9:16; non-9:16 gets scaled/cropped by assemble
- dialogue lines are short (<= 28 chars per overlay line), no "|" or brackets
- bg_music path (optional) exists and is read-only used
- Qwen free cadence: ~one short movie's shots per day (rate-limited)
"""

SHOTLIST_TEMPLATE = """\
{{
  "_help": "i: frame = image or mp4 under this kit. text[] lines are overlaid + TTS; empty = clean shot. tones = seconds. bg_music = optional local audio, referenced read-only.",
  "title": "{title}",
  "runtime": 60,
  "voice": "same",
  "lang": "en",
  "layout": "fullbleed",
  "bg_music": null,
  "shots": [
    {{
      "id": 1,
      "frame": "frames/01_open.png",
      "text": ["LINE ONE", "LINE TWO"],
      "tones": 6
    }}
  ]
}}
"""


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "untitled"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("title", help="one-line description of the movie")
    ap.add_argument("--dir", default=None, help="parent dir for the kit (default kits/)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing kit")
    args = ap.parse_args()

    slug = slugify(args.title)
    base = Path(args.dir) if args.dir else KITS
    kit = base / slug
    if kit.exists() and not args.force:
        sys.exit(f"kit already exists: {kit} (use --force to overwrite)")

    for sub in ("frames", "out"):
        (kit / sub).mkdir(parents=True, exist_ok=True)

    kit_md = kit / "kit.md"
    if not kit_md.exists() or args.force:
        kit_md.write_text(KIT_MD_TEMPLATE.format(title=args.title, slug=slug))

    shots = kit / "shotlist.json"
    if not shots.exists() or args.force:
        shots.write_text(SHOTLIST_TEMPLATE.format(title=args.title))

    print(f"kit ready: {kit}")
    print(f"  edit {kit_md.name}  (agent fills concept/characters/prompts)")
    print(f"  edit {shots.name}  (shot list drives assembly)")
    print("  drop Qwen Chat / NightCafe outputs into frames/, then run:")
    print(f"  python3 assemble.py {slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())