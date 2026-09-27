#!/bin/bash
# 45dgof8 installer library v2
# Sourced by install.sh / bootstrap.sh. No side effects on load.

# ─────────────────────────────────────────────────────────
# Non-interactive input
# ─────────────────────────────────────────────────────────
# v1 used bare `read -rp`. In a pipeline (curl | bash) or CI,
# read hits EOF and, with `set -e`, kills the whole installer.
# ask() returns a default instead of failing.
NONINTERACTIVE="${NONINTERACTIVE:-0}"
_answers_file="${_answers_file:-}"

ask() {
    local prompt="$1" default="${2:-}" reply=""
    # A piped answer stream (printf 'x\ny\n' | bash install.sh) must still
    # work even though there is no terminal. NONINTERACTIVE only means
    # "do not block on a human", not "ignore stdin". If reading fails we
    # fall back to the default, which is what makes CI safe.
    local can_read=0
    if [ -t 0 ] || [ -p /dev/stdin ] || { [ ! -t 0 ] && [ -r /dev/stdin ]; }; then
        can_read=1
    fi
    if [ "$NONINTERACTIVE" = "1" ] && [ "$can_read" = "0" ]; then
        printf '%s%s\n' "$prompt" "$default"
        REPLY="$default"
        return 0
    fi
    if [ -n "$_answers_file" ] && [ -r "$_answers_file" ]; then
        if ! IFS= read -r reply < "$_answers_file"; then
            REPLY="$default"; return 0
        fi
        _answers_file=""
        printf '%s%s\n' "$prompt" "$reply"
        REPLY="$reply"
        return 0
    fi
    if ! printf '%s' "$prompt" >&2; then REPLY="$default"; return 0; fi
    if ! IFS= read -r reply; then
        printf '\n'
        REPLY="$default"
        return 0
    fi
    [ -z "$reply" ] && reply="$default"
    REPLY="$reply"
}

ask_yes() {
    local prompt="$1" default="${2:-N}"
    ask "$prompt" "$default"
    [[ "$REPLY" =~ ^[Yy] ]]
}

ask_secret() {
    local prompt="$1" reply=""
    if [ "$NONINTERACTIVE" = "1" ]; then REPLY=""; return 0; fi
    printf '%s' "$prompt" >&2
    if ! IFS= read -rs reply; then printf '\n'; REPLY=""; return 0; fi
    printf '\n' >&2
    REPLY="$reply"
}

# ─────────────────────────────────────────────────────────
# Download with integrity verification
# ─────────────────────────────────────────────────────────
# v1 curl'd binaries straight into $BIN_DIR and chmod +x'd them.
# If the published file was ever replaced, that code runs as the user.
# v2: download to a temp file, verify SHA256, only then install.
# Set EXPECTED_SHA256_<key>=<hash> in a manifest next to the script.

fetch_verified() {
    local url="$1" dest="$2" expected="${3:-}"
    local tmp
    tmp="$(mktemp)" || return 1

    info "Downloading $(basename "$dest")..."
    if ! curl -fsSL --proto '=https' --tlsv1.2 "$url" -o "$tmp"; then
        err "download failed: $url"
        rm -f "$tmp"
        return 1
    fi

    if [ -z "$expected" ]; then
        err "REFUSING: no SHA256 pinned for $(basename "$dest")."
        err "This installer will not run unverified binaries."
        err "Add EXPECTED_SHA256 to the manifest, or install manually:"
        err "  curl -fsSL '$url' -o '$dest'   # then verify yourself"
        rm -f "$tmp"
        return 2
    fi

    local actual
    actual="$(sha256sum "$tmp" | cut -d' ' -f1)"
    if [ "${actual,,}" != "${expected,,}" ]; then
        err "CHECKSUM MISMATCH for $(basename "$dest")"
        err "  expected: $expected"
        err "  actual:   $actual"
        err "The file was NOT installed. Treat this as a security warning."
        rm -f "$tmp"
        return 3
    fi

    ok "checksum verified (${actual:0:12}...)"
    mkdir -p "$(dirname "$dest")"
    mv "$tmp" "$dest" || { rm -f "$tmp"; return 1; }
    return 0
}

# ─────────────────────────────────────────────────────────
# Config writes - never destroy, always back up
# ─────────────────────────────────────────────────────────
# v1 did `cat > opencode.json` unconditionally. Selecting the
# default provider wiped a full existing config (MCP servers,
# agents, skills) with no backup and no prompt.
# v2: detect, back up, merge when possible, refuse when not.

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/opencode}"
OC_CONFIG="$CONFIG_DIR/opencode.json"
BACKUP_STAMP="$(date +%Y%m%d-%H%M%S)"

# JSON merge via python3 (no jq dependency). Existing keys win unless
# FORCE_REPLACE=1, so we never silently drop a provider the user set up.
write_opencode_config() {
    local new_json="$1"
    mkdir -p "$CONFIG_DIR"

    if [ -s "$OC_CONFIG" ]; then
        cp -a "$OC_CONFIG" "$OC_CONFIG.bak-$BACKUP_STAMP"
        ok "existing opencode.json backed up → $OC_CONFIG.bak-$BACKUP_STAMP"
    fi

    if [ -z "$(ls -A "$CONFIG_DIR" 2>/dev/null)" ] || [ ! -s "$OC_CONFIG" ]; then
        printf '%s\n' "$new_json" > "$OC_CONFIG"
        ok "opencode.json created"
        return 0
    fi

    if [ "${FORCE_REPLACE:-0}" = "1" ]; then
        printf '%s\n' "$new_json" > "$OC_CONFIG"
        ok "opencode.json REPLACED (backup kept)"
        return 0
    fi

    # merge: run both configs through python, existing keys take precedence
    # Both paths are passed explicitly. Do NOT rely on OC_CONFIG being
    # exported from the caller's environment - it is a plain shell
    # variable here, and os.environ["OC_CONFIG"] would raise KeyError,
    # making the merge fail silently. That bug shipped once already.
    if command -v python3 >/dev/null 2>&1; then
        if OC_PATH="$OC_CONFIG" NEW_JSON="$new_json" python3 - <<'PY' > "$OC_CONFIG.merged" 2>/dev/null
import json, os, pathlib, sys
try:
    old = json.loads(pathlib.Path(os.environ["OC_PATH"]).read_text())
    new = json.loads(os.environ["NEW_JSON"])
except Exception:
    sys.exit(1)
def deep_merge(defaults, existing):
    """existing (the user's live config) wins every conflict.

    Installer defaults only contribute keys the user never set.
    Recursion lets a new default section be filled in without
    touching anything the user configured inside it.
    """
    out = dict(existing)
    for k, v in defaults.items():
        if k not in out:
            out[k] = v
        elif isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(v, out[k])
    return out
print(json.dumps(deep_merge(new, old), indent=2))
PY
        then
            mv "$OC_CONFIG.merged" "$OC_CONFIG"
            ok "opencode.json MERGED (your existing settings kept)"
            return 0
        fi
        rm -f "$OC_CONFIG.merged" 2>/dev/null || true
    fi

    # merge failed - do not guess
    err "Could not merge automatically. Your file is untouched."
    err "New config NOT written. Merge by hand, or re-run with FORCE_REPLACE=1."
    printf '%s\n' "$new_json" > "$OC_CONFIG.proposed"
    ok "proposed config saved → $OC_CONFIG.proposed"
    return 0
}

# ─────────────────────────────────────────────────────────
# Disk safety helpers
# ─────────────────────────────────────────────────────────
# Learned the hard way on 2026-09-27: two drives shared the
# label "berryboot", /dev/sdc pointed at three different things
# in one hour, and a wrong /dev/sdX would have reformatted
# the wrong disk. Never write to a raw device without this.

# disk_matches <path> <expected-label> - verify by filesystem label
disk_matches() {
    local dev="$1" want="$2" got
    got="$(blkid -s LABEL -o value "$dev" 2>/dev/null || true)"
    [ "$got" = "$want" ]
}

# refuse_write_to_unlabelled <dev> - belt-and-braces before any mkfs/wipefs
refuse_write_to_unlabelled() {
    local dev="$1"
    if [ -z "$(blkid -s LABEL -o value "$dev" 2>/dev/null || true)" ]; then
        err "REFUSING to write to $dev: it has no filesystem label."
        err "Unlabelled devices are the #1 cause of destroying the wrong disk."
        return 1
    fi
    return 0
}

# backup_mount_ready <mountpoint> <expected-label> [required-marker]
backup_mount_ready() {
    local mp="$1" want="$2" marker="${3:-}" src label
    if ! mountpoint -q "$mp" 2>/dev/null; then
        err "backup disk not mounted at $mp"
        return 1
    fi
    src="$(findmnt -n -o SOURCE "$mp" 2>/dev/null || true)"
    # kernel label first: blkid's udev cache goes stale after e2label
    label="$(findmnt -n -o LABEL "$mp" 2>/dev/null || true)"
    [ -z "$label" ] && [ -n "$src" ] && label="$(blkid -s LABEL -o value "$src" 2>/dev/null || true)"
    if [ "$label" != "$want" ]; then
        err "wrong disk at $mp: label='${label:-none}', expected '$want'"
        return 1
    fi
    if [ -n "$marker" ] && [ ! -f "$mp/$marker" ]; then
        err "$mp has no '$marker' marker - not our backup disk"
        return 1
    fi
    return 0
}

# ─────────────────────────────────────────────────────────
# Secret handling for external backups
# ─────────────────────────────────────────────────────────
# v1 rsync'd ~/.ssh, ~/.gnupg and secrets.env onto a plain ext4
# disk. Anyone with physical access had every key.
# v2: secrets go into a GPG container, verified non-empty, and the
# plaintext tree is excluded from the copy entirely.

BACKUP_GPG_KEY="${BACKUP_GPG_KEY:-backup@45dgof8.ch}"

# build_secret_container <outfile.tgz> - stages nothing; use encrypt_stage
encrypt_stage() {
    local stage="$1" out="$2"
    tar cf "$stage/secrets.tar" -C "$stage" . 2>/dev/null || return 1
    gpg --batch --yes --quiet --trust-model always -r "$BACKUP_GPG_KEY" \
        --output "$out" --encrypt "$stage/secrets.tar" 2>/dev/null || return 1
    local sz
    sz="$(stat -c%s "$out" 2>/dev/null || echo 0)"
    if [ "$sz" -lt 100 ]; then
        err "encrypted container looks empty (${sz}B) - refusing"
        rm -f "$out"
        return 1
    fi
    return 0
}

# Verify a container decrypts and contains what we expect.
# "Backup SUCCESS" after a silently-failed compress is exactly the
# failure mode we hit; never trust the exit code alone.
verify_secret_container() {
    local gpgfile="$1" want="${2:-}"
    [ -s "$gpgfile" ] || { err "container missing/empty: $gpgfile"; return 1; }
    local listing
    listing="$(gpg --batch --quiet --trust-model always -d "$gpgfile" 2>/dev/null | tar tf - 2>/dev/null)"
    if [ -z "$listing" ]; then
        err "container does not decrypt: $gpgfile"
        return 1
    fi
    if [ -n "$want" ] && ! printf '%s' "$listing" | grep -q "$want"; then
        err "container is valid but missing '$want'"
        return 1
    fi
    ok "container verified: $(printf '%s' "$listing" | grep -c .) entries, includes '$want'"
    return 0
}

# Excludes shared by every plaintext backup path.
# NOTE: tar --exclude needs a leading ./ when archiving "-C dir .",
# otherwise patterns silently do not match. Verified 2026-09-27.
SECRET_EXCLUDES=(
    --exclude='./.opencode/secrets.env'
    --exclude='./.memory/rot-backups'
    --exclude='*secrets*'
    --exclude='*.env'
    --exclude='./.config/n8n.env'
    --exclude='./.gnupg'
    --exclude='./.ssh/id_rsa'
    --exclude='./.ssh/id_ed25519'
    --exclude='./.ssh/termux_phone'
)
