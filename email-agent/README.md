# Email & Telegram Agent – Setup Guide

> **Bonus for customers** – Fully configured AI mail assistant for opencode
>
> May 2026 | Author: Jace

---

## What This Package Does

| Feature | Status |
|---|---|
| **Send email** from up to 3 Gmail accounts | ✅ |
| **Read email** via IMAP (last 50) | ✅ |
| **Telegram bot** send & receive | ✅ |
| **Encrypted credentials** (AES-256-GCM, passphrase RAM-only) | ✅ |
| **Invisible passphrase entry** (`read -s`, no plaintext logs) | ✅ |

---

## Files

| File | Purpose |
|---|---|
| `credentials.html` | Browser form: enter Gmail accounts, export encrypted |
| `email-credentials.enc.json` | AES-256 encrypted credentials (exported from browser) |
| `mcp-email.mjs` | MCP server: send & read email |
| `mcp-telegram.mjs` | MCP server: Telegram bot send & receive |
| `mail.sh` | Launcher: asks passphrase (invisible), starts opencode |
| `email-tool.js` | CLI email tool (fallback) |

---

## Setup (for customers)

### 1. Prepare Gmail accounts

Create an **App Password** per Gmail account:

- https://myaccount.google.com/apppasswords
- Generate a 16-char password (e.g. `xxxx xxxx xxxx xxxx`)

### 2. Encrypt credentials

- Open `credentials.html` in your browser
- Enter account details + app passwords
- Choose a passphrase → **"Encrypt & Save"** → export
- Place `email-credentials.enc.json` in the `email-agent/` directory

### 3. Create Telegram bot

- In Telegram: `@BotFather` → `/newbot`
- Choose bot name + username → copy token
- In `~/.opencode/opencode.json`, under `telegram` → set `TG_BOT_TOKEN`
- Message your bot (`/start`) → chat ID is auto-detected
- Add it to `TG_ALLOWED_IDS`

### 4. Launch opencode

```bash
~/email-agent/mail.sh
# → type passphrase (blind, no echo)
# → opencode starts with email + Telegram MCP
```

---

## Usage

### Send email

```
Send an email to max@example.com from "Gmail 1"
Subject: Proposal
Body: Hi Max, ...
```

### Read email

```
Show me the last 5 emails from "Gmail 2 (Bot)"
```

### Telegram

```
Send via Telegram: "I'll be there in 10 minutes"
Check Telegram for new messages
```

---

## Security

- **Credentials** are AES-256-GCM encrypted (PBKDF2, 600,000 iterations)
- **Passphrase** is never stored — only `read -s` in the terminal
- **MCP servers** decrypt in RAM per tool call, discard after
- **Bot token** lives in opencode.json (can be moved to `{env:...}`)
- No plaintext passwords in logs

---

## Tech Stack

- **opencode** (AI client)
- **Node.js 22+** (MCP servers, nodemailer, imap)
- **Telegram Bot API** (HTTP, no SDK)
- **Web Crypto API** (client-side encryption in browser)
- **keepassxc-cli** (optional, for KeePass DB)

---
