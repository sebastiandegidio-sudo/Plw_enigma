#!/bin/bash
# Baut beide Videos komplett neu: Bilder rendern, Musik erzeugen, zusammenfügen.
set -e
cd "$(dirname "$0")"
python3 music.py .music.wav
for f in land port; do
  node render.js $f .video_$f.mp4
  name=$([ $f = land ] && echo Querformat || echo Hochformat)
  ffmpeg -v error -y -i .video_$f.mp4 -i .music.wav -c:v copy -af volume=-4dB -c:a aac -b:a 192k -movflags +faststart -shortest "Platzwerk_Statistik_$name.mp4"
  rm .video_$f.mp4
done
rm .music.wav
