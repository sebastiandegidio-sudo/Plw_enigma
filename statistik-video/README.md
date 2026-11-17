# Platzwerk Statistik-Video

Animiertes Statistik-Video in Glasoptik, gebaut aus der Google-Tabelle „Statistik Entsorgung & Tanken (automatisch)“.

- `Platzwerk_Statistik_Querformat.mp4`: 1920×1080, für den Fernseher im Lager
- `Platzwerk_Statistik_Hochformat.mp4`: 1080×1920, fürs Handy
- `Platzwerk_Statistik_Mail.mp4`: kleine Fassung für den E-Mail-Anhang

Neu bauen: Tabelle als `daten/statistik.xlsx` ablegen, dann `./build.sh`. Braucht Node mit Playwright, ffmpeg, Python mit numpy, scipy und openpyxl.

- `daten.py` rechnet alle Zahlen aus der Tabelle und schreibt `data.js`; feste Vorgaben stehen in `stammdaten.json`.
- `index.html` ist die Animation (Vorschau im Browser, Hochformat mit `?fmt=port`).
- `music.py` erzeugt die Musik, `render.js` die Bilder, `shot.js` Kontrollbilder.
- `MONATSLAUF.md` beschreibt den monatlichen Versand.
