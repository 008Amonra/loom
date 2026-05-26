# Agent Skills

Implementable agent personas for solo creators. Each is a standalone CLI tool.

## Client Whisperer (`client-whisperer.mjs`)

Client intake, brief analysis, scope drift tracking, and revision quotes.

Usage:
```
node client-whisperer.mjs init "Project Name" "Brief description"
node client-whisperer.mjs brief "Project Name" "Client's message or @file"
node client-whisperer.mjs sign-off "Project Name" <scope>
node client-whisperer.mjs status ["Project Name"]
node client-whisperer.mjs scope-change "Project Name" "What changed"
node client-whisperer.mjs log-time "Project Name" <hours> "Description"
node client-whisperer.mjs quote "Project Name"
node client-whisperer.mjs close-out "Project Name" "Summary"
node client-whisperer.mjs help
```

Data stored in `whisperer-data/` (per-project JSON files).

## Planned

- **Deadline Ferret** — Milestone tracking, creative reminders, scope boundary enforcement
- **Budget Badger** — Cost tracking, API usage alerts, burn rate projection
