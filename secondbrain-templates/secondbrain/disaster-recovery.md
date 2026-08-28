# Disaster Recovery — Second Brain

> How to revive this knowledge system after a machine wipe or drive failure.
> Every path here is a *template* — replace with your actual machine/locations.

## What "the brain" consists of
- The **Obsidian vault** — notes, memory, session log, recovery maps.
- The **skills** — the agent↔vault bridge (`obsidian-*` skills).
- The **plugin** — Obsidian Local REST API (lets tools/agents talk to the vault).
- The **persistence** — session wrapper + bootstrap + wakeup routine.

## Step 0 — Prerequisites for a clean machine
```bash
# A working OS + these:
sudo apt update && sudo apt install -y curl git
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install --lts
```

## Step 1 — Reinstall the agent
```bash
curl -fsSL https://opencode.ai/install | bash
export PATH="$HOME/.opencode/bin:$PATH"
```

## Step 2 — Reinstall the second brain
```bash
# From the loom repo clone (or directly via the hosted URL):
curl -fsSL https://008amonra.github.io/loom/install-obsidian-secondbrain.sh | bash
```
This recreates the vault, plugin, skills, and scaffolding.

## Step 3 — Restore your actual notes (if you backed them up)
The scaffolding is just seeds. Your real notes come from backup:
```bash
# Example: restore an encrypted vault backup
#   tar -xzf obsidian-vault-*.tar.gz -C ~/Documents/
#   # then decrypt per your backup script's instructions
```

## Step 4 — Regenerate plugin secrets
On a fresh vault the Local REST API plugin generates a **new** API key and cert.
Open Obsidian → Settings → Community plugins → Local REST API → set/verify the key.
Agent tools that connect must be updated with the new key.

## Step 5 — Verify the loop
```bash
~/bin/oc            # start a persistent agent session
# in the agent: /save-session, then /resume-session to confirm persistence
```

## Critical file inventory
| File | Why it matters |
|---|---|
| `Memory.md` | Long-term facts |
| `Session Log.md` | History + pending |
| `wakeup.md` | Write-ahead checkpoint |
| `secondbrain/disaster-recovery.md` | This map |
| `.obsidian/plugins/*/data.json` | Per-vault plugin secrets (do NOT share) |

## Quick recovery command
```bash
curl -fsSL https://008amonra.github.io/loom/install-obsidian-secondbrain.sh | bash
```
Then restore your notes from backup and regenerate plugin keys.
