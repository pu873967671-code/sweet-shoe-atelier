#!/usr/bin/env python3
"""Compose the tuned UI cues for Sweet Shoe Atelier (original, offline, no samples).

Every cue sits in D major so the whole game sounds like one family: a soft
harp (Karplus-Strong pluck), a celesta-like pearl bell (inharmonic partials)
and a glass twinkle, with a small shared room reverb. Physical actions keep the
Kenney cloth/paper/tissue recordings built by dev/build-sfx.py.

Writes assets/sfx/<name>.ogg and .mp3 (mono, 32 kHz) like build-sfx.py.
usage: python3 dev/build-elegant-sfx.py
"""
import subprocess, tempfile, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/sfx'
SR = 32000
rng = np.random.default_rng(1104)


def hz(note):
    """MIDI note number -> Hz."""
    return 440.0 * 2 ** ((note - 69) / 12)


D5, E5, Fs5, A5, B5, D6, E6, Fs6, A6, B6, D7 = 74, 76, 78, 81, 83, 86, 88, 90, 93, 95, 98
A4, Fs4, D4 = 69, 66, 62


def env(n, attack=0.004, decay=0.6):
    t = np.arange(n) / SR
    a = np.minimum(1, t / max(attack, 1e-4))
    return a * np.exp(-t / decay)


def bell(note, dur=1.2, decay=0.5, bright=1.0):
    """Celesta / pearl bell: soft inharmonic partials, upper ones die faster."""
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(note); y = np.zeros(n)
    for ratio, amp, dk in [(1, 1, 1), (2.0, .35 * bright, .55), (3.01, .16 * bright, .35), (4.17, .08 * bright, .22), (5.43, .04 * bright, .15)]:
        y += amp * np.sin(2 * np.pi * f * ratio * t + rng.uniform(0, 6)) * np.exp(-t / (decay * dk))
    return y * env(n, .003, 10)


def harp(note, dur=1.6, damp=0.996, bright=0.5):
    """Karplus-Strong pluck, low-passed for a warm nylon-harp tone."""
    n = int(dur * SR); f = hz(note); p = max(2, int(round(SR / f)))
    buf = rng.uniform(-1, 1, p)
    for _ in range(3):  # soften the excitation
        buf = .5 * (buf + np.roll(buf, 1))
    y = np.zeros(n); b = buf.copy()
    for i in range(n):
        y[i] = b[i % p]
        b[i % p] = damp * (bright * b[i % p] + (1 - bright) * b[(i - 1) % p])
    return y * env(n, .002, 10)


def twinkle(note, dur=.5):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(note)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / .09) + .3 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / .05)
    return y * env(n, .001, 10)


def place(total, parts):
    """Mix (start_seconds, signal, gain) parts into one buffer."""
    y = np.zeros(int(total * SR))
    for start, sig, g in parts:
        i = int(start * SR); j = min(len(y), i + len(sig))
        y[i:j] += g * sig[:j - i]
    return y


def reverb(y, mix=.18, size=.9):
    """Small airy room: decaying filtered noise impulse."""
    n = int(size * SR); t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t / (size / 5))
    k = np.ones(6) / 6; ir = np.convolve(ir, k, 'same'); ir /= np.sqrt((ir ** 2).sum())
    wet = np.convolve(y, ir)[:len(y) + n // 2]
    dry = np.concatenate([y, np.zeros(len(wet) - len(y))])
    return (1 - mix) * dry + mix * wet * 3


def lowpass(y, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); out = np.zeros_like(y); s = 0.0
    for i, v in enumerate(y):
        s = (1 - a) * v + a * s; out[i] = s
    return out


def finish(y, peak=0.7, tail=.05):
    y = y - y.mean()
    n = int(tail * SR)
    if n and len(y) > n:
        y[-n:] *= np.linspace(1, 0, n)
    return y / (np.abs(y).max() + 1e-9) * peak


CUES = {
    # Gentle selection: a single tiny pearl tick.
    'tap': lambda: finish(reverb(bell(A6, .25, .05, .5), .1, .4), .45),
    # A new material appears: two rising pearl notes.
    'spawn': lambda: finish(reverb(place(.6, [(0, bell(D6, .5, .14), .8), (.06, bell(A6, .5, .14), .7)]))),
    # Merge: a soft harp dyad (pitch rises with tier in the engine).
    'merge': lambda: finish(reverb(place(.9, [(0, harp(D5, .9), .9), (.035, harp(A5, .9), .7), (.07, bell(D6, .6, .2, .6), .35)]), .22)),
    # Glass twinkle used as garnish by coins and try-on.
    'sparkle': lambda: finish(reverb(place(.4, [(0, twinkle(D7), .6), (.05, twinkle(B6), .5), (.1, twinkle(Fs6), .4)]), .25, .6), .5),
    # Order delivered: harp arpeggio up to the octave.
    'delivery': lambda: finish(reverb(place(1.1, [(i * .07, harp(n, 1.0), .85) for i, n in enumerate([D5, Fs5, A5, D6])] + [(.3, bell(Fs6, .8, .3), .3)]), .24)),
    # Level / renovation / perfect look: harp glissando into a bell chord.
    'level': lambda: finish(reverb(place(1.7, [(i * .045, harp(n, 1.3), .7) for i, n in enumerate([D5, E5, Fs5, A5, B5, D6, E6, Fs6])] + [(.42, bell(D6, 1.2, .5), .4), (.42, bell(Fs6, 1.2, .5), .3), (.42, bell(A6, 1.2, .5), .25)]), .28, 1.1)),
    # New detail unlocked: a blooming Dmaj7 bell chord.
    'unlock': lambda: finish(reverb(place(1.4, [(i * .05, bell(n, 1.2, .55, .8), .5) for i, n in enumerate([D6, Fs6, A6, 85])]), .26, 1.0)),
    # Coins: a bright pearl ping (the engine cascades up to three).
    'coin': lambda: finish(reverb(place(.45, [(0, bell(A6, .4, .08, .7), .8), (.03, twinkle(D7, .3), .35)]), .15, .5), .55),
    # Not possible right now: a quiet, low two-note "felt" sigh. Never harsh.
    'error': lambda: finish(lowpass(reverb(place(.55, [(0, harp(A4, .5, .992, .3), .9), (.09, harp(Fs4, .5, .992, .3), .8)]), .15, .5), 1400), .35),
}


def write(name, y):
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'cue.wav'
        pcm = np.clip(y * 32767, -32768, 32767).astype('<i2')
        with wave.open(str(wav), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
        for ext, codec in [('ogg', ['-c:a', 'libvorbis', '-q:a', '3']), ('mp3', ['-c:a', 'libmp3lame', '-b:a', '64k'])]:
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav), *codec, str(OUT / f'{name}.{ext}')], check=True)


def main():
    lic = OUT / 'LICENSE.txt'
    lines = [l for l in lic.read_text().splitlines() if not any(l.startswith(n + '.ogg') for n in CUES)]
    for name, make in CUES.items():
        write(name, make())
        lines.append(f'{name}.ogg / {name}.mp3 <- original composition, dev/build-elegant-sfx.py (CC0)')
    lic.write_text('\n'.join(lines) + '\n')
    print('PASS:', ', '.join(CUES))


if __name__ == '__main__':
    main()
