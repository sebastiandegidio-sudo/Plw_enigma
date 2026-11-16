"""Rechnet aus der Statistik-Tabelle (als .xlsx aus Google Drive geladen) alle Zahlen fürs Video
und schreibt sie nach data.js.

Aufruf: python3 daten.py [--bis JJJJ-MM] [--stand TT.MM.JJJJ] [--xlsx daten/statistik.xlsx]
Ohne --bis gilt der Vormonat von heute.

Regeln (Vorgaben von Sebastian, 16.11.2026):
- Sperrmüll zählt als Baumischabfall.
- Alle Schätzungen (ZAK-Fahrten x 1,2 t, Baustellen mit Hubert Schmid, Zuschlag) zählen als Baumischabfall
  und sind in der Gesamtmenge enthalten, ohne eigene Szene.
- Schießler und Altreifen werden eigens ausgewiesen.
"""
import argparse, collections, datetime, json, re
import openpyxl

MON = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
MONL = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
SORTENREIN = ['Altholz A I–III', 'Metall / Schrott', 'Bauschutt / mineralisch', 'Elektro- / Kühlgeräte', 'Papier / Pappe', 'Glas', 'Gips', 'Altreifen']
GEFAEHRLICH = ['Asbest / Dämmstoffe (gefährlich)', 'Altholz A IV']

ap = argparse.ArgumentParser()
today = datetime.date.today()
prev = (today.replace(day=1) - datetime.timedelta(days=1))
ap.add_argument('--bis', default=prev.strftime('%Y-%m'))
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


def rows(ws):
    it = ws.iter_rows(values_only=True)
    head = [str(h or '').strip() for h in next(it)]
    out = []
    for r in it:
        if r[0] is None:
            continue
        out.append({h: (v if v is not None else '') for h, v in zip(head, r)})
    return out


def monat(r):
    m = r.get('Monat') or ''
    if not m:
        d = r['Datum']
        m = d.strftime('%Y-%m') if hasattr(d, 'strftime') else f'{str(d)[6:10]}-{str(d)[3:5]}'
    return str(m)[:7]


wb = openpyxl.load_workbook(a.xlsx, data_only=True)
ent = [r for r in rows(wb['Einzelposten Entsorgung']) if monat(r) <= BIS]
tank = [r for r in rows(wb['Einzelbelege Tanken']) if monat(r) <= BIS]
zak = [r for r in rows(wb['ZAK Belege']) if monat(r) <= BIS]
cont = [r for r in rows(wb['Container Einsätze'])]
cont = [r for r in cont if (r['Datum'].strftime('%Y-%m') if hasattr(r['Datum'], 'strftime') else f"{str(r['Datum'])[6:10]}-{str(r['Datum'])[3:5]}") <= BIS]

# Monatsachse
allm = sorted({monat(r) for r in ent + tank})
y, m = map(int, allm[0].split('-'))
months = []
while f'{y}-{m:02d}' <= BIS:
    months.append(f'{y}-{m:02d}')
    m += 1
    if m > 12:
        y, m = y + 1, 1

# ---------- Entsorgung ----------
def tons(r):
    e = str(r['Einheit']).strip()
    return num(r['Menge']) if e == 't' else num(r['Menge']) / 1000 if e == 'kg' else 0.0

frak = collections.defaultdict(float); byent = collections.defaultdict(float)
bym = collections.defaultdict(float); byyear = collections.defaultdict(float)
for r in ent:
    t = tons(r)
    frak[r['Hauptgruppe']] += t; byent[r['Entsorger']] += t; bym[monat(r)] += t; byyear[monat(r)[:4]] += t
belegt = sum(frak.values())

# Schätzungen: ZAK aus den Kassenbelegen, Rest aus dem Blatt „Schätzungen“
TZ = stamm['tonnen_je_zak_fahrt']
zak_t = len(zak) * TZ
est = []
for r in wb['Schätzungen'].iter_rows(min_row=3, values_only=True):
    if not r[0] or str(r[0]).startswith('Summe'):
        break
    if str(r[0]).startswith('ZAK'):
        continue
    est.append((str(r[0]), num(r[3]), str(r[4] or '')))
est_t = sum(t for _, t, _ in est)
geschaetzt = zak_t + est_t
total = belegt + geschaetzt
ohne_datum = 0.0
for r in zak:
    bym[monat(r)] += TZ; byyear[monat(r)[:4]] += TZ
for name, t, zr in est:
    mm = re.fullmatch(r'\s*(\d\d)\.(\d{4})\s*', zr)
    yy = re.search(r'(20\d\d)', zr)
    if mm and f'{mm.group(2)}-{mm.group(1)}' in months:
        bym[f'{mm.group(2)}-{mm.group(1)}'] += t
    if yy:
        byyear[yy.group(1)] += t
    else:
        ohne_datum += t

baumisch = frak.get('Baumischabfall', 0) + frak.get('Sperrmüll / Siedlungsabfall', 0) + geschaetzt
named = [('Baumischabfall', baumisch)] + [(k.replace(' (gefährlich)', ''), frak.get(k, 0)) for k in
         ['Altholz A I–III', 'Metall / Schrott', 'Bauschutt / mineralisch', 'Asbest / Dämmstoffe (gefährlich)', 'Altreifen']]
named.sort(key=lambda x: -x[1])
rest = total - sum(v for _, v in named)
fr = named + [('Übrige Fraktionen', rest)]
pct = lambda v, tot: '<1' if 0 < v / tot < 0.005 else str(round(v / tot * 100))

ents = dict(byent); ents['ZAK Kempten'] = zak_t
top = sorted(ents.items(), key=lambda x: -x[1])[:6]
weitere = sum(ents.values()) - sum(v for _, v in top)
entsorger = [{'n': k, 't': round(v, 1), 'sub': f'{len(zak)} Fahrten × {str(TZ).replace(".", ",")} t' if k == 'ZAK Kempten' else ''} for k, v in top]
entsorger.append({'n': 'Weitere', 't': round(weitere, 1), 'sub': ''})

# Schießler
sch = [r for r in ent if 'Schie' in str(r['Entsorger'])]
sg = collections.defaultdict(float); smat = collections.defaultdict(float); stk = 0
for r in sch:
    sg[r['Hauptgruppe']] += tons(r); smat[r['Fraktion (Bezeichnung auf dem Beleg)']] += tons(r)
    if str(r['Einheit']).strip() == 'Stück' and r['Hauptgruppe'] == 'Altreifen':
        stk += int(num(r['Menge']))
schiessler = {
    't': round(sum(sg.values()), 1),
    'anlieferungen': len({r['Lieferschein-Nr.'] for r in sch if r['Lieferschein-Nr.']}),
    'metall': round(sg.get('Metall / Schrott', 0), 1), 'elektro': round(sg.get('Elektro- / Kühlgeräte', 0), 1),
    'reifen': round(sg.get('Altreifen', 0), 1), 'reifen_stk': stk,
    'top': [[k, round(v, 1)] for k, v in sorted(smat.items(), key=lambda x: -x[1])[:5]],
}

# Container, Trennquote
cv = collections.Counter(str(r['Vorgang']).strip() for r in cont)
container = {'gestellt': cv['stellen'], 'getauscht': cv['tauschen'], 'abgeholt': cv['abholen']}
container['einsaetze'] = sum(container.values()); container['gefuellt'] = container['gestellt'] + container['getauscht']
sr = sum(frak.get(k, 0) for k in SORTENREIN); gf = sum(frak.get(k, 0) for k in GEFAEHRLICH); gm = belegt - sr - gf
trenn = {'sortenrein': round(sr, 1), 'gemischt': round(gm, 1), 'gefaehrlich': round(gf, 1),
         'p_sortenrein': round(sr / belegt * 100), 'p_gemischt': round(gm / belegt * 100)}

# ---------- Tanken ----------
lm = collections.defaultdict(float); fuel = collections.defaultdict(float); card = collections.defaultdict(float); stn = collections.defaultdict(float)
for r in tank:
    l = num(r['Liter']); lm[monat(r)] += l; fuel[r['Kraftstoff']] += l
    c = r['Fahrzeug / Karte']
    if r['Kraftstoff'] != 'AdBlue':  # Karten wie in der Tabelle: Diesel + Benzin, ohne AdBlue
        card['Einzelbelege ohne Karte' if c == 'ohne Fahrzeugangabe' else c] += l
    stn[r['Tankstelle']] += l
ltot = sum(lm.values())
cards = sorted(card.items(), key=lambda x: -x[1])
if len(cards) > 8:
    cards = cards[:7] + [('Weitere Karten', sum(v for _, v in cards[7:]))]
st = sorted(((k, v) for k, v in stn.items() if k != 'unbekannt'), key=lambda x: -x[1])
st6 = st[:6]
stations = [{'n': k, 'l': round(v), 'p': pct(v, ltot)} for k, v in st6]
r_ = ltot - sum(v for _, v in st6)
stations.append({'n': 'Alle anderen', 'l': round(r_), 'p': pct(r_, ltot)})

# ---------- Fuhrpark ----------
fz = []
for r in wb['Fahrzeuge'].iter_rows(min_row=3, values_only=True):
    if r[0]:
        seit = r[3].strftime('%m.%Y') if hasattr(r[3], 'strftime') else str(r[3]).strip()
        fz.append({'kz': str(r[0]).strip(), 'name': str(r[1]).strip(), 'seit': seit})
for z in stamm.get('fahrzeuge_zusatz', []):
    if z['kz'] not in [f['kz'] for f in fz]:
        fz.append(dict(z))
for f in fz:
    f.update(stamm.get('fahrzeuge_korrektur', {}).get(f['kz'], {}))
def key(f):
    s = f['seit']
    return (s[3:] + '-' + s[:2]) if '.' in s else s + '-00'
fz = sorted([f for f in fz if key(f)[:7] <= BIS], key=key)

lab = lambda ym: MON[int(ym[5:]) - 1]
labl = lambda ym: f'{MONL[int(ym[5:]) - 1]} {ym[:4]}'
tm = [round(bym.get(k, 0), 1) for k in months]; lmv = [round(lm.get(k, 0), 1) for k in months]
ip = max(range(len(months)), key=lambda i: tm[i]); il = max(range(len(months)), key=lambda i: lmv[i])
years = sorted(byyear)
D = {
    'von': labl(months[0]), 'bis': labl(months[-1]), 'stand': a.stand,
    'total': round(total, 1), 'belegt': round(belegt, 1), 'geschaetzt': round(geschaetzt, 1),
    'jahre': [{'l': (f'{y} (ab {MONL[int(months[0][5:]) - 1]})' if y == months[0][:4] else f'{y} (bis {MONL[int(months[-1][5:]) - 1]})' if y == months[-1][:4] else y), 't': round(byyear[y], 1)} for y in years],
    'ohne_datum': round(ohne_datum, 1),
    'mon': [lab(k) for k in months], 'jahr_idx': [[i, k[:4]] for i, k in enumerate(months) if i == 0 or k[5:] == '01'],
    'tons': tm, 'tons_peak': ip, 'tons_peak_label': f'{lab(months[ip])} {months[ip][:4]}',
    'liter_m': lmv, 'liter_peak': il, 'liter_peak_label': f'{lab(months[il])} {months[il][:4]}',
    'frak': [{'n': k, 't': round(v, 1), 'p': pct(v, total)} for k, v in fr],
    'ents': entsorger, 'schiessler': schiessler, 'container': container, 'trenn': trenn,
    'liter': round(ltot), 'diesel': round(fuel.get('Diesel', 0)), 'benzin': round(fuel.get('Benzin', 0)), 'adblue': round(fuel.get('AdBlue', 0)),
    'karten': [{'n': k, 'l': round(v), 'p': pct(v, ltot)} for k, v in cards],
    'tankstellen': stations, 'fuhrpark': fz,
}
open('data.js', 'w', encoding='utf-8').write('// Automatisch erzeugt von daten.py – nicht von Hand ändern.\nconst D = ' + json.dumps(D, ensure_ascii=False, indent=1) + ';\n')
print(json.dumps(D, ensure_ascii=False))
