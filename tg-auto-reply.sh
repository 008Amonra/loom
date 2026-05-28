#!/bin/bash
# tg-auto-reply — polls Telegram for /start and auto-replies with voice + text
# Run in background: nohup ./tg-auto-reply.sh &
# Uses tg-voice for audio + sendMessage for text

BOT_TOKEN="${TG_BOT_TOKEN:-$(grep TG_BOT_TOKEN ~/.opencode/secrets.env 2>/dev/null | head -1 | cut -d= -f2 | tr -d "'")}"
API="https://api.telegram.org/bot${BOT_TOKEN}"
OFFSET_FILE="/tmp/tg-auto-reply-offset"

OFFSET=0
[ -f "$OFFSET_FILE" ] && OFFSET=$(cat "$OFFSET_FILE")

WELCOME_TEXT="Welcome to 45dgof8. Custom AI agents for solo creators. No subscriptions, no lock-in. Describe what you need and I will build it. Starting at 15 Swiss Francs. First revision free."
SERVICES_TEXT="What I offer: Custom music tracks SFr. 15, Automation workflows SFr. 25, Revisions SFr. 5, Setup support SFr. 49. Or pay any amount — I will follow up within 24h. https://008amonra.github.io/loom/"

while true; do
  RESP=$(curl -s "$API/getUpdates" \
    -d offset=$OFFSET \
    -d timeout=30 \
    -d allowed_updates='["message"]')

  OK=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok',False))" 2>/dev/null)
  [ "$OK" != "True" ] && sleep 5 && continue

  RESULT=$(echo "$RESP" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for u in data.get('result', []):
    m = u.get('message', {})
    text = m.get('text', '')
    cid = m.get('chat', {}).get('id')
    uid = u['update_id']
    name = m.get('from', {}).get('first_name', 'there')
    if text and cid:
        print(f'{uid}|{cid}|{name}|{text[:100]}')" 2>/dev/null)

  while IFS='|' read -r UID CID NAME TEXT; do
    [ -z "$CID" ] && continue

    case "$TEXT" in
      /start*)
        curl -s "$API/sendMessage" -d chat_id=$CID -d text="Hey $NAME! $WELCOME_TEXT" > /dev/null
        # send voice (reuse tg-voice approach)
        TMP=$(mktemp /tmp/tg-reply-XXXXXX.ogg)
        echo "$WELCOME_TEXT" | piper --model "$HOME/.local/share/piper/en-us-lessac-medium.onnx" --length-scale 1.3 --output-raw | ffmpeg -f s16le -ar 22050 -ac 1 -i pipe: -c:a libopus -b:a 16k "$TMP" -y 2>/dev/null
        curl -s -X POST "$API/sendVoice" -F chat_id=$CID -F voice=@"$TMP" > /dev/null
        rm -f "$TMP"
        ;;
      /services*)
        curl -s "$API/sendMessage" -d chat_id=$CID -d text="$SERVICES_TEXT" > /dev/null
        ;;
    esac

    OFFSET=$((UID + 1))
    echo $OFFSET > "$OFFSET_FILE"
  done <<< "$RESULT"

  sleep 2
done
