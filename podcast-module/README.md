# 45dgof8 Podcast Studio

Turn text into narrated audio with natural-sounding pauses, laughter, sighing,
and breath — like a real podcast.

## Markers

Put these in your text and we splice them in:

| Marker | Effect |
|--------|--------|
| `[lacht]` | Laughter |
| `[räusper]` | Throat clear |
| `[seufz]` | Sigh |
| `[ähm]` | Hesitation |
| `[atmen]` | Breath |
| `[pause 2]` | 2 seconds silence |
| `[laugh]` | English alias |
| `[cough]` | English alias |
| `[sigh]` | English alias |
| `[um]` | English alias |
| `[breath]` | English alias |

## Usage

### Generate from file
```
./podcast.sh -f script.txt
./podcast.sh -f script.txt -o output.wav
./podcast.sh -f script.txt -l de -o podcast.wav   # German
./podcast.sh -f script.txt --mp3                   # MP3 output
```

### One-liner
```
./podcast.sh "Welcome to our show [lacht] today we talk about..."
```

### Pipe
```
cat script.txt | ./podcast.sh
```

## Recording your own sounds

Place your own WAV files in `sounds/` to replace the placeholders:

```
sounds/laugh.wav          # [lacht]
sounds/throat_clear.wav   # [räusper]
sounds/sigh.wav           # [seufz]
sounds/um.wav             # [ähm]
sounds/breath.wav         # [atmen]
sounds/cough.wav          # [cough]
```

Keep them short (0.3–1.5 seconds). Mono, 22050 Hz WAV works best.

## Example

```
[pause 1]
Willkommen zu unserem Podcast.
[atmen]
Heute reden wir über KI Agenten.
[räusper]
[lacht]
Keine Sorge, bleibt verständlich.
[pause 0.5]
Viel Spass beim Zuhören.
```

Generates: `examples/example-podcast.wav`

## Requirements

- Linux with `piper-tts` and `ffmpeg` installed
- ~200 MB for voice models (English + German)
- ~100 MB for sound library
