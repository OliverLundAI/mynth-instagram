"""Ljud till Mynths Reels, syntetiserat från grunden (inga samplade eller licensierade ljud).

mix(cues, seconds, path) skriver en WAV (48 kHz, stereo, 24-bit) med:
  - ljudeffekter på cue-tiderna från scenerna: filtrerat brus, FM-klockor, fysikaliskt modellerade
    knäppningar (Karplus-Strong), med rumsklang via faltning
  - en lågmäld musikbädd: varma ackord, en knäppt arpeggio och en mjuk puls efter introt,
    som duckar under ljudeffekterna
  - mastring: lågskärning, mjuk kompression och begränsning. Ljudstyrkan normaliseras sedan
    till -14 LUFS av ffmpeg (loudnorm) i tools/video.py.
Allt är deterministiskt, så samma post.json ger samma ljud.
"""
import wave
import numpy as np
from scipy import signal

SR = 48000


def _rng(seed):
    return np.random.default_rng(seed)


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def _env(n, attack, decay, hold=0.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-5), 0, 1) ** 2
    return a * np.exp(-np.maximum(t - attack - hold, 0) / decay)


def _bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, min(hi, SR / 2 - 100)], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def _lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)


def _hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


def _norm(x):
    return x / (np.abs(x).max() + 1e-9)


def _pink(n, seed):
    """Rosa brus (1/f) via spektral formning – mjukare och mer naturligt än vitt brus."""
    spec = np.fft.rfft(_rng(seed).standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[1:] /= np.sqrt(f[1:])
    spec[0] = 0
    return _norm(np.fft.irfft(spec, n))


def _sweep_tone(f0, f1, sec, curve=4.0):
    t = _t(sec)
    f = f1 + (f0 - f1) * np.exp(-curve * t / sec)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def _moving_band(x, centers, q=1.4):
    """Brus genom ett bandpass som glider (STFT-maskning), för luftiga svepljud."""
    nper = 1024
    f, _, Z = signal.stft(x, SR, nperseg=nper)
    k = Z.shape[1]
    c = np.interp(np.linspace(0, 1, k), np.linspace(0, 1, len(centers)), centers)
    lf, lc = np.log(f[:, None] + 1), np.log(c[None, :])
    Z *= np.exp(-((lf - lc) ** 2) / (2 * (q / 2.5) ** 2))
    _, y = signal.istft(Z, SR, nperseg=nper)
    return y[: len(x)]


def _pad(a, n):
    return np.pad(a, (0, max(0, n - len(a))))[:n]


# ---------- rumsklang ----------
def _ir(sec=1.6, decay=.42, seed=5, damp=6000):
    n = int(sec * SR)
    t = np.arange(n) / SR
    irs = []
    for s in (seed, seed + 1):
        x = _rng(s).standard_normal(n) * np.exp(-t / decay)
        # högre frekvenser dör ut snabbare: blanda mörkt och ljust över tid
        dark = _lp(x, 2200)
        mix = np.clip(t / sec * 2.5, 0, 1)
        y = _lp(x, damp) * (1 - mix) + dark * mix
        y[: int(.012 * SR)] *= np.linspace(0, 1, int(.012 * SR))  # förfördröjning-ish
        irs.append(y / np.sqrt(np.sum(y ** 2)))
    return np.stack(irs, 1)


IR_ROOM = None


def _reverb(st, wet=.18, ir=None):
    global IR_ROOM
    if ir is None:
        if IR_ROOM is None:
            IR_ROOM = _ir()
        ir = IR_ROOM
    out = np.zeros((st.shape[0] + ir.shape[0] - 1, 2))
    for c in range(2):
        out[:, c] = signal.fftconvolve(st[:, c], ir[:, c])
    dry = np.zeros_like(out)
    dry[: st.shape[0]] = st
    return dry * (1 - wet * .5) + out * wet


# ---------- instrument ----------
def _ks(freq, sec, bright=.5, seed=0):
    """Karplus-Strong: en knäppt sträng/kalimba-liknande ton med naturlig avklingning."""
    n = int(sec * SR)
    p = max(2, int(round(SR / freq)))
    buf = _lp(_rng(seed).uniform(-1, 1, p * 4), 900 + 3500 * bright, 4)[-p:]
    out = np.zeros(n)
    out[:p] = buf
    d = .996 + .003 * (1 - bright)
    for i in range(p, n):
        out[i] = d * .5 * (out[i - p] + out[i - p + 1 if i - p + 1 < i else i - p])
    return _lp(out * _env(n, .004, sec * .45), 5500)


def _fm_bell(f, sec=2.2, ratio=3.5, index=3.0):
    t = _t(sec)
    ienv = index * np.exp(-t / .35)
    mod = np.sin(2 * np.pi * f * ratio * t) * ienv
    car = np.sin(2 * np.pi * f * t + mod)
    return car * _env(len(t), .002, .7) + .25 * np.sin(2 * np.pi * f * 2 * t) * _env(len(t), .001, .25)


# ---------- ljudeffekter (mono, normaliserade) ----------
def click(v=0):
    """Tangent: kort transient + liten resonans i plast/metall, varierar per tangent."""
    r = _rng(100 + v)
    n = int(.045 * SR)
    hit = _bp(r.standard_normal(n), 1800, 9000) * _env(n, .0003, .004)
    body = _bp(r.standard_normal(n), 900 + 300 * r.random(), 2600, 2) * _env(n, .0005, .012) * .6
    return _norm(hit + body) * (.8 + .2 * r.random())


def pop(v=0):
    f0 = 700 * 2 ** (v * 2 / 12)
    n = int(.16 * SR)
    tone = _sweep_tone(f0, f0 * .5, .16, 6) * _env(n, .0015, .04)
    air = _bp(_rng(200 + v).standard_normal(n), 2000, 8000) * _env(n, .0005, .006) * .3
    return _norm(tone + air)


def blip(v=0):
    f = 1046.5 * 2 ** ((v % 5) * 2 / 12)
    return _norm(_fm_bell(f, .35, 2.0, 1.2) * _env(int(.35 * SR), .002, .08))


def tick(v=0):
    n = int(.06 * SR)
    x = _bp(_rng(300 + v).standard_normal(n), 2500, 5200, 4) * _env(n, .0004, .006)
    return _norm(x + .4 * np.sin(2 * np.pi * 3100 * _t(.06)) * _env(n, .0005, .01))


def scan(v=0):
    n = int(.14 * SR)
    return _norm(_sweep_tone(1300 + v * 150, 2000 + v * 150, .14, 2) * _env(n, .01, .05))


def whoosh(v=0, sec=.7):
    n = int(sec * SR)
    x = _pink(n, 400 + v)
    y = _moving_band(x, [350, 900, 2600, 1400], 1.6)
    shape = np.sin(np.pi * np.clip(np.arange(n) / n, 0, 1)) ** 2.2
    return _norm(y * shape)


def swish(v=0):
    n = int(.36 * SR)
    x = _moving_band(_pink(n, 500 + v), [1200, 4200, 2600], 1.2)
    return _norm(x * np.sin(np.pi * np.arange(n) / n) ** 2) * .8


def thud(v=0):
    n = int(.5 * SR)
    body = _sweep_tone(120, 45, .5, 6) * _env(n, .002, .11)
    hit = _lp(_rng(600).standard_normal(n), 1200) * _env(n, .0005, .012) * 1.5
    return _norm(body + hit)


def boom(v=0):
    n = int(1.6 * SR)
    sub = _sweep_tone(90, 36, 1.6, 4) * _env(n, .003, .5)
    knock = _lp(_rng(700).standard_normal(n), 600) * _env(n, .001, .03)
    rise = whoosh(1, .55)[::-1] * .35  # omvänd luft före landningen
    out = _norm(sub + knock * .8)
    pre = np.concatenate([rise, np.zeros(n)])
    pre[len(rise):] += out
    return pre, len(rise)  # (ljud, förskjutning i samplingar så att smällen landar på cue-tiden)


def chime(v=0):
    f = [659.25, 830.61, 987.77][v % 3]  # E5, G#5, B5
    return _norm(_fm_bell(f, 2.4, 3.5, 2.2))


def _scratch(sec, seed, density=1.0):
    """Penna mot papper: textur av korta korn (grafit mot fibrer) i drag med pauser."""
    r = _rng(seed)
    n = int(sec * SR)
    grain = r.standard_normal(n) * (r.random(n) < .35 * density)
    tex = _bp(grain, 2200, 9500, 2) + .35 * _bp(r.standard_normal(n), 700, 2200, 2)
    amp = np.zeros(n)
    i = 0
    while i < n:
        L = int(r.uniform(.06, .22) * SR)
        e = min(L, n - i)
        tt = np.arange(e) / L
        amp[i:i + e] = (np.sin(np.pi * tt) ** .7) * r.uniform(.45, 1) * (1 + .25 * np.sin(2 * np.pi * r.uniform(9, 16) * tt * L / SR))
        i += e + int(r.uniform(.015, .06) * SR)
    fade = np.clip(np.arange(n) / (.04 * SR), 0, 1) * np.clip((n - np.arange(n)) / (.12 * SR), 0, 1)
    return _norm(_lp(tex * amp * fade, 8500))


def pencil(v=0):
    return _scratch(2.0, 11)


def write(v=0):
    return _scratch(max(.4, v / 100), 23, 1.3) * .85


def paper(v=0):
    n = int(.6 * SR)
    r = _rng(800)
    slide = _moving_band(_pink(n, 801), [600, 1800, 900], 1.8) * np.sin(np.pi * np.arange(n) / n) ** 1.5
    crinkle = np.zeros(n)
    for _ in range(14):
        s = int(r.uniform(.05, .45) * SR)
        L = int(r.uniform(.004, .015) * SR)
        crinkle[s:s + L] += _bp(r.standard_normal(L), 2500, 9000) * np.hanning(L) * r.uniform(.3, 1)
    return _norm(_lp(slide + crinkle * .5, 10000))


SFX = dict(pencil=pencil, write=write, paper=paper, click=click, pop=pop, blip=blip, tick=tick, scan=scan,
           whoosh=whoosh, swish=swish, thud=thud, boom=boom, chime=chime)
PAN = dict(pencil=.12, write=-.1, paper=0, click=.18, pop=.05, blip=-.2, tick=.2, scan=.25, whoosh=0, swish=-.15,
           thud=0, boom=0, chime=.1)
SEND = dict(pencil=.12, write=.1, paper=.15, click=.05, pop=.25, blip=.4, tick=.2, scan=.3, whoosh=.25, swish=.2,
            thud=.25, boom=.35, chime=.55)


# ---------- musikbädd ----------
def _hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


# A-dur, ljust och lugnt: Amaj9 – F#m9 – Dmaj9 – E6/9 (MIDI-noter)
CHORDS = [[45, 52, 56, 59, 61], [42, 49, 52, 56, 57], [38, 45, 49, 52, 54], [40, 47, 49, 54, 56]]
ARP = [[69, 73, 76, 80], [66, 69, 73, 76], [69, 73, 74, 78], [68, 71, 73, 76]]


def bed(seconds, beat_from):
    n = int(seconds * SR)
    out = np.zeros((n, 2))
    bar, beat = 2.4, .6  # 100 BPM
    # varma ackord: flera lätt ostämda oscillatorer med få övertoner, lågpass
    for ci in range(int(seconds / bar) + 1):
        s0 = int(ci * bar * SR)
        seg = min(int((bar + 1.0) * SR), n - s0)
        if seg <= 0:
            break
        tt = np.arange(seg) / SR
        env = np.clip(tt / .7, 0, 1) ** 2 * np.clip((bar + 1.0 - tt) / 1.0, 0, 1)
        for j, m in enumerate(CHORDS[ci % 4]):
            f = _hz(m)
            for ch, det in ((0, -.003), (1, .003)):
                ph = 2 * np.pi * f * (1 + det) * tt + .002 * np.sin(2 * np.pi * 4.5 * tt)
                x = sum(np.sin(k * ph) / k ** 1.6 for k in range(1, 6))
                out[s0:s0 + seg, ch] += x * env * (.05 if j == 0 else .028)
    out = np.stack([_lp(out[:, 0], 1500), _lp(out[:, 1], 1500)], 1)
    # knäppt arpeggio (åttondelar) efter introt
    step = beat / 2
    k = 0
    while beat_from + k * step < seconds - .5:
        t0 = beat_from + k * step
        ci = int(t0 / bar) % 4
        m = ARP[ci][k % 4] + (12 if k % 8 == 6 else 0)
        tone = _ks(_hz(m), 1.2, .35, seed=900 + k % 13) * (.11 if k % 2 == 0 else .075)
        s = int(t0 * SR)
        e = min(len(tone), n - s)
        pan = .35 * np.sin(k * 1.3)
        out[s:s + e, 0] += tone[:e] * (1 - pan)
        out[s:s + e, 1] += tone[:e] * (1 + pan)
        k += 1
    # mjuk puls: dov kick på 1 och 3, borstad hi-hat på offbeats
    k = 0
    while beat_from + k * beat < seconds - .4:
        s = int((beat_from + k * beat) * SR)
        if k % 2 == 0:
            kick = _sweep_tone(95, 42, .35, 7) * _env(int(.35 * SR), .002, .09) * .22
            e = min(len(kick), n - s)
            out[s:s + e] += kick[:e, None]
        hs = int((beat_from + (k + .5) * beat) * SR)
        if hs < n:
            hat = _bp(_rng(1000 + k).standard_normal(int(.05 * SR)), 6000, 12000) * _env(int(.05 * SR), .002, .012) * .022
            e = min(len(hat), n - hs)
            out[hs:hs + e, 0] += hat[:e] * .7
            out[hs:hs + e, 1] += hat[:e]
        k += 1
    t = np.arange(n) / SR
    fade = np.clip(t / 1.2, 0, 1) * np.clip((seconds - t) / 1.4, 0, 1)
    return out * fade[:, None]


def _compress(x, thresh=.35, ratio=3.0, attack=.005, release=.12):
    """Enkel bredbandskompressor (RMS-följare) för ett sammanhållet ljud."""
    lvl = np.sqrt(_lp(np.mean(x ** 2, 1), 30, 1).clip(0))
    over = np.maximum(lvl / thresh, 1)
    gain = over ** (1 / ratio - 1)
    # mjuk attack/release på förstärkningen
    g = np.empty_like(gain)
    a, r = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    acc = 1.0
    for i, v in enumerate(gain):
        c = a if v < acc else r
        acc = c * acc + (1 - c) * v
        g[i] = acc
    return x * g[:, None]


def mix(cues, seconds, path, beat_from=2.7):
    n = int(seconds * SR)
    music = bed(seconds, beat_from)
    fx = np.zeros((n + SR * 2, 2))
    send = np.zeros_like(fx)
    duck = np.zeros(n)
    cache = {}
    for ms, name, gain, *var in cues:
        v = int(var[0]) if var else 0
        key = (name, v)
        if key not in cache:
            res = SFX[name](v)
            cache[key] = res if isinstance(res, tuple) else (res, 0)
        x, off = cache[key]
        x = x * float(gain) * .55
        s = int(ms / 1000 * SR) - off
        if s < 0:
            x, s = x[-s:], 0
        if s >= n:
            continue
        e = min(len(x), fx.shape[0] - s)
        pan = PAN.get(name, 0) * (1 if v % 2 else -1)
        L, R = np.sqrt(.5 * (1 - pan)), np.sqrt(.5 * (1 + pan))
        fx[s:s + e, 0] += x[:e] * L * 1.41
        fx[s:s + e, 1] += x[:e] * R * 1.41
        send[s:s + e] += x[:e, None] * SEND.get(name, .2)
        d = min(len(x), n - s)
        duck[s:s + d] = np.maximum(duck[s:s + d], np.abs(x[:d]))
    # musiken duckar mjukt under effekterna
    duck = _lp(duck, 8, 1).clip(0, 1)
    music *= (1 - .45 * np.clip(duck * 2, 0, 1))[:, None]
    wet = _reverb(send, wet=1.0)[: fx.shape[0]]
    music_wet = _reverb(music * .5, wet=.35)[:n]
    out = fx[:n] + wet[:n] * .35 + music * .9 + music_wet * .25
    out = np.stack([_hp(out[:, 0], 30), _hp(out[:, 1], 30)], 1)
    out = _compress(out / (np.abs(out).max() + 1e-9))
    out = np.tanh(out / (np.abs(out).max() + 1e-9) * 1.2) / np.tanh(1.2) * .9
    pcm = (np.clip(out, -1, 1) * 8388607).astype("<i4")
    raw = pcm.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()  # 24-bit little endian
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(raw)
