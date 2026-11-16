"""Erzeugt die Musik-Unterlage (selbst synthetisiert, keine fremden Samples).
Aufruf: python3 music.py ausgabe.wav
100 BPM, 64 Takte = 153,6 s, Szenenwechsel liegen genau auf Taktgrenzen."""
import sys
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
BEAT = 0.6
BAR = 4 * BEAT
BARS = 64
N = int(SR * BARS * BAR)
rng = np.random.default_rng(7)
SCENES = [4, 5, 5, 6, 5, 6, 6, 5, 5, 5, 6, 6]
STARTS = np.cumsum([0] + SCENES[:-1])  # in Takten

# Akkorde je Takt (Am – F – C – G): (Bass, Flächen-Töne) als MIDI-Noten
CH = [(45, [57, 60, 64, 71]), (41, [57, 60, 65, 69]), (36, [55, 60, 64, 67, 74]), (43, [55, 59, 62, 69])]
f = lambda m: 440.0 * 2 ** ((m - 69) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x, axis=0)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x, axis=0)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)


def add(buf, sig, t0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    e[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return e


pad = np.zeros((N, 2)); arp = np.zeros((N, 2)); bass = np.zeros(N); kick = np.zeros(N)
hat = np.zeros((N, 2)); clap = np.zeros(N); fx = np.zeros((N, 2)); kenv = np.zeros(N)

# ---------- Flächen ----------
for b in range(BARS):
    _, notes = CH[b % 4]
    dur = BAR + 1.4
    n = int(dur * SR); t = np.arange(n) / SR
    e = env(n, 0.9, 1.4)
    lvl = 0.7 if b < 4 else (1.25 if b >= 58 else 1.0)
    for m in notes + ([notes[0] - 12] if b >= 4 else []):
        for ch, det in ((0, -0.06), (1, 0.06), (0, 0.11), (1, -0.11)):
            fr = f(m + det)
            s = sum(np.sin(2 * np.pi * fr * k * t + rng.uniform(0, 6.28)) / k ** 1.6 for k in range(1, 8))
            tmp = np.zeros(N); add(tmp, s * e * 0.03 * lvl, b * BAR - 0.45 if b else 0)
            pad[:, ch] += tmp
pad = lp(pad, 2200)

# ---------- Arpeggio ----------
PAT = [0, 2, 1, 3, 2, 3, 1, 2]
for b in range(4, BARS):
    _, notes = CH[b % 4]
    hi = 24 if b >= 58 else 12
    lvl = 0.55 if b < 9 else 1.0
    for i in range(8):
        m = notes[PAT[i] % len(notes)] + hi
        n = int(0.9 * SR); t = np.arange(n) / SR
        s = (np.sin(2 * np.pi * f(m) * t) + 0.35 * np.sin(4 * np.pi * f(m) * t) + 0.12 * np.sin(6 * np.pi * f(m) * t)) * np.exp(-t * 6.5)
        s[:220] *= np.linspace(0, 1, 220)
        pan = 0.5 + 0.35 * np.sin(i * 1.7 + b)
        vel = (0.9 if i % 2 == 0 else 0.6) * lvl * 0.085
        t0 = b * BAR + i * BEAT / 2
        add(arp[:, 0], s * vel * (1 - pan), t0); add(arp[:, 1], s * vel * pan, t0)
# Ping-Pong-Echo
d = int(0.45 * SR)
for k in range(1, 5):
    g = 0.42 ** k
    src = arp[:-d * k, (k % 2)].copy() if d * k < N else None
    if src is not None:
        arp[d * k:, 1 - (k % 2)] += src * g

# ---------- Bass ----------
for b in range(4, BARS):
    root, _ = CH[b % 4]
    hits = [(0, 1.7)] if b >= 58 else [(0, 1.0), (1.5, 0.45), (2.5, 0.9), (3.5, 0.4)]
    for bt, ln in hits:
        n = int(ln * BEAT * SR); t = np.arange(n) / SR
        fr = f(root - (12 if root > 40 else 0) + 12) / 2
        s = (np.sin(2 * np.pi * fr * t) + 0.3 * np.sin(4 * np.pi * fr * t)) * env(n, 0.012, min(0.12, ln * BEAT * 0.4))
        add(bass, s * 0.3, b * BAR + bt * BEAT)

# ---------- Schlagzeug ----------
def drums_on(b):
    return 9 <= b < 58 and b not in (25, 26, 44)

for b in range(BARS):
    if not drums_on(b):
        continue
    for q in range(4):
        t0 = b * BAR + q * BEAT
        n = int(0.34 * SR); t = np.arange(n) / SR
        ph = 2 * np.pi * (48 * t + (130 - 48) * (1 - np.exp(-t * 28)) / 28)
        add(kick, np.sin(ph) * np.exp(-t * 11) * 0.62, t0)
        add(kenv, np.exp(-np.arange(int(0.3 * SR)) / SR * 9), t0)
        if b >= 14:
            for off, v in ((0.5, 1.0), (0.25, 0.35), (0.75, 0.35)):
                nh = int(0.07 * SR)
                s = rng.standard_normal(nh) * np.exp(-np.arange(nh) / SR * 70) * 0.05 * v
                p = 0.35 if off == 0.5 else 0.65
                add(hat[:, 0], s * (1 - p), t0 + off * BEAT); add(hat[:, 1], s * p, t0 + off * BEAT)
        if b >= 19 and q in (1, 3):
            nc = int(0.22 * SR)
            add(clap, rng.standard_normal(nc) * np.exp(-np.arange(nc) / SR * 22) * 0.16, t0)
hat = hp(hat, 7000)
clap = bp(clap, 900, 3200)
kenv = np.clip(kenv, 0, 1)

# ---------- Übergänge: Rauschen schwillt an, weicher Einschlag ----------
for sb in list(STARTS[1:]):
    t0 = sb * BAR
    n = int(1.6 * SR); x = np.linspace(0, 1, n)
    s = rng.standard_normal((n, 2)) * (x ** 2.5)[:, None] * 0.05
    s = bp(s, 1500, 9000)
    add(fx[:, 0], s[:, 0], t0 - 1.6); add(fx[:, 1], s[:, 1], t0 - 1.6)
    nb = int(1.6 * SR); t = np.arange(nb) / SR
    boom = np.sin(2 * np.pi * (38 * t + 30 * (1 - np.exp(-t * 9)) / 9)) * np.exp(-t * 3.2) * 0.3
    add(fx[:, 0], boom, t0); add(fx[:, 1], boom, t0)
    ns = int(2.2 * SR)
    sh = bp(rng.standard_normal((ns, 2)), 3000, 11000) * np.exp(-np.arange(ns) / SR * 2.2)[:, None] * 0.035
    add(fx[:, 0], sh[:, 0], t0); add(fx[:, 1], sh[:, 1], t0)

# ---------- Mischung ----------
# Balance der Spuren
arp *= 3.0; bass *= 0.5; kick *= 0.8; hat *= 5.0; clap *= 4.0
duck = (1 - 0.38 * kenv)
mix = pad * duck[:, None] + arp + hat + fx
mono = bass * duck + kick + clap * 0.6
mix[:, 0] += mono; mix[:, 1] += mono

# Hall
nr = int(2.8 * SR)
ir = rng.standard_normal((nr, 2)) * np.exp(-np.arange(nr) / SR * 2.4)[:, None]
ir = lp(hp(ir, 300), 6000); ir /= np.sqrt((ir ** 2).sum(axis=0))
send = pad * 0.5 + arp * 0.9 + fx * 0.5 + np.stack([clap, clap], 1) * 0.5
wet = np.stack([fftconvolve(send[:, c], ir[:, c])[:N] for c in (0, 1)], 1)
mix += wet * 0.45

# Ein- und Ausblenden, Limiter
t = np.arange(N) / SR
g = np.clip(t / 1.2, 0, 1) * np.clip((N / SR - t) / 3.0, 0, 1) ** 1.5
mix *= g[:, None]
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(np.asarray(x)[SR * 60:SR * 120] ** 2)) + 1e-9)
print('Pegel dB  Fläche %.1f  Arp %.1f  Bass %.1f  Kick %.1f  Hat %.1f  Clap %.1f  FX %.1f  Hall %.1f  Spitze vor Limiter %.2f' % (rms(pad), rms(arp), rms(bass), rms(kick), rms(hat), rms(clap * 0.6), rms(fx), rms(wet * 0.45), np.abs(mix).max()))
mix = np.tanh(mix * 1.5) / np.max(np.abs(np.tanh(mix * 1.5))) * 0.84
wavfile.write(sys.argv[1], SR, (mix * 32767).astype(np.int16))
print('ok', N / SR, 's')
