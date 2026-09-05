# movie-director

Semi-automated AI movie production. Jace generates visuals in Qwen Chat
(free path) or NightCafe (paid upgrade); the agent does everything else
locally and free.

## Flow
1. **Brief** — tell the agent one line: *"a 60s music video about a lighthouse keeper"*.
2. **Kit** — the agent runs `new_kit.py` and fills `kit.md` (concept brief, character
   bibles) + `shotlist.json`, and writes copy-paste-ready prompts:
   - **IMAGE phase:** Qwen-Image 3.0 prompts (still frames, 9:16)
   - **VIDEO phase:** Wan image→video motion prompts (upload the still, animate)
3. **Paste** — Jace pastes each prompt into Qwen Chat and saves the output into
   `kits/<slug>/frames/` (~10-15 min per ~5 shots, free, rate-limited to ~a movie/day).
   Paid upgrade: same shot list → NightCafe Seedance/Kling for 1080p + strict
   character lock. No scraping, no ToS risk on either path.
4. **Assemble** — the agent runs `assemble.py <slug>`: QC (frame presence,
   playability, aspect), then `make_short.py` renders the final vertical MP4 —
   Ken Burns on stills, direct cut on video clips, Piper TTS narration, optional
   bg-music bed. Free-tier 720p frames get upscaled automatically.

## Commands
```
python3 new_kit.py "a 60s music video about a lighthouse keeper"
python3 assemble.py <slug>                 # QC + render
python3 assemble.py <slug> --duration 45   # override runtime
```

## Shotlist schema
`shots[]`: `frame` (image or mp4 under the kit), `text[]` (overlay + TTS lines;
empty = clean shot), `tones` (seconds). Top-level: `runtime`, `voice`, `lang`,
`layout` (default `fullbleed`), `tts_speed`, `bg_music` (local audio, read-only),
`text_bg` (theme box behind text: earth/wind/fire/water or hex).

## Budget note
Free path first (Qwen Chat: a few gens/day, 1080p 30s, native audio). Only buy
credits when a paid job demands 1080p character-locked work — pre-sell a
commission before upgrading (NightCafe or Higgsfield). No fully-free commercial
path exists on either paid platform; free tiers are watermarked/personal-use.