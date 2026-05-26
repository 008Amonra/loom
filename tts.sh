#!/bin/bash
# 45dgof8 TTS - speak text or read files aloud
# Usage:
#   ./tts.sh "text"              speak English through speakers
#   ./tts.sh -l de "text"        speak German
#   ./tts.sh -f file.txt         read a file
#   ./tts.sh -o out.wav "text"   save to file
#   echo "text" | ./tts.sh       pipe mode

EN_VOICE="$HOME/.local/share/piper/en-us-lessac-medium.onnx"
DE_VOICE="$HOME/.local/share/piper/de_DE-thorsten-high.onnx"
MODEL="$EN_VOICE"
PLAY=true
OUTPUT=""
INPUT=""

while getopts "l:f:o:h" opt; do
  case $opt in
    l) [ "$OPTARG" = "de" ] && MODEL="$DE_VOICE";;
    f) INPUT="-i $OPTARG";;
    o) OUTPUT="$OPTARG"; PLAY=false;;
    h) echo "tts.sh [options] \"text\"
  -l de    German (default: English)
  -f file  read file
  -o file  save to WAV
  -h       help"; exit 0;;
    *) exit 1;;
  esac
done
shift $((OPTIND-1))

if [ -n "$OUTPUT" ]; then
  if [ -n "$INPUT" ]; then
    piper --model "$MODEL" $INPUT --output-file "$OUTPUT"
  else
    echo "$1" | piper --model "$MODEL" --output-file "$OUTPUT"
  fi
  echo "Saved: $OUTPUT ($(du -h "$OUTPUT" | awk '{print $1}'))"
elif [ -n "$INPUT" ]; then
  piper --model "$MODEL" $INPUT --output-raw | aplay -r 22050 -f S16_LE -c 1 -q && echo "Done."
elif [ $# -ge 1 ]; then
  echo "$1" | piper --model "$MODEL" --output-raw | aplay -r 22050 -f S16_LE -c 1 -q && echo "Done."
else
  piper --model "$MODEL" --output-raw | aplay -r 22050 -f S16_LE -c 1 -q
fi
