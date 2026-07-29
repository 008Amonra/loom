#!/usr/bin/env python3
"""
nomad dashboard — Minimal web UI for agent drift detection.
"""

import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

from nomad import NomadEngine
from config import SCAN_INTERVAL

app = Flask(__name__)
engine = NomadEngine(dry_run=True)
_last_result = {"drifters": [], "migrations": [], "timestamp": 0}
_last_security = {"available": False, "posture_score": 0, "sections": [], "critical_issues": [], "warnings": []}
_lock = threading.Lock()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nomad — drift detector</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'SF Mono', 'Fira Code', monospace;
    background: #0a0a0f;
    color: #e0e0e0;
    padding: 24px;
  }
  h1 { color: #ff6b6b; font-size: 1.6em; margin-bottom: 8px; }
  .subtitle { color: #666; font-size: 0.85em; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px; }
  .stat {
    background: #111118;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
  }
  .stat .num { font-size: 2em; color: #ff6b6b; }
  .stat .label { font-size: 0.75em; color: #666; margin-top: 4px; }
  .drifter {
    background: #1a0a0a;
    border: 1px solid #3a1515;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
  }
  .drifter.safe { background: #0a1a0a; border-color: #153a15; }
  .drifter-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .drifter-name { font-weight: bold; font-size: 1.1em; }
  .drifter-score {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.85em;
    font-weight: bold;
  }
  .score-high { background: #3a1515; color: #ff6b6b; }
  .score-med { background: #3a3a15; color: #ffdd6b; }
  .score-low { background: #153a15; color: #6bff6b; }
  .drifter-kind { color: #888; font-size: 0.8em; }
  .drifter-reason { color: #aaa; font-size: 0.85em; margin-top: 4px; }
  .drifter-evidence { color: #666; font-size: 0.8em; margin-top: 4px; }
  .migration {
    background: #0a0a1a;
    border: 1px solid #15153a;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.9em;
  }
  .migration-arrow { color: #6b6bff; font-size: 1.2em; }
  .empty { color: #444; text-align: center; padding: 32px; }
  .section-title { font-size: 1.1em; color: #ff6b6b; margin-bottom: 12px; }
  .refresh { color: #444; font-size: 0.75em; }
  .sec-panel { background: #111118; border: 1px solid #222; border-radius: 8px; padding: 16px; margin-bottom: 24px; }
  .sec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .sec-score { font-size: 2em; font-weight: bold; }
  .sec-score.good { color: #6bff6b; }
  .sec-score.warn { color: #ffdd6b; }
  .sec-score.bad { color: #ff6b6b; }
  .sec-label { color: #888; font-size: 0.85em; }
  .sec-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; }
  .sec-item { font-size: 0.85em; padding: 6px 10px; border-radius: 4px; }
  .sec-item.ok { background: #0a1a0a; color: #6bff6b; }
  .sec-item.warn { background: #1a1a0a; color: #ffdd6b; }
  .sec-item.critical { background: #1a0a0a; color: #ff6b6b; }
  .sec-unavail { color: #666; font-size: 0.85em; font-style: italic; }
  .cred-item, .net-item {
    background: #111118;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 0.85em;
  }
  .cred-item.critical { border-color: #ff6b6b; background: #1a0a0a; }
  .cred-item.high { border-color: #ffaa6b; background: #1a1a0a; }
  .cred-item.medium { border-color: #ffdd6b; background: #1a1a0a; }
  .net-item.high { border-color: #ff6b6b; background: #1a0a0a; }
  .net-item.medium { border-color: #ffdd6b; background: #1a1a0a; }
  .cred-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
  .cred-risk { padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
  .risk-critical { background: #3a1515; color: #ff6b6b; }
  .risk-high { background: #3a2a15; color: #ffaa6b; }
  .risk-medium { background: #3a3a15; color: #ffdd6b; }
  .risk-low { background: #153a15; color: #6bff6b; }
</style>
</head>
<body>
<h1>nomad</h1>
<div class="subtitle">catch autonomous agents that spawn ephemeral infrastructure</div>
<div class="grid">
  <div class="stat"><div class="num" id="s-containers">0</div><div class="label">Containers</div></div>
  <div class="stat"><div class="num" id="s-services">0</div><div class="label">Services</div></div>
  <div class="stat"><div class="num" id="s-processes">0</div><div class="label">Processes</div></div>
  <div class="stat"><div class="num" id="s-drifters">0</div><div class="label">Drifters</div></div>
</div>
<div class="section-title">Drifters</div>
<div id="drifters"><div class="empty">No drifters detected</div></div>
<div class="section-title" style="margin-top:24px">Migrations</div>
<div id="migrations"><div class="empty">No migrations detected</div></div>
<div class="section-title" style="margin-top:24px">🔐 Credential Access</div>
<div id="credentials"><div class="empty">No credential access detected</div></div>
<div class="section-title" style="margin-top:24px">🌐 Network Anomalies</div>
<div id="network"><div class="empty">No network anomalies detected</div></div>
<div class="section-title" style="margin-top:24px">System Security</div>
<div class="sec-panel" id="sec-panel">
  <div class="sec-header">
    <div>
      <div class="sec-score" id="sec-score">--</div>
      <div class="sec-label">Posture Score</div>
    </div>
    <div style="text-align:right">
      <div class="sec-label" id="sec-verify"></div>
      <div class="sec-label" id="sec-time"></div>
    </div>
  </div>
  <div class="sec-grid" id="sec-items"></div>
</div>
<div class="refresh" id="refresh-time"></div>
<script>
function update() {
  fetch('/api/last').then(r => r.json()).then(d => {
    document.getElementById('s-containers').textContent = d.containers || 0;
    document.getElementById('s-services').textContent = d.services || 0;
    document.getElementById('s-processes').textContent = d.processes || 0;
    document.getElementById('s-drifters').textContent = (d.drifters || []).length;

    const dc = document.getElementById('drifters');
    if (d.drifters && d.drifters.length) {
      dc.innerHTML = d.drifters.map(dr => {
        const cls = dr.score > 0.8 ? '' : ' safe';
        const scls = dr.score > 0.8 ? 'score-high' : dr.score > 0.5 ? 'score-med' : 'score-low';
        return `<div class="drifter${cls}">
          <div class="drifter-header">
            <span class="drifter-name">${dr.name}</span>
            <span class="drifter-score ${scls}">${dr.score.toFixed(2)}</span>
          </div>
          <div class="drifter-kind">${dr.kind} — ${dr.alive ? 'alive' : 'dead'}</div>
          <div class="drifter-reason">${dr.reason}</div>
          <div class="drifter-evidence">${dr.evidence.join(' | ')}</div>
        </div>`;
      }).join('');
    } else {
      dc.innerHTML = '<div class="empty">No drifters detected</div>';
    }

    const mc = document.getElementById('migrations');
    if (d.migrations && d.migrations.length) {
      mc.innerHTML = d.migrations.map(m =>
        `<div class="migration">
          <span>${m.source}</span>
          <span class="migration-arrow">→</span>
          <span>${m.target}</span>
          <span style="color:#666">(${m.kind}, sim=${m.similarity.toFixed(2)})</span>
        </div>`
      ).join('');
    } else {
      mc.innerHTML = '<div class="empty">No migrations detected</div>';
    }

    const cc = document.getElementById('credentials');
    if (d.credential_findings && d.credential_findings.length) {
      cc.innerHTML = d.credential_findings.map(c => {
        const rcls = 'risk-' + c.risk_level;
        return `<div class="cred-item ${c.risk_level}">
          <div class="cred-header">
            <span>${c.process_name} (PID ${c.pid})</span>
            <span class="cred-risk ${rcls}">${c.risk_level}</span>
          </div>
          <div style="color:#888;font-size:0.9em">${c.file_path}</div>
          <div style="color:#666;font-size:0.8em;margin-top:4px">${c.evidence.join(' | ')}</div>
        </div>`;
      }).join('');
    } else {
      cc.innerHTML = '<div class="empty">No credential access detected</div>';
    }

    const nc = document.getElementById('network');
    if (d.network_anomalies && d.network_anomalies.length) {
      nc.innerHTML = d.network_anomalies.map(n => {
        const rcls = 'risk-' + n.risk_level;
        return `<div class="net-item ${n.risk_level}">
          <div class="cred-header">
            <span>${n.process_name} (PID ${n.pid})</span>
            <span class="cred-risk ${rcls}">${n.risk_level}</span>
          </div>
          <div style="color:#888;font-size:0.9em">${n.anomaly_type} → ${n.remote_addr || 'N/A'}</div>
          <div style="color:#666;font-size:0.8em;margin-top:4px">${n.evidence.join(' | ')}</div>
        </div>`;
      }).join('');
    } else {
      nc.innerHTML = '<div class="empty">No network anomalies detected</div>';
    }

    document.getElementById('refresh-time').textContent =
      'last scan: ' + new Date(d.timestamp * 1000).toLocaleTimeString();
  });

  fetch('/api/security').then(r => r.json()).then(s => {
    const el = document.getElementById('sec-score');
    const items = document.getElementById('sec-items');
    const verify = document.getElementById('sec-verify');
    const time = document.getElementById('sec-time');

    if (!s.available) {
      el.textContent = '--';
      el.className = 'sec-score';
      items.innerHTML = '<div class="sec-unavail">sec-toolkit.sh not installed — <a href="#setup" style="color:#c8a87c">install it</a></div>';
      verify.textContent = '';
      time.textContent = '';
      return;
    }

    const score = s.posture_score || 0;
    el.textContent = score + '%';
    el.className = 'sec-score ' + (score >= 70 ? 'good' : score >= 40 ? 'warn' : 'bad');

    verify.textContent = s.verify_passed + '/' + s.verify_total + ' checks passed';
    time.textContent = s.timestamp ? new Date(s.timestamp).toLocaleTimeString() : '';

    let html = '';
    (s.critical_issues || []).forEach(i => {
      html += '<div class="sec-item critical">🔴 ' + i + '</div>';
    });
    (s.warnings || []).forEach(w => {
      html += '<div class="sec-item warn">⚠️ ' + w + '</div>';
    });
    if (!s.critical_issues?.length && !s.warnings?.length) {
      html = '<div class="sec-item ok">✅ All checks passed</div>';
    }
    items.innerHTML = html;
  });
}
update();
setInterval(update, 10000);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/last")
def api_last():
    with _lock:
        return jsonify(_last_result)


@app.route("/api/alerts")
def api_alerts():
    limit = request.args.get("limit", 50, type=int)
    return jsonify(engine.get_alerts(limit=limit))


@app.route("/api/scan", methods=["POST"])
def api_scan():
    result = engine.run_once()
    with _lock:
        global _last_result
        _last_result = result
    return jsonify(result)


@app.route("/api/security")
def api_security():
    with _lock:
        return jsonify(_last_security)


@app.route("/api/health")
def api_health():
    with _lock:
        last_ts = _last_result.get("timestamp", 0)
    age = time.time() - last_ts if last_ts else 999
    status = "ok" if age < 120 else "stale" if age < 600 else "dead"
    return jsonify({
        "status": status,
        "last_scan_age_sec": round(age, 1),
        "last_scan": datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat() if last_ts else None,
        "service": "nomad",
    })


def _background_scan():
    scan_count = 0
    while True:
        try:
            result = engine.run_once()
            with _lock:
                global _last_result
                _last_result = result

            if scan_count % 10 == 0:
                try:
                    from security import get_security_summary
                    sec = get_security_summary()
                    with _lock:
                        global _last_security
                        _last_security = sec
                except Exception:
                    pass

            scan_count += 1
        except Exception:
            pass
        time.sleep(SCAN_INTERVAL)


def run_dashboard(host="0.0.0.0", port=5010, debug=False):
    t = threading.Thread(target=_background_scan, daemon=True)
    t.start()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5010)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    run_dashboard(host=args.host, port=args.port, debug=args.debug)
