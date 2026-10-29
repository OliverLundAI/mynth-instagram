"""Ljud till Mynths Reels, syntetiserat från grunden (inga samplade eller licensierade ljud).

mix(cues, seconds, path) skriver en WAV (48 kHz, stereo) med:
  - ljudeffekter på cue-tiderna från scenerna (klick, pop, whoosh, duns, klang ...)
  - en lågmäld musikbädd: mjuka ackord och en dov puls som startar efter introt.
Allt är deterministiskt, så samma post.json ger samma ljud.
"""
import wave
import numpy as np

SR = 48000
RNG = np.random.default_rng(7)


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def _env(n, attack, decay):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / decay)


def _sweep(f0, f1, sec, curve=3.0):
    t = _t(sec)
    f = f1 + (f0 - f1) * np.exp(-curve * t / sec)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def _lp(x, cutoff):
    """Enpolig lågpass (vektoriserad via FFT-fönster duger inte för korta ljud, så enkel loop)."""
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def _band_noise(sec, lo, hi):
    n = int(sec * SR)
    spec = np.fft.rfft(RNG.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    x = np.fft.irfft(spec, n)
    return x / (np.abs(x).max() + 1e-9)


def _add(a, b, gb=1.0):
    n = max(len(a), len(b))
    out = np.zeros(n)
    out[:len(a)] += a
    out[:len(b)] += b * gb
    return out


# ---------- ljudeffekter (mono, normaliserade till ~1) ----------
def click(v=0):
    n = int(.018 * SR)
    hp = np.diff(RNG.standard_normal(n + 1))
    tone = np.sin(2 * np.pi * (2600 + 180 * (v % 5)) * _t(.018))
    return (hp * .35 + tone * .5) * _env(n, .0005, .004)


def pop(v=0):
    f0 = 820 * 2 ** (v * 2 / 12)  # stiger en heltonsteg per variant
    x = _sweep(f0, f0 * .45, .12, 4) * _env(int(.12 * SR), .002, .045)
    return _add(x, click(v), .15)


def blip(v=0):
    f = 1320 * 2 ** ((v % 5) * 3 / 12)
    t = _t(.09)
    return (np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)) * _env(len(t), .003, .03)


def tick(v=0):
    t = _t(.05)
    return _add(np.sin(2 * np.pi * 2350 * t) * _env(len(t), .001, .012), click(v), .3)


def scan(v=0):
    return _sweep(1500 + v * 120, 2100 + v * 120, .11, 2) * _env(int(.11 * SR), .01, .04) * .8


def whoosh(v=0, sec=.62):
    x = _band_noise(sec, 250, 5200)
    x = _lp(x, 2400)
    t = _t(sec)
    shape = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 2
    return x / (np.abs(x).max() + 1e-9) * shape


def swish(v=0):
    return whoosh(v, .34) * .8


def thud(v=0):
    body = _sweep(140, 42, .38, 5) * _env(int(.38 * SR), .002, .12)
    hit = _lp(RNG.standard_normal(int(.06 * SR)), 900) * _env(int(.06 * SR), .001, .015) * 4
    out = body.copy()
    out[:len(hit)] += hit
    return out


def boom(v=0):
    sub = _sweep(95, 34, 1.4, 4) * _env(int(1.4 * SR), .004, .45)
    air = whoosh(0, .5) * .25
    out = sub.copy()
    out[:len(air)] += air[::-1]  # omvänd luft före smällen ger "landning"
    return out


def chime(v=0):
    f = [659.25, 830.61, 987.77][v % 3]  # E5, G#5, B5 – ett ljust E-dur-ackord byggs upp
    t = _t(1.6)
    x = sum(a * np.sin(2 * np.pi * f * m * t) for m, a in [(1, 1), (2, .28), (3, .1), (4.2, .05)])
    return x * _env(len(t), .003, .42)


def _scratch(sec, seed):
    """Penna mot papper: bandpassat brus i korta drag med pauser."""
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    x = _band_noise(sec, 1800, 7500)
    amp = np.zeros(n)
    i = 0
    while i < n:
        L = int(r.uniform(.07, .24) * SR)
        e = min(L, n - i)
        tt = np.arange(e) / SR
        amp[i:i + e] = np.sin(np.pi * tt / (L / SR)) ** .6 * r.uniform(.5, 1)
        i += e + int(r.uniform(.02, .07) * SR)
    fade = np.clip(np.arange(n) / (.05 * SR), 0, 1) * np.clip((n - np.arange(n)) / (.1 * SR), 0, 1)
    return x * amp * fade


def pencil(v=0):
    return _scratch(2.0, 11)


def write(v=0):
    return _scratch(max(.4, v / 100), 23) * .8


def paper(v=0):
    x = _lp(_band_noise(.5, 120, 4000), 1500)
    t = _t(.5)
    return x / (np.abs(x).max() + 1e-9) * np.sin(np.pi * t / .5) ** 1.5


SFX = dict(pencil=pencil, write=write, paper=paper, click=click, pop=pop, blip=blip, tick=tick, scan=scan, whoosh=whoosh, swish=swish,
           thud=thud, boom=boom, chime=chime)
PAN = dict(pencil=.1, write=-.1, paper=0, click=.15, pop=0, blip=-.2, tick=.2, scan=.25, whoosh=0, swish=-.15, thud=0, boom=0, chime=0)


# ---------- musikbädd ----------
NOTE = {n: 440 * 2 ** ((i - 9) / 12) for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())}


def _f(name, octave):
    return NOTE[name] * 2 ** (octave - 4)


CHORDS = [  # Amaj9 -> F#m9 -> Dmaj9 -> E6/9 (ljust och lugnt)
    [("A", 2), ("E", 3), ("G#", 3), ("B", 3), ("C#", 4)],
    [("F#", 2), ("C#", 3), ("E", 3), ("G#", 3), ("A", 3)],
    [("D", 2), ("A", 2), ("C#", 3), ("E", 3), ("F#", 3)],
    [("E", 2), ("B", 2), ("C#", 3), ("F#", 3), ("G#", 3)],
]


def bed(seconds, beat_from):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    bar = 2.4  # 100 BPM, 4/4
    for ci in range(int(seconds / bar) + 1):
        notes = CHORDS[ci % len(CHORDS)]
        s0 = int(ci * bar * SR)
        seg = min(int((bar + .8) * SR), n - s0)
        if seg <= 0:
            break
        tt = np.arange(seg) / SR
        env = np.clip(tt / .5, 0, 1) * np.clip((bar + .8 - tt) / .8, 0, 1)
        for j, (nm, octv) in enumerate(notes):
            f = _f(nm, octv)
            for side, det in ((0, -.0025), (1, .0025)):
                ph = 2 * np.pi * f * (1 + det) * tt
                x = np.sin(ph) + .18 * np.sin(2 * ph) + .06 * np.sin(3 * ph)
                out[s0:s0 + seg, side] += x * env * (.055 if j == 0 else .035)
    # dov puls (kick) och lätt hi-hat efter introt
    beat = 60 / 100
    k = 0
    while beat_from + k * beat < seconds - .3:
        s = int((beat_from + k * beat) * SR)
        kick = _sweep(110, 44, .3, 6) * _env(int(.3 * SR), .002, .09) * .32
        e = min(len(kick), n - s)
        out[s:s + e] += kick[:e, None]
        hs = int((beat_from + (k + .5) * beat) * SR)
        hat = np.diff(RNG.standard_normal(int(.03 * SR) + 1)) * _env(int(.03 * SR), .001, .008) * .05
        e = min(len(hat), max(0, n - hs))
        out[hs:hs + e, 0] += hat[:e] * .8
        out[hs:hs + e, 1] += hat[:e]
        k += 1
    fade = np.clip(t / 1.0, 0, 1) * np.clip((seconds - t) / 1.2, 0, 1)
    return out * fade[:, None]


def mix(cues, seconds, path, beat_from=2.6):
    n = int(seconds * SR)
    out = bed(seconds, beat_from)
    cache = {}
    for ms, name, gain, *var in cues:
        v = int(var[0]) if var else 0
        key = (name, v)
        if key not in cache:
            x = SFX[name](v)
            cache[key] = x / (np.abs(x).max() + 1e-9)
        x = cache[key] * float(gain) * .6
        s = int(ms / 1000 * SR)
        if s >= n:
            continue
        e = min(len(x), n - s)
        pan = PAN.get(name, 0) * (1 if v % 2 else -1)
        out[s:s + e, 0] += x[:e] * (1 - max(pan, 0))
        out[s:s + e, 1] += x[:e] * (1 + min(pan, 0))
    peak = np.abs(out).max()
    out = np.tanh(out / max(peak, 1e-9) * 1.4) / np.tanh(1.4) * .89  # mjuk begränsning
    pcm = (out * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
