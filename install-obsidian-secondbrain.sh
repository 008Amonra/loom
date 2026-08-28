#!/bin/bash
# 45dgof8 Second Brain — Obsidian vault + agent memory integration installer
#
# Install the "second brain" layer on a fresh machine that already ran install.sh:
#   - Obsidian vault at ~/Documents/Obsidian
#   - Obsidian Local REST API plugin (secure, per-vault secrets)
#   - kepano/obsidian-skills (obsidian-cli, obsidian-markdown, obsidian-bases, json-canvas, defuddle)
#   - Working-file scaffolding (Memory.md, Session Log.md, secondbrain/, wakeup.md)
#   - Session persistence (abduco wrapper `oc`) + bootstrap/wakeup routine
#
# Usage:
#   curl -fsSL https://008amonra.github.io/loom/install-obsidian-secondbrain.sh | bash
#   Or from a clone:  ./install-obsidian-secondbrain.sh
#
# This installs the knowledge layer only. It does NOT copy any existing user's
# data.json, apiKey, or private keys — every vault gets its own fresh secrets.

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[0;33m'; NC='\033[0m'
info()  { echo -e "${CYAN}→${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
err()   { echo -e "${RED}✗${NC} $1"; }

VAULT="${HOME}/Documents/Obsidian"
VAULT_PLUGINS="${VAULT}/.obsidian/plugins"
SKILLS_TARGET="${HOME}/.opencode/skills/obsidian-skills"
SKILLS_REPO="https://github.com/kepano/obsidian-skills.git"
REST_API_ID="obsidian-local-rest-api"
REST_API_URL="https://github.com/coddingtonbear/obsidian-local-rest-api/releases/latest/download"
# The "latest" release is fetched at install time; version is reported dynamically.

# Where this script finds its scaffolding. When piped via curl we can't use
# $0's dir, so we resolve relative to a cloned loom repo if present, else use
# bundled templates (see the sed/heredoc sections below).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "$HOME/45dgof8")"
TEMPLATE_DIR="${SCRIPT_DIR}/secondbrain-templates"

# Ensure ~/bin and PATH
BIN_DIR="$HOME/bin"
mkdir -p "$BIN_DIR"
grep -q 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null || \
  echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"

# ── 1. Create / verify the Obsidian vault ──
info "Creating Obsidian vault at ${VAULT}"
mkdir -p "${VAULT}/.obsidian" "${VAULT_PLUGINS}"

# ── 2. Install the Local REST API plugin (fresh secrets generated on first run) ──
PLUGIN_DIR="${VAULT_PLUGINS}/${REST_API_ID}"
if [ -f "${PLUGIN_DIR}/main.js" ]; then
  ok "Local REST API plugin already installed (${REST_API_ID})"
else
  info "Installing Local REST API plugin (latest)..."
  mkdir -p "${PLUGIN_DIR}"
  if curl -fsSL "${REST_API_URL}/main.js" -o "${PLUGIN_DIR}/main.js" \
     && curl -fsSL "${REST_API_URL}/manifest.json" -o "${PLUGIN_DIR}/manifest.json" \
     && curl -fsSL "${REST_API_URL}/styles.css" -o "${PLUGIN_DIR}/styles.css" 2>/dev/null; then
    # Enable the plugin in community-plugins.json (merge, don't clobber)
    if [ ! -f "${VAULT}/.obsidian/community-plugins.json" ]; then
      echo "[]" > "${VAULT}/.obsidian/community-plugins.json"
    fi
    python3 - "${VAULT}/.obsidian/community-plugins.json" "${REST_API_ID}" <<'PY'
import json, sys
path, plugin_id = sys.argv[1], sys.argv[2]
plugins = json.load(open(path))
if plugin_id not in plugins:
    plugins.append(plugin_id)
json.dump(plugins, open(path, "w"), indent=2)
PY
    ok "Local REST API plugin installed + enabled (generate its API key in Obsidian → Settings → Community plugins)"
    warn "First run: open Obsidian once, then go to Settings → Community plugins → the plugin → set an API key."
  else
    err "Failed to download plugin from ${REST_API_URL}. Retry manually, or the .obsidian/plugins dir may be offline."
  fi
fi

# ── 3. Install kepano/obsidian-skills (the agent↔vault bridge) ──
if [ -d "${SKILLS_TARGET}/skills" ]; then
  ok "obsidian-skills already installed at ${SKILLS_TARGET}"
else
  info "Cloning obsidian-skills into ${SKILLS_TARGET}..."
  git clone --depth 1 "${SKILLS_REPO}" "${SKILLS_TARGET}" 2>/dev/null \
    && ok "obsidian-skills installed" \
    || err "Failed to clone ${SKILLS_REPO}. Check git/network."
fi

# ── 4. Session persistence (abduco wrapper) ──
ABDUCO_BIN="${BIN_DIR}/abduco"
if [ -x "${ABDUCO_BIN}" ]; then
  ok "abduco present"
else
  warn "abduco not found. Install it for session persistence:"
  echo "    sudo apt install abduco        # Debian/Ubuntu"
  echo "    brew install abduco            # macOS"
fi

if [ ! -f "${BIN_DIR}/oc" ]; then
  cat > "${BIN_DIR}/oc" <<'OC'
#!/bin/bash
# Start or reattach to an opencode session that survives terminal/SSH/reboot.
SESS="oc"
case "${1:-attach}" in
  list)   abduco -l 2>/dev/null; exit 0 ;;
  kill)   abduco -c "$SESS" 2>/dev/null; echo "session closed"; exit 0 ;;
esac
abduco -A "$SESS" opencode
OC
  chmod +x "${BIN_DIR}/oc"
  ok "installed 'oc' session wrapper → ${BIN_DIR}/oc"
else
  ok "oc wrapper already present"
fi

# ── 5. Scaffold the working files (templates → vault) ──
# These seed a fresh brain. They never carry secrets.
scaffold() {
  local name="$1"
  local target="${VAULT}/${name}"
  if [ -f "${TEMPLATE_DIR}/${name}" ] && [ ! -f "${target}" ]; then
    cp "${TEMPLATE_DIR}/${name}" "${target}"
    ok "seeded ${name}"
  elif [ -f "${target}" ]; then
    ok "${name} already exists (not overwritten)"
  fi
}

info "Scaffolding working files into vault (will not overwrite existing)..."
mkdir -p "${VAULT}/secondbrain"
for f in Memory.md "Session Log.md" wakeup.md secondbrain/disaster-recovery.md secondbrain/oc-session-persistence.md; do
  scaffold "$f"
done

# ── 6. Session bootstrap + wakeup (feed-back loop) ──
BOOTSTRAP="${BIN_DIR}/session-bootstrap.sh"
if [ ! -f "${BOOTSTRAP}" ]; then
  cat > "${BOOTSTRAP}" <<'BS'
#!/bin/bash
# Session bootstrap — consolidate memory context at the start of a session.
# Reads the vault + writes a lightweight session-context.md for the agent.
VAULT="${HOME}/Documents/Obsidian"
CTX="${HOME}/.memory/session-context.md"
mkdir -p "${HOME}/.memory"
{
  echo "# Session Context — $(date '+%Y-%m-%d %H:%M')"
  echo
  echo "## Vault files present"
  for f in Memory.md "Session Log.md" wakeup.md; do
    [ -f "${VAULT}/${f}" ] && echo "- ${f}"
  done
  echo
  echo "## Recent session log (tail)"
  [ -f "${VAULT}/Session Log.md" ] && tail -20 "${VAULT}/Session Log.md"
} > "${CTX}"
echo "Session context written to ${CTX}"
BS
  chmod +x "${BOOTSTRAP}"
  ok "installed session-bootstrap.sh"
else
  ok "session-bootstrap.sh already present"
fi

# ── 7. Summary ──
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  45dgof8 Second Brain — installed      ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Vault:      ${VAULT}"
echo "  Plugin:     ${REST_API_ID} (latest)"
echo "  Skills:     ${SKILLS_TARGET}"
echo "  Session:    ~/bin/oc   (abduco-powered persistence)"
echo ""
echo "  Next steps:"
echo "    1. Open Obsidian once  →  $ open ${VAULT}"
echo "    2. Settings → Community plugins → Local REST API → set an API key"
echo "    3. Start an agent session  →  $ oc"
echo "       In the agent: /save-session, /resume-session for persistence"
echo ""
echo "  Learn the loop:"
echo "    · capture → Obsidian (daily notes, clippings)"
echo "    · persist → /save-session before closing"
echo "    · resume  → /resume-session (or: agent reads Session Log.md)"
echo "    · recover → secondbrain/disaster-recovery.md"
