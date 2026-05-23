#!/usr/bin/env node
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const nodemailer = require('nodemailer');
const Imap = require('imap');

const CONFIG_FILE = path.join(__dirname, 'email-credentials.enc.json');

function deriveKey(passphrase, salt) {
  return crypto.pbkdf2Sync(passphrase, salt, 600000, 32, 'sha256');
}

function decrypt(encryptedPath, passphrase) {
  const blob = JSON.parse(fs.readFileSync(encryptedPath, 'utf-8'));
  const salt = Buffer.from(blob.salt, 'base64');
  const iv = Buffer.from(blob.iv, 'base64');
  const data = Buffer.from(blob.data, 'base64');
  const key = deriveKey(passphrase, salt);
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
  decipher.setAuthTag(data.subarray(data.length - 16));
  const decrypted = decipher.update(data.subarray(0, data.length - 16)) + decipher.final('utf-8');
  return JSON.parse(decrypted);
}

function getTransport(config, accountName) {
  const account = config[accountName];
  if (!account) throw new Error(`Account "${accountName}" not found`);
  return nodemailer.createTransport({
    host: account.smtp || 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: { user: account.email, pass: account.appPassword },
  });
}

async function send(config, accountName, to, subject, text) {
  const account = config[accountName];
  const transport = getTransport(config, accountName);
  const info = await transport.sendMail({
    from: account.email, to, subject, text,
  });
  transport.close();
  return info;
}

async function list(config, accountName) {
  const account = config[accountName];
  return new Promise((resolve, reject) => {
    const imap = new Imap({
      user: account.email,
      password: account.appPassword,
      host: account.imap || 'imap.gmail.com',
      port: 993,
      tls: true,
    });
    const emails = [];
    imap.once('ready', () => {
      imap.openBox('INBOX', true, (err, box) => {
        if (err) { reject(err); return; }
        const f = imap.seq.fetch(`1:${Math.min(box.messages.total, 10)}`, {
          bodies: ['HEADER.FIELDS (FROM TO SUBJECT DATE)'],
          struct: true,
        });
        f.on('message', (msg, seqno) => {
          msg.on('body', (stream) => {
            let body = '';
            stream.on('data', chunk => body += chunk.toString());
            stream.on('end', () => {
              const header = Imap.parseHeader(body);
              emails.push(header);
            });
          });
        });
        f.once('end', () => { imap.end(); resolve(emails); });
        f.once('error', reject);
      });
    });
    imap.once('error', reject);
    imap.connect();
  });
}

async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (cmd === 'encrypt-test') {
    // Test: encrypt some data for verification
    const salt = crypto.randomBytes(32);
    const iv = crypto.randomBytes(12);
    const key = deriveKey('test', salt);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    const enc = cipher.update(JSON.stringify({test: true}), 'utf-8') + cipher.final('utf-8');
    const tag = cipher.getAuthTag();
    console.log(JSON.stringify({
      salt: salt.toString('base64'),
      iv: iv.toString('base64'),
      data: Buffer.concat([Buffer.from(enc, 'utf-8'), tag]).toString('base64'),
    }));
    return;
  }

  const configPath = args[1] || CONFIG_FILE;
  if (!fs.existsSync(configPath)) {
    console.error('Config not found:', configPath);
    console.error('Usage: node email-tool.js <send|list> [config-path]');
    process.exit(1);
  }

  const passphrase = process.env.EMAIL_PASSPHRASE;
  if (!passphrase) {
    console.error('Set EMAIL_PASSPHRASE environment variable');
    process.exit(1);
  }

  let config;
  try {
    config = decrypt(configPath, passphrase);
  } catch (e) {
    console.error('Decryption failed. Wrong passphrase?');
    process.exit(1);
  }

  if (cmd === 'list') {
    const accountName = args[2] || Object.keys(config)[0];
    const emails = await list(config, accountName);
    console.log(JSON.stringify(emails, null, 2));
  } else if (cmd === 'send') {
    const accountName = args[2];
    const to = args[3];
    const subject = args[4];
    const text = args[5];
    if (!accountName || !to || !subject) {
      console.error('Usage: email-tool.js send <account> <to> <subject> <text>');
      process.exit(1);
    }
    const info = await send(config, accountName, to, subject, text);
    console.log('Sent:', info.messageId);
  } else {
    console.error('Commands: send, list');
    process.exit(1);
  }
}

main().catch(err => { console.error(err); process.exit(1); });
