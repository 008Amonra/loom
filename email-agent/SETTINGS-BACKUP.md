# Settings Backup — Email & Telegram Agent

> Generated: May 2026 | Recreate everything from this file

---

## 1. Node.js

```
Version: v22.22.3
NPM:     10.9.8
Install: nvm (already installed)
```

## 2. Files & Locations

| Path | Content |
|---|---|
| `/home/jace/email-agent/` | MCP servers, credentials, scripts |
| `/home/jace/email-agent/mcp-email.mjs` | Email MCP server (send/list) |
| `/home/jace/email-agent/mcp-telegram.mjs` | Telegram MCP server |
| `/home/jace/email-agent/credentials.html` | Browser form for encrypted credential entry |
| `/home/jace/email-agent/email-credentials.enc.json` | AES-256-GCM encrypted Gmail credentials |
| `/home/jace/email-agent/mail.sh` | Launch script (blind passphrase entry → opencode) |
| `/home/jace/email-agent/package.json` | Dependencies: @modelcontextprotocol/sdk, nodemailer, imap |
| `/home/jace/email-agent/BETA-GUIDE.md` | English beta setup guide |
| `/home/jace/email-agent/README.md` | Full documentation (English) |
| `/home/jace/email-agent/RESTART-ADVICE.md` | How to restart when offline |
| `/home/jace/.opencode/opencode.json` | MCP + agent configuration |
| `/home/jace/.opencode/.env` | OBSIDIAN_VAULT_PATH |
| `/home/jace/.opencode/secrets.env` | BRAVE_API_KEY, OBSIDIAN_API_KEY |

## 3. MCP Servers (in opencode.json)

### email
```json
{
  "type": "local",
  "command": ["node", "/home/jace/email-agent/mcp-email.mjs"],
  "environment": {
    "EMAIL_CONFIG": "/home/jace/email-agent/email-credentials.enc.json",
    "EMAIL_PASSPHRASE": "{env:EMAIL_PASSPHRASE}"
  }
}
```

### telegram
```json
{
  "type": "local",
  "command": ["node", "/home/jace/email-agent/mcp-telegram.mjs"],
  "environment": {
    "TG_BOT_TOKEN": "8720707203:AAFGfmpO4xB56coYgmX8se8Qmaz1cLQ30UA",
    "TG_ALLOWED_IDS": "5032947163"
  }
}
```
- Bot username: `@Jace_mail_bot`
- Allowed chat IDs: `5032947163`

### Other MCP Servers
- `filesystem` → `/home/jace/node_modules/.bin/mcp-server-filesystem /home/jace`
- `memory` → `/home/jace/node_modules/.bin/mcp-server-memory`
- `puppeteer` → `/home/jace/node_modules/.bin/mcp-server-puppeteer` (env: DOCKER_CONTAINER=true)
- `brave-search` → npx `@modelcontextprotocol/server-brave-search` (env: BRAVE_API_KEY)
- `n8n` → SSE at `https://changes-snapshot-insert-ranger.trycloudflare.com/mcp-server/http` (Bearer token)
- `obsidian` → docker `mcp/obsidian` (env: OBSIDIAN_API_KEY, OBSIDIAN_VAULT_PATH)

## 4. Gmail Accounts

Three accounts configured in `email-credentials.enc.json`:
- `45dgof8.bot@gmail.com` (alias: "Gmail 1")
- `amonra.008@gmail.com` (alias: "Gmail 2 (Bot)")
- `45dgof8@gmail.com` (alias: "Gmail 3")

All use App Passwords. IMAP/SMTP requires `tls: { rejectUnauthorized: false }` due to network proxy.

## 5. Setup Steps (clean install)

```bash
# 1. Install dependencies
cd ~/email-agent && npm install

# 2. Open credentials.html in browser
#    - Enter Gmail accounts + app passwords
#    - Choose passphrase → Encrypt & Save
#    - Save as email-credentials.enc.json

# 3. Launch
~/email-agent/mail.sh
# type passphrase (blind entry) → opencode starts
```

## 6. Website

| Site | URL |
|---|---|
| Main | https://45dgof8.com |
| Beta | https://45dgof8.com/beta/ |
| Video services | https://45dgof8.com/video-services.html |
| Automation | https://45dgof8.com/automation-services.html |
| Agent services | https://45dgof8.com/agent-services.html |

Astro project: `/home/jace/45dgof8-newspaper/` (Astro v6.3.7)
Build: `npm run build` (in project dir)

## 7. n8n

| Config | Value |
|---|---|
| Location | `/home/jace/n8n-local/docker-compose.yml` |
| Container | `n8n-local` |
| Port | 5678 |
| URL | agent-n8n.45dgof8.com |
| Data volume | `n8n_data` (docker volume) |

## 8. Cron Jobs

```
0  2 * * * /home/jace/.opencode/auto-backup.sh          # Backup to external disk
15 3 * * * /home/jace/bin/backup-critical-folders.sh    # Critical folders backup
45 3 * * * /home/jace/.opencode/daily-backup.sh         # Daily backup
30 7 * * * /home/jace/.opencode/daily-briefing.sh       # Daily briefing
0  * * * * /home/jace/bin/backup-hourly.sh              # Hourly backup
```

## 9. Other Files of Note

| Path | Description |
|---|---|
| `/home/jace/email-agent-package.tar.gz` | Beta distribution package (24KB) |
| `/home/jace/goa-video-final.mp4` | Goa trance music video (30s, flow-field) |
| `/home/jace/goa-final-audio.wav` | Stereo Goa track |
| `/home/jace/synthwave-track.wav` | Synthwave track (60s) |
| `/home/jace/45dgof8-expansion-plan.md` | 3-phase business plan |
| `/home/jace/these_apps.txt` | Tool/app inventory |

## 10. Secrets NOT in this file

- EMAIL_PASSPHRASE (passphrase for encrypted credentials)
- Gmail App Passwords (inside encrypted email-credentials.enc.json)
- n8n Bearer token (in opencode.json, can be regenerated)
- BRAVE_API_KEY (in secrets.env)
- OBSIDIAN_API_KEY (in secrets.env)
