"""Rechnet aus der Statistik-Tabelle (als .xlsx aus Google Drive geladen) alle Zahlen fürs Video
und schreibt sie nach data.js. Die Tabelle ist die einzige Quelle; Blätter und Spalten werden
über ihre Namen gesucht, nicht über feste Positionen.

Aufruf: python3 daten.py [--bis JJJJ-MM] [--stand TT.MM.JJJJ] [--xlsx daten/statistik.xlsx]
Ohne --bis gilt der laufende Monat (er wird im Video als „läuft noch“ markiert).

Vorgaben von Sebastian (16./17.11.2026):
- Baumischabfall und Sperrmüll sind eine Gruppe („Baumischabfall / Sperrmüll“).
- Alle Schätzungen (ZAK-Fahrten x 1,2 t, Baustellen über Hubert Schmid, Zuschlag) zählen zu dieser Gruppe
  und zur Gesamtmenge; Hubert Schmid wird nicht eigens genannt.
- Metalle werden im Detail gezeigt, Schießler und Altreifen eigens.
- Nie zeigen: Preise, Audi SQ8 / KF-DE 12.
"""
import argparse, collections, datetime, json, re
import openpyxl

MON = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
MONL = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
MISCH = 'Baumischabfall / Sperrmüll'
MISCH_ALT = ['Baumischabfall', 'Sperrmüll / Siedlungsabfall', MISCH]
SORTENREIN = ['Altholz A I–III', 'Metall / Schrott', 'Bauschutt / mineralisch', 'Elektro- / Kühlgeräte', 'Papier / Pappe', 'Glas', 'Gips', 'Altreifen']
GEFAEHRLICH = ['Asbest / Dämmstoffe (gefährlich)', 'Altholz A IV']
# Metallgruppen nach Stichwort im Materialnamen, Reihenfolge zählt
METALL = [('kabel', 'Kupferkabel'), ('motor', 'E-Motoren'), ('kupfer', 'Kupfer blank'), ('messing', 'Messing'),
          ('v2a', 'Edelstahl V2A'), ('alu', 'Aluminium'), ('blei', 'Blei und Batterien'), ('zinn', 'Zinn')]

ap = argparse.ArgumentParser()
today = datetime.date.today()
ap.add_argument('--bis', default=today.strftime('%Y-%m'))
ap.add_argument('--stand', default=today.strftime('%d.%m.%Y'))
ap.add_argument('--xlsx', default='daten/statistik.xlsx')
a = ap.parse_args()
BIS = a.bis
stamm = json.load(open('stammdaten.json', encoding='utf-8'))


def num(v):
    if v is None or v == '':
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    return float(str(v).replace('.', '').replace(',', '.'))


def table(ws, key):
    """Zeilen eines Blatts als Wörterbücher; die Kopfzeile ist die erste Zeile, die `key` enthält."""
    head, out = None, []
    for r in ws.iter_rows(values_only=True):
        if head is None:
            if key in [str(c).strip() if c is not None else '' for c in r]:
                head = [str(c).strip() if c is not None else '' for c in r]
            continue
        if r[0] is None or str(r[0]).strip() == '':
            break
        out.append({h: (v if v is not None else '') for h, v in zip(head, r) if h})
    return out


def ym(d):
    if hasattr(d, 'strftime'):
        return d.strftime('%Y-%m')
    s = str(d)
    return f'{s[6:10]}-{s[3:5]}'


def zeit(v):
    """Zeitangabe aus der Tabelle -> ('2026-04' | None, '2026' | None)."""
    if hasattr(v, 'strftime'):
        return v.strftime('%Y-%m'), v.strftime('%Y')
    if isinstance(v, (int, float)):
        return None, str(int(v))
    s = str(v)
    m = re.fullmatch(r'\s*(\d\d)\.(\d{4})\s*', s)
    if m:
        return f'{m.group(2)}-{m.group(1)}', m.group(2)
    y = re.search(r'(20\d\d)', s)
    return None, (y.group(1) if y else None)


wb = openpyxl.load_workbook(a.xlsx, data_only=True)
ent = [r for r in table(wb['Einzelposten Entsorgung'], 'Hauptgruppe') if ym(r['Datum']) <= BIS]
tank = [r for r in table(wb['Einzelbelege Tanken'], 'Kraftstoff') if ym(r['Datum']) <= BIS]
zak = [r for r in table(wb['ZAK Belege'], 'Datum') if ym(r['Datum']) <= BIS]
cont = [r for r in table(wb['Container Einsätze'], 'Vorgang') if ym(r['Datum']) <= BIS]
for r in ent:
    if r['Hauptgruppe'] in MISCH_ALT:
        r['Hauptgruppe'] = MISCH

first = min(ym(r['Datum']) for r in ent + tank)
y, m = map(int, first.split('-'))
months = []
while f'{y}-{m:02d}' <= BIS:
    months.append(f'{y}-{m:02d}')
    m += 1
    if m > 12:
        y, m = y + 1, 1
laufend = BIS == datetime.datetime.strptime(a.stand, '%d.%m.%Y').strftime('%Y-%m')

# ---------- Entsorgung ----------
def tons(r):
    e = str(r['Einheit']).strip()
    return num(r['Menge']) if e == 't' else num(r['Menge']) / 1000 if e == 'kg' else 0.0

frak = collections.defaultdict(float); byent = collections.defaultdict(float)
bym = collections.defaultdict(float); byyear = collections.defaultdict(float)
for r in ent:
    t = tons(r)
    frak[r['Hauptgruppe']] += t; byent[r['Entsorger']] += t; bym[ym(r['Datum'])] += t; byyear[ym(r['Datum'])[:4]] += t
belegt = sum(frak.values())
belegt_jahr = dict(byyear)

TZ = stamm['tonnen_je_zak_fahrt']
zak_t = len(zak) * TZ
est = [(str(r['Posten']), num(r['Tonnen (geschätzt)']), r['Zeitraum']) for r in table(wb['Schätzungen'], 'Posten')
       if not str(r['Posten']).startswith(('ZAK', 'Summe'))]
geschaetzt = zak_t + sum(t for _, t, _ in est)
total = belegt + geschaetzt
ohne_datum = 0.0
for r in zak:
    byyear[ym(r['Datum'])[:4]] += TZ
for _, t, zr in est:
    _, yy = zeit(zr)
    if yy:
        byyear[yy] += t
    else:
        ohne_datum += t

pct = lambda v, tot: '<1' if 0 < v / tot < 0.005 else str(round(v / tot * 100))
named = [(MISCH, frak.get(MISCH, 0) + geschaetzt)] + sorted(
    [(k.replace(' (gefährlich)', ''), v) for k, v in frak.items() if k != MISCH], key=lambda x: -x[1])[:4]
fr = named + [('Übrige Fraktionen', total - sum(v for _, v in named))]

ents = dict(byent); ents['ZAK Kempten'] = zak_t
top = sorted(ents.items(), key=lambda x: -x[1])[:6]
kurz = lambda n: re.sub(r'\s*\(.*\)', '', n)
entsorger = [{'n': kurz(k), 't': round(v, 1), 'sub': f'{len(zak)} Fahrten, geschätzt' if k == 'ZAK Kempten' else ''} for k, v in top]
entsorger.append({'n': 'Weitere', 't': round(sum(ents.values()) - sum(v for _, v in top), 1), 'sub': ''})

sch = [r for r in ent if 'Schie' in str(r['Entsorger'])]
sg = collections.defaultdict(float); stk = 0
for r in sch:
    sg[r['Hauptgruppe']] += tons(r)
    if str(r['Einheit']).strip() == 'Stück' and r['Hauptgruppe'] == 'Altreifen':
        stk += int(num(r['Menge']))
schiessler = {'t': round(sum(sg.values()), 1), 'wiegescheine': len({r['Lieferschein-Nr.'] for r in sch if r['Lieferschein-Nr.']}),
              'elektro': round(sg.get('Elektro- / Kühlgeräte', 0), 1), 'reifen': round(sg.get('Altreifen', 0), 1), 'reifen_stk': stk}

# Metalle im Detail (alle Händler)
mg = collections.defaultdict(float)
for r in ent:
    if r['Hauptgruppe'] == 'Metall / Schrott' and tons(r):
        name = str(r['Fraktion (Bezeichnung auf dem Beleg)']).lower()
        mg[next((g for k, g in METALL if k in name), 'Eisen- und Stahlschrott')] += tons(r)
eisen = mg.pop('Eisen- und Stahlschrott', 0.0)
bunt = sorted(mg.items(), key=lambda x: -x[1])
rows_m = bunt[:5]
if len(bunt) > 5:
    rest = bunt[5:]
    rows_m.append((' und '.join(n for n, _ in rest) if len(rest) <= 2 else 'Weitere Buntmetalle', sum(v for _, v in rest)))
metalle = {'t': round(eisen + sum(mg.values()), 1), 'eisen_t': round(eisen, 1), 'bunt_kg': round(sum(mg.values()) * 1000),
           'rows': [{'n': n, 'kg': round(v * 1000)} for n, v in rows_m]}

cv = collections.Counter(str(r['Vorgang']).strip() for r in cont)
container = {'gestellt': cv['stellen'], 'getauscht': cv['tauschen'], 'abgeholt': cv['abholen']}
container['einsaetze'] = sum(container.values()); container['gefuellt'] = container['gestellt'] + container['getauscht']
sr = sum(frak.get(k, 0) for k in SORTENREIN); gf = sum(frak.get(k, 0) for k in GEFAEHRLICH); gm = belegt - sr - gf
trenn = {'sortenrein': round(sr, 1), 'gemischt': round(gm, 1), 'gefaehrlich': round(gf, 1),
         'p_sortenrein': round(sr / belegt * 100), 'p_gemischt': round(gm / belegt * 100), 'p_gefaehrlich': round(gf / belegt * 100)}

# ---------- Tanken ----------
lm = collections.defaultdict(float); fuel = collections.defaultdict(float); card = collections.defaultdict(float); stn = collections.defaultdict(float)
for r in tank:
    l = num(r['Liter']); lm[ym(r['Datum'])] += l; fuel[r['Kraftstoff']] += l
    c = r['Fahrzeug / Karte']
    if r['Kraftstoff'] != 'AdBlue':  # Karten wie in der Tabelle: Diesel + Benzin, ohne AdBlue
        card['Einzelbelege ohne Karte' if c == 'ohne Fahrzeugangabe' else c] += l
    stn[r['Tankstelle']] += l
ltot = sum(lm.values())
cards = sorted(card.items(), key=lambda x: -x[1])
if len(cards) > 8:
    cards = cards[:7] + [('Weitere Karten', sum(v for _, v in cards[7:]))]
st5 = sorted(((k, v) for k, v in stn.items() if k != 'unbekannt'), key=lambda x: -x[1])[:5]
stations = [{'n': k, 'l': round(v), 'p': pct(v, ltot)} for k, v in st5]
r_ = ltot - sum(v for _, v in st5)
stations.append({'n': 'Alle anderen', 'l': round(r_), 'p': pct(r_, ltot)})

# ---------- Fuhrpark ----------
fz = []
for r in table(wb['Fahrzeuge'], 'Kennzeichen'):
    mo, yy = zeit(r['Bei Platzwerk seit'])
    fz.append({'kz': str(r['Kennzeichen']).strip(), 'name': str(r['Fahrzeug']).strip(), 'seit': f'{mo[5:]}.{mo[:4]}' if mo else yy})
for f in fz:
    f.update(stamm.get('fahrzeuge_korrektur', {}).get(f['kz'], {}))
key = lambda f: (f['seit'][3:] + '-' + f['seit'][:2]) if '.' in f['seit'] else f['seit'] + '-00'
verboten = re.compile('|'.join(re.escape(v.lower()) + r'(?!\d)' for v in stamm.get('nie_zeigen', [])) or r'$^')
fz = sorted([f for f in fz if key(f)[:7] <= BIS and not verboten.search((f['kz'] + ' ' + f['name']).lower())], key=key)
for f in fz:
    f['neu'] = laufend and key(f)[:7] == BIS

# ---------- Ausgabe ----------
labl = lambda k: f'{MONL[int(k[5:]) - 1]} {k[:4]}'
jahre_detail = []
for yr in sorted({k[:4] for k in months}):
    ms = [k for k in months if k[:4] == yr]
    jahre_detail.append({'jahr': yr, 'mon': [MON[int(k[5:]) - 1] for k in ms],
                         't': [round(bym.get(k, 0), 1) for k in ms], 'l': [round(lm.get(k, 0)) for k in ms],
                         't_sum': round(sum(bym.get(k, 0) for k in ms), 1), 'l_sum': round(sum(lm.get(k, 0) for k in ms)),
                         'laufend': len(ms) - 1 if (laufend and ms[-1] == BIS) else -1})
years = sorted(byyear)
D = {
    'von': labl(months[0]), 'bis': labl(months[-1]), 'stand': a.stand, 'laufend': laufend,
    'total': round(total, 1), 'belegt': round(belegt, 1), 'geschaetzt': round(geschaetzt, 1),
    'jahre': [{'l': y, 't': round(byyear[y], 1)} for y in years], 'ohne_datum': round(ohne_datum, 1),
    'jd': jahre_detail,
    'frak': [{'n': k, 't': round(v, 1), 'p': pct(v, total)} for k, v in fr],
    'ents': entsorger, 'schiessler': schiessler, 'metalle': metalle, 'container': container, 'trenn': trenn,
    'liter': round(ltot), 'diesel': round(fuel.get('Diesel', 0)), 'benzin': round(fuel.get('Benzin', 0)), 'adblue': round(fuel.get('AdBlue', 0)),
    'karten': [{'n': k, 'l': round(v), 'p': pct(v, ltot)} for k, v in cards],
    'tankstellen': stations, 'fuhrpark': fz,
}
text = json.dumps(D, ensure_ascii=False, indent=1)
assert not verboten.search(text.lower()), 'Gesperrter Begriff in den Daten'
open('data.js', 'w', encoding='utf-8').write('// Automatisch erzeugt von daten.py – nicht von Hand ändern.\nconst D = ' + text + ';\n')
print(json.dumps(D, ensure_ascii=False))
