#!/bin/bash
# Baut alles neu: Zahlen aus daten/statistik.xlsx, Bilder rendern, Musik erzeugen, zusammenfügen.
# Aufruf: ./build.sh [JJJJ-MM]   (letzter Monat, der gezeigt wird; ohne Angabe der Vormonat)
set -e
cd "$(dirname "$0")"
python3 daten.py ${1:+--bis $1} > /dev/null
python3 music.py .music.wav
for f in land port; do
  node render.js $f .video_$f.mp4
  name=$([ $f = land ] && echo Querformat || echo Hochformat)
  ffmpeg -v error -y -i .video_$f.mp4 -i .music.wav -c:v copy -af volume=-4dB -c:a aac -b:a 192k -movflags +faststart -shortest "Platzwerk_Statistik_$name.mp4"
  rm .video_$f.mp4
done
rm .music.wav
# Kleine Fassung für den E-Mail-Anhang (720p, rund 13 MB)
for p in 1 2; do
  ffmpeg -v error -y -i Platzwerk_Statistik_Querformat.mp4 -vf "hqdn3d=3:3:6:6,scale=1280:720" -c:v libx264 -preset slow -b:v 600k -pass $p -passlogfile .pass \
    $([ $p = 1 ] && echo "-an -f null /dev/null" || echo "-c:a aac -b:a 96k -movflags +faststart Platzwerk_Statistik_Mail.mp4")
done
rm -f .pass*
ls -la *.mp4
