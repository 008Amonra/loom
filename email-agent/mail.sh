#!/usr/bin/env bash
# Launch opencode with EMAIL_PASSPHRASE set
source ~/.opencode/secrets.env 2>/dev/null
if [ -z "$EMAIL_PASSPHRASE" ]; then
  echo "📧 Passphrase eingeben (unsichtbar):"
  read -s EMAIL_PASSPHRASE
  export EMAIL_PASSPHRASE
  echo ""
fi
echo "🔓 Starte opencode..."
opencode
