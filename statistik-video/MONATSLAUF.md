# Monatslauf: Statistik-Video am 15. jedes Monats

Auftrag von Sebastian (16.11.2026): Jeden Monat am 15. das Statistik-Video mit den Zahlen bis einschließlich Vormonat neu bauen und per E-Mail an info@platzwerk-allgaeu.de schicken.

## Ablauf

1. **Neue Belege in die Tabelle eintragen.**
   Tabelle: „Statistik Entsorgung & Tanken (automatisch)“, Google-Sheets-ID `1rm8ArH8X78n7hfbN003ZyVGoSgp24oiz20KrszTYmB0`.
   Belege: Google Drive → „Platzwerk Allgäu - FIRMA“ → „02 Buchhaltung & Steuern“ → Jahr → Monatsordner (2025: `1qjfRBlF7L7MR6vOjdo7-VSpd22y9cRkc`, 2026: `1rDlacr5tRSmg-FPVcfgK8liDYOwgrZdT`), dazu „00 Eingang Scans“.
   - Rechnungen, Gutschriften und Wiegescheine der Entsorger (Höbel, Settele, Knettenbrech, Schießler, Geiger und weitere) lesen, die seit dem letzten Lauf dazugekommen sind. Jede Position, die noch nicht im Blatt „Einzelposten Entsorgung“ steht (Abgleich über Beleg-Nr. und Lieferschein-Nr.), als neue Zeile anhängen. Spalten und Schreibweise wie die vorhandenen Zeilen; Datum ist der Tag der Anlieferung, nicht das Rechnungsdatum.
   - Tankbelege (Radius-Rechnungen, Kassenbelege) genauso ins Blatt „Einzelbelege Tanken“, ZAK-Kassenbelege ins Blatt „ZAK Belege“, Container-Bewegungen ins Blatt „Container Einsätze“.
   - Die Regeln im Blatt „Hinweise“ gelten weiter (nur gewogene Mengen als Tonnen, nichts doppelt zählen).
   - Nichts löschen, nichts verschieben, nichts freigeben. Unlesbare Belege nicht raten, sondern in der Mail nennen.
2. **Tabelle laden.** Die Tabelle als `.xlsx` aus Drive herunterladen und als `statistik-video/daten/statistik.xlsx` speichern.
3. **Video bauen.** In `statistik-video/`: `./build.sh` (nimmt automatisch den Vormonat als letzten Monat). Dauert rund 25 Minuten. Braucht `pip install scipy openpyxl`.
4. **Prüfen.** `data.js` ansehen: Summen plausibel, Zeitraum endet mit dem Vormonat. Mit `node shot.js land 20 46.5 73` drei Kontrollbilder machen und ansehen.
5. **Mail senden** an info@platzwerk-allgaeu.de, Betreff „Platzwerk Statistik bis <Monat Jahr>“, Anhang `Platzwerk_Statistik_Mail.mp4` (rund 13 MB). Im Text kurz: Gesamtmenge, was im Vormonat dazukam, fehlende oder unlesbare Belege. Quer- und Hochformat in voller Qualität liegen im Repository.
6. **Sichern.** Änderungen committen und auf den Arbeitszweig pushen.

## Feste Vorgaben für die Zahlen

Stehen in `daten.py` und `stammdaten.json`:
- Sperrmüll zählt als Baumischabfall.
- Schätzungen (ZAK-Fahrten × 1,2 t, Baustellen mit Hubert Schmid, Zuschlag) zählen als Baumischabfall und sind in der Gesamtmenge enthalten; Hubert Schmid wird nicht eigens genannt.
- Schießler und Altreifen werden eigens gezeigt.
- Fahrzeuge: KF-DE 100 VW Caddy (weiß) seit 2022, KF-DE 150 VW Caddy (rot) seit 09.2025. Neue Fahrzeuge kommen aus dem Blatt „Fahrzeuge“ dazu, sobald ihr Monat erreicht ist.
