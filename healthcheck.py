#!/usr/bin/env python3
"""45DGOF8 Infrastructure Health Check.

Usage:
  ./healthcheck.sh              # JSON output (default)
  ./healthcheck.sh --report     # Human-readable report
  ./healthcheck.sh --quiet      # Exit code only
"""
import json, os, signal, subprocess, sys, time, socket

MODE = sys.argv[1] if len(sys.argv) > 1 else "json"
TIMESTAMP = time.strftime("%Y-%m-%dT%H:%M:%S%z")
results = []
def add(status, label, detail, hint=""):
    results.append({"status": status, "label": label, "detail": detail, "hint": hint})

def run(cmd, timeout=10, input=None):
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, input=input,
            start_new_session=True,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return -1, "", "not found"
    except subprocess.TimeoutExpired as e:
        _kill_group(e.args[0])
        return -1, "", "timeout"

def _kill_group(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        pass

def pgrep(pattern):
    rc, out, _ = run(["pgrep", "-f", pattern])
    return rc == 0

# ── n8n ──
# Single-flight guard: only one n8n export may run at a time.
# Concurrent healthcheck invocations (command-center auto-refresh) would
# otherwise stack overlapping 120s exports, exhausting RAM/swap (HD "tornado").
N8N_LOCK = "/tmp/_n8n_health.lock"

healthz = run(["curl", "-sf", "--max-time", "5", "http://localhost:5678/healthz"])[0]
if healthz == 0:
    wf_dir = "/tmp/_n8n_health"
    n8n_cli = os.environ.get("N8N_CLI", "/home/jace/.local/bin/n8n")
    n8n_cmd = [n8n_cli]
    rc = -1
    if os.path.exists(N8N_LOCK):
        # A previous export is still running (or was interrupted). Do not pile on.
        add("warn", "n8n", "export already in progress — skipped (single-flight)", "check for stuck n8n export")
    else:
        try:
            open(N8N_LOCK, "w").close()
            rc, _, _ = run(n8n_cmd + ["export:workflow", "--backup", "--output", wf_dir], timeout=60)
        finally:
            try: os.remove(N8N_LOCK)
            except: pass
    if rc == 0 and os.path.isdir(wf_dir):
        files = [f for f in os.listdir(wf_dir) if f.endswith(".json")]
        wf_total = len(files)
        wf_active = 0
        for f in files:
            try:
                d = json.load(open(os.path.join(wf_dir, f)))
                if d.get("active"):
                    wf_active += 1
            except: pass
        for f in files:
            try: os.remove(os.path.join(wf_dir, f))
            except: pass
        try: os.rmdir(wf_dir)
        except: pass
    else:
        wf_total, wf_active = "?", "?"
    add("ok", "n8n", f"running — {wf_active}/{wf_total} workflows active", "http://localhost:5678")

    # Chat webhook test
    rc, out, _ = run(["curl", "-sf", "--max-time", "15",
        "https://agent-n8n.45dgof8.com/webhook/chat",
        "-X", "POST", "-H", "Content-Type: application/json",
        "-d", '{"message":"healthcheck ping"}'])
    if rc == 0 and out:
        try:
            content = json.loads(out).get("choices", [{}])[0].get("message", {}).get("content", "")[:80]
        except:
            content = out.strip()[:80]
        add("ok", "Chat Webhook", content, "POST /webhook/chat → local Gemma 3 4B")
    else:
        add("warn", "Chat Webhook", "webhook did not respond — n8n running but tunnel/webhook may be down", "check n8n workflow is active & WEBHOOK_URL matches tunnel")
else:
    add("crit", "n8n", "not responding on :5678", "run ~/45dgof8/start-n8n.sh")
    add("crit", "Chat Webhook", "n8n is down", "start n8n first")

# ── Tunnel ──
if pgrep("cloudflared tunnel run"):
    tunnel_pid = run(["pgrep", "-f", "cloudflared tunnel run"])[1].split("\n")[0] if run(["pgrep", "-f", "cloudflared tunnel run"])[0] == 0 else "?"
    try:
        socket.getaddrinfo("agent-n8n.45dgof8.com", 443)
        dns_ok = True
    except: dns_ok = False
    rc2, _, _ = run(["curl", "-sf", "--max-time", "5", "https://agent-n8n.45dgof8.com/healthz"])
    upstream = rc2 == 0
    if dns_ok and upstream:
        add("ok", "Tunnel", f"agent-n8n.45dgof8.com — reachable", "")
    elif dns_ok:
        add("warn", "Tunnel", f"DNS OK but upstream unreachable", "check n8n is running")
    else:
        add("warn", "Tunnel", f"DNS does not resolve", "check cloudflared tunnel status")
else:
    add("crit", "Tunnel", "cloudflared not running", "run: cloudflared tunnel run n8n-tunnel")

# ── Telegram ──
rc, _, _ = run(["systemctl", "--user", "is-active", "telegram-listen"], timeout=5)
add("ok" if rc == 0 else "warn", "Telegram", "active" if rc == 0 else "not running", "" if rc == 0 else "check systemctl --user status telegram-listen")

# ── Backups ──
backup_dir = "/home/jace/.n8n-backups"
total_size = ""
if os.path.isdir(backup_dir):
    snaps = sorted([d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))], reverse=True)
    if snaps:
        latest = snaps[0]
        age_h = (time.time() - os.path.getmtime(os.path.join(backup_dir, latest))) / 3600
        total_size = run(["du", "-sh", backup_dir])[1].split()[0] if run(["du", "-sh", backup_dir])[0] == 0 else "?"
        if age_h < 48:
            add("ok", "Backups", f"last: {latest} ({age_h:.0f}h ago) — total {total_size}", "")
        else:
            add("warn", "Backups", f"stale: last backup was {age_h:.0f}h ago", "run ~/45dgof8/n8n-timeshift.sh")
    else:
        add("warn", "Backups", "backup dir is empty", "run ~/45dgof8/n8n-timeshift.sh")
else:
    add("warn", "Backups", "no backup directory", "run ~/45dgof8/n8n-timeshift.sh")

# ── System Health ──
mem = run(["free", "-h"])[1]
mem_used_total = ""
for line in mem.split("\n"):
    if line.startswith("Mem:"):
        p = line.split()
        mem_used_total = f"{p[2]}/{p[1]}"
disk_line = run(["df", "-h", "/"])[1]
disk_used_pct = ""
for line in disk_line.split("\n"):
    if line.endswith("/"):
        p = line.split()
        disk_used_pct = f"{p[2]}/{p[1]} ({p[4]})"
        disk_pct = int(p[4].replace("%", ""))
uptime = run(["uptime", "-p"])[1].replace("up ", "")
load = run(["uptime"])[1]
load_avg = load.split("load average:")[1].strip() if "load average:" in load else "?"
cpu_cores = run(["nproc"])[1]

add("ok", "Memory", mem_used_total or "?")
if disk_pct > 90:
    add("crit", "Disk", disk_used_pct or "?")
elif disk_pct > 80:
    add("warn", "Disk", disk_used_pct or "?")
else:
    add("ok", "Disk", disk_used_pct or "?")
add("ok", "Uptime", uptime)
add("ok", "CPU Load", f"{load_avg} ({cpu_cores} cores)")

# ── External Drive (tb1) ──
rc, out, _ = run(["mountpoint", "-q", "/media/jace/tb1"])
if rc == 0:
    tb1_line = run(["df", "-h", "/media/jace/tb1"])[1]
    tb1_info = ""
    for line in tb1_line.split("\n"):
        if "tb1" in line or "/media/jace/tb1" in line:
            p = line.split()
            tb1_info = f"{p[2]}/{p[1]} ({p[4]})"
            tb1_pct = int(p[4].replace("%", ""))
    if tb1_pct > 95:
        add("warn", "External Drive", f"/media/jace/tb1 {tb1_info}", "")
    else:
        add("ok", "External Drive", f"/media/jace/tb1 {tb1_info}", "")
else:
    add("warn", "External Drive", "tb1 not mounted", "unlock + mount external drive")

# ── Command Center ──
if os.environ.get("COMMAND_CENTER_RUNNING"):
    add("ok", "Command Center", "running (self-check skipped)", "http://localhost:42042")
else:
    rc, _, _ = run(["curl", "-sf", "--max-time", "10", "http://localhost:42042/api/status"])
    if rc == 0:
        import urllib.request
        try:
            cv = json.loads(urllib.request.urlopen("http://localhost:42042/api/counter", timeout=3).read()).get("visits", "?")
        except:
            cv = "?"
        add("ok", "Command Center", f"running on :42042 — {cv} visits", "http://localhost:42042")
    else:
        add("crit", "Command Center", "not serving on :42042", "restart python3 ~/command-center/server.py")

# ── nomad ──
nomad_rc, nomad_out, _ = run(["curl", "-sf", "--max-time", "5", "http://localhost:5010/api/health"])
if nomad_rc == 0:
    try:
        health = json.loads(nomad_out)
        status = health.get("status", "unknown")
        age = health.get("last_scan_age_sec", 999)
        if status == "ok":
            add("ok", "nomad", f"scanning — last scan {int(age)}s ago", "http://localhost:5010")
        elif status == "stale":
            add("warn", "nomad", f"stale — last scan {int(age)}s ago (threshold: 120s)", "check nomad-watch.service")
        else:
            add("crit", "nomad", f"dead — last scan {int(age)}s ago", "systemctl --user restart nomad-watch.service")
    except:
        add("warn", "nomad", "running but health response unparseable", "http://localhost:5010/api/health")
else:
    add("crit", "nomad", "not serving on :5010", "systemctl --user restart nomad-dashboard.service")

# ── YT Producer ──
ytp_rc, ytp_out, _ = run(["curl", "-sf", "--max-time", "5", "http://localhost:5005/"])
if ytp_rc == 0 and "YT Producer" in ytp_out:
    add("ok", "YT Producer", "running on :5005", "http://localhost:5005")
else:
    add("crit", "YT Producer", "not serving on :5005", "systemctl --user start yt-producer.service")

# ── 45dgof8 Tools ──
tools_rc, tools_out, _ = run(["curl", "-sf", "--max-time", "5", "http://localhost:5006/tools"])
if tools_rc == 0 and "45dgof8 Tools" in tools_out:
    add("ok", "45dgof8 Tools", "running on :5006", "http://localhost:5006/tools")
else:
    add("crit", "45dgof8 Tools", "not serving on :5006", "systemctl --user start 45dgof8-tools.service")

# ── Tools ──
pinokio_installed = os.path.isfile("/home/jace/apps/Pinokio-7.2.6.AppImage")
pinokio_running = pgrep("Pinokio.*AppImage")
add("ok", "Pinokio", f"{'installed' if pinokio_installed else 'missing'} — {'running' if pinokio_running else 'stopped'}", "")

ace_installed = os.path.isdir("/home/jace/ACE-Step-1.5")
ace_running = pgrep("acestep.api_server|uv run acestep")
add("ok", "ACE-Step", f"{'installed' if ace_installed else 'missing'} — {'API running' if ace_running else 'offline'}", "")

comfy_installed = os.path.isdir("/home/jace/comfy/ComfyUI")
comfy_running = pgrep("comfyui|main\\.py.*comfy")
add("ok", "ComfyUI", f"{'installed' if comfy_installed else 'missing'} — {'running' if comfy_running else 'stopped'}", "")

# ── TLS ──
add("ok", "TLS", "Cloudflare-managed (auto-renew)", "")

# ── Build output ──
s_ok = sum(1 for r in results if r["status"] == "ok")
s_warn = sum(1 for r in results if r["status"] == "warn")
s_crit = sum(1 for r in results if r["status"] == "crit")
overall = "critical" if s_crit > 0 else "warning" if s_warn > 0 else "healthy"

payload = {
    "status": overall,
    "timestamp": TIMESTAMP,
    "summary": {"ok": s_ok, "warn": s_warn, "crit": s_crit},
    "results": results,
}

if MODE == "--report":
    icon_map = {"ok": "\u2713", "warn": "\u25b3", "crit": "\u2717"}
    sep = "\u2550" * 55
    print(sep)
    print(f"  45DGOF8 Health Report  \u00b7 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(sep)
    print(f"  Overall: {'CRITICAL' if overall == 'critical' else 'WARNING' if overall == 'warning' else 'HEALTHY'}")
    print(f"  Checks:  {s_ok} ok \u00b7 {s_warn} warnings \u00b7 {s_crit} critical")
    print()
    for r in results:
        print(f"  {icon_map[r['status']]} {r['label']}: {r['detail']}")
        if r["hint"]:
            print(f"       \u2514\u2500 {r['hint']}")
    print()
    print(f"  Timestamp: {TIMESTAMP}")
    print(sep)
elif MODE == "--quiet":
    pass
else:
    print(json.dumps(payload, indent=2))

sys.exit(2 if s_crit > 0 else 1 if s_warn > 0 else 0)
