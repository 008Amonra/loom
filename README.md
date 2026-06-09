# 008Amonra / loom

Asset hosting for [45DGOF8](https://45dgof8.com) — a one-person studio building AI agents, audio stories, and weird signals.

## What lives here

- **Agent Services** — landing page for AI automation services: custom agents, n8n workflows, talking head videos
- **Morning Signals** — daily (ish) audio story series. Sci-fi, odd signals, small wonders
- **Product catalog** — cups, art prints, merch from the Etsy shop (hosted here because Pinterest blocks direct Etsy feeds)
- **German Hörspiel** — "Die Letzte Frequenz", a short audio drama in German
- **Talking head pipeline** — Piper TTS → SadTalker → MP4 video, all CPU local

## Why this repo exists instead of a subfolder on 45dgof8.com

The custom domain 45dgof8.com is served through Fastly CDN which caches aggressively and returns stale results for subdirectory paths. New filenames do serve fresh, so all assets use absolute URLs pointing to:

```
https://008amonra.github.io/loom/
```

This bypasses the CDN and serves current content directly from GitHub Pages.

## Stack

- Static HTML/CSS/JS — no frameworks, no build step, no dependencies
- Piper TTS + SadTalker for voice/face animation
- n8n for workflow automation (local, Cloudflare tunnel)
- Local LLMs (llama-server, Gemma 4 12B QAT)

## Contact

45dgof8@gmail.com
