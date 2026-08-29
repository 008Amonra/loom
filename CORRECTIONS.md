# CORRECTIONS — 45dgof8 service pack

A running journal of root-cause fixes made on this machine, framed so each one is
portable. Every entry answers three questions:

1. **What broke** — symptom observed.
2. **Why** — the root cause (not the band-aid).
3. **Fix + portability** — the durable change, and how to re-apply it on a future
   system / offer it to someone else.

Use this to: reproduce fixes on fresh installs, catch repeat patterns early, and
excerpt into a sellable "corrections service" offering.

---

<!-- Newest on top. Tag cards: INFRA / SEC / PROC / WEB / AUTOMATION -->

## 2026-08-30 — systemd unit crash-loop from a port taken by a manual process (INFRA)

**What broke.** `command-center.service` sat in `activating (auto-restart)` and each
attempt exited `status=1/FAILURE`. The dashboard did load, but from a stray
manually-launched `server.py` (a different process), so the systemd unit was
fighting the port with no winner — a latent single-point-of-truth split.

**Why.** A `python3 server.py` had been started by hand earlier and held `:42042`.
When systemd started its own instance, `HTTPServer` raised
`Address already in use` → exit 1 → unit auto-restarted → same failure, forever.

**Fix.**
- `systemctl --user stop command-center.service`
- `kill <manual-pid>`
- `systemctl --user start command-center.service`
- Verify ownership: `ss -ltnp | grep :42042` → `users:(("python3",pid=<systemd-pid>))`
  and unit `Active: active (running)`.

**Portability.** Classic "two processes, one socket" failure. Golden rule:
a service should bound to a port via **one** owns-it process — either a systemd
unit *or* a manual run, never both. On a fresh box, check
`ss -ltnp` ownership before blaming the unit, and ensure only one launcher is
enabled. A reboot-proof setup is systemd-owned (manual processes die on logout/boot).

---

## 2026-08-30 — n8n backup storm: orphaned subprocesses on timeout (PROC)

**What broke.** The command-center health check ran an n8n workflow export as a
subprocess with a 15s timeout; when it timed out, the child kept running (and
forking) in the background, spamming the process table until I found hundreds of
leftover procs. The n8n service itself was fine — it was our *checker* leaking.

**Why.** `subprocess.run(timeout=15)` kills only the direct child on timeout, not
the child's own spawned children. If the export process forks (n8n/node spawns
workers or a task runner), the grandchildren survive the "kill" and keep running.
A second retry in the code doubled the leak window.

**Fix.** In `healthcheck.py`:
- launch the subprocess with `start_new_session=True`,
- on `TimeoutExpired`, kill the **process group** with `killpg(..., SIGKILL)` instead
  of just the PID,
- raise the export timeout 15s → 120s,
- drop the double-retry (single run, cleaned up properly).

**Portability.** Any script that runs long/daemonizing children under a timeout
leaks them the same way. Rule: **timeout a process group, not a PID.** When wrapping
children that can fork their own processes (node, gunicorn, ffmpeg pools, workers),
use `start_new_session=True` + `killpg` on timeout. Applies to cron checks, health
monitors, and any "run this and give up if slow" automation.

---

## 2026-08-29/30 — domain-switch asset/resource fallout (WEB)

**What broke.** After 45dgof8.com moved from the `45dgof8_ComplianceSuite` repo to
`loom`, several pages referenced assets/URLs that only existed under the old repo:
relative `/loom/chat.html` and product images `cups-products/...`, plus a nav link
that loaded from the now-404 old root.

**Why.** The site's canonical URL changed (repo swapped), but content still baked in
paths that resolved against the old origin. Relative/root-relative links and
assets tied to the previous mount point broke the moment the domain owner changed.

**Fix.**
- Chat button `/loom/chat.html` → `/chat.html` (absolute, matches new root).
- cups product images `cups-products/${p.img}` → absolute
  `https://45dgof8.com/cups-products/${p.img}`.
- Back link `href="/"` → `https://45dgof8.com/`.
- "GPT Hub" nav → "Legacy GPT Hub" pointing to the still-alive archive repo URL.

**Portability.** When migrating a site between repos/hosters, search for **relative
and root-relative** references (images, links, forms, nav) and think in terms of
the *new* canonical origin, not the old mount. Rule: after any domain/repo swap,
grep for `href="/…"`, `src="…products/…"`, `../`, and `loom/`-style prefixes and
rewrite to absolute URLs against the new root. Domain migration is a link-rewrite
audit, not just a DNS change.

---
