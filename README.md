# 45dgof8 — AI Agent Studio

One-person studio. AI agents, automation, tools. Based in Switzerland.

## Products

- **[YT Producer](https://yt-producer.45dgof8.com/landing)** — YouTube Shorts generator. Multi-frame comic-movie editor with AI voiceover, Ken Burns zoom, crossfades. Free trial → $19/mo or $97 lifetime.
- **[Tools Hub](https://tools.45dgof8.com)** — 8 free micro-SaaS tools: PDF merge, PDF compress, image compress, text diff, QR code generator, JSON formatter, color palette extractor, video→GIF.
- **Agent Services** — Custom AI agents, n8n workflows, Telegram bots, ChatGPT integrations.
- **[Chat](https://n8n.45dgof8.com/webhook/chat)** — AI chat powered by GPT-4o-mini via n8n.

## Infrastructure

All self-hosted on Pop!_OS, exposed via Cloudflare Tunnel:

| Service | Port | Stack |
|---------|------|-------|
| YT Producer | 5005 | Flask + FFmpeg + Piper TTS |
| Tools Hub | 5006 | Flask + Pillow + Ghostscript |
| n8n | 5678 | Workflow automation + GPT |
| Telegram Bot | — | n8n → GPT webhook |
| Cloudflare Tunnel | — | agent-n8n, yt-producer, tools, n8n |

## Contact

45dgof8@gmail.com · [PayPal.Me](https://paypal.me/45dgof8)

---

Built with FFmpeg, Flask, Piper TTS, and too much caffeine.
