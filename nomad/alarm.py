#!/usr/bin/env python3
"""
nomad alarm — Sophisticated remote connection alarm system.

Monitors SSH, VNC/RDP, Tailscale peers, listening ports, login events,
and remote access tools. Compares against a learned baseline.
Active/inactive toggle via state/alarm_enabled.json.
"""

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from config import (
    STATE_DIR, LOGS_DIR,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
)

ALARM_STATE_FILE = STATE_DIR / "alarm_state.json"
ALARM_BASELINE_FILE = STATE_DIR / "alarm_baseline.json"
ALARM_LOG = LOGS_DIR / "alarm_events.jsonl"
ALARM_ALERT_LOG = LOGS_DIR / "alarm_alerts.jsonl"

# Remote access tool names to watch for
REMOTE_ACCESS_TOOLS = [
    "anydesk", "teamviewer", "rustdesk", "remmina", "x11vnc",
    "tigervnc", "vncserver", "xrdp", "freerdp", "rdesktop",
    "nomachine", "apache-guacamole", "chrome-remote-desktop",
    "parsec", "splashtop", "sunlogin", "向日葵",
]

# Known SSH key paths
SSH_KEY_PATHS = [
    "/etc/ssh/ssh_host_",
    str(Path.home() / ".ssh/authorized_keys"),
    str(Path.home() / ".ssh/known_hosts"),
]

# Listening port thresholds
SUSPICIOUS_LISTEN_PORTS = {4444, 5555, 6666, 7777, 8888, 9999, 1234, 31337, 1337}


@dataclass
class RemoteConnection:
    """A single remote connection or access event."""
    kind: str  # ssh, tailscale, vnc_rdp, listening_port, login, remote_tool
    source: str  # IP, device name, port, etc.
    detail: str  # additional context
    risk: str  # low, medium, high, critical
    timestamp: float = 0.0
    evidence: list = field(default_factory=list)


@dataclass
class AlarmScan:
    """Complete alarm scan result."""
    timestamp: float
    active: bool
    connections: list  # list of RemoteConnection dicts
    new_threats: list  # connections not in baseline
    baseline_known: int
    alert_level: str  # safe, watch, alert


class ConnectionScanner:
    """Scans all remote connection surfaces."""

    def scan(self) -> list:
        connections = []
        connections.extend(self._scan_ssh())
        connections.extend(self._scan_tailscale())
        connections.extend(self._scan_listening_ports())
        connections.extend(self._scan_remote_tools())
        connections.extend(self._scan_login_events())
        connections.extend(self._scan_established_connections())
        return connections

    def _scan_ssh(self) -> list:
        """Scan for active SSH connections and recent auth events."""
        conns = []

        # Active SSH sessions
        try:
            result = subprocess.run(
                ["ss", "-tnp", "state established", "sport", "=", ":22"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    peer = parts[4]  # peer address
                    remote_ip = peer.rsplit(":", 1)[0] if ":" in peer else peer
                    conns.append(RemoteConnection(
                        kind="ssh",
                        source=remote_ip,
                        detail=f"active SSH session from {peer}",
                        risk="low",
                        timestamp=time.time(),
                        evidence=[f"ss output: {line.strip()}"],
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Recent SSH auth failures (last 5 minutes)
        try:
            cutoff = datetime.now().strftime("%b %d %H:%M")
            result = subprocess.run(
                ["grep", "-i", "failed password", "/var/log/auth.log"],
                capture_output=True, text=True, timeout=5,
            )
            lines = result.stdout.strip().split("\n")[-20:]  # last 20
            for line in lines:
                if not line:
                    continue
                # Extract IP: "Failed password for root from 1.2.3.4 port 12345 ssh2"
                ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", line)
                if ip_match:
                    ip = ip_match.group(1)
                    conns.append(RemoteConnection(
                        kind="ssh_fail",
                        source=ip,
                        detail=f"SSH auth failure: {line.strip()[:100]}",
                        risk="medium",
                        timestamp=time.time(),
                        evidence=[line.strip()],
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Check if SSH port is exposed
        try:
            result = subprocess.run(
                ["ss", "-tlnp", "sport", "=", ":22"],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip():
                for line in result.stdout.splitlines()[1:]:
                    if "0.0.0.0:" in line or ":::" in line:
                        conns.append(RemoteConnection(
                            kind="ssh_listen",
                            source="0.0.0.0:22",
                            detail="SSH listening on all interfaces",
                            risk="medium",
                            timestamp=time.time(),
                            evidence=[line.strip()],
                        ))
                        break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return conns

    def _scan_tailscale(self) -> list:
        """Scan for Tailscale peers — new devices are suspicious."""
        conns = []
        try:
            result = subprocess.run(
                ["tailscale", "status", "--json"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                peers = data.get("Peer", {})
                for peer_id, peer in peers.items():
                    hostname = peer.get("HostName", "?")
                    ip = peer.get("TailscaleIPs", ["?"])[0] if peer.get("TailscaleIPs") else "?"
                    os_name = peer.get("OS", "?")
                    online = peer.get("Online", False)
                    conns.append(RemoteConnection(
                        kind="tailscale",
                        source=f"{hostname} ({ip})",
                        detail=f"Tailscale peer: {hostname}, OS={os_name}, online={online}",
                        risk="low",
                        timestamp=time.time(),
                        evidence=[f"PeerID={peer_id}, IP={ip}, OS={os_name}"],
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        return conns

    def _scan_listening_ports(self) -> list:
        """Scan for new listening ports — unexpected listeners are suspicious."""
        conns = []
        try:
            result = subprocess.run(
                ["ss", "-tlnp"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 4:
                    local = parts[3]
                    # Extract port
                    port_match = re.search(r":(\d+)$", local)
                    if port_match:
                        port = int(port_match.group(1))
                        # Skip well-known system ports
                        if port < 1024 and port != 22:
                            continue
                        if port in SUSPICIOUS_LISTEN_PORTS:
                            conns.append(RemoteConnection(
                                kind="suspicious_port",
                                source=local,
                                detail=f"Suspicious port {port} listening",
                                risk="high",
                                timestamp=time.time(),
                                evidence=[line.strip()],
                            ))
                        elif port > 1024:
                            # Check if it's bound to all interfaces
                            if "0.0.0.0:" in local or ":::" in local:
                                proc_info = ""
                                for p in parts[4:]:
                                    if "users:" in p:
                                        proc_info = p
                                        break
                                conns.append(RemoteConnection(
                                    kind="listening_port",
                                    source=local,
                                    detail=f"Port {port} listening on all interfaces {proc_info}",
                                    risk="medium",
                                    timestamp=time.time(),
                                    evidence=[line.strip()],
                                ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return conns

    def _scan_remote_tools(self) -> list:
        """Scan for running remote access tools."""
        conns = []
        if not HAS_PSUTIL:
            return conns

        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                info = p.info
                name = (info.get('name', '') or '').lower()
                cmdline = " ".join(info.get('cmdline') or []).lower()

                for tool in REMOTE_ACCESS_TOOLS:
                    if tool in name or tool in cmdline:
                        conns.append(RemoteConnection(
                            kind="remote_tool",
                            source=f"{info.get('name')} (PID {info.get('pid')})",
                            detail=f"Remote access tool detected: {tool}",
                            risk="high",
                            timestamp=time.time(),
                            evidence=[f"Process: {info.get('name')}, PID: {info.get('pid')}, Cmdline: {cmdline[:200]}"],
                        ))
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return conns

    def _scan_login_events(self) -> list:
        """Scan for recent login events from auth.log."""
        conns = []
        try:
            # Get last 50 lines of auth.log
            result = subprocess.run(
                ["tail", "-50", "/var/log/auth.log"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                line_lower = line.lower()
                # Successful SSH login
                if "accepted" in line_lower and "ssh" in line_lower:
                    user_match = re.search(r"for (\w+) from (\d+\.\d+\.\d+\.\d+)", line)
                    if user_match:
                        user = user_match.group(1)
                        ip = user_match.group(2)
                        conns.append(RemoteConnection(
                            kind="login",
                            source=ip,
                            detail=f"SSH login accepted for user '{user}' from {ip}",
                            risk="medium",
                            timestamp=time.time(),
                            evidence=[line.strip()],
                        ))
                # Sudo usage
                elif "sudo:" in line_lower and "command" in line_lower:
                    user_match = re.search(r"sudo:\s+(\w+)", line)
                    if user_match:
                        conns.append(RemoteConnection(
                            kind="sudo",
                            source=user_match.group(1),
                            detail=f"Sudo usage: {line.strip()[:100]}",
                            risk="low",
                            timestamp=time.time(),
                            evidence=[line.strip()],
                        ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return conns

    def _scan_established_connections(self) -> list:
        """Scan for established connections to unusual destinations."""
        conns = []
        if not HAS_PSUTIL:
            return conns

        for p in psutil.process_iter(['pid', 'name']):
            try:
                proc = psutil.Process(p.info['pid'])
                for conn in proc.connections(kind='inet'):
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port

                        # Skip known safe destinations
                        if remote_port in (80, 443, 53):
                            continue
                        if remote_ip.startswith("127."):
                            continue
                        if remote_ip.startswith("100.64."):  # Tailscale CGNAT
                            continue

                        # Flag outbound connections to unusual ports
                        if remote_port > 1024 and remote_port not in (8080, 8443):
                            conns.append(RemoteConnection(
                                kind="outbound",
                                source=f"{p.info['name']}→{remote_ip}:{remote_port}",
                                detail=f"Outbound connection to non-standard port",
                                risk="low",
                                timestamp=time.time(),
                                evidence=[f"PID={p.info['pid']}, Remote={remote_ip}:{remote_port}"],
                            ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return conns


class AlarmEngine:
    """Core alarm engine with baseline comparison and alerting."""

    def __init__(self):
        self.baseline = self._load_baseline()
        self.enabled = self._is_enabled()
        self.scanner = ConnectionScanner()
        self._last_alert_time = {}

    def _load_baseline(self) -> dict:
        """Load known-good connections baseline."""
        if ALARM_BASELINE_FILE.exists():
            try:
                return json.loads(ALARM_BASELINE_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {"known_connections": [], "last_learned": 0}

    def _save_baseline(self):
        """Save baseline to disk."""
        ALARM_BASELINE_FILE.write_text(json.dumps(self.baseline, indent=2))

    def _is_enabled(self) -> bool:
        """Check if alarm system is enabled."""
        enabled_file = STATE_DIR / "alarm_enabled.json"
        if enabled_file.exists():
            try:
                data = json.loads(enabled_file.read_text())
                return data.get("enabled", True)
            except (json.JSONDecodeError, IOError):
                pass
        return True  # Default: enabled

    def set_enabled(self, enabled: bool):
        """Enable or disable the alarm system."""
        self.enabled = enabled
        STATE_DIR.mkdir(exist_ok=True)
        ALARM_STATE_FILE.parent.mkdir(exist_ok=True)
        (STATE_DIR / "alarm_enabled.json").write_text(json.dumps({
            "enabled": enabled,
            "changed_at": datetime.now(timezone.utc).isoformat(),
        }))

    def _connection_key(self, conn: RemoteConnection) -> str:
        """Generate a unique key for a connection (for baseline comparison)."""
        # Group by kind + source (ignore detail changes)
        return f"{conn.kind}:{conn.source}"

    def _is_known(self, conn: RemoteConnection) -> bool:
        """Check if a connection is in the known baseline."""
        key = self._connection_key(conn)
        known_keys = set(self.baseline.get("known_keys", []))
        return key in known_keys

    def learn(self) -> dict:
        """Learn current connections as baseline (mark them as known)."""
        connections = self.scanner.scan()
        known_keys = list({self._connection_key(c) for c in connections})
        self.baseline = {
            "known_keys": known_keys,
            "known_count": len(known_keys),
            "last_learned": time.time(),
            "last_learned_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_baseline()
        return self.baseline

    def scan(self) -> AlarmScan:
        """Run a full alarm scan, compare against baseline, return results."""
        if not self.enabled:
            return AlarmScan(
                timestamp=time.time(),
                active=False,
                connections=[],
                new_threats=[],
                baseline_known=0,
                alert_level="safe",
            )

        connections = self.scanner.scan()
        new_threats = [c for c in connections if not self._is_known(c)]

        # Determine alert level
        alert_level = "safe"
        if new_threats:
            high_risk = any(c.risk in ("high", "critical") for c in new_threats)
            if high_risk:
                alert_level = "alert"
            else:
                alert_level = "watch"

        return AlarmScan(
            timestamp=time.time(),
            active=True,
            connections=[asdict(c) for c in connections],
            new_threats=[asdict(c) for c in new_threats],
            baseline_known=len(self.baseline.get("known_keys", [])),
            alert_level=alert_level,
        )

    def alert_new_threats(self, scan: AlarmScan):
        """Send alerts for new threats not in baseline."""
        if not scan.new_threats:
            return

        now = datetime.now(timezone.utc).isoformat()
        for t in scan.new_threats:
            # Log event
            event = {
                "type": "alarm_new_connection",
                "timestamp": now,
                "kind": t.get("kind"),
                "source": t.get("source"),
                "detail": t.get("detail"),
                "risk": t.get("risk"),
                "evidence": t.get("evidence"),
            }
            self._log_event(event)

            # Telegram alert for medium+ risk
            if t.get("risk") in ("medium", "high", "critical"):
                self._log_alert(event)
                self._telegram_alert(t)

    def _log_event(self, event: dict):
        with open(ALARM_LOG, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _log_alert(self, alert: dict):
        with open(ALARM_ALERT_LOG, "a") as f:
            f.write(json.dumps(alert) + "\n")

    def _telegram_alert(self, threat: dict):
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return

        # Rate limit
        alert_key = f"alarm:{threat.get('kind')}:{threat.get('source')}"
        now = time.time()
        if alert_key in self._last_alert_time:
            if now - self._last_alert_time[alert_key] < 300:
                return
        self._last_alert_time[alert_key] = now

        try:
            import requests
            risk = threat.get("risk", "low")
            emoji = "🔴" if risk == "critical" else "🟠" if risk == "high" else "🟡" if risk == "medium" else "⚪"
            msg = (
                f"{emoji} *nomad alarm*\n"
                f"Kind: `{threat.get('kind', '?')}`\n"
                f"Source: `{threat.get('source', '?')}`\n"
                f"Detail: {threat.get('detail', '?')}\n"
                f"Risk: `{risk}`"
            )
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception:
            pass

    def get_alerts(self, limit: int = 50) -> list:
        """Get recent alarm alerts."""
        alerts = []
        if ALARM_ALERT_LOG.exists():
            for line in ALARM_ALERT_LOG.read_text().splitlines()[-limit:]:
                if line.strip():
                    try:
                        alerts.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return alerts

    def get_status(self) -> dict:
        """Get current alarm system status."""
        scan = self.scan()
        return {
            "enabled": self.enabled,
            "alert_level": scan.alert_level,
            "total_connections": len(scan.connections),
            "new_threats": len(scan.new_threats),
            "baseline_known": scan.baseline_known,
            "last_learned": self.baseline.get("last_learned_at", "never"),
        }
