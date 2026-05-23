# AI Email Agent – Beta Setup Guide

Welcome beta tester! This guide gets you from zero to sending/receiving email via AI in ~10 minutes.

## What you get

- Send email from up to 3 Gmail accounts via AI
- Read recent emails (IMAP)
- Telegram bot integration
- Your passwords stay encrypted (AES-256, passphrase never stored)

## Prerequisites

- Gmail account(s) with 2FA enabled
- A Telegram account + phone
- Node.js 22+ installed
- opencode (or any MCP-compatible AI client)

## Setup

### 1. App passwords (one per Gmail account)

1. Go to https://myaccount.google.com/apppasswords
2. Generate a 16-character app password (looks like: `xxxx xxxx xxxx xxxx`)
3. Save it – you'll need it in step 3

### 2. Telegram bot (optional but recommended)

1. Open Telegram, search `@BotFather`
2. Send `/newbot`, pick a name and username
3. Copy the bot token (`1234567890:ABCdef...`)

### 3. Encrypt your credentials

1. Open `email-agent/credentials.html` in your browser
2. Enter your Gmail accounts + app passwords
3. Choose a passphrase → click "Encrypt & Save"
4. Download the file → save as `email-agent/email-credentials.enc.json`

### 4. Wire it up

1. Run `npm install` in the `email-agent/` folder
2. Add the bot token to `~/.opencode/opencode.json` under `telegram` → `TG_BOT_TOKEN`
3. Message your bot on Telegram (`/start`) → get your chat ID from `TG_ALLOWED_IDS`

### 5. Launch

```bash
cd email-agent
./mail.sh
```
Enter your passphrase (invisible – no echo) → opencode starts → you're ready.

## Usage

Just tell your AI:

- *"Send an email to john@example.com from 'Gmail 1' with subject 'Proposal' and body 'Hi John...'"*
- *"Show me my last 5 emails"*
- *"Send via Telegram: I'll be there in 10 minutes"*
- *"Check Telegram for new messages"*

## Security

- Your passphrase is **never stored** – enter it fresh each session
- Credentials are encrypted with AES-256-GCM + PBKDF2 (600K iterations)
- Decryption happens in memory only, per request, then dropped
- No plaintext passwords in logs or config files

## Troubleshooting

| Problem | Fix |
|---|---|
| `self-signed certificate` error | TLS proxy? Set `tls: { rejectUnauthorized: false }` in MCP server |
| Telegram bot not responding | Make sure you message the bot `/start` first |
| SMTP fails | Check app password, not your regular Gmail password |
| IMAP fails | Verify IMAP is enabled in Gmail settings |

---

*Questions? Feedback? You're a beta user – your input shapes the product.*
