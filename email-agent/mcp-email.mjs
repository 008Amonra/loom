#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import crypto from "crypto";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import nodemailer from "nodemailer";
import Imap from "imap";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CONFIG_PATH = process.env.EMAIL_CONFIG || path.join(__dirname, "email-credentials.enc.json");

function deriveKey(passphrase, salt) {
  return crypto.pbkdf2Sync(passphrase, salt, 600000, 32, "sha256");
}

function loadConfig(passphrase) {
  try {
    const blob = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf-8"));
    const salt = Buffer.from(blob.salt, "base64");
    const iv = Buffer.from(blob.iv, "base64");
    const data = Buffer.from(blob.data, "base64");
    const key = deriveKey(passphrase, salt);
    const decipher = crypto.createDecipheriv("aes-256-gcm", key, iv);
    decipher.setAuthTag(data.subarray(data.length - 16));
    const decrypted = decipher.update(data.subarray(0, data.length - 16)) + decipher.final("utf-8");
    return JSON.parse(decrypted);
  } catch {
    return null;
  }
}

function getPassphrase(args) {
  return args.passphrase || process.env.EMAIL_PASSPHRASE || null;
}

const server = new McpServer({
  name: "email-agent",
  version: "1.0.0",
});

server.tool(
  "email-status",
  {
    passphrase: z.string().optional().describe("Leave empty if EMAIL_PASSPHRASE env var is set"),
    reveal: z.boolean().optional().describe("Show account email addresses"),
  },
  async (args) => {
    const pp = getPassphrase(args);
    if (!pp) return { content: [{ type: "text", text: "❌ No passphrase. Set EMAIL_PASSPHRASE env var or pass it as parameter." }] };
    const config = loadConfig(pp);
    if (!config) return { content: [{ type: "text", text: "❌ Wrong passphrase or config not found." }] };
    const accounts = Object.keys(config);
    const list = args.reveal
      ? accounts.map(a => `  - ${a}: ${config[a].email}`).join("\n")
      : `  - ${accounts.length} account(s) configured`;
    return { content: [{ type: "text", text: `🔓 Authenticated\n${list}` }] };
  }
);

server.tool(
  "email-send",
  {
    passphrase: z.string().optional().describe("Leave empty if EMAIL_PASSPHRASE env var is set"),
    account: z.string().describe("Account name (e.g. 'Gmail 1', 'Gmail 2 (Bot)')"),
    to: z.string().describe("Recipient email address"),
    subject: z.string().describe("Email subject"),
    text: z.string().describe("Email body text"),
  },
  async (args) => {
    const pp = getPassphrase(args);
    if (!pp) throw new Error("No passphrase. Set EMAIL_PASSPHRASE env var or pass it as parameter.");
    const config = loadConfig(pp);
    if (!config) throw new Error("Wrong passphrase or config not found.");
    const account = config[args.account];
    if (!account) throw new Error(`Account "${args.account}" not found. Available: ${Object.keys(config).join(", ")}`);
    const transport = nodemailer.createTransport({
      host: account.smtp || "smtp.gmail.com",
      port: 587,
      secure: false,
      tls: { rejectUnauthorized: false },
      auth: { user: account.email, pass: account.appPassword },
    });
    const info = await transport.sendMail({
      from: account.email,
      to: args.to,
      subject: args.subject,
      text: args.text,
    });
    transport.close();
    return { content: [{ type: "text", text: `✅ Sent to ${args.to}\nMessage-ID: ${info.messageId}` }] };
  }
);

server.tool(
  "email-list",
  {
    passphrase: z.string().optional().describe("Leave empty if EMAIL_PASSPHRASE env var is set"),
    account: z.string().describe("Account name"),
    count: z.number().min(1).max(50).default(10).describe("Number of recent emails"),
    reveal: z.boolean().optional().describe("Show full email addresses"),
  },
  async (args) => {
    const pp = getPassphrase(args);
    if (!pp) throw new Error("No passphrase. Set EMAIL_PASSPHRASE env var or pass it as parameter.");
    const config = loadConfig(pp);
    if (!config) throw new Error("Wrong passphrase or config not found.");
    const account = config[args.account];
    if (!account) throw new Error(`Account "${args.account}" not found.`);

    const emails = await new Promise((resolve, reject) => {
      const imap = new Imap({
        user: account.email,
        password: account.appPassword,
        host: account.imap || "imap.gmail.com",
        port: 993,
        tls: true,
        tlsOptions: { rejectUnauthorized: false },
      });
      const results = [];
      imap.once("ready", () => {
        imap.openBox("INBOX", true, (err, box) => {
          if (err) { reject(err); return; }
          const total = box.messages.total;
          const start = Math.max(1, total - args.count + 1);
          const f = imap.seq.fetch(`${start}:${total}`, {
            bodies: ["HEADER.FIELDS (FROM TO SUBJECT DATE)"],
          });
          f.on("message", (msg) => {
            msg.on("body", (stream) => {
              let body = "";
              stream.on("data", chunk => body += chunk.toString());
              stream.on("end", () => {
                const parsed = Imap.parseHeader(body);
                results.push({
                  from: (parsed.from || [""])[0],
                  to: (parsed.to || [""])[0],
                  subject: (parsed.subject || [""])[0],
                  date: (parsed.date || [""])[0],
                });
              });
            });
          });
          f.once("end", () => { imap.end(); resolve(results); });
          f.once("error", reject);
        });
      });
      imap.once("error", reject);
      imap.connect();
    });

    const rows = emails.map((e, i) => {
      const from = args.reveal ? e.from : e.from.replace(/(.{3}).*(@.*)/, "$1***$2");
      return `${i + 1}. [${e.date}] ${from} – ${e.subject}`;
    });
    return { content: [{ type: "text", text: `📬 ${args.account} – letzten ${emails.length} Mails\n${rows.join("\n")}` }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
