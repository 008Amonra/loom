#!/usr/bin/env python3
"""45dgof8 Telegram Bridge.

Spricht mit dem lokalen opencode-Agenten ueber Telegram. Der Agent laeuft
auf derselben Maschine, es geht nichts ueber fremde Server.

Zwei Betriebsarten:
  poll     fragt Telegram ab. Braucht keine oeffentliche Adresse,
           funktioniert hinter NAT und Firewall. Standard.
  webhook  Telegram schickt Nachrichten an eine oeffentliche HTTPS-Adresse.
           Nur sinnvoll, wenn bereits ein Tunnel existiert. Zusaetzlich
           wird ein Secret geprueft, sonst nimmt jeder die Nachrichten an.

Konfiguration und Zustand liegen in ~/.local/state/telegram-bridge/:
  config    mode, webhook_url, port, workdir, opencode_bin
  token     Bot-Token, Modus 600. Wie ein SSH-Key behandeln.
  secret    Webhook-Secret, Modus 600
  owner     Telegram-User-ID des ersten privaten Absenders
  offset    letzter verarbeiteter Poll-Stand
  session   opencode Session-ID, damit der Gedaechtnisstand bleibt

WICHTIG: Der Bot-Token ist ein Fernzugriffsschluessel. Wer ihn besitzt,
kann den Agenten anweisen, und der Agent handelt mit den Rechten dieses
Benutzers. Nie ins Git, nie ins Log, nie in Screenshots.

Nur Standardbibliothek. Getestet mit Python 3.8+.
"""

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = os.environ.get(
    "45DGOF8_TELEGRAM_STATE", os.path.expanduser("~/.local/state/telegram-bridge")
)
CONFIG_FILE = os.path.join(STATE, "config")
TOKEN_FILE = os.path.join(STATE, "token")
SECRET_FILE = os.path.join(STATE, "secret")
OWNER_FILE = os.path.join(STATE, "owner")
OFFSET_FILE = os.path.join(STATE, "offset")
SESSION_FILE = os.path.join(STATE, "session")
LOG_FILE = os.path.join(STATE, "bridge.log")

TG_LIMIT = 4000
POLL_TIMEOUT = 25
MAX_RUN_SECONDS = 1800
WORK = queue.Queue()


def log(msg):
    line = "%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOG_FILE, "a") as fh:
            fh.write(line)
    except OSError:
        pass
    sys.stderr.write(line)
    sys.stderr.flush()


def read_file(path, default=""):
    try:
        with open(path) as fh:
            return fh.read().strip()
    except OSError:
        return default


def write_file(path, value, mode=0o600):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(value)
    try:
        os.chmod(tmp, mode)
    except OSError:
        pass
    os.replace(tmp, path)


def load_config():
    cfg = {}
    for line in read_file(CONFIG_FILE).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        cfg[key.strip()] = value.strip()
    return cfg


def find_opencode(cfg):
    cand = cfg.get("opencode_bin") or os.environ.get("45DGOF8_OPENCODE")
    if cand and os.path.exists(cand):
        return cand
    for path in (
        os.path.expanduser("~/.opencode/bin/opencode"),
        os.path.expanduser("~/.local/bin/opencode"),
    ):
        if os.path.exists(path):
            return path
    return shutil.which("opencode")


def find_workdir(cfg):
    if cfg.get("workdir") and os.path.isdir(cfg["workdir"]):
        return cfg["workdir"]
    for path in (os.path.expanduser("~/45dgof8-agent"), os.path.expanduser("~")):
        if os.path.isdir(path):
            return path
    return os.getcwd()


def api(token, method, params):
    query = urllib.parse.urlencode(params)
    url = "https://api.telegram.org/bot%s/%s?%s" % (token, method, query)
    with urllib.request.urlopen(url, timeout=POLL_TIMEOUT + 20) as resp:
        return json.loads(resp.read().decode())


def send(chat_id, text):
    """Schickt Text, in Bloecken von 4000 Zeichen, mit Retries."""
    token = read_file(TOKEN_FILE)
    if not text or not token:
        return
    for start in range(0, len(text), TG_LIMIT):
        chunk = text[start:start + TG_LIMIT]
        for attempt in range(3):
            try:
                api(token, "sendMessage", {
                    "chat_id": chat_id,
                    "text": chunk,
                    "disable_web_page_preview": "true",
                })
                break
            except Exception as exc:  # noqa: BLE001
                log("sendMessage fehlgeschlagen: %s" % exc)
                time.sleep(2 * (attempt + 1))


def run_opencode(text, cfg):
    binary = find_opencode(cfg)
    if not binary:
        return "Ich finde das opencode-Binary nicht. Bitte opencode_bin in der config setzen."
    workdir = find_workdir(cfg)
    session = read_file(SESSION_FILE)
    args = [binary, "run", "-s", session, text] if session else [binary, "run", text]
    try:
        proc = subprocess.run(
            args, cwd=workdir, capture_output=True, text=True,
            timeout=MAX_RUN_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "Das hat zu lange gedauert, ich habe abgebrochen."
    except OSError as exc:
        return "opencode liess sich nicht starten: %s" % exc
    if proc.returncode != 0:
        err = (proc.stderr or "").strip().splitlines()
        tail = err[-1] if err else "unbekannter Fehler"
        log("opencode run fehlgeschlagen: %s" % tail)
        return "Fehler beim Antworten: %s" % tail[:600]
    return (proc.stdout or "").strip() or "(leere Antwort)"


def remember_session(cfg):
    """Haengt die Telegram-Unterhaltung an eine feste opencode Session."""
    if read_file(SESSION_FILE):
        return
    binary = find_opencode(cfg)
    if not binary:
        return
    try:
        out = subprocess.run(
            [binary, "session", "list"], cwd=find_workdir(cfg),
            capture_output=True, text=True, timeout=60,
        ).stdout
        lines = [ln for ln in out.strip().splitlines() if ln.strip()]
        if lines:
            sid = lines[0].split()[0]
            if len(sid) > 8:
                write_file(SESSION_FILE, sid)
                log("Session gesetzt: %s" % sid)
    except Exception:  # noqa: BLE001
        pass


HELP = (
    "Schreib mir einfach deine Frage, ich leite sie an den lokalen "
    "Agenten weiter.\n\n"
    "Befehle:\n"
    "/stand  Status der Bruecke\n"
    "/neu    Neue Unterhaltung, Gedaechtnis weg\n"
    "/hilfe  Diese Liste"
)


def process(job, cfg):
    chat_id = job["chat_id"]
    text = job["text"].strip()
    if not text:
        return

    if text.startswith("/"):
        cmd = text.split()[0].lower()
        if cmd in ("/start", "/hilfe", "/help"):
            send(chat_id, HELP)
            return
        if cmd == "/stand":
            send(chat_id, "Bruecke laeuft. Modus: %s. Session: %s" % (
                job.get("mode", "?"),
                read_file(SESSION_FILE) or "noch keine",
            ))
            return
        if cmd == "/neu":
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            send(chat_id, "Neue Unterhaltung. Was steht an?")
            return

    log("Anfrage (%d Zeichen): %s" % (len(text), text[:140]))
    try:
        send(chat_id, "Ich lese das und melde mich.")
    except Exception:  # noqa: BLE001
        pass
    answer = run_opencode(text, cfg)
    remember_session(cfg)
    send(chat_id, answer)
    log("Antwort gesendet")


def worker(cfg):
    while True:
        job = WORK.get()
        try:
            process(job, cfg)
        except Exception as exc:  # noqa: BLE001
            log("Worker-Fehler: %s" % exc)
        finally:
            WORK.task_done()


def accept(token, payload, cfg, mode):
    """Prueft Ownership, legt die Nachricht in die Queue."""
    msg = payload.get("message") or payload.get("edited_message")
    if not msg:
        return
    chat = msg.get("chat") or {}
    sender = msg.get("from") or {}
    text = (msg.get("text") or "").strip()
    if not text or chat.get("type") != "private":
        return

    owner = read_file(OWNER_FILE)
    if not owner:
        write_file(OWNER_FILE, str(sender.get("id", "")))
        log("Besitzer gesetzt")
        send(chat["id"],
             "Bruecke aktiv. Du bist der Besitzer dieser Brueche.\n\n" + HELP)
        return
    if str(sender.get("id", "")) != owner:
        log("Fremde Nachricht verworfen")
        return
    WORK.put({"chat_id": chat["id"], "text": text, "mode": mode})


def run_poll(token, cfg):
    log("Modus poll")
    while True:
        offset = int(read_file(OFFSET_FILE, "0") or 0)
        try:
            params = {"timeout": POLL_TIMEOUT}
            if offset:
                params["offset"] = offset
            res = api(token, "getUpdates", params)
        except urllib.error.HTTPError as exc:
            body = exc.read()[:200].decode("utf-8", "replace")
            if exc.code == 409:
                log("getUpdates 409: ein Webhook ist aktiv oder ein zweiter "
                    "Abfrager laeuft. 60s warten.")
                time.sleep(60)
            else:
                log("getUpdates HTTP %d: %s" % (exc.code, body))
                time.sleep(15)
            continue
        except Exception as exc:  # noqa: BLE001
            log("getUpdates Fehler: %s" % exc)
            time.sleep(15)
            continue

        for upd in res.get("result", []):
            write_file(OFFSET_FILE, str(upd.get("update_id", 0) + 1))
            accept(token, upd, cfg, "poll")
        time.sleep(1)


def make_handler(cfg, secret):
    class Handler(BaseHTTPRequestHandler):
        server_version = "45dgof8-tg"
        sys_version = ""

        def log_message(self, fmt, *args):
            return

        def _reply(self, code):
            self.send_response(code)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def do_GET(self):  # noqa: N802
            self._reply(200 if self.path == "/healthz" else 404)

        def do_POST(self):  # noqa: N802
            if self.path.rstrip("/") not in ("/telegram-hook", "/hook"):
                self._reply(404)
                return
            given = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if not secret or given != secret:
                log("Webhook-Aufruf ohne korrektes Secret abgelehnt")
                self._reply(403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode())
            except Exception as exc:  # noqa: BLE001
                log("Webhook-Payload kaputt: %s" % exc)
                self._reply(400)
                return
            self._reply(200)
            accept(read_file(TOKEN_FILE), payload, cfg, "webhook")

    return Handler


def register_webhook(token, cfg, secret):
    url = cfg["webhook_url"]
    api(token, "setWebhook", {
        "url": url,
        "secret_token": secret,
        "allowed_updates": '["message"]',
    })
    log("Webhook registriert: %s" % url)


def main():
    try:
        os.makedirs(STATE, mode=0o700, exist_ok=True)
    except OSError as exc:
        sys.stderr.write("State-Verzeichnis nicht anlegbar: %s\n" % exc)
        return 1

    token = read_file(TOKEN_FILE)
    if not token:
        sys.stderr.write(
            "Kein Bot-Token. Datei anlegen:\n  %s\nInhalt: der Token von "
            "BotFather, Rechte 600.\n" % TOKEN_FILE
        )
        return 2

    cfg = load_config()
    mode = (cfg.get("mode") or "auto").lower()
    if mode == "auto":
        mode = "webhook" if cfg.get("webhook_url") else "poll"

    secret = read_file(SECRET_FILE)
    if mode == "webhook":
        if not secret:
            sys.stderr.write(
                "Modus webhook braucht ein Secret. Anlegen:\n  %s\n"
                "Wert:openssl rand -hex 24\n" % SECRET_FILE
            )
            return 2
        if not cfg.get("webhook_url"):
            sys.stderr.write("Modus webhook braucht webhook_url in der config.\n")
            return 2

    if not find_opencode(cfg):
        sys.stderr.write("opencode-Binary nicht gefunden.\n")
        return 1

    # Port zuerst belegen, erst danach den Webhook bei Telegram anmelden.
    # Sonst ist der Bot schon umgestellt, obwohl lokal gar nichts laeuft.
    srv = None
    if mode == "webhook":
        port = int(cfg.get("port") or 8790)
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(cfg, secret))
        except OSError as exc:
            sys.stderr.write(
                "Port %d nicht belegbar: %s\n"
                "Entweder laeuft schon eine Brueche, oder ein anderes "
                "Programm nutzt den Port. In der config einen freien Port "
                "eintragen.\n" % (port, exc)
            )
            return 3

    threading.Thread(target=worker, args=(cfg,), daemon=True).start()
    log("Bruecke gestartet, Modus %s" % mode)

    if srv is not None:
        try:
            register_webhook(token, cfg, secret)
        except Exception as exc:  # noqa: BLE001
            log("setWebhook fehlgeschlagen: %s" % exc)
        log("Webhook lauscht auf 127.0.0.1:%d" % srv.server_address[1])
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0

    run_poll(token, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
