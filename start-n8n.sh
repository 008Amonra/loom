#!/usr/bin/env bash
set -e
export WEBHOOK_URL=https://agent-n8n.45dgof8.com

# Chat API — set your key here for the phone chat PWA
# Supported: OpenRouter (free tier), OpenAI, or any OpenAI-compatible API
# Get key from .zshrc (OPENAI_API_KEY) or set manually
export CHAT_API_KEY=${OPENAI_API_KEY:?set OPENAI_API_KEY in .zshrc}
export CHAT_API_URL=https://api.openai.com/v1/chat/completions
export CHAT_MODEL=gpt-4o-mini
export N8N_BLOCK_ENV_ACCESS_IN_NODE=false
exec n8n start
