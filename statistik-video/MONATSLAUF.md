# Monatslauf: Statistik-Video am 15. jedes Monats

Auftrag von Sebastian (16./17.11.2026): Jeden Monat am 15. das Statistik-Video mit den aktuellen Zahlen neu bauen und per E-Mail an info@platzwerk-allgaeu.de schicken.

## Quelle

Einzige Quelle ist die Google-Tabelle „Statistik Entsorgung & Tanken (automatisch)“, ID `1rm8ArH8X78n7hfbN003ZyVGoSgp24oiz20KrszTYmB0`.

**Hier keine Belege eintragen.** Das macht die Aufgabe „Statistik Entsorgung & Tanken (montags)“ jeden Montag. Doppelte Einträge wären die Folge.

## Ablauf

1. Die Tabelle als `.xlsx` aus Drive herunterladen und als `statistik-video/daten/statistik.xlsx` speichern.
2. In `statistik-video/`: `pip install scipy openpyxl`, dann `./build.sh` (rund 30 Minuten, im Hintergrund). Ohne Angabe läuft das Video bis zum laufenden Monat, der als „läuft noch“ markiert ist.
3. Prüfen: `data.js` ansehen (Summen plausibel, mit der Tabelle „Übersicht“ vergleichen). Mit `OUT=<ordner> node shot.js land` ein Bild je Szene machen und ansehen; die Ausgabe nennt die kleinste Schrift je Szene.
4. Mail an info@platzwerk-allgaeu.de, Betreff „Platzwerk Statistik bis <Monat Jahr>“, Anhang `Platzwerk_Statistik_Mail.mp4` (rund 13 MB). Im Text kurz: Gesamtmenge, was seit dem letzten Lauf dazukam, Lücken laut Blatt „Hinweise“.
5. Änderungen committen und pushen.

## Feste Vorgaben

Stehen in `daten.py` und `stammdaten.json`:
- Blätter und Spalten werden über ihre Namen gesucht, nie über feste Positionen.
- Baumischabfall und Sperrmüll sind eine Gruppe.
- Schätzungen (ZAK-Fahrten × 1,2 t, Baustellen über Hubert Schmid, Zuschlag) zählen zu dieser Gruppe und zur Gesamtmenge; Hubert Schmid wird nicht genannt.
- Metalle im Detail, gruppiert nach Stichwort im Materialnamen (kabel, motor, kupfer, messing, v2a, alu, blei, zinn, sonst Eisen und Stahl).
- Fahrzeuge aus dem Blatt „Fahrzeuge“, mit Sebastians Korrekturen: KF-DE 100 VW Caddy (weiß) seit 2022, KF-DE 150 VW Caddy (rot) seit 09.2025.
- **Nie zeigen:** Preise, Aufträge und Besichtigungen, Tonnen pro Auftrag, Kilometerstände, Entkernungen, Audi SQ8 / KF-DE 12. `daten.py` bricht ab, wenn das gesperrte Kennzeichen in den Daten auftaucht.

## Lesbarkeit (Lager-Fernseher, 16:9)

- Im Querformat keine Zahl kleiner als etwa 40 px bei 1080p.
- Pro Jahr eine eigene Monatsgrafik, höchstens 12 Balken, Wert über jedem Balken, laufender Monat markiert.
- Höchstens 6 Zeilen je Liste.
