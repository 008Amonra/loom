import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BOT_TOKEN = process.env.TG_BOT_TOKEN;
const ALLOWED_IDS = (process.env.TG_ALLOWED_IDS || "5032947163").split(",").filter(Boolean);
const API = `https://api.telegram.org/bot${BOT_TOKEN}`;
const INBOX = path.join(__dirname, 'telegram-inbox.json');
const OFFSET_FILE = path.join(__dirname, 'telegram-offset.txt');

let lastOffset = 0;
if (fs.existsSync(OFFSET_FILE)) {
  lastOffset = parseInt(fs.readFileSync(OFFSET_FILE, 'utf8').trim()) || 0;
}

async function api(method, body) {
  const r = await fetch(`${API}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return r.json();
}

function loadInbox() {
  try {
    return JSON.parse(fs.readFileSync(INBOX, 'utf8'));
  } catch {
    return [];
  }
}

function saveInbox(messages) {
  fs.writeFileSync(INBOX, JSON.stringify(messages, null, 2));
}

function isAllowed(chatId) {
  return ALLOWED_IDS.includes(String(chatId));
}

async function poll() {
  try {
    const r = await api("getUpdates", {
      offset: lastOffset + 1,
      timeout: 30,
      allowed_updates: ["message"],
    });

    if (!r.ok) return;

    for (const update of r.result || []) {
      const updateId = update.update_id;
      if (updateId <= lastOffset) continue;
      lastOffset = updateId;

      const m = update.message;
      if (!m || !m.text) continue;
      if (!isAllowed(m.chat.id)) continue;

      const inbox = loadInbox();
      const entry = {
        id: updateId,
        chat_id: m.chat.id,
        from: m.from?.first_name || "?",
        username: m.from?.username || "?",
        text: m.text,
        date: new Date(m.date * 1000).toISOString(),
        replied: false,
      };

      if (inbox.length > 0 && inbox[inbox.length - 1].text === m.text &&
          (Date.now() - new Date(inbox[inbox.length - 1].date).getTime()) < 5000) {
        continue;
      }

      inbox.push(entry);
      saveInbox(inbox);

      await api("sendMessage", {
        chat_id: m.chat.id,
        text: `📨 Message received. Will respond when online.\n\n> ${m.text}`,
      });

      console.log(`[${entry.date}] ${entry.from}: ${m.text}`);
    }

    fs.writeFileSync(OFFSET_FILE, String(lastOffset));
  } catch (err) {
    console.error("Poll error:", err.message);
  }
}

const INTERVAL_MS = 10 * 60 * 1000;
const QUIET_START = 20;
const QUIET_END = 6;
const QUIET_OVERRIDE_FILE = path.join(__dirname, '.telegram-awake');

function shouldPoll() {
  if (fs.existsSync(QUIET_OVERRIDE_FILE)) return true;
  const h = new Date().getHours();
  if (h >= QUIET_START || h < QUIET_END) return false;
  return true;
}

function scheduleNext() {
  if (shouldPoll()) {
    poll();
  } else {
    console.log(`[${new Date().toISOString()}] Quiet hours (${QUIET_START}:00-${QUIET_END}:00). Skipping poll.`);
  }
}

console.log(`Telegram listener started. Polling every ${INTERVAL_MS/60000}min (quiet ${QUIET_START}:00-${QUIET_END}:00).`);
console.log(`Override: touch ${QUIET_OVERRIDE_FILE} to wake me up.`);
scheduleNext();
setInterval(scheduleNext, INTERVAL_MS);
