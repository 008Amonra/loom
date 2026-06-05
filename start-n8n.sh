#!/usr/bin/env bash
set -e
export WEBHOOK_URL=https://agent-n8n.45dgof8.com

# Chat API — set your key here for the phone chat PWA
# Supported: OpenRouter (free tier), OpenAI, or any OpenAI-compatible API
# export CHAT_API_KEY=sk-or-v1-your-key-here
# export CHAT_API_URL=https://openrouter.ai/api/v1/chat/completions
# export CHAT_MODEL=openai/gpt-4o-mini
# Don't set N8N_SECURE_COOKIE=false in production - needed for HTTP-only local dev
exec n8n start
