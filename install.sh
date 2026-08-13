#!/bin/bash
# 45dgof8 Agent Services — Cross-platform installer
# Usage: curl -fsSL https://008amonra.github.io/loom/install.sh | bash
# For Windows: curl -fsSL https://008amonra.github.io/loom/install.ps1 | powershell -c -

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}→${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
err()   { echo -e "${RED}✗${NC} $1"; }

# Detect OS
OS="$(uname -s)"
case "$OS" in
  Linux*)  PLATFORM="linux" ;;
  Darwin*) PLATFORM="macos" ;;
  *)       err "Unsupported: $OS"; exit 1 ;;
esac

info "45dgof8 Agent Services — installing for $PLATFORM"

# ── 1. Install opencode ──
if command -v opencode &>/dev/null; then
  ok "opencode already installed: $(opencode --version 2>/dev/null || true)"
else
  info "Installing opencode..."
  curl -fsSL https://opencode.ai/install | bash
  export PATH="$HOME/.opencode/bin:$PATH"
  if ! command -v opencode &>/dev/null; then
    err "opencode install failed — try manually: curl -fsSL https://opencode.ai/install | bash"
    exit 1
  fi
  ok "opencode installed"
fi

# ── 2. Configure opencode ──
CONFIG_DIR="$HOME/.config/opencode"
mkdir -p "$CONFIG_DIR"

# Prompt for provider
echo ""
echo "Select AI provider:"
echo "  0) LM Studio (local, free — needs LM Studio running)"
echo "  1) Anthropic Claude  (needs API key)"
echo "  2) OpenAI GPT        (needs API key)"
echo "  3) Custom            (any OpenAI-compatible endpoint)"
read -rp "Choice [0]: " PROVIDER_CHOICE
PROVIDER_CHOICE=${PROVIDER_CHOICE:-0}

case "$PROVIDER_CHOICE" in
  1)
    read -rsp "Enter your Anthropic API key (sk-...): " ANTHROPIC_KEY; echo
    cat > "$CONFIG_DIR/opencode.json" <<CONFIG
{
  "\$schema": "https://opencode.ai/config.json",
  "provider": {
    "anthropic": {
      "name": "Anthropic Claude",
      "apiKey": "$ANTHROPIC_KEY"
    }
  }
}
CONFIG
    ;;
  2)
    read -rsp "Enter your OpenAI API key: " OPENAI_KEY; echo
    cat > "$CONFIG_DIR/opencode.json" <<CONFIG
{
  "\$schema": "https://opencode.ai/config.json",
  "provider": {
    "openai": {
      "name": "OpenAI",
      "apiKey": "$OPENAI_KEY"
    }
  }
}
CONFIG
    ;;
  3)
    read -rp "Custom name: " CUSTOM_NAME
    read -rp "Base URL (e.g. http://localhost:1234/v1): " CUSTOM_URL
    read -rsp "API key (blank if none): " CUSTOM_KEY; echo
    cat > "$CONFIG_DIR/opencode.json" <<CONFIG
{
  "\$schema": "https://opencode.ai/config.json",
  "provider": {
    "custom": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "$CUSTOM_NAME",
      "options": {
        "baseURL": "$CUSTOM_URL",
        "apiKey": "${CUSTOM_KEY:-not-needed}"
      }
    }
  }
}
CONFIG
    ;;
  *)
    cat > "$CONFIG_DIR/opencode.json" <<CONFIG
{
  "\$schema": "https://opencode.ai/config.json",
  "provider": {
    "lmstudio": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "LM Studio (Local)",
      "options": {
        "baseURL": "http://127.0.0.1:1234/v1",
        "apiKey": "not-needed"
      }
    }
  }
}
CONFIG
    echo "  Note: The next step will help you get a local LLM running on port 1234"
    ;;
esac
ok "opencode configured"

# ── 3. Local LLM server — detect & guide (non-invasive) ──
# Checks whether a local LLM already answers on port 1234 (LM Studio, llama-server, ...).
# If not, shows a guided walkthrough instead of downloading anything automatically.
echo ""
echo "── Local LLM server ──"
echo "  opencode needs a local model server on port 1234"
echo "  (e.g. LM Studio, free, runs entirely on your machine)."
if curl -fsS -m 3 http://127.0.0.1:1234/v1/models >/dev/null 2>&1; then
  ok "LLM server already running on port 1234 — nothing to do."
else
  info "No LLM server detected on port 1234 yet."
  echo ""
  echo "  Guided setup (about 2 minutes, free, no account):"
  echo ""
  echo "    1. Download LM Studio:  https://lmstudio.ai  (Linux / macOS / Windows)"
  echo "    2. Open LM Studio → search for \"Gemma 3 4B\""
  echo "       and click Download (pick the Q4_K_M quant if asked)."
  echo "    3. Click the model to load it, then open the Developer tab"
  echo "       and press \"Start Server\" (port 1234)."
  echo ""
  echo "  Alternatively, from a terminal with LM Studio installed:"
  echo "      lms get lmstudio-community/gemma-3-4b-it-GGUF@Q4_K_M"
  echo "      lms server start -p 1234"
  echo ""
  echo "  Run a hardware check first? (picks the best model for your machine)"
  read -rp "  Run llmfit hardware check? [y/N]: " RUN_LLMFIT
  if [[ "$RUN_LLMFIT" =~ ^[Yy]$ ]]; then
    if command -v llmfit &>/dev/null; then
      llmfit recommend --cli --limit 3 2>/dev/null || true
      echo ""
      echo "  Full details saved to llmfit-recommendations.json"
      llmfit recommend --json --limit 3 2>/dev/null > llmfit-recommendations.json 2>/dev/null || true
    else
      info "Installing llmfit (hardware-aware model recommender)..."
      if command -v brew &>/dev/null; then
        brew install AlexsJones/llmfit/llmfit 2>/dev/null || true
      fi
      if ! command -v llmfit &>/dev/null; then
        curl -fsSL https://llmfit.axjns.dev/install.sh | sh -s -- --local 2>/dev/null || true
      fi
      if command -v llmfit &>/dev/null; then
        llmfit recommend --cli --limit 3 2>/dev/null || true
        echo ""
        echo "  Full details saved to llmfit-recommendations.json"
        llmfit recommend --json --limit 3 2>/dev/null > llmfit-recommendations.json 2>/dev/null || true
      else
        err "llmfit install failed — try: brew install llmfit"
      fi
    fi
  fi
  echo ""
  echo "  When the server is running, opencode connects automatically."
  echo "  Waiting for a server on port 1234... (press Enter once LM Studio is started)"
  read -rp "" _
  if curl -fsS -m 3 http://127.0.0.1:1234/v1/models >/dev/null 2>&1; then
    ok "LLM server detected on port 1234 — opencode will connect."
  else
    err "No server on port 1234 yet. You can start it later; opencode retries on launch."
  fi
fi

# ── 4. Optional: fully automatic local LLM setup (opt-in) ──
# Downloads Gemma 3 4B via LM Studio's CLI and starts the server — only if the
# user explicitly confirms. Nothing is downloaded without consent.
echo ""
echo "── Fully automatic LLM setup (optional) ──"
echo "  Downloads Gemma 3 4B (about 3 GB) and starts the server on port 1234."
echo "  Requires LM Studio's command-line tool (lms)."
read -rp "  Run fully automatic setup? [y/N]: " AUTO_LLM
if [[ "$AUTO_LLM" =~ ^[Yy]$ ]]; then
  if curl -fsS -m 3 http://127.0.0.1:1234/v1/models >/dev/null 2>&1; then
    ok "Server already running on port 1234 — skipping auto setup."
  elif command -v lms &>/dev/null; then
    info "Downloading Gemma 3 4B (Q4_K_M) via lms..."
    lms get lmstudio-community/gemma-3-4b-it-GGUF@Q4_K_M >/dev/null 2>&1 || true
    info "Loading model..."
    lms load lmstudio-community/gemma-3-4b-it-GGUF@Q4_K_M >/dev/null 2>&1 || true
    info "Starting server on port 1234..."
    lms server start -p 1234 >/dev/null 2>&1 || lms server start --port 1234 >/dev/null 2>&1 || true
    if curl -fsS -m 5 http://127.0.0.1:1234/v1/models >/dev/null 2>&1; then
      ok "LLM server running on port 1234 — done."
    else
      err "Server not up yet. Start it manually: lms server start -p 1234  (opencode retries on launch)."
    fi
  else
    err "lms not found — install LM Studio (https://lmstudio.ai) first, then rerun this step."
  fi
fi

# ── 5. Install utility scripts ──
BIN_DIR="$HOME/bin"
mkdir -p "$BIN_DIR"

# speak — cross-platform TTS
cat > "$BIN_DIR/speak" << 'SCRIPT'
#!/bin/bash
# 45dgof8 TTS — works on Linux (Piper) and macOS (say)
TEXT="${*:-$(cat)}"
case "$(uname -s)" in
  Darwin) say "$TEXT" ;;
  Linux)
    VOICE="$HOME/.local/share/piper/en_US-lessac-medium.onnx"
    if [ -f "$VOICE" ]; then
      echo "$TEXT" | piper --model "$VOICE" --output-raw 2>/dev/null | aplay -q -r 22050 -f S16_LE -c 1 2>/dev/null
    else
      echo "Piper voice not found. Install: download en_US-lessac-medium.onnx to ~/.local/share/piper/"
    fi
    ;;
esac
SCRIPT
chmod +x "$BIN_DIR/speak"

# v-toggle — voice input (Linux only for now)
cat > "$BIN_DIR/v-toggle" << 'SCRIPT'
#!/bin/bash
# 45dgof8 Voice Input Toggle — Linux only (needs arecord + Python)
LOCK="/tmp/v-record.lock"
WAV="/tmp/v-record.wav"

if [ -f "$LOCK" ]; then
  PID=$(cat "$LOCK")
  kill "$PID" 2>/dev/null; rm -f "$LOCK"
  notify-send -t 1500 "45dgof8" "Transcribing..."
  TEXT=$(python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('tiny', cpu_threads=4, num_workers=2)
segments, _ = model.transcribe('$WAV', language='en', beam_size=3)
print(' '.join(s.text.strip() for s in segments), end='')
" 2>/dev/null)
  if [ -z "$TEXT" ]; then notify-send -t 2000 "45dgof8" "Nothing heard"; exit 1; fi
  echo -n "$TEXT" | xclip -selection clipboard 2>/dev/null || echo -n "$TEXT"
  notify-send -t 3000 "45dgof8" "✓ $TEXT"
else
  rm -f "$WAV"
  arecord -f cd -t wav "$WAV" &
  echo $! > "$LOCK"
  notify-send -t 1500 "45dgof8" "Recording..."
fi
SCRIPT
chmod +x "$BIN_DIR/v-toggle"

# voice-button — clickable voice chat (click, speak 5s, hear reply)
cat > "$BIN_DIR/voice-button" << 'SCRIPT'
#!/bin/bash
# voice-button: click, speak 5s, hear Big Pickle reply
WAV="/tmp/voice-button.wav"
notify() { notify-send -t "$1" "Big Pickle" "$2" 2>/dev/null || echo "$2"; }
notify 2000 "Recording for 5 seconds..."
rm -f "$WAV"
arecord -f cd -t wav -d 5 "$WAV" 2>/dev/null
[ ! -f "$WAV" ] && notify 2000 "Recording failed" && exit 1
notify 1500 "Transcribing..."
TEXT=$(python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('tiny', cpu_threads=4, num_workers=2)
segments, _ = model.transcribe('$WAV', language='en', beam_size=3)
print(' '.join(s.text.strip() for s in segments), end='')
" 2>/dev/null)
[ -z "$TEXT" ] && notify 2000 "Nothing heard" && exit 1
notify 3000 "You: $TEXT"
REPLY=$(opencode run "$TEXT" 2>/dev/null | head -1)
[ -z "$REPLY" ] && notify 2000 "No response" && exit 1
clean=$(echo "$REPLY" | sed 's/^>.*//; s/^# //; s/^## //; s/\*//g; s/_//g' | head -1)
notify 5000 "$clean"
speak "$clean" 2>/dev/null
SCRIPT
chmod +x "$BIN_DIR/voice-button"

# voice-assistant — local web app for blind (speech) + deaf (live transcript) users
if [ -f "$BIN_DIR/voice-assistant" ]; then
  ok "voice-assistant already installed"
else
  info "Installing voice-assistant (blind + deaf local assistant)..."
  curl -fsSL https://008amonra.github.io/loom/voice-assistant -o "$BIN_DIR/voice-assistant" \
    && chmod +x "$BIN_DIR/voice-assistant" \
    && ok "voice-assistant installed — run 'voice-assistant'"
fi

# Desktop launcher for voice-button
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/big-pickle-voice.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Big Pickle Voice
Comment=Click, speak 5s, hear Big Pickle reply
Exec=voice-button
Icon=audio-input-microphone
Terminal=false
Categories=Utility;
Keywords=voice;speech;ai;chat;
StartupNotify=false
EOF

# Add ~/bin to PATH if not already there
grep -q 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null || \
  echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"

ok "utility scripts installed (speak, v-toggle, voice-button)"

# ── 6. Create project directory ──
PROJECT_DIR="$HOME/45dgof8-agent"
mkdir -p "$PROJECT_DIR"
ok "project directory: $PROJECT_DIR"

# ── 7. Welcome ──
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  45dgof8 Agent Services — installed   ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Next steps:"
echo "    1. source ~/.bashrc"
echo "    2. Pin 'Big Pickle Voice' to panel (right-click → Add to Panel)"
echo "    3. cd $PROJECT_DIR"
echo "    4. opencode"
echo ""
echo "  Commands:"
echo "    speak \"Hello\"    — text to speech"
echo "    voice-button      — click, speak 5s, hear Big Pickle reply"
echo "    v-toggle          — push-to-talk (press twice)"
echo "    voice-assistant   — blind + deaf assistant (opens in browser)"
echo "    llmfit            — model recommender (if installed)"
echo "    lms               — LM Studio CLI (download/start models)"
echo ""
echo "  Tip: Bind Super+V to 'voice-button' in COSMIC Settings → Keyboard → Shortcuts"

# Add to bashrc PATH if needed
grep -q "$HOME/.opencode/bin" "$HOME/.bashrc" 2>/dev/null || \
  echo 'export PATH="$HOME/.opencode/bin:$PATH"' >> "$HOME/.bashrc"
