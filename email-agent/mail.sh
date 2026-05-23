#!/usr/bin/env bash
# Launch opencode with EMAIL_PASSPHRASE set (securely, no echo)
echo "📧 Email-Agent: Passphrase eingeben (unsichtbar):"
read -s EMAIL_PASSPHRASE
export EMAIL_PASSPHRASE
echo ""
echo "🔓 Passphrase gesetzt. Starte opencode..."
opencode
