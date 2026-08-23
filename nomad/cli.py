#!/usr/bin/env python3
"""
nomad CLI — Catch autonomous agents that spawn ephemeral infrastructure
and migrate fluidly between services.
"""

import argparse
import json
import sys
import time
import os
from datetime import datetime, timezone

from dataclasses import asdict
from nomad import NomadEngine, Scanner, Fingerprinter, Tracker

# ─── ANSI Colors ────────────────────────────────────────────
C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"
C_DIM    = "\033[2m"
C_BLINK  = "\033[5m"
C_GREEN  = "\033[38;5;46m"
C_TEAL   = "\033[38;5;51m"
C_CYAN   = "\033[38;5;87m"
C_LGRAY  = "\033[38;5;250m"
C_DGRAY  = "\033[38;5;240m"
C_RED    = "\033[38;5;196m"
C_ORANGE = "\033[38;5;208m"
C_YELLOW = "\033[38;5;226m"
C_AMBER  = "\033[38;5;214m"
C_SCORE_OK  = "\033[38;5;46m"
C_SCORE_MED = "\033[38;5;226m"
C_SCORE_HI  = "\033[38;5;208m"
C_SCORE_CR  = "\033[38;5;196m"

def _has_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"

NO_COLOR = not _has_color()

def c(code, text):
    if NO_COLOR:
        return str(text)
    return f"{code}{text}{C_RESET}"

def radar_line(i, total=12):
    """Single line of a radar sweep."""
    dots = ""
    for j in range(total):
        dist = abs(j - total // 2)
        if dist == 0:
            dots += "█"
        elif dist <= 1:
            dots += "▓"
        elif dist <= 2:
            dots += "▒"
        else:
            dots += "░"
    return dots

def score_color(score):
    if score >= 0.8: return C_SCORE_CR
    if score >= 0.6: return C_SCORE_HI
    if score >= 0.4: return C_SCORE_MED
    return C_SCORE_OK

def threat_label(score):
    if score >= 0.8: return "ALERT"
    if score >= 0.6: return "SUSPICIOUS"
    if score >= 0.4: return "WATCH"
    return "SAFE"

def threat_bar(score, width=20):
    filled = int(score * width)
    empty = width - filled
    color = score_color(score)
    return c(color, "█" * filled) + c(C_DGRAY, "░" * empty) + f" {score:.2f}"

BANNER = rf"""
{c(C_TEAL, '  ┌──────────────────────────────────────────────────────┐')}
{c(C_TEAL, '  │')}{c(C_GREEN + C_BOLD, '  ◉  NOMAD  ')}{c(C_DGRAY, '─')} {c(C_LGRAY, 'AUTONOMOUS AGENT DRIFT DETECTOR')}  {c(C_TEAL, '│')}
{c(C_TEAL, '  │')}{c(C_DGRAY, '     scanning your machine for things that move        ')}{c(C_TEAL, '│')}
{c(C_TEAL, '  └──────────────────────────────────────────────────────┘')}"""


def cmd_scan(args):
    if args.block:
        print(c(C_RED + C_BOLD, "\n  ⚠  BLOCK MODE ENGAGED — high-confidence drifters will be terminated."))
        print(c(C_DGRAY, "  ⚠  Use at your own risk. See LICENSE.\n"))

    engine = NomadEngine(dry_run=not args.block)
    result = engine.run_once()

    if args.json:
        print(json.dumps(result, indent=2))
        return

    ts = datetime.fromtimestamp(result["timestamp"], tz=timezone.utc).strftime("%H:%M:%S")

    # Banner
    print(BANNER)
    print()

    # Timestamp + sweep
    print(f"  {c(C_DGRAY, 'SCAN')}  {c(C_GREEN + C_BOLD, ts)}  {c(C_DGRAY, 'UTC')}")
    print()

    # System layer counts
    containers = result["containers"]
    services = result["services"]
    processes = result["processes"]

    print(f"  {c(C_TEAL, '◆ LAYERS SCANNED')}")
    print(f"    {c(C_GREEN, '●')} Containers   {c(C_GREEN + C_BOLD, str(containers).rjust(4))}")
    print(f"    {c(C_GREEN, '●')} Services     {c(C_GREEN + C_BOLD, str(services).rjust(4))}")
    print(f"    {c(C_GREEN, '●')} Processes    {c(C_GREEN + C_BOLD, str(processes).rjust(4))}")
    print()

    # Changes — radar style
    has_changes = any([
        result["new_containers"], result["gone_containers"],
        result["new_services"], result["gone_services"],
        result["new_processes"], result["gone_processes"]
    ])

    if has_changes:
        print(f"  {c(C_TEAL, '◆ RADAR CONTACTS')}")
        if result["new_containers"]:
            print(f"    {c(C_GREEN, '►')} New containers  {c(C_GREEN + C_BOLD, ', '.join(result['new_containers']))}")
        if result["gone_containers"]:
            print(f"    {c(C_RED, '◄')} Gone containers {c(C_RED + C_BOLD, ', '.join(result['gone_containers']))}")
        if result["new_services"]:
            print(f"    {c(C_GREEN, '►')} New services    {c(C_GREEN + C_BOLD, str(result['new_services']))}")
        if result["gone_services"]:
            print(f"    {c(C_RED, '◄')} Gone services   {c(C_RED + C_BOLD, str(result['gone_services']))}")
        if result["new_processes"]:
            print(f"    {c(C_GREEN, '►')} Spawned         {c(C_GREEN + C_BOLD, str(result['new_processes']) + ' processes')}")
        if result["gone_processes"]:
            print(f"    {c(C_RED, '◄')} Vanished        {c(C_RED + C_BOLD, str(result['gone_processes']) + ' processes')}")
        print()

    # Migrations
    if result["migrations"]:
        print(f"  {c(C_YELLOW, '◆ MIGRATIONS DETECTED')}")
        for m in result["migrations"]:
            sim = m["similarity"]
            sc = score_color(sim)
            bar = threat_bar(sim, 15)
            print(f"    {c(C_AMBER, '↻')} {c(C_LGRAY, m['source'])} → {c(C_LGRAY, m['target'])}  {c(C_DGRAY, '(' + m['kind'] + ')')}")
            print(f"      similarity {bar}  {c(sc, threat_label(sim))}")
        print()

    # Credential access
    if result.get("credential_findings"):
        print(f"  {c(C_RED + C_BLINK, '◆ CREDENTIAL ACCESS DETECTED')}")
        for cr in result["credential_findings"]:
            level = cr["risk_level"]
            color = C_RED if level == "critical" else C_ORANGE if level == "high" else C_YELLOW
            print(f"    {c(color, '●')} {c(C_LGRAY, cr['process_name'])} {c(C_DGRAY, 'PID ' + str(cr['pid']))} → {c(color, cr['file_path'])}  {c(color + C_BOLD, level.upper())}")
        print()

    # Network anomalies
    if result.get("network_anomalies"):
        print(f"  {c(C_ORANGE, '◆ NETWORK ANOMALIES')}")
        for n in result["network_anomalies"]:
            level = n["risk_level"]
            color = C_RED if level == "critical" else C_ORANGE if level == "high" else C_YELLOW
            remote = n["remote_addr"] or "N/A"
            print(f"    {c(color, '●')} {c(C_LGRAY, n['process_name'])} {c(C_DGRAY, 'PID ' + str(n['pid']))} — {c(color, n['anomaly_type'])} → {c(C_LGRAY, remote)}  {c(color + C_BOLD, level.upper())}")
        print()

    # Disk
    disk = result.get("disk", {})
    if disk:
        level = disk["level"]
        color = C_RED if level == "crit" else C_YELLOW if level == "warn" else C_GREEN
        pct = disk["pct"]
        bar_w = 30
        filled = int(pct / 100 * bar_w)
        bar = c(color, "█" * filled) + c(C_DGRAY, "░" * (bar_w - filled))
        print(f"  {c(C_TEAL, '◆ DISK')}  {bar}  {c(color, str(pct) + '%')}  {c(C_LGRAY, str(disk['free_gb']) + 'G free / ' + str(disk['total_gb']) + 'G')}")
        print()

    # Threat summary
    total_threats = len(result.get("credential_findings", [])) + len(result.get("network_anomalies", []))
    migrations = len(result["migrations"])
    if total_threats > 0:
        print(f"  {c(C_RED + C_BOLD, '⚠ ' + str(total_threats) + ' THREAT(S) DETECTED')}  {c(C_DGRAY, 'Run')} {c(C_TEAL, 'nomad scan --block')} {c(C_DGRAY, 'to terminate')}")
        print()
    elif migrations > 0:
        print(f"  {c(C_YELLOW, '● ' + str(migrations) + ' migration(s) tracked')}  {c(C_DGRAY, 'monitoring for escalation')}")
        print()

    # Mode footer
    mode = c(C_RED + C_BOLD, "BLOCKING") if args.block else c(C_DGRAY, "monitoring (dry-run)")
    print(f"  {c(C_DGRAY, 'mode')} {mode}")


def cmd_watch(args):
    if args.block:
        print(c(C_RED + C_BOLD, "\n  ⚠  BLOCK MODE ENGAGED — high-confidence drifters will be terminated."))
        print(c(C_DGRAY, "  ⚠  Use at your own risk. See LICENSE.\n"))

    engine = NomadEngine(dry_run=not args.block)
    print(BANNER)
    print()
    print(f"  {c(C_TEAL, '◆ MONITORING')}  scanning every {c(C_GREEN + C_BOLD, str(args.interval) + 's')}  {c(C_DGRAY, '(Ctrl+C to stop)')}")
    print(f"  {c(C_DGRAY, 'self-heal: slow scans → throttle → backoff → recovery')}")
    print()
    engine.run_loop(interval=args.interval)


def cmd_alerts(args):
    engine = NomadEngine()
    alerts = engine.get_alerts(limit=args.limit)
    if not alerts:
        print(f"  {c(C_GREEN, '✓')} No alerts recorded. All clear.")
        return
    print(f"\n  {c(C_RED, '◆ ALERT HISTORY')}  ({len(alerts)} entries)")
    print()
    for a in alerts[-args.limit:]:
        ts = a.get("timestamp", "?")
        kind = a.get("type", "unknown")
        name = a.get("name", "")
        score = a.get("score", "")
        sc = score_color(float(score)) if score else C_DGRAY
        print(f"    {c(C_DGRAY, ts)}  {c(sc, kind)}  {c(C_LGRAY, name)}  {c(sc, 'score=' + str(score))}")
    print()


def cmd_fingerprint(args):
    scanner = Scanner()
    snapshot = scanner.scan()
    fp = Fingerprinter()
    drifters = fp.analyze(snapshot, {})

    if args.json:
        from dataclasses import asdict
        print(json.dumps([asdict(d) for d in drifters], indent=2))
        return

    if not drifters:
        print(f"  {c(C_GREEN, '✓')} No drifters found. System clean.")
        return

    print(f"\n  {c(C_RED, '◆ DRIFTERS FOUND')}: {c(C_RED + C_BOLD, str(len(drifters)))}")
    print()
    for d in drifters:
        sc = score_color(d.score)
        bar = threat_bar(d.score, 15)
        print(f"    {c(sc, '●')} [{c(C_LGRAY, d.kind)}] {c(C_LGRAY, d.name)}")
        print(f"      {bar}  {c(sc + C_BOLD, threat_label(d.score))}")
        print(f"      {c(C_DGRAY, 'reason:')} {c(C_LGRAY, d.reason)}")
        for ev in d.evidence:
            print(f"      {c(C_DGRAY, 'evidence:')} {c(C_LGRAY, ev)}")
        print()


def cmd_state(args):
    engine = NomadEngine()
    history = engine.get_state()
    if args.json:
        print(json.dumps(history, indent=2))
        return
    print(f"  State history entries: {len(history)}")


# ─── Alarm Commands ─────────────────────────────────────────

ALARM_BANNER = rf"""
{c(C_TEAL, '  ┌──────────────────────────────────────────────────────┐')}
{c(C_TEAL, '  │')}{c(C_RED + C_BOLD, '  ◉  NOMAD ALARM  ')}{c(C_DGRAY, '─')} {c(C_LGRAY, 'REMOTE CONNECTION DETECTOR')}  {c(C_TEAL, '│')}
{c(C_TEAL, '  │')}{c(C_DGRAY, '     watching for things that connect to your box     ')}{c(C_TEAL, '│')}
{c(C_TEAL, '  └──────────────────────────────────────────────────────┘')}"""

def cmd_alarm_scan(args):
    from alarm import AlarmEngine

    engine = AlarmEngine()

    if not engine.enabled:
        print(f"\n  {c(C_DGRAY, 'Alarm system is')} {c(C_RED + C_BOLD, 'OFF')}  {c(C_DGRAY, '(use')} {c(C_TEAL, 'nomad alarm on')} {c(C_DGRAY, 'to enable)')}\n")
        return

    scan = engine.scan()

    if args.json:
        print(json.dumps(asdict(scan), indent=2))
        return

    print(ALARM_BANNER)
    print()

    ts = datetime.fromtimestamp(scan.timestamp, tz=timezone.utc).strftime("%H:%M:%S")
    print(f"  {c(C_DGRAY, 'SCAN')}  {c(C_GREEN + C_BOLD, ts)}  {c(C_DGRAY, 'UTC')}")
    print()

    # Connection summary
    kinds = {}
    for c_item in scan.connections:
        k = c_item.get("kind", "unknown")
        kinds[k] = kinds.get(k, 0) + 1

    print(f"  {c(C_TEAL, '◆ CONNECTIONS DETECTED')}")
    kind_icons = {
        "ssh": "🔑", "ssh_fail": "❌", "ssh_listen": "📡",
        "tailscale": "🔗", "listening_port": "🔌", "suspicious_port": "⚠️",
        "remote_tool": "🖥️", "login": "👤", "sudo": "🔧", "outbound": "📤",
    }
    for kind, count in sorted(kinds.items()):
        icon = kind_icons.get(kind, "●")
        print(f"    {icon} {c(C_LGRAY, kind.ljust(16))} {c(C_GREEN + C_BOLD, str(count).rjust(4))}")
    print()

    # Baseline comparison
    print(f"  {c(C_TEAL, '◆ BASELINE')}")
    print(f"    {c(C_GREEN, '●')} Known connections  {c(C_GREEN + C_BOLD, str(scan.baseline_known).rjust(4))}")
    print(f"    {c(C_YELLOW, '●')} Current total     {c(C_YELLOW + C_BOLD, str(len(scan.connections)).rjust(4))}")
    print()

    # New threats
    if scan.new_threats:
        print(f"  {c(C_RED + C_BOLD, '◆ NEW THREATS')}  {c(C_DGRAY, '(not in baseline)')}")
        for t in scan.new_threats:
            risk = t.get("risk", "low")
            risk_color = C_RED if risk in ("critical", "high") else C_YELLOW if risk == "medium" else C_DGRAY
            icon = kind_icons.get(t.get("kind", ""), "●")
            print(f"    {icon} {c(C_LGRAY, t.get('kind', '?').ljust(16))} {c(C_LGRAY, t.get('source', '?'))}")
            print(f"      {c(C_DGRAY, 'detail:')} {c(C_LGRAY, t.get('detail', '?')[:80])}")
            print(f"      {c(C_DGRAY, 'risk:')}   {c(risk_color + C_BOLD, risk.upper())}")
            print()
    else:
        print(f"  {c(C_GREEN, '✓')} No new threats — all connections match baseline")
        print()

    # Alert level
    level = scan.alert_level
    if level == "alert":
        print(f"  {c(C_RED + C_BOLD, '🔴 ALERT — new high-risk connections detected')}")
    elif level == "watch":
        print(f"  {c(C_YELLOW, '🟡 WATCH — new medium-risk connections detected')}")
    else:
        print(f"  {c(C_GREEN, '🟢 SAFE — no anomalies')}")
    print()


def cmd_alarm_watch(args):
    from alarm import AlarmEngine

    engine = AlarmEngine()

    if not engine.enabled:
        print(f"\n  {c(C_DGRAY, 'Alarm system is')} {c(C_RED + C_BOLD, 'OFF')}  {c(C_DGRAY, '(use')} {c(C_TEAL, 'nomad alarm on')} {c(C_DGRAY, 'to enable)')}\n")
        return

    print(ALARM_BANNER)
    print()
    print(f"  {c(C_TEAL, '◆ MONITORING')}  scanning every {c(C_GREEN + C_BOLD, str(args.interval) + 's')}  {c(C_DGRAY, '(Ctrl+C to stop)')}")
    print()

    import signal
    running = True
    def stop(sig, frame):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    while running:
        scan = engine.scan()
        engine.alert_new_threats(scan)

        ts = datetime.fromtimestamp(scan.timestamp, tz=timezone.utc).strftime("%H:%M:%S")
        total = len(scan.connections)
        threats = len(scan.new_threats)
        level = scan.alert_level
        level_icon = {"alert": "🔴", "watch": "🟡", "safe": "🟢"}.get(level, "?")

        if threats > 0:
            print(f"  [{ts}] {level_icon} {total} connections, {c(C_RED + C_BOLD, str(threats))} NEW — {c(C_YELLOW, level.upper())}", flush=True)
        else:
            print(f"  [{ts}] {level_icon} {total} connections, all known", flush=True)

        time.sleep(args.interval)


def cmd_alarm_learn(args):
    from alarm import AlarmEngine

    engine = AlarmEngine()
    baseline = engine.learn()
    print(f"\n  {c(C_GREEN, '✓')} Baseline learned: {c(C_GREEN + C_BOLD, str(baseline['known_count']))} connections marked as known")
    print(f"  {c(C_DGRAY, 'Learned at:')} {c(C_LGRAY, baseline['last_learned_at'])}")
    print()


def cmd_alarm_on(args):
    from alarm import AlarmEngine
    engine = AlarmEngine()
    engine.set_enabled(True)
    print(f"\n  {c(C_GREEN, '✓')} Alarm system {c(C_GREEN + C_BOLD, 'ENABLED')}")
    print(f"  {c(C_DGRAY, 'Run')} {c(C_TEAL, 'nomad alarm scan')} {c(C_DGRAY, 'to check now')}\n")


def cmd_alarm_off(args):
    from alarm import AlarmEngine
    engine = AlarmEngine()
    engine.set_enabled(False)
    print(f"\n  {c(C_RED, '✗')} Alarm system {c(C_RED + C_BOLD, 'DISABLED')}")
    print(f"  {c(C_DGRAY, 'Run')} {c(C_TEAL, 'nomad alarm on')} {c(C_DGRAY, 'to re-enable')}\n")


def cmd_alarm_status(args):
    from alarm import AlarmEngine

    engine = AlarmEngine()
    status = engine.get_status()

    if args.json:
        print(json.dumps(status, indent=2))
        return

    enabled = status["enabled"]
    level = status["alert_level"]
    level_icon = {"alert": "🔴", "watch": "🟡", "safe": "🟢"}.get(level, "?")
    enabled_str = c(C_GREEN + C_BOLD, "ON") if enabled else c(C_RED + C_BOLD, "OFF")
    enabled_icon = c(C_GREEN, "●") if enabled else c(C_RED, "●")

    print(f"\n  {c(C_TEAL, '◆ ALARM STATUS')}")
    print(f"    {enabled_icon} Enabled    {enabled_str}")
    print(f"    {level_icon} Level      {c(C_LGRAY, level.upper())}")
    print(f"    {c(C_GREEN, '●')} Baseline   {c(C_GREEN + C_BOLD, str(status['baseline_known']).rjust(4))} known connections")
    print(f"    {c(C_YELLOW, '●')} Current    {c(C_YELLOW + C_BOLD, str(status['total_connections']).rjust(4))} connections seen")
    print(f"    {c(C_RED, '●')} New        {c(C_RED + C_BOLD, str(status['new_threats']).rjust(4))} threats")
    print(f"    {c(C_DGRAY, '●')} Last learn {c(C_LGRAY, status['last_learned'][:19])}")
    print()


def cmd_alarm_alerts(args):
    from alarm import AlarmEngine

    engine = AlarmEngine()
    alerts = engine.get_alerts(limit=args.limit)

    if not alerts:
        print(f"\n  {c(C_GREEN, '✓')} No alarm alerts recorded.")
        return

    print(f"\n  {c(C_RED, '◆ ALARM ALERTS')}  ({len(alerts)} entries)")
    print()
    for a in alerts[-args.limit:]:
        ts = a.get("timestamp", "?")
        kind = a.get("kind", "?")
        source = a.get("source", "?")
        risk = a.get("risk", "low")
        risk_color = C_RED if risk in ("critical", "high") else C_YELLOW if risk == "medium" else C_DGRAY
        print(f"    {c(C_DGRAY, ts[:19])}  {c(risk_color, kind.ljust(16))} {c(C_LGRAY, source)}  {c(risk_color + C_BOLD, risk.upper())}")
    print()


def cmd_security(args):
    from security import run_check, run_verify, get_security_summary

    if args.verify:
        result = run_verify()
        if args.json:
            print(json.dumps(result, indent=2))
            return

        print(f"\n  nomad security verify")
        print(f"  {'─' * 50}")
        if not result.get("available"):
            print(f"  ❌ {result.get('error', 'sec-toolkit.sh not found')}")
            return

        checks = result.get("checks", {})
        passed = result.get("passed", 0)
        total = result.get("total", 0)
        score = result.get("score", 0)

        for key, status in checks.items():
            if status == "ok":
                print(f"  ✅ {key}")
            elif status == "warn":
                print(f"  ⚠️  {key}")
            elif status == "critical":
                print(f"  🔴 {key}")

        print(f"\n  Score: {score}% ({passed}/{total} passed)")
        return

    result = run_check()
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"\n  {c(C_TEAL, '◆ SECURITY POSTURE')}")
    print(f"  {'─' * 50}")
    if not result.get("available"):
        print(f"  {c(C_RED, '✗')} {result.get('error', 'sec-toolkit.sh not found')}")
        return

    sections = result.get("sections", {})
    score = result.get("score", 0)

    color = C_GREEN if score >= 80 else C_YELLOW if score >= 50 else C_RED
    bar_w = 30
    filled = int(score / 100 * bar_w)
    bar = c(color, "█" * filled) + c(C_DGRAY, "░" * (bar_w - filled))

    print(f"\n  {bar}  {c(color + C_BOLD, str(score) + '/100')}\n")

    for name, content in sections.items():
        preview = content[:200].replace("\n", "\n    ")
        print(f"  {c(C_TEAL, '[' + name + ']')}")
        print(f"    {c(C_LGRAY, preview)}")
        if len(content) > 200:
            print(f"    {c(C_DGRAY, '... (' + str(len(content)) + ' chars total)')}")
        print()


def main():
    parser = argparse.ArgumentParser(
        prog="nomad",
        description="Catch autonomous agents that spawn ephemeral infrastructure. "
                    "Monitors processes, containers, and services. Use --block with caution.\n"
                    "Free core: scan, fingerprint, state. Pro: dashboard, Telegram, blocking.",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command", help="Command")

    p_scan = sub.add_parser("scan", help="Run a single scan")
    p_scan.add_argument("--block", action="store_true", help="[Pro] Enable blocking mode")
    p_scan.add_argument("--json", action="store_true", help="JSON output")
    p_scan.set_defaults(func=cmd_scan)

    p_watch = sub.add_parser("watch", help="Continuous monitoring")
    p_watch.add_argument("--interval", type=int, default=30, help="Scan interval (seconds)")
    p_watch.add_argument("--block", action="store_true", help="[Pro] Enable blocking mode")
    p_watch.set_defaults(func=cmd_watch)

    p_alerts = sub.add_parser("alerts", help="View alert history")
    p_alerts.add_argument("--limit", type=int, default=20, help="Number of alerts")
    p_alerts.add_argument("--json", action="store_true", help="JSON output")
    p_alerts.set_defaults(func=cmd_alerts)

    p_fp = sub.add_parser("fingerprint", help="Fingerprint current processes")
    p_fp.add_argument("--json", action="store_true", help="JSON output")
    p_fp.set_defaults(func=cmd_fingerprint)

    p_state = sub.add_parser("state", help="View tracked state")
    p_state.add_argument("--json", action="store_true", help="JSON output")
    p_state.set_defaults(func=cmd_state)

    p_sec = sub.add_parser("security", help="[Pro] System security check (requires sec-toolkit.sh)")
    p_sec.add_argument("--verify", action="store_true", help="Run verification instead of check")
    p_sec.add_argument("--json", action="store_true", help="JSON output")
    p_sec.set_defaults(func=cmd_security)

    # Alarm subcommand group
    p_alarm = sub.add_parser("alarm", help="Remote connection alarm system")
    alarm_sub = p_alarm.add_subparsers(dest="alarm_command", help="Alarm command")

    p_alarm_scan = alarm_sub.add_parser("scan", help="Run a single alarm scan")
    p_alarm_scan.add_argument("--json", action="store_true", help="JSON output")
    p_alarm_scan.set_defaults(func=cmd_alarm_scan)

    p_alarm_watch = alarm_sub.add_parser("watch", help="Continuous alarm monitoring")
    p_alarm_watch.add_argument("--interval", type=int, default=60, help="Scan interval (seconds)")
    p_alarm_watch.set_defaults(func=cmd_alarm_watch)

    p_alarm_learn = alarm_sub.add_parser("learn", help="Learn current connections as baseline")
    p_alarm_learn.set_defaults(func=cmd_alarm_learn)

    p_alarm_on = alarm_sub.add_parser("on", help="Enable alarm system")
    p_alarm_on.set_defaults(func=cmd_alarm_on)

    p_alarm_off = alarm_sub.add_parser("off", help="Disable alarm system")
    p_alarm_off.set_defaults(func=cmd_alarm_off)

    p_alarm_status = alarm_sub.add_parser("status", help="Show alarm system status")
    p_alarm_status.add_argument("--json", action="store_true", help="JSON output")
    p_alarm_status.set_defaults(func=cmd_alarm_status)

    p_alarm_alerts = alarm_sub.add_parser("alerts", help="View alarm alert history")
    p_alarm_alerts.add_argument("--limit", type=int, default=20, help="Number of alerts")
    p_alarm_alerts.set_defaults(func=cmd_alarm_alerts)

    args = parser.parse_args()
    if args.version:
        try:
            ver = Path(__file__).resolve().parent.joinpath("VERSION").read_text().strip()
            print(f"nomad {ver}")
        except Exception:
            print("nomad unknown")
        return
    if not args.command:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
