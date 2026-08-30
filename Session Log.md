
## 2026-07-01

### YT Producer
- Fixed 0-byte third frame bug — empty `new Blob([])` files now detected and replaced with black fallback
- Hardened error handler with nested try/except
- Added audio X button to clear per-frame audio uploads
- Moved style tokens hint into frame textarea area (was hidden near bg music section)
- Created `/report-error` POST endpoint + frontend crash reporter (5s rate limit, logs to `.error-reports.log`)
- All changes tested and server running

### FFmpeg
- Root cause of exit code 183: 0-byte third image file from browser empty blob upload
- Render took ~2min on 8000x4500 images with complex zoompan/crop/drawtext filter chain

### Health
- System healthy: 16 ok, 1 warning (stale backups), 0 critical
- Memory 11/15Gi, Disk 72%, CPU load normal
- All services running: n8n, YT Producer, Tools, Command Center, Cloudflare tunnel

### Pending
- YouTube Data API v3 not yet enabled in Google Cloud Console
- n8n backups stale (161h)
- User to test generation with 3 real images, then YouTube publish

## 2026-07-03

### YT Producer — Crop normalisation & focus control
- Verified crop normalisation fix: slider 0-maxPct now maps to 0-100% of overhang (1920x1080 → x=1313 at max = far right edge)
- Identified that `crop_9_16_filter` returns None for already-9:16 images (1080x1920 cutout from landscape) — crop slider does nothing
- Ken Burns focus_x mechanism built (backend + frontend focus-mode) but reverted at Jace's request (was in old thread, will restart fresh)
- Explained presets: intro/services/testimonial/promo fill first frame text templates, endcard adds new black frame with gold subscribe text

### Pending
- Focus-mode for 9:16 images needs re-implementation in fresh session
- ±64px Ken Burns focus range may need widening depending on actual usage

## 2026-07-12

### Session summary
- TB1 now mounted at `/media/jace/tb11` (was tb1) — working, 77% full
- 4ofcups physically disconnected (not a failure)
- YT Producer service was inactive — restarted, now active
- Cleaned ~530MB from safe caches (puppeteer, node-gyp, tracker3, huggingface)
- LM Studio cache (11GB) — sacred, untouched per Jace
- Blog returns 200 at `https://008amonra.github.io/loom/blog/`
- `45dgof8.com/blog/` still 404 — custom domain points to ComplianceSuite repo, not loom

### Pending
- Gumroad listing for Productivity Agent (t-006, overdue)
- ComfyUI evaluation (t-013)
- Housing: waiting on Feldmeilen landlord reply
- Cloudflare analytics for blog
- Disk cleanup needs sudo (journal 504MB, LM Studio 11GB)

## 2026-07-30 — English-only voice assistant + terminal transcript

### Voice assistant (all scripts)
- voice-loop, voice-setup, record, voice-loop-toggle: German language references removed
- System prompt → English, TTS always English Piper (en_US-lessac-medium)
- Whisper language: de→en in all scripts
- voice-setup wizard: all spoken prompts converted to English
- Terminal now shows readable transcript: `[HH:MM] You: ... / Assistant: ...`
- German Piper model kept on disk (109 MB) but unused

### Disk cleanup
- All 7 remaining Docker images removed (2.96 GB freed)
- Mozilla cache, npm cache, pip cache, thumbnails cleared
- Jace removed 4 old Snap revisions + apt cache via sudo
- Disk: 73% (58 GB free) — from 98% peak

### Decisions
- Voice-loop stays on local Gemma 3 for privacy. NOT connected to terminal agent.
- English-only voice output consistently across all scripts

## 2026-07-31 (evening) — voice-assistant in installers + deploy

### Done
- install.sh: voice-assistant block added (curl https://008amonra.github.io/loom/voice-assistant → ~/bin, chmod +x) + Commands line
- install.ps1: new section 3 (voice-assistant → %USERPROFILE%\bin, user PATH added) + Commands line, sections renumbered
- agent-services.html: "Voice access" card (blind: speech, deaf: live transcript) next to n8n card
- Committed + pushed d9b9811 (4 files: install.sh, install.ps1, agent-services.html, voice-assistant)
- URL verified live (HTTP 200, byte-identical to local), downloaded copy runs (--help OK)

### Decisions
- Ship voice-assistant from repo root (GitHub Pages path = curl URL), no separate CDN
- Only voice-assistant added to ps1 — speak/v-toggle/voice-button are bash-only scripts

## 2026-08-29 — SEO launch + newsletter homepage dual stars (opencode)

### SEO launch (github.io side = primary)
- Pushed empty commit ad437e7 to force GH Pages rebuild from main.
- 008amonra.github.io/loom now serves correct 40KB portfolio fresh.
- 45dgof8.com custom-domain STILL serves stale GPT Hub page — edge CDN cache stuck (known "force rebuild v3" fight); left unresolved.
- Applied SEO to index.html (commit f2df82b): +36 lines — Organization + WebSite JSON-LD, canonical, batusi video link. JSON-LD validated. Backup in /tmp/opencode/.

### Newspaper homepage — batusi star restored
- Root cause of "batusi star disappeared": big gold homepage star pointed to to_enter_5d; batusi only had tiny muted footer star-link.
- Replaced single TO_ENTER_5D star in src/pages/index.astro with TWO gold stars:
  1. TSG PROMPT FORGE -> https://45dgof8.com/TSG-prompt-forge.html
  2. BATUSI -> https://youtu.be/FubBF-zmPNY
- Rebuilt (118 pages) + restarted newspaper-astro.service. LIVE verified.
- Drafted seo-proposals/batusi-yt-copy.md (paste-ready title/desc with keyword + site link).

### Pending
- Jace: paste new batusi title/description into YouTube Studio.
- Custom domain edge cache may need GH Pages UI re-verify (manual).
## 2026-08-29 — newsletter: "Search on YouTube" button
- Added a `.button-link` "Search on YouTube" button to the Les Discrets / Arctic Plateau article (src/content/articles/les-discrets-arctic-plateau.md) linking to https://www.youtube.com/results?search_query=Les+Discrets+Arctic+Plateau. Rebuilt + restarted newspaper-astro.service. Live. (Minor change.)

## 2026-08-29 — newspaper public page watchdog
- Added hourly systemd user timer + script `~/bin/newspaper-page-watch.sh`.
- Verifies newspaper.45dgof8.com homepage + rotating ~12 of 118 built pages for HTTP 200, logs to /tmp/newspaper-page-watch.log (no email/alert, log auto-trimmed to 200 lines).
- Live now: timer enabled+active, next run 14:54, test run 0 failed.

## 2026-08-29 — fixes (domain switch fallout)
- Fixed Open Chat button in `index.html`: `/loom/chat.html` (404 on 45dgof8.com) -> `/chat.html` (200). Commit `25f2427`, pushed, verified live on 45dgof8.com.
- Fixed newspaper daily Field Archive artwork: was loading from `45dgof8.com/*.webp` (now 404 after domain switch) -> repointed to `008amonra.github.io/45dgof8_ComplianceSuite/*.webp`. Rebuilt + restarted astro, verified image 200.
- Repointed "GPT Hub" nav link in `index.html` (was circular self-link to 45dgof8.com/) -> "Legacy GPT Hub" -> https://008amonra.github.io/45dgof8_ComplianceSuite/ so old tools stay reachable. Commit `80c19fc`, verified live.
- Built new "Everything Hub" page `hub.html` (https://45dgof8.com/hub.html): curated Eva + AI family (Eva, TSG, Dion, LinguaNode translator), Compliance & Trust (Global/GDPR-Nibbler/LGPD/PIPEDA/POPIA/APPI/USA/Australia/FADP), Creative & Fun (CatArt, GalacticChoices, ListGenius, Cups), Utilities (Pulse, DNS). All links -> live archive. Commit `a415c44`.
- Added "Hub" link to index.html nav. Verified live: hub.html 200 on 45dgof8.com.
- cups.html fix (ARCHIVE repo): product images were relative `cups-products/${p.img}` (broken from archive, no such folder) + back link `href="/"` (pointed at portfolio root). Changed to absolute `https://45dgof8.com/cups-products/${p.img}` and back -> `https://45dgof8.com/`. Pushed 847ccdf to 45dgof8_ComplianceSuite/main (cloned to /tmp/opencode/ccs-archive, SSH remote). **NOT live yet** — repo's github-pages env has required_reviewers (008Amonra), deploy stuck in "waiting" until Jace approves the deployment review in GH UI (or removes the gate). Two GH "Deployment review" emails received.
- Hub countries (loom repo): added Peru (PDP), Mexico (LFPDPPP), India, Indonesia compliance GPT cards to hub.html compliance section. Commit 0787e33, pushed, verified live on 45dgof8.com/hub.html (all 4 present).
- Built new "Assistant" page assistant.html at https://45dgof8.com/assistant.html — presents the AI helper (Big Pickle/opencode) as a valuable engineering partner: what it does (fix at root, security-first, build real things, back up first), recent wins (n8n fix, domain rescue, watchdog, hub, content repair, email triage), on-brand dark/Cinzel/neon theme. Added "Assistant" link to index.html nav. Commit 7ae957d, pushed to loom, verified live 200 + nav link present.
- TO-DO for Jace: cancel NetFlix subscription (noted in session, he asked to be reminded).
- NightCafe subscription cancel confirmed intentional (email #2 Gmail 3) — he cancelled it; no action needed.
- Built new accessibility page accessibility.html at https://45dgof8.com/accessibility.html — "Made Accessible". Dedicated page for the needy, reachable but not primary (footer links on index/hub/assistant). Two-mode "click here, show begins" design: Blind/Visually impaired (screen-reader friendly + high-contrast toggle via body.hc, localStorage persist) and Deaf/Hard of hearing (text-only mode with 45dgof8 explained in words). Plus text-size controls, reduce-motion toggle, skip-to-content link, aria-labels, prefers-reduced-motion support. Honest note that any media needing captions/transcripts can be provided on request. Commit 2619534, pushed to loom, verified live 200 + footer links on 3 pages. JS syntax checked + interaction logic simulated OK.
- Also confirmed cups.html archive fix now LIVE (images -> https://45dgof8.com/cups-products/, back -> https://45dgof8.com/) after Jace approved the GH deployment review.

## 2026-08-30 — nomad status tile on command-center
- Jace approved Option 1: nomad drift-detector tile on the command-center dashboard (localhost:42042).
- Added `get_nomad_status()` to /home/jace/command-center/server.py — reports FREE-tier health only: installed (project dir), watch_active (live `cli.py watch`/alarm detector proc), running = installed && watch_active, plus informational dashboard_running/last_scan_age_sec pulled from nomad's own /api/health on :5010. Also added to /api/status + render_page grid tile ("Nomad Drift Detector", green dot "watching · last scan Ns ago", sub "drift detector on ::5010").
- Kept free/Pro boundary clean: OK dot driven by free-tier detector; Pro web UI surfaced as informational only, no subscription gate.
- Fixed pre-existing infra issue: command-center.service was crash-looping (activating auto-restart, exit 1) because a manually-launched server.py (PID 1013883) held :42042. Per Jace's approval (Option A): stopped unit, killed manual PID, started unit cleanly. Now single systemd-owned process, active(running), holds :42042 (PID 1181339), crash-loop silenced, service reboot-proof.
- Verified live: /api/status returns nomad {installed:true, watch_active:true, running:true, dashboard_running:true, last_scan_age_sec:~38, ok:true}; rendered HTML shows the green "watching" tile. n8n/telegram/tunnel/chat_webhook tiles intact.
- Note for Jace: browser tab at localhost:42042 will auto-refresh every 30s; the tile reflects live scan age.

## 2026-08-30 — corrections journal (service pack)
- Jace asked to keep a durable journal of root-cause corrections so they can be repackaged as a service-pack for future iterations/system offers.
- Created `CORRECTIONS.md` in repo root — dual-purpose (internal engineering knowledge + easily excerptable for a client-facing offering).
- Format per entry: What broke → Why (root cause) → Fix → Portability (how to re-apply / offer to others). Tag cards: INFRA / SEC / PROC / WEB / AUTOMATION. Newest on top.
- Backfilled from this session: (1) systemd unit crash-loop from manual process holding the port (INFRA), (2) n8n backup storm from orphaned subprocesses on timeout (PROC), (3) domain-switch asset/resource fallout (WEB). Future corrections go here, newest first.

## 2026-08-30 — homepage redesign: GPT link fix (legacy hub)
- Jace approved pointing the ~21 GPT "Homepage" catalog links from the 404ing 45dgof8.com/...html to the legacy hub `https://008amonra.github.io/45dgof8_ComplianceSuite/...`.
- Rewrote all `h:` fields (and the 3 that used `c:` for detail pages — GalacticChoices, CatArt, DNS) in `/tmp/opencode/homepage-playground/homepage.html` to the legacy hub base. Percent-encoded the LinguaNode™ `/™/` -> `/®%E2%84%A2/` path for browser safety.
- All 26 legacy homepage URLs verified HTTP 200.
- Dead ChatGPT channels found + handled: ListGeniusGPT (`g-j1EuI5Coa*`) and Pulse (`g-67d8be...`) both return 404 (unpublished/removed) — cleared their `c` ChatGPT button, kept the working Homepage button.
- Remaining single "FAIL" is Etsy shop 403 = Etsy bot firewall (valid link, works in real browser).
- Final: 27 of 27 tools render, 46 unique catalog links all resolve (only Etsy bot-blocked). Playground still live at http://127.0.0.1:8899/homepage.html.
- NEXT: visual iteration with Jace (theme colors, catalog grouping, pricing/contact), mobile 390px check, then copy into loom as preview page, commit+push, and only swap as homepage after final approval.

## 2026-08-30 — homepage preview deployed live (new-index.html)
- Per Jace's choice (keep homepage as a SEPARATE page, not appended to agent-services — appending would break both standalone HTML docs), deployed the new homepage prototype to loom as `new-index.html`.
- Fixed dangling LinguaNode image ref (`linguanode256.webp` doesn't exist anywhere — 404 on loom + legacy hub + raw github) -> cleared `i:` so the card degrades to no-thumbnail instead of a broken image.
- Nav targets referenced by the new page all confirmed present in loom (accessibility, agent-services, ambient, apps, assistant, chat, hub, tools).
- Committed ONLY `new-index.html` + Session Log (commit 6f1f858, pushed). Real `index.html` untouched.
- Verified live: https://45dgof8.com/new-index.html = 200, renders 27/27 tools, data-theme ember; https://45dgof8.com/ still old homepage (unchanged).
- NEXT (gated on Jace approval of the design): add nav link to index.html/hub, then swap new-index -> index.html as the real homepage.

## 2026-08-30 — homepage restructure (agent-services becomes home)
- Jace decisions: (1) agent-services = the brand/homepage design; (2) GPT catalog = secondary page with icons added; (3) old confusing index kept at legacy URL.
- Restructure (in loom repo, commit pending):
  - `index.html` is now the agent-services content (the real homepage). Old homepage moved to `legacy.html`.
  - `agent-services.html` is now an instant redirect to `/` (preserves all inbound links, no duplicate content).
  - Canonicalized all 10 stale `008amonra.github.io/loom/...` links in the new homepage -> `45dgof8.com/...`; removed a redundant footer link; added `id="contact"` and repointed the contact link `-> #contact`.
  - Added a "📚 Browse the GPT Family" button in the homepage's "Enter the Realm" invitation card -> `new-index.html`.
  - `new-index.html` (secondary GPT catalog): added the `loom-figure.webp` hero image, the "may the RIGHT Answer be with you" signature, and repointed its primary CTA from agent-services.html -> `/` ("🏠 Homepage").
- Safety: git tag `homepage-restore-before-restructure-2026-08-30` + tarball at /tmp/opencode/loom-restore-2026-08-30/ BEFORE changes.
- Verified: inline JS syntax OK on index + new-index; new-index renders 27/27 tools + new iconography; legacy 200; agent-services redirect works.
- NEXT: commit only intended files, push, verify all URLs live (/, legacy.html, new-index.html, agent-services redirect); then show Jace.

### DEPLOY + VERIFY (this session, same day)
- Committed (a86da33) + pushed restructure to loom main. Auto-deployed to 45dgof8.com (~40-45s).
- Verified all 4 URLs live HTTP 200: `/` (agent-services home: "Agent Services", "What is 45dgof8", "Enter the Realm", "Browse the GPT Family"), `/agent-services.html` (meta-refresh redirect), `/new-index.html` (GPT catalog), `/legacy.html` (retired old homepage).
- Memory close-out: wakeup.md + jobs.json (homepage backlog -> done_summary) + knowledge graph entity updated to COMPLETE.
- Main homepage locked/approved; further iconography iterations (if any) go to secondary new-index.html only.

## 2026-08-30 — TSG Prompt Forge link placed (Creative & Fun + homepage)
- Jace: "TSG Prompt Forge" = app to generate pictures/animations for YouTube (NOT a tech-support tool) — so it does NOT belong on the TSG Tech Support GPT card.
- Reverted my earlier misplacement on the TSG GPT card (new-index `p:` field + hub.html "TSG Prompt Forge" link) — hub.html back to original.
- Placed it properly:
  - new-index.html: standalone entry in the "Creative & Fun" catalog group (28 of 28 tools now), homepage link -> https://45dgof8.com/TSG-prompt-forge.html, desc "pictures and animations for your YouTube content".
  - index.html (homepage): dedicated "TSG Prompt Forge" card (🎬) before the "What is 45dgof8?" About block, green "🧭 Open the Forge" button.
- Verified: JS syntax OK (28 tools renders), homepage card structure correct sibling, hub reverted clean.

## 2026-08-30 — nomad enhancement protocol (standing)
- Jace green-lit: when idle at night, if the sophisticated articles mention something NEW, prototype a NON-DISRUPTIVE UPGRADE FOR nomad (drift detector, dashboard :5010, cli.py watch + alarm detector) — build nomad features/improvements FROM the new techniques.
- NOT testing against nomad; enhancing it. Constraint: non-disruptive — no breaking prod state/running services.
- Filed in jobs.json backlog for cross-session persistence.

## 2026-08-30 — fix /loom/ 404 links (canonicalize to root)
- Root cause: site is GitHub Pages with 45dgof8.com as custom domain → served at ROOT; but ~100 links still used the old /loom/ prefix from the github.io/loom project-page path → all 404 on 45dgof8.com. NOT related to the ufw firewall work.
- Fixed: replaced relative `/loom/` → `/` in all live HTML files (apps, blog/*, automation-services, beta, video-services, trashbox/gpt-hub). Now /chat.html, /blog/, /apps.html, images, mp3s, install.sh, sec-toolkit.sh etc. all resolve 200 at root (verified locally).
- Preserved absolute `https://008amonra.github.io/loom/...` legacy canonical URLs intact (restored the /loom/ segment my sed had stripped, incl. artist-profile + legacy footer hrefs).
- Safety: pre-edit backup of all 25 touched files at /tmp/opencode/loom-link-fix-backup/.
- Verified: 10/10 converted links return 200 locally; js untouched. NEXT: commit only the 11 changed HTML files + this log, push, verify live.

## 2026-08-30 — contact form: add Telegram option (homepage)
- Added "✈️ Message me on Telegram" button (https://t.me/Jace_mail_bot) under the "Get in touch" section on homepage (index.html), alongside the existing email mailto form.
- Verified assistant.html + hub.html (blind/deaf accessibility + hub sibling pages) have NO /loom/ links — clean, all resolve at root. accessibility.html = 200 live.
