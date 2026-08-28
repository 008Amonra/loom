# Session Persistence

## What
A session that survives terminal close, SSH disconnect, and (if the machine stays
up) reboot. Uses `abduco` (a lightweight terminal multiplexer) so the agent keeps
running detached in the background.

## The `oc` wrapper
| Command | What it does |
|---|---|
| `oc` | Start or reattach to the agent session |
| `oc list` | List active sessions |
| `oc kill` | Terminate the session |
| `oc detach` | Detach (Ctrl+\\ by default) |

## Files
- `~/bin/oc` — wrapper script
- `~/bin/abduco` — the static binary (or system `abduco`)

## Recovery flow
Terminal crashed / SSH dropped:
1. Open a new terminal
2. `oc` — reattaches to the still-running session
3. `/resume-session` — reload context from last checkpoint

Machine rebooted (session killed):
1. `oc` — starts fresh
2. `/resume-session` — picks up from last checkpoint

## Checkpointing
Slash commands inside the agent:
- `/save-session` — write full state to a dated checkpoint
- `/resume-session` — load the most recent checkpoint

Best practice: `/save-session` before closing or at milestones.

## If broken
- `which abduco` / check `~/bin/abduco` exists and is executable
- `which oc` / check `~/bin/oc` exists and is executable
- `oc list` — is a session still alive?
- Missing abduco: `sudo apt install abduco` or `brew install abduco`
