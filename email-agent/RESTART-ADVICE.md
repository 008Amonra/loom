# How to restart me if I seem offline

## 1. First check: am I still running?

```bash
ps aux | grep opencode
```

If you see a process → I'm alive, might just be thinking. Wait 30s.

## 2. If not running → restart

```bash
cd ~/email-agent && ./mail.sh
```

Type your passphrase (blind entry, no echo) → I'll start with email + Telegram.

## 3. If the MCP servers are dead but I'm alive

Tell me:

```
Check if email and telegram MCP servers are working
```

I'll restart them from here.

## 4. If everything fails (nuclear option)

```bash
pkill -f opencode
# wait 2s
~/email-agent/mail.sh
```

## 5. Telegram fallback

Message `@Jace_mail_bot` on Telegram — the bot runs independently of me. I'll see your message when I come back.

---

Quick one-liner restore:

```bash
pkill -f opencode 2>/dev/null; sleep 1; ~/email-agent/mail.sh
```
