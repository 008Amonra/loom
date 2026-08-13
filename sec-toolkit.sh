#!/usr/bin/env bash
export LC_ALL=C
set -euo pipefail

# ─── sec-toolkit.sh ── unified Linux security toolkit ────────────────
# Usage:
#   ./sec-toolkit.sh                  interactive menu (guided setup)
#   ./sec-toolkit.sh check            read-only security check
#   ./sec-toolkit.sh harden           conservative desktop hardening
#   ./sec-toolkit.sh verify           verify hardening results
#   ./sec-toolkit.sh scan [path]      ClamAV scan (default: ~/Downloads)
#   ./sec-toolkit.sh clam-setup       install ClamAV + ClamTk
#   ./sec-toolkit.sh fw               firewall setup only
#   ./sec-toolkit.sh files            write toolkit helper files to ~/sec-toolkit
#
# DISCLAIMER: This tool modifies system configuration (firewall, sysctl,
# AppArmor, auto-updates). Always create a backup before hardening.
# Provided "as is" without warranty. See LICENSE for full terms.
# ─────────────────────────────────────────────────────────────────────

BASE_DIR="${HOME}/sec-toolkit"
REPORT_DIR="${HOME}/sec-check-reports"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${REPORT_DIR}/sec-toolkit_${STAMP}.log"
LANG_CHOICE="en"
SUPPORT_LINK="https://paypal.me/45dgof8"

mkdir -p "${BASE_DIR}" "${REPORT_DIR}"

# ═══════════════════════════════════════════════════════════════════════
#  BILINGUAL MESSAGES
# ═══════════════════════════════════════════════════════════════════════

msg() {
  local key="$1"
  case "$LANG_CHOICE:$key" in
    en:welcome) echo "This starter guides you step by step through security check, firewall setup, hardening, and verification." ;;
    de:welcome) echo "Dieser Starter führt dich Schritt für Schritt durch Sicherheitscheck, Firewall-Setup, Hardening und Verifikation." ;;
    en:gentle_support) echo "If this toolkit helps you and you want to support the project, you can do so here:" ;;
    de:gentle_support) echo "Wenn dir dieses Toolkit hilft und du das Projekt unterstützen möchtest, kannst du das hier tun:" ;;
    en:needsudo) echo "This script uses sudo for system changes and full verification." ;;
    de:needsudo) echo "Dieses Skript nutzt sudo für Systemänderungen und vollständige Prüfungen." ;;
    en:popcheck) echo "Checking whether this is Pop!_OS / Ubuntu-based..." ;;
    de:popcheck) echo "Prüfe, ob dies ein Pop!_OS-/Ubuntu-basiertes System ist..." ;;
    en:notubuntu) echo "This system does not look Ubuntu-based. The script may still work, but it was designed for Pop!_OS / Ubuntu." ;;
    de:notubuntu) echo "Dieses System wirkt nicht Ubuntu-basiert. Das Skript kann trotzdem funktionieren, ist aber für Pop!_OS / Ubuntu gedacht." ;;
    en:phase_check) echo "Phase 1: Read-only security check" ;;
    de:phase_check) echo "Phase 1: Nur lesender Sicherheitscheck" ;;
    en:phase_fw) echo "Phase 2: UFW desktop firewall baseline" ;;
    de:phase_fw) echo "Phase 2: UFW-Desktop-Firewall-Basis" ;;
    en:phase_harden) echo "Phase 3: Conservative desktop hardening" ;;
    de:phase_harden) echo "Phase 3: Konservatives Desktop-Hardening" ;;
    en:phase_verify) echo "Phase 4: Verify results" ;;
    de:phase_verify) echo "Phase 4: Ergebnisse verifizieren" ;;
    en:phase_clam) echo "Phase 5: Optional ClamAV + ClamTk setup" ;;
    de:phase_clam) echo "Phase 5: Optionales ClamAV + ClamTk Setup" ;;
    en:continue) echo "Press Enter to continue." ;;
    de:continue) echo "Drücke Enter zum Fortfahren." ;;
    en:confirm) echo "Do you want to continue? [y/N]: " ;;
    de:confirm) echo "Möchtest du fortfahren? [j/N]: " ;;
    en:skip) echo "Skipped." ;;
    de:skip) echo "Übersprungen." ;;
    en:report) echo "Reports and logs are stored in:" ;;
    de:report) echo "Reports und Logs werden gespeichert in:" ;;
    en:fw_info) echo "Recommended for a normal desktop: deny incoming, allow outgoing, deny routed, low logging." ;;
    de:fw_info) echo "Empfohlen für einen normalen Desktop: deny incoming, allow outgoing, deny routed, logging low." ;;
    en:ssh_q) echo "Do you want to add SSH rate limiting on port 22? [y/N]: " ;;
    de:ssh_q) echo "Möchtest du SSH-Rate-Limiting auf Port 22 hinzufügen? [j/N]: " ;;
    en:lan_q) echo "Do you want to allow your private LAN to reach this machine? Usually NO for max desktop security. [y/N]: " ;;
    de:lan_q) echo "Möchtest du deinem privaten LAN Zugriff auf diesen Rechner erlauben? Für maximale Desktop-Sicherheit meist NEIN. [j/N]: " ;;
    en:clam_q) echo "Do you want to install ClamAV + ClamTk? [y/N]: " ;;
    de:clam_q) echo "Möchtest du ClamAV + ClamTk installieren? [j/N]: " ;;
    en:hard_info) echo "Hardening includes: unattended-upgrades, AppArmor tools, and conservative sysctl settings." ;;
    de:hard_info) echo "Hardening umfasst: unattended-upgrades, AppArmor-Werkzeuge und konservative sysctl-Einstellungen." ;;
    en:verify_info) echo "Verification checks UFW, AppArmor, updates, sysctl values, and listening ports." ;;
    de:verify_info) echo "Die Verifikation prüft UFW, AppArmor, Updates, sysctl-Werte und offene Ports." ;;
    en:clam_info) echo "This installs ClamAV, ClamTk, the signature updater, and a small scan helper script." ;;
    de:clam_info) echo "Dies installiert ClamAV, ClamTk, den Signatur-Updater und ein kleines Scan-Helferskript." ;;
    en:end) echo "Starter finished. You can re-run it any time." ;;
    de:end) echo "Starter abgeschlossen. Du kannst ihn jederzeit erneut starten." ;;
    en:sudo_hint) echo "You may be asked for your sudo password now." ;;
    de:sudo_hint) echo "Du wirst jetzt eventuell nach deinem sudo-Passwort gefragt." ;;
    en:bad_sudo) echo "sudo authentication failed." ;;
    de:bad_sudo) echo "sudo-Authentifizierung fehlgeschlagen." ;;
    en:menu) echo "Select what you want to do:" ;;
    de:menu) echo "Wähle aus, was du tun möchtest:" ;;
    en:menu_1) echo "1) Full guided setup" ;;
    de:menu_1) echo "1) Vollständiges geführtes Setup" ;;
    en:menu_2) echo "2) Check only" ;;
    de:menu_2) echo "2) Nur Check" ;;
    en:menu_3) echo "3) Firewall only" ;;
    de:menu_3) echo "3) Nur Firewall" ;;
    en:menu_4) echo "4) Hardening only" ;;
    de:menu_4) echo "4) Nur Hardening" ;;
    en:menu_5) echo "5) Verify only" ;;
    de:menu_5) echo "5) Nur Verifikation" ;;
    en:menu_6) echo "6) Write toolkit files only" ;;
    de:menu_6) echo "6) Nur Toolkit-Dateien schreiben" ;;
    en:menu_7) echo "7) About / Support" ;;
    de:menu_7) echo "7) Über / Unterstützung" ;;
    en:menu_8) echo "8) Install / configure ClamAV + ClamTk" ;;
    de:menu_8) echo "8) ClamAV + ClamTk installieren / konfigurieren" ;;
    en:menu_prompt) echo -n "Enter choice [1-8]: " ;;
    de:menu_prompt) echo -n "Auswahl eingeben [1-8]: " ;;
    en:about_title) echo "About / Support" ;;
    de:about_title) echo "Über / Unterstützung" ;;
    en:about_text) echo "This toolkit is meant to make Linux desktop security easier, clearer, and repeatable." ;;
    de:about_text) echo "Dieses Toolkit soll Linux-Desktop-Sicherheit einfacher, klarer und wiederholbar machen." ;;
    en:write_files) echo "Writing sec-chk.sh, sec-harden.sh, and sec-verify.sh into the toolkit directory..." ;;
    de:write_files) echo "Schreibe sec-chk.sh, sec-harden.sh und sec-verify.sh in das Toolkit-Verzeichnis..." ;;
    en:files_written) echo "Toolkit files written successfully:" ;;
    de:files_written) echo "Toolkit-Dateien erfolgreich geschrieben:" ;;
  esac
}

# ═══════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

have_cmd() { command -v "$1" >/dev/null 2>&1; }
check_pkg() { dpkg -s "$1" >/dev/null 2>&1; }

print_header() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

pause_step() { echo; msg continue; read -r; }

ask_yes_no() {
  local prompt_key="$1" ans
  printf "%s" "$(msg "$prompt_key")"
  read -r ans
  case "${LANG_CHOICE}:${ans:-n}" in
    en:y|en:Y|en:yes|en:YES|de:j|de:J|de:ja|de:JA|de:y|de:Y) return 0 ;;
    *) return 1 ;;
  esac
}

run_logged() { echo "+ $*"; "$@"; }

choose_language() {
  echo "=========================================="
  echo " Linux Security Starter / Sicherheitsstarter"
  echo "=========================================="
  echo
  echo "1) English"
  echo "2) Deutsch"
  echo
  read -r -p "Choose language / Sprache wählen [1/2]: " ans
  case "${ans:-1}" in
    2) LANG_CHOICE="de" ;; *) LANG_CHOICE="en" ;;
  esac
}

show_support() {
  echo; echo "--------------------------------------------------"
  msg about_title; echo "--------------------------------------------------"
  msg about_text; echo; msg gentle_support
  echo "  ${SUPPORT_LINK}"; echo
}

check_os() {
  msg popcheck | tee -a "$LOG_FILE"
  if [[ -r /etc/os-release ]]; then
    . /etc/os-release
    echo "ID=${ID:-unknown} VERSION_ID=${VERSION_ID:-unknown} PRETTY_NAME=${PRETTY_NAME:-unknown}" | tee -a "$LOG_FILE"
    if [[ "${ID:-}" != "ubuntu" && "${ID:-}" != "pop" ]]; then
      msg notubuntu | tee -a "$LOG_FILE"
    fi
  fi
}

# ═══════════════════════════════════════════════════════════════════════
#  1) SECURITY CHECK  (sec-chk)
# ═══════════════════════════════════════════════════════════════════════

do_check() {
  local TIMESTAMP
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  local REPORT_FILE="${REPORT_DIR}/sec-check_${TIMESTAMP}.log"
  mkdir -p "${REPORT_DIR}"

  {
    echo "Linux Security Check Report"
    echo "Generated: $(date -Is)"
    echo "Host: $(hostname 2>/dev/null || echo unknown)"
    echo "User: $(id -un 2>/dev/null || echo unknown)"
    echo "Report: ${REPORT_FILE}"

    print_header "SYSTEM BASICS"
    [ -r /etc/os-release ] && cat /etc/os-release
    echo; echo "Kernel: $(uname -r)"; echo "Architecture: $(uname -m)"
    uptime || true

    print_header "LAST BOOT / TIME"
    who -b 2>/dev/null || true
    timedatectl 2>/dev/null || true

    print_header "LOGGED-IN USERS"
    who 2>/dev/null || true

    print_header "FAILED SERVICES"
    have_cmd systemctl && systemctl --failed --no-pager 2>&1 || echo "systemctl not available"

    print_header "UFW STATUS"
    if have_cmd ufw; then
      sudo ufw status verbose 2>&1 || true; echo; sudo ufw status numbered 2>&1 || true
    else echo "ufw not installed"; fi

    print_header "LISTENING PORTS"
    have_cmd ss && { sudo ss -tulpen 2>&1 || ss -tuln 2>&1 || true; } || echo "ss not available"

    print_header "RECENT LOGIN HISTORY"
    have_cmd last && last -a 2>&1 | head -n 20 || echo "last not available"

    print_header "RECENT AUTH FAILURES / SECURITY-RELEVANT LOGS"
    if have_cmd journalctl; then
      journalctl -p warning -b --no-pager -n 50 2>&1 || true
      echo
      journalctl --since "7 days ago" --no-pager 2>&1 \
        | grep -Ei "failed password|authentication failure|sudo:|invalid user|ufw block|segfault|denied" \
        | tail -n 50 || true
    else echo "journalctl not available"; fi

    print_header "UPDATES"
    if have_cmd apt; then
      echo "APT package count upgradable:"; apt list --upgradable 2>/dev/null | sed '1d' | wc -l
      echo; echo "Upgradable packages:"; apt list --upgradable 2>/dev/null | sed '1d' || true
    else echo "apt not available"; fi

    print_header "AUTO-UPDATES"
    [[ -f /etc/apt/apt.conf.d/20auto-upgrades ]] && cat /etc/apt/apt.conf.d/20auto-upgrades || echo "20auto-upgrades not found"

    print_header "DISK USAGE"
    df -hT 2>&1 || true

    print_header "INODE USAGE"
    df -ih 2>&1 || true

    print_header "APPARMOR"
    have_cmd systemctl && systemctl status apparmor --no-pager 2>&1 || true
    have_cmd aa-status && sudo aa-status 2>&1 || true

    print_header "TOP MEMORY PROCESSES"
    have_cmd ps && ps -eo pid,user,%mem,%cpu,comm --sort=-%mem | head -n 15 || echo "ps not available"

    print_header "TOP CPU PROCESSES"
    have_cmd ps && ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu | head -n 15 || echo "ps not available"

    print_header "SUDO ACCESS"
    getent group sudo 2>/dev/null || echo "sudo group not found"

    print_header "ROOT LOGIN SHELL USERS"
    awk -F: '($3 == 0) {print $1 ":" $7}' /etc/passwd 2>/dev/null || true

    print_header "WORLD-WRITABLE DIRECTORIES IN /tmp AND /var/tmp"
    find /tmp /var/tmp -maxdepth 1 -type d -printf '%M %u:%g %p\n' 2>/dev/null || true

    print_header "HOME SSH MATERIAL"
    for d in /home/*; do
      [ -d "$d" ] || continue
      if [ -d "$d/.ssh" ]; then
        echo "[SSH DIR] $d/.ssh"; ls -ld "$d/.ssh" 2>/dev/null || true; ls -l "$d/.ssh" 2>/dev/null || true
      fi
    done
    if [ -d "${HOME}/.ssh" ]; then
      echo; echo "[CURRENT USER AUTHORIZED KEYS]"; ls -l "${HOME}/.ssh" 2>/dev/null || true
    fi

    print_header "NETWORK INTERFACES"
    if have_cmd ip; then
      ip -brief address 2>&1 || true; echo; ip route 2>&1 || true
    else echo "ip command not available"; fi

    print_header "KERNEL HARDENING QUICK CHECK"
    for f in \
      /proc/sys/kernel/randomize_va_space \
      /proc/sys/net/ipv4/conf/all/rp_filter \
      /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts \
      /proc/sys/net/ipv4/conf/all/accept_redirects \
      /proc/sys/net/ipv4/conf/default/accept_redirects \
      /proc/sys/net/ipv4/conf/all/send_redirects; do
      [[ -r "$f" ]] && printf "%s = %s\n" "$f" "$(cat "$f")"
    done

    print_header "SNAP / FLATPAK"
    have_cmd snap && snap list 2>&1 || echo "snap not available"
    echo
    have_cmd flatpak && flatpak list 2>&1 || echo "flatpak not available"

    print_header "SUMMARY"
    echo "- Check failed services above"
    echo "- Check listening ports above"
    echo "- Check auth warnings above"
    echo "- Check pending updates above"
    echo "- Review sudo group membership above"
    echo "- Review SSH key material above"
    echo; echo "Report saved to: ${REPORT_FILE}"
  } | tee "${REPORT_FILE}"

  echo; echo "Done. Report saved to:"; echo "${REPORT_FILE}"
}

# ═══════════════════════════════════════════════════════════════════════
#  2) FIREWALL SETUP
# ═══════════════════════════════════════════════════════════════════════

do_firewall() {
  local add_ssh="no" add_lan="no"

  msg fw_info | tee -a "$LOG_FILE"
  if ask_yes_no ssh_q; then add_ssh="yes"; fi
  if ask_yes_no lan_q; then add_lan="yes"; fi

  run_logged sudo apt-get update
  run_logged sudo apt-get install -y ufw
  run_logged sudo ufw --force reset
  run_logged sudo ufw default deny incoming
  run_logged sudo ufw default allow outgoing
  run_logged sudo ufw default deny routed
  run_logged sudo ufw logging low

  [[ "$add_ssh" == "yes" ]] && run_logged sudo ufw limit 22/tcp

  if [[ "$add_lan" == "yes" ]]; then
    run_logged sudo ufw allow from 192.168.0.0/16
    run_logged sudo ufw allow from 10.0.0.0/8
    run_logged sudo ufw allow from 172.16.0.0/12
  fi

  run_logged sudo ufw --force enable
  run_logged sudo ufw status verbose
}

# ═══════════════════════════════════════════════════════════════════════
#  3) HARDENING  (sec-harden)
# ═══════════════════════════════════════════════════════════════════════

do_harden() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "This step requires root. Please run with sudo:"
    echo "  sudo ./sec-toolkit.sh harden"
    exit 1
  fi

  local BACKUP_DIR="/root/sec-harden-backups-${STAMP}"
  local SYSCTL_FILE="/etc/sysctl.d/60-local-security.conf"
  local APT_AUTO_FILE="/etc/apt/apt.conf.d/20auto-upgrades"
  local APT_UNATTENDED_FILE="/etc/apt/apt.conf.d/52local-unattended-upgrades"
  mkdir -p "${BACKUP_DIR}"

  backup_file() { [[ -f "$1" ]] && cp -a "$1" "${BACKUP_DIR}/"; }

  echo "[1/7] Backups..."
  backup_file "$SYSCTL_FILE"
  backup_file "$APT_AUTO_FILE"
  backup_file "$APT_UNATTENDED_FILE"

  echo "[2/7] Updating package lists..."
  apt-get update

  echo "[3/7] Installing security packages..."
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    unattended-upgrades apt-listchanges needrestart \
    apparmor apparmor-utils apparmor-profiles apparmor-profiles-extra \
    curl ca-certificates ufw

  echo "[4/7] Configuring auto-updates..."
  cat > "$APT_AUTO_FILE" <<'EOC'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOC

  cat > "$APT_UNATTENDED_FILE" <<'EOC'
Unattended-Upgrade::Origins-Pattern {
        "origin=Ubuntu,codename=${distro_codename},label=Ubuntu";
        "origin=Ubuntu,codename=${distro_codename},label=Ubuntu-Security";
        "origin=UbuntuESMApps,codename=${distro_codename},label=UbuntuESMApps";
        "origin=UbuntuESM,codename=${distro_codename},label=UbuntuESM";
};
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::SyslogEnable "true";
EOC

  systemctl enable --now unattended-upgrades.service || true

  echo "[5/7] Configuring AppArmor..."
  systemctl enable apparmor.service || true
  systemctl restart apparmor.service || true

  echo "[6/7] Applying conservative sysctl hardening..."
  cat > "$SYSCTL_FILE" <<'EOC'
# Local security hardening for desktop systems
# Conservative settings to avoid breaking normal desktop use.

# ASLR
kernel.randomize_va_space = 2
# Restrict ptrace
kernel.yama.ptrace_scope = 1
# Protect kernel pointer info
kernel.kptr_restrict = 2
# Restrict dmesg for non-root
kernel.dmesg_restrict = 1

# Link/symlink attack protection
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Disable redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Reverse path filtering
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# SYN cookies
net.ipv4.tcp_syncookies = 1

# ICMP hardening
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Log martians
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
EOC

  sysctl --system

  echo "[7/7] Setting safe UFW defaults..."
  if command -v ufw >/dev/null 2>&1; then
    ufw logging low || true
    ufw default deny incoming || true
    ufw default allow outgoing || true
    ufw default deny routed || true
    ufw limit 22/tcp || true
    ufw --force enable || true
  else echo "UFW not installed, skipping."; fi

  echo; echo "Done. Backups: ${BACKUP_DIR}"
}

# ═══════════════════════════════════════════════════════════════════════
#  4) VERIFY  (sec-verify)
# ═══════════════════════════════════════════════════════════════════════

do_verify() {
  local GREEN='\033[0;32m' YELLOW='\033[1;33m' RED='\033[0;31m' NC='\033[0m'
  ok()   { printf "${GREEN}[OK]${NC} %s\n" "$1"; }
  warn() { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
  bad()  { printf "${RED}[CRITICAL]${NC} %s\n" "$1"; }

  check_sysctl_value() {
    local key="$1" expected="$2" current
    current="$(sysctl -n "$key" 2>/dev/null || true)"
    if [[ -z "$current" ]]; then warn "$key could not be read"
    elif [[ "$current" == "$expected" ]]; then ok "$key = $current"
    else warn "$key = $current (expected: $expected)"; fi
  }

  if [[ "${EUID}" -ne 0 ]]; then
    echo "Hint: for complete results, run with sudo:"; echo "  sudo ./sec-toolkit.sh verify"; echo
  fi

  echo "============================================================"
  echo "Linux Security Verify"
  echo "Time: $(date -Is)"
  echo "Host: $(hostname 2>/dev/null || echo unknown)"
  echo "User: $(id -un 2>/dev/null || echo unknown)"
  echo "============================================================"; echo

  echo "=== 1) UFW ==="
  if have_cmd ufw; then
    local UFW_STATUS
    UFW_STATUS="$(ufw status verbose 2>/dev/null || true)"
    if [[ -z "$UFW_STATUS" ]]; then warn "UFW not fully readable without sudo"
    else
      echo "$UFW_STATUS"; echo
      echo "$UFW_STATUS" | grep -q "^Status: active" && ok "UFW is active" || bad "UFW is not active"
      echo "$UFW_STATUS" | grep -q "Default: deny (incoming)" && ok "Default incoming = deny" || warn "Default incoming is not deny"
      echo "$UFW_STATUS" | grep -q "allow (outgoing)" && ok "Default outgoing = allow" || warn "Default outgoing is not allow"
      echo "$UFW_STATUS" | grep -Eq "deny \(routed\)|disabled \(routed\)" && ok "Routed traffic is not open" || warn "Check routed traffic"
      echo; echo "--- UFW Rules ---"
      ufw status numbered 2>/dev/null || warn "UFW rules not fully readable without sudo"
    fi
  else bad "UFW is not installed"; fi

  echo; echo "=== 2) AppArmor ==="
  if have_cmd systemctl; then
    systemctl is-active --quiet apparmor 2>/dev/null && ok "AppArmor service is running" || warn "AppArmor service is not running"
  fi
  if have_cmd aa-status; then
    sudo aa-status 2>/dev/null || warn "aa-status could not be fully executed"
  else warn "aa-status not installed"; fi

  echo; echo "=== 3) Automatic updates ==="
  check_pkg unattended-upgrades && ok "unattended-upgrades installed" || bad "unattended-upgrades missing"

  if [[ -f /etc/apt/apt.conf.d/20auto-upgrades ]]; then
    cat /etc/apt/apt.conf.d/20auto-upgrades; echo
    grep -q 'APT::Periodic::Update-Package-Lists "1";' /etc/apt/apt.conf.d/20auto-upgrades \
      && ok "Automatic package list updates enabled" || warn "Automatic package list updates not clearly enabled"
    grep -q 'APT::Periodic::Unattended-Upgrade "1";' /etc/apt/apt.conf.d/20auto-upgrades \
      && ok "Unattended upgrades enabled" || warn "Unattended upgrades not clearly enabled"
  else bad "/etc/apt/apt.conf.d/20auto-upgrades missing"; fi

  if have_cmd systemctl; then
    systemctl is-enabled --quiet unattended-upgrades 2>/dev/null \
      && ok "unattended-upgrades is enabled" || warn "unattended-upgrades is not enabled"
  fi

  echo; echo "=== 4) Security packages ==="
  for pkg in apparmor apparmor-utils apparmor-profiles apparmor-profiles-extra apt-listchanges needrestart; do
    check_pkg "$pkg" && ok "$pkg installed" || warn "$pkg missing"
  done

  echo; echo "=== 5) Sysctl hardening ==="
  check_sysctl_value "kernel.randomize_va_space" "2"
  check_sysctl_value "kernel.yama.ptrace_scope" "1"
  check_sysctl_value "kernel.kptr_restrict" "2"
  check_sysctl_value "kernel.dmesg_restrict" "1"
  check_sysctl_value "fs.protected_hardlinks" "1"
  check_sysctl_value "fs.protected_symlinks" "1"
  check_sysctl_value "net.ipv4.conf.all.accept_redirects" "0"
  check_sysctl_value "net.ipv4.conf.default.accept_redirects" "0"
  check_sysctl_value "net.ipv4.conf.all.send_redirects" "0"
  check_sysctl_value "net.ipv4.conf.default.send_redirects" "0"
  check_sysctl_value "net.ipv4.conf.all.rp_filter" "1"
  check_sysctl_value "net.ipv4.conf.default.rp_filter" "1"
  check_sysctl_value "net.ipv4.tcp_syncookies" "1"
  check_sysctl_value "net.ipv4.icmp_echo_ignore_broadcasts" "1"
  check_sysctl_value "net.ipv4.icmp_ignore_bogus_error_responses" "1"

  echo; echo "=== 6) Listening ports ==="
  if have_cmd ss; then
    sudo ss -tulpen 2>/dev/null || ss -tuln 2>/dev/null || true
    echo
    ss -tuln 2>/dev/null | grep -q ':22 ' && warn "Port 22 is listening locally" || ok "Port 22 is not listening"
  else warn "ss not available"; fi

  echo; echo "=== 7) SSH Server ==="
  if check_pkg openssh-server; then
    warn "openssh-server is installed"
    if have_cmd systemctl; then
      systemctl is-active --quiet ssh 2>/dev/null && warn "SSH service is running" || ok "SSH service is not running"
    fi
  else ok "openssh-server is not installed"; fi

  echo; echo "=== 8) Updates available? ==="
  if have_cmd apt; then
    local COUNT
    COUNT="$(apt list --upgradable 2>/dev/null | sed '1d' | wc -l)"
    echo "Upgradable packages: ${COUNT}"
    [[ "${COUNT}" -eq 0 ]] && ok "No immediately visible updates pending" || warn "${COUNT} updates available"
  else warn "apt not available"; fi

  echo; echo "=== 9) Quick Assessment ==="
  echo "Check especially:"
  echo "- UFW active, incoming deny"
  echo "- AppArmor running"
  echo "- unattended-upgrades enabled"
  echo "- sysctl values as expected"
  echo "- no unexpected open ports"
  echo "- SSH only if intentionally wanted"

  echo; echo "Done."
}

# ═══════════════════════════════════════════════════════════════════════
#  5) CLAMAV SCAN
# ═══════════════════════════════════════════════════════════════════════

do_clam_scan() {
  local SCAN_BASE="${1:-$HOME/Downloads}"
  local SCAN_LOG="${REPORT_DIR}/clam-scan_${STAMP}.log"

  if [[ ! -e "$SCAN_BASE" ]]; then
    echo "Target does not exist: $SCAN_BASE"; exit 1
  fi

  echo "Scanning: $SCAN_BASE"
  echo "Log: $SCAN_LOG"

  if ! have_cmd clamscan; then
    echo "clamscan not found. Run 'sec-toolkit.sh clam-setup' first, or install ClamAV manually."
    exit 1
  fi

  clamscan -r -i --log="$SCAN_LOG" "$SCAN_BASE"
  echo; echo "Done. Log saved to:"; echo "$SCAN_LOG"
}

# ═══════════════════════════════════════════════════════════════════════
#  6) CLAMAV + CLAMTK SETUP
# ═══════════════════════════════════════════════════════════════════════

do_clam_setup() {
  echo "Installing ClamAV + ClamTk..."
  sudo apt-get update
  sudo apt-get install -y clamav clamav-daemon clamtk

  echo "Updating virus signatures..."
  sudo systemctl stop clamav-freshclam 2>/dev/null || true
  sudo freshclam || true
  sudo systemctl start clamav-freshclam 2>/dev/null || true
  sudo systemctl enable clamav-freshclam 2>/dev/null || true

  echo; echo "ClamAV + ClamTk installed."
  echo "Launch ClamTk from your app menu or run: clamtk"
  echo "To scan a directory: $0 scan /path/to/dir"
}

# ═══════════════════════════════════════════════════════════════════════
#  7) WRITE TOOLKIT FILES (standalone helpers)
# ═══════════════════════════════════════════════════════════════════════

do_write_files() {
  msg write_files | tee -a "$LOG_FILE"

  cat > "${BASE_DIR}/sec-chk.sh" <<'EOC'
#!/usr/bin/env bash
# Standalone security check — extracted from sec-toolkit.sh
export LC_ALL=C
cd "$(dirname "$0")" && exec bash -c 'source sec-toolkit.sh 2>/dev/null; do_check' 2>/dev/null \
  || echo "Run via: ./sec-toolkit.sh check"
EOC
  chmod +x "${BASE_DIR}/sec-chk.sh"

  cat > "${BASE_DIR}/sec-harden.sh" <<'EOC'
#!/usr/bin/env bash
# Standalone hardening — extracted from sec-toolkit.sh
export LC_ALL=C
cd "$(dirname "$0")" && exec sudo bash -c 'source sec-toolkit.sh 2>/dev/null; do_harden' 2>/dev/null \
  || echo "Run via: sudo ./sec-toolkit.sh harden"
EOC
  chmod +x "${BASE_DIR}/sec-harden.sh"

  cat > "${BASE_DIR}/sec-verify.sh" <<'EOC'
#!/usr/bin/env bash
# Standalone verification — extracted from sec-toolkit.sh
export LC_ALL=C
cd "$(dirname "$0")" && exec bash -c 'source sec-toolkit.sh 2>/dev/null; do_verify' 2>/dev/null \
  || echo "Run via: ./sec-toolkit.sh verify"
EOC
  chmod +x "${BASE_DIR}/sec-verify.sh"

  msg files_written | tee -a "$LOG_FILE"
  echo "  ${BASE_DIR}/sec-chk.sh" | tee -a "$LOG_FILE"
  echo "  ${BASE_DIR}/sec-harden.sh" | tee -a "$LOG_FILE"
  echo "  ${BASE_DIR}/sec-verify.sh" | tee -a "$LOG_FILE"
}

# ═══════════════════════════════════════════════════════════════════════
#  INTERACTIVE MENU
# ═══════════════════════════════════════════════════════════════════════

full_guided_setup() {
  check_os; pause_step

  msg sudo_hint
  if ! sudo -v; then msg bad_sudo; exit 1; fi

  do_check; pause_step

  if ask_yes_no confirm; then do_firewall; else msg skip; fi
  pause_step

  if ask_yes_no confirm; then do_harden; else msg skip; fi
  pause_step

  if ask_yes_no confirm; then do_verify; else msg skip; fi
  pause_step

  if ask_yes_no clam_q; then do_clam_setup; else msg skip; fi
}

do_interactive() {
  exec > >(tee -a "$LOG_FILE") 2>&1

  choose_language; echo
  msg welcome; msg needsudo; echo
  msg gentle_support; echo "  ${SUPPORT_LINK}"; echo
  msg report; echo "  $REPORT_DIR"
  echo "Toolkit directory:"; echo "  $BASE_DIR"; echo

  echo; msg menu
  msg menu_1; msg menu_2; msg menu_3; msg menu_4; msg menu_5
  msg menu_6; msg menu_7; msg menu_8
  echo; msg menu_prompt
  read -r MENU_CHOICE

  case "${MENU_CHOICE:-1}" in
    1) full_guided_setup ;;
    2) msg sudo_hint; sudo -v || true; do_check ;;
    3) msg sudo_hint; sudo -v || true; do_firewall ;;
    4) msg sudo_hint; sudo -v || true; do_harden ;;
    5) msg sudo_hint; sudo -v || true; do_verify ;;
    6) do_write_files ;;
    7) show_support ;;
    8) do_clam_setup ;;
    *) echo "Invalid choice, starting full guided setup."; full_guided_setup ;;
  esac

  echo; msg end; msg report; echo "  $REPORT_DIR"; echo "  $LOG_FILE"
  echo "Toolkit directory:"; echo "  $BASE_DIR"; echo
  msg gentle_support; echo "  ${SUPPORT_LINK}"; echo
}

# ═══════════════════════════════════════════════════════════════════════
#  CLI DISPATCHER
# ═══════════════════════════════════════════════════════════════════════

usage() {
  cat <<EOF
sec-toolkit.sh — unified Linux security toolkit

Usage:
  $(basename "$0")                  interactive menu (guided setup)
  $(basename "$0") check            read-only security check
  $(basename "$0") harden           conservative desktop hardening (needs sudo)
  $(basename "$0") verify           verify hardening results
  $(basename "$0") scan [path]      ClamAV scan (default: ~/Downloads)
  $(basename "$0") clam-setup       install ClamAV + ClamTk
  $(basename "$0") fw               firewall setup only
  $(basename "$0") files            write standalone helper files to ~/sec-toolkit
  $(basename "$0") help             show this help

Reports are saved to ~/sec-check-reports/
EOF
}

case "${1:-}" in
  check)      do_check ;;
  harden)     do_harden ;;
  verify)     do_verify ;;
  scan)       do_clam_scan "${2:-}" ;;
  clam-setup) do_clam_setup ;;
  fw)         do_firewall ;;
  files)      do_write_files ;;
  help|-h|--help) usage ;;
  "")         do_interactive ;;
  *)          echo "Unknown command: $1"; echo; usage; exit 1 ;;
esac
