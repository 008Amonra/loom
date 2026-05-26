#!/bin/bash
# 45dgof8 Podcast Generator
# Converts text with markers into a narrated audio file with sound effects
#
# Markers:
#   [lacht] [laugh]    → laughter
#   [räusper] [cough]  → throat clear / cough
#   [seufz] [sigh]     → sigh
#   [ähm] [ehm] [um]   → hesitation
#   [atmen] [breath]   → breath
#   [pause 2]          → N seconds of silence
#
# Usage:
#   ./podcast.sh -f script.txt          generate podcast from file
#   ./podcast.sh -f script.txt -o out.wav   save to file
#   ./podcast.sh -f script.txt -l de        German (default: English)
#   ./podcast.sh "text with [lacht] markers"   one-liner

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOUNDS="$SCRIPT_DIR/sounds"
EN_VOICE="$HOME/.local/share/piper/en-us-lessac-medium.onnx"
DE_VOICE="$HOME/.local/share/piper/de_DE-thorsten-high.onnx"
MODEL="$EN_VOICE"
INPUT=""
INPUT_TEXT=""
OUTPUT=""
PLAY=true

# Marker → sound file mapping
declare -A MARKERS
MARKERS["lacht"]="laugh.wav"
MARKERS["laugh"]="laugh.wav"
MARKERS["räusper"]="throat_clear.wav"
MARKERS["cough"]="cough.wav"
MARKERS["hust"]="cough.wav"
MARKERS["seufz"]="sigh.wav"
MARKERS["sigh"]="sigh.wav"
MARKERS["ähm"]="um.wav"
MARKERS["ehm"]="um.wav"
MARKERS["um"]="um.wav"
MARKERS["atmen"]="breath.wav"
MARKERS["breath"]="breath.wav"

usage() {
  head -20 "$0" | grep -A 20 "^# 45dgof8 Podcast Generator"
  echo ""
  echo "Usage:"
  echo "  ./podcast.sh -f file.txt         generate podcast"
  echo "  ./podcast.sh -f file.txt -o out   save to WAV"
  echo "  ./podcast.sh -f file.txt -l de    German"
  echo "  ./podcast.sh -f file.txt --mp3    output MP3"
  echo "  echo \"text\" | ./podcast.sh       pipe"
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f) INPUT="$2"; shift 2 ;;
    -o) OUTPUT="$2"; PLAY=false; shift 2 ;;
    -l) [ "$2" = "de" ] && MODEL="$DE_VOICE"; shift 2 ;;
    --mp3) MP3=true; shift ;;
    -h) usage ;;
    *) INPUT_TEXT="$1"; shift ;;
  esac
done

WORKDIR=$(mktemp -d)
trap "rm -rf $WORKDIR" EXIT

# Read input
if [ -n "$INPUT" ]; then
  TEXT=$(cat "$INPUT")
elif [ -n "$INPUT_TEXT" ]; then
  TEXT="$INPUT_TEXT"
else
  TEXT=$(cat)
fi

echo "Parsing $(echo "$TEXT" | wc -c) characters..."

# Split into segments: text and markers
# Each line: either text content or [marker] or [pause N]
SEGMENTS=()
TEMP=""
while IFS= read -r -n1 ch; do
  if [[ "$ch" == "[" ]]; then
    if [ -n "$TEMP" ]; then
      SEGMENTS+=("text:$TEMP")
      TEMP=""
    fi
    TEMP="$ch"
  elif [[ "$ch" == "]" ]]; then
    TEMP="$TEMP]"
    MARKER="${TEMP:1:${#TEMP}-2}"
    # Check if it's a pause marker
    if [[ "$MARKER" =~ ^pause[[:space:]]([0-9]+(\\.[0-9]+)?)$ ]]; then
      DUR="${BASH_REMATCH[1]}"
      SEGMENTS+=("pause:$DUR")
    elif [[ "$MARKER" =~ ^[0-9]+(\\.[0-9]+)?$ ]]; then
      SEGMENTS+=("pause:$MARKER")
    elif [ -n "${MARKERS[$MARKER]}" ]; then
      SEGMENTS+=("sound:${MARKERS[$MARKER]}")
    else
      TEMP=" $TEMP "
      SEGMENTS+=("text:$TEMP")
    fi
    TEMP=""
  else
    TEMP="$TEMP$ch"
  fi
done < <(printf '%s' "$TEXT")
if [ -n "$TEMP" ]; then
  SEGMENTS+=("text:$TEMP")
fi

echo "Processing ${#SEGMENTS[@]} segments..."

IDX=0
CONCAT="$WORKDIR/concat.txt"
for seg in "${SEGMENTS[@]}"; do
  TYPE="${seg%%:*}"
  VAL="${seg#*:}"
  OFILE="$WORKDIR/seg_$(printf '%04d' $IDX).wav"

  case "$TYPE" in
    text)
      if [ -z "$(echo "$VAL" | tr -d '[:space:]')" ]; then
        IDX=$((IDX+1))
        continue
      fi
      echo "$VAL" | piper --model "$MODEL" --output-file "$OFILE" 2>/dev/null
      if [ -f "$OFILE" ] && [ -s "$OFILE" ]; then
        echo "file '$OFILE'" >> "$CONCAT"
      fi
      ;;
    sound)
      SFX="$SOUNDS/$VAL"
      if [ -f "$SFX" ]; then
        cp "$SFX" "$OFILE"
        echo "file '$OFILE'" >> "$CONCAT"
      fi
      ;;
    pause)
      ffmpeg -y -f lavfi -i "anullsrc=r=22050:cl=mono" -t "$VAL" "$OFILE" 2>/dev/null
      echo "file '$OFILE'" >> "$CONCAT"
      ;;
  esac
  IDX=$((IDX+1))
done

if [ ! -f "$CONCAT" ]; then
  echo "ERROR: No audio generated"
  exit 1
fi

RESULT="$WORKDIR/podcast-final.wav"
ffmpeg -y -f concat -safe 0 -i "$CONCAT" "$RESULT" 2>/dev/null

if [ ! -f "$RESULT" ]; then
  echo "ERROR: Concatenation failed"
  exit 1
fi

if [ "$MP3" = true ]; then
  ffmpeg -y -i "$RESULT" -codec:a libmp3lame -qscale:a 2 "${OUTPUT:-podcast.mp3}" 2>/dev/null
  echo "Output: ${OUTPUT:-podcast.mp3} ($(du -h "${OUTPUT:-podcast.mp3}" | awk '{print $1}'))"
elif [ -n "$OUTPUT" ]; then
  cp "$RESULT" "$OUTPUT"
  echo "Output: $OUTPUT ($(du -h "$OUTPUT" | awk '{print $1}'))"
elif [ "$PLAY" = true ]; then
  aplay -q "$RESULT"
  echo "Played. ($(du -h "$RESULT" | awk '{print $1}'))"
fi
