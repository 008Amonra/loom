# Disk Rules — Jace's System

Last audit: 2026-07-29
Last cleanup: 2026-07-29 (freed ~2G)
Filesystem: Pop!_OS 22.04, ext4 on NVMe
Root disk: ~225G total, ~14G free (~94% used)

## Sacred — NEVER touch, delete, or modify

These are untouchable. No cleanup, no moving, no renaming.

| Path | Size | Why |
|------|------|-----|
| `~/.cache/lm-studio/` | 11G | LM Studio model cache. You explicitly said this stays. |
| `/media/jace/tb1/` | external | TB drive — never modify or delete anything. |
| `~/Music/` | external | Music library — never modify or delete. |

## Recovery — keep safe, do not touch

| Path | Size | Why |
|------|------|-----|
| `/media/jace/4ofcups/` | 167.7G ext4 | OCZ SSD, worst-case recovery disk. Revival backup lives here. |
| `/mnt/wwn-...-part1/` ("ext") | 168G NTFS | Same physical OCZ drive (sdd), secondary revival copy. |

## Agent directories — I create and manage these

These are my working directories. I own them fully.

| Path | Size | Purpose |
|------|------|---------|
| `~/45dgof8/` | 944M | Main workspace: ambient.html, nomad, healthcheck, revive.sh |
| `~/.opencode/` | 732M | My config: skills, MCP, agent setup |
| `~/.memory/` | 1M | Persistent memory: jobs, productivity, shared state |
| `~/.agents/` | 624K | Skills: banana-pro-director, cinema-worldbuilder, etc. |
| `~/.claude/` | 1.5G | Claude Code CLI config and cache |
| `~/.gstack/` | 7.4M | GStack browser skill config |

## Conditional — ask user before cleaning

These are safe to clean **conceptually**, but need explicit permission first.

| Path | Size | Question to ask |
|------|------|----------------|
| `~/.local/share/Trash/` | 1.4G | "Empty trash?" — always safe |
| `~/.local/share/flatpak/` | 4.1G | "Remove unused flatpak apps?" (currently: Obsidian, Melody, QDirStat, Calculator) |
| `~/.cache/ms-playwright/` | 622M | "Remove Playwright browser binaries?" (needed for gstack browsing) |
| `~/.cache/n8n/` | 62M | "Clear n8n cache?" |
| `~/.n8n-backups/` | 367M | "Remove old n8n backups?" |
| `~/.cache/mozilla/` | 128M | "Clear Firefox cache?" |
| `~/.npm/` | 236M | "Clear npm cache?" (`npm cache clean --force`) |
| `~/.cache/thumbnails/` | 83M | "Clear thumbnail cache?" |
| `~/.cache/tracker3/` | 69M | "Clear tracker3 index?" |
| `~/snap/` | 161M | "Remove snap packages?" (currently: chromium + runtime deps) |
| `~/.thunderbird/` | 1.1G | "Compact Thunderbird folders?" or "Archive old email?" |
| `~/.clamtk/` | 168M | "Remove ClamTK virus definitions?" |

## User data — I NEVER touch without explicit permission

| Path | Size | What it is |
|------|------|------------|
| `~/Pictures/` | 2.1G | ~530 loose images + 312M webp copies exist. Originals stay unless you say otherwise. |
| `~/Documents/pureos_laptop/` | 795M | Old laptop backup — contains tax returns (2020-2022, ~766M total). **Tax data is critical**, never touch. |
| `~/Documents/Tarot/` | 184M | Tarot image assets (converted to WebP already) |
| `~/Documents/stick/` | 125M | Stick figure project |
| `~/Documents/2026/` | 98M | 2026 documents |
| `~/Documents/png/` | 36M | Source PNGs (including bottle composite) |
| `~/Documents/Obsidian/` | 17M | Obsidian vault |
| `~/Documents/bewerbung/` | 17M | Job applications |
| `~/Telegram/` | 223M | Telegram desktop data |
| `~/Videos/` | 169M | Video files |
| `~/goa-frames/` | 132M | ~1063 PNG frames (160x120) — probably project output |
| `~/OpenMontage/` | 650M | Some project with AGENT_GUIDE.md etc. |

## App directories — user-installed, I don't touch

| Path | Size | What |
|------|------|------|
| `~/comfy/ComfyUI/` | 7.5G | ComfyUI (5.7G models + 1.7G .venv) |
| `~/apps/` | 1.4G | AppImages: Obsidian, LM Studio, OpenShot, Firefly, Zen |
| `~/pinokio/` | 648M | Pinokio app manager |
| `~/gfpgan/` | 187M | GFPGAN (face restoration) |
| `~/jan/` | 162M | Jan AI desktop |
| `~/node_modules/` | 101M | Global npm modules |

---

## Safe cleanup commands (always safe, confirmed)

These I can run without asking:

```bash
# Empty trash
rm -rf ~/.local/share/Trash/files/* ~/.local/share/Trash/expunged/*

# Clear thumbnails (they regenerate on demand)
rm -rf ~/.cache/thumbnails/*

# Clear tracker3 index (regenerates)
rm -rf ~/.cache/tracker3/*

# Vacuum journal logs (keep last 200M)
journalctl --vacuum-size=200M

# Remove old kernels (keeps current)
sudo apt autoremove --purge

# Clean apt cache
sudo apt clean

# Clear gnome-desktop-thumbnailer cache
rm -rf ~/.cache/gnome-desktop-thumbnailer/*
```

## Project-specific directories I use

| Directory | What I do there |
|-----------|-----------------|
| `~/45dgof8/` | Edit ambient.html, nomad.py, healthcheck.py, revive.sh |
| `~/45dgof8-newspaper/` | Edit Astro newspaper site |
| `~/45dgof8-agent/` | Agent config |
| `~/45dgof8-website/` | Website |
| `~/.config/systemd/user/` | Create/manage user services (e.g. newspaper-astro.service) |
| `~/.cloudflared/config.yml` | Tunnel config for newspaper |
| `~/graphify/` | Graphify output (rocket sim etc.) |

## Recovery TL;DR

If disk is critically full and you need space **right now**:

1. **Ask me** to empty trash (safest, biggest gain: ~1.4G)
2. **Ask me** to vacuum journal (another ~800M)
3. **Ask me** to clean apt cache (~120M)
4. **Ask me** if thumbnail/tracker3 caches are okay (~150M)
5. **Ask me** before touching flatpak, npm, playwright, n8n, snap, mozilla

Never run BleachBit. Never touch `~/.cache/lm-studio/`. Never touch external drives.
