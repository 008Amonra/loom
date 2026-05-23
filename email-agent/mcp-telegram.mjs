#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const BOT_TOKEN = process.env.TG_BOT_TOKEN;
const ALLOWED_IDS = (process.env.TG_ALLOWED_IDS || "").split(",").filter(Boolean);
const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

async function api(method, body) {
  const r = await fetch(`${API}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return r.json();
}

const server = new McpServer({ name: "telegram-bot", version: "1.0.0" });

server.tool(
  "tg_me",
  {},
  async () => {
    const r = await api("getMe");
    return { content: [{ type: "text", text: JSON.stringify(r.result, null, 2) }] };
  }
);

server.tool(
  "tg_send",
  {
    chat_id: z.union([z.string(), z.number()]),
    text: z.string(),
  },
  async (args) => {
    const r = await api("sendMessage", {
      chat_id: args.chat_id,
      text: args.text,
    });
    if (r.ok) return { content: [{ type: "text", text: `✅ Gesendet an ${args.chat_id}` }] };
    return { content: [{ type: "text", text: `❌ ${r.description}` }] };
  }
);

server.tool(
  "tg_recent",
  {
    limit: z.number().min(1).max(50).default(10),
  },
  async (args) => {
    const r = await api("getUpdates", {
      timeout: 0,
      allowed_updates: ["message"],
    });
    if (!r.ok) return { content: [{ type: "text", text: "❌ " + r.description }] };
    const messages = (r.result || [])
      .filter(u => u.message && u.message.text)
      .sort((a, b) => b.message.date - a.message.date)
      .slice(0, args.limit);

    if (messages.length === 0) {
      return { content: [{ type: "text", text: "📭 Keine Nachrichten." }] };
    }
    const lines = messages.map((u, i) => {
      const m = u.message;
      return `${i + 1}. [${new Date(m.date * 1000).toLocaleString()}] von ${m.from?.first_name || "?"} (@${m.from?.username || "?"}): ${m.text}`;
    });
    return { content: [{ type: "text", text: lines.join("\n") }] };
  }
);

server.tool(
  "tg_send_jace",
  {
    text: z.string(),
  },
  async (args) => {
    const results = [];
    for (const chatId of ALLOWED_IDS) {
      const r = await api("sendMessage", { chat_id: parseInt(chatId), text: args.text });
      results.push(r.ok ? `✅ ${chatId}` : `❌ ${chatId}: ${r.description}`);
    }
    return { content: [{ type: "text", text: results.join("\n") || "❌ No recipients configured." }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
