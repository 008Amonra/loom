#!/usr/bin/env node
const Imap = require('imap');
const { inspect } = require('util');

const ENC = '/home/jace/45dgof8/email-agent/email-credentials.enc.json';
const TG_TOKEN = process.env.TG_BOT_TOKEN;
const TG_CHAT = '5032947163';

const crypto = require('crypto');
const fs = require('fs');

function decrypt(pp) {
  const blob = JSON.parse(fs.readFileSync(ENC, 'utf-8'));
  const salt = Buffer.from(blob.salt, 'base64');
  const iv = Buffer.from(blob.iv, 'base64');
  const data = Buffer.from(blob.data, 'base64');
  const key = crypto.pbkdf2Sync(pp, salt, 600000, 32, 'sha256');
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
  decipher.setAuthTag(data.subarray(data.length - 16));
  return JSON.parse(decipher.update(data.subarray(0, data.length - 16)) + decipher.final('utf-8'));
}

async function main() {
  const pp = process.env.EMAIL_PASSPHRASE;
  if (!pp) { console.log('No EMAIL_PASSPHRASE'); process.exit(1); }
  const cfg = decrypt(pp);
  const acct = cfg['Gmail 3']; // 45dgof8@gmail.com
  if (!acct) { console.log('Gmail 3 not found'); process.exit(1); }

  const seen = new Set();
  try {
    const d = fs.readFileSync('/tmp/email-watch-seen.json', 'utf-8');
    JSON.parse(d).forEach(id => seen.add(id));
  } catch {}

  const emails = await new Promise((resolve, reject) => {
    const imap = new Imap({
      user: acct.email, password: acct.appPassword,
      host: 'imap.gmail.com', port: 993, tls: true,
      tlsOptions: { rejectUnauthorized: false },
    });
    const results = [];
    imap.once('ready', () => {
      imap.openBox('INBOX', false, (err, box) => {
        if (err) { reject(err); return; }
        imap.search(['UNSEEN'], (err, uids) => {
          if (err || !uids || !uids.length) { imap.end(); resolve([]); return; }
          const f = imap.fetch(uids.slice(-5), { bodies: ['HEADER.FIELDS (FROM SUBJECT DATE)'], struct: true });
          f.on('message', (msg) => {
            msg.on('body', (stream) => {
              let body = '';
              stream.on('data', c => body += c.toString());
              stream.on('end', () => {
                const h = Imap.parseHeader(body);
                results.push({ uid: msg.seqno, from: (h.from || [''])[0], subject: (h.subject || [''])[0], date: (h.date || [''])[0] });
              });
            });
          });
          f.once('end', () => { imap.end(); resolve(results); });
          f.once('error', reject);
        });
      });
    });
    imap.once('error', reject);
    imap.connect();
  });

  let changed = false;
  for (const e of emails) {
    if (!seen.has(e.uid)) {
      seen.add(e.uid);
      changed = true;
      const from = e.from.replace(/@.*/, '@...');
      const msg = `📬 ${e.subject}\nFrom: ${from}\n${e.date}`;
      try {
        await fetch(`https://api.telegram.org/bot${TG_TOKEN}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chat_id: TG_CHAT, text: msg }),
        });
      } catch {}
    }
  }
  if (changed) fs.writeFileSync('/tmp/email-watch-seen.json', JSON.stringify([...seen]));
}

main().catch(() => {});
