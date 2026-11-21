#!/usr/bin/env python3
"""LEGACY (superseded by dev/build-fresh-sfx.py). Pure, crisp, elegant tones.

No noise anywhere: each cue is built from clean sine partials (a glass bell,
a soft harp-like pluck and a tiny "pearl" pop), with a gentle low-pass and a
clean two-tap echo instead of a noise reverb. All notes are in D major so
every cue belongs to one family. Original composition, CC0.

Writes assets/sfx/<name>.ogg and .mp3 (mono 44.1 kHz) and LICENSE.txt.
usage: python3 dev/build-elegant-sfx.py
"""
import subprocess, tempfile, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/sfx'
SR = 44100


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


A4, B4, D5, E5, Fs5, A5, B5, Cs6, D6, E6, Fs6, A6, B6, D7 = 69, 71, 74, 76, 78, 81, 83, 85, 86, 88, 90, 93, 95, 98


def tone(note, dur, partials, attack=.004):
    """Sum of (ratio, amplitude, decay seconds) sine partials, click-free."""
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(note); y = np.zeros(n)
    for ratio, amp, dk in partials:
        y += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / dk)
    return y * np.minimum(1, t / attack)


def glass(note, dur=1.0, ring=.45):
    """Glass / celesta bell: fundamental with soft octave and twelfth."""
    return tone(note, dur, [(1, 1, ring), (2, .28, ring * .45), (3, .07, ring * .25)], .003)


def pluck(note, dur=1.2, ring=.6):
    """Harp-like pluck from pure partials: bright onset, warm tail."""
    return tone(note, dur, [(1, 1, ring), (2, .42, ring * .4), (3, .16, ring * .22), (4, .06, ring * .14)], .002)


def pearl(note, dur=.18):
    """A tiny round pop: short sine with a slight downward glide."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(note) * (1 + .06 * np.exp(-t / .015))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / .045) * np.minimum(1, t / .002)


def mix(total, parts):
    y = np.zeros(int(total * SR))
    for start, sig, g in parts:
        i = int(start * SR); j = min(len(y), i + len(sig)); y[i:j] += g * sig[:j - i]
    return y


def echo(y, taps=((.11, .22), (.23, .10))):
    out = np.concatenate([y, np.zeros(int(.3 * SR))])
    for d, g in taps:
        k = int(d * SR); out[k:k + len(y)] += g * y
    return out


def soften(y, cutoff=5200):
    a = np.exp(-2 * np.pi * cutoff / SR); b = 1 - a
    out = np.empty_like(y); s = 0.0
    for i, v in enumerate(y):
        s = b * v + a * s; out[i] = s
    return out


def finish(y, peak=.62):
    y = soften(y)
    n = int(.03 * SR); y[-n:] *= np.linspace(1, 0, n)
    return y / (np.abs(y).max() + 1e-9) * peak


CUES = {
    # selection and movement: tiny, quiet pearls
    'tap':    lambda: finish(pearl(A6), .38),
    'pick':   lambda: finish(pearl(D6), .42),
    'drop':   lambda: finish(mix(.25, [(0, pearl(A5), 1), (.05, pearl(D6, .14), .5)]), .42),
    'switch': lambda: finish(echo(mix(.3, [(0, glass(Fs6, .3, .08), 1)]), ((.09, .15),)), .34),
    # creation
    'spawn':  lambda: finish(echo(mix(.5, [(0, glass(D6, .5, .12), .8), (.07, glass(A6, .5, .12), .7)])), .52),
    'merge':  lambda: finish(echo(mix(.9, [(0, pluck(D5, .9, .45), 1), (.04, pluck(A5, .9, .4), .7), (.08, glass(D6, .7, .25), .4)])), .6),
    'sparkle':lambda: finish(mix(.45, [(0, glass(D7, .3, .06), .6), (.06, glass(B6, .3, .06), .5), (.12, glass(Fs6, .3, .06), .45)]), .4),
    'coin':   lambda: finish(mix(.4, [(0, glass(A6, .4, .1), .9), (.035, glass(D7, .3, .06), .4)]), .5),
    # packing and showing
    'box':    lambda: finish(echo(mix(.5, [(0, pluck(A5, .5, .2), 1), (.09, pluck(Fs5, .5, .22), .9)])), .5),
    'ribbon': lambda: finish(echo(mix(.7, [(i * .045, glass(n, .4, .1), .55) for i, n in enumerate([D6, E6, Fs6, A6, B6])])), .46),
    'tryon':  lambda: finish(echo(mix(1.2, [(0, pluck(D5, 1.2, .7), .7), (.0, glass(Fs6, 1.1, .45), .35), (.05, glass(A6, 1.0, .4), .3), (.1, glass(D7, .9, .35), .2)])), .52),
    # rewards
    'delivery': lambda: finish(echo(mix(1.1, [(i * .075, pluck(n, 1.0, .5), .85) for i, n in enumerate([D5, Fs5, A5, D6])])), .6),
    'level':  lambda: finish(echo(mix(1.8, [(i * .05, pluck(n, 1.3, .55), .6) for i, n in enumerate([D5, E5, Fs5, A5, B5, D6, E6, Fs6])] + [(.45, glass(D6, 1.3, .6), .35), (.45, glass(Fs6, 1.3, .6), .28), (.45, glass(A6, 1.3, .6), .22)])), .6),
    'unlock': lambda: finish(echo(mix(1.4, [(i * .06, glass(n, 1.2, .55), .5) for i, n in enumerate([D6, Fs6, A6, Cs6 + 12])])), .55),
    # not now: a low, soft two-note sigh
    'error':  lambda: finish(mix(.5, [(0, pluck(A4, .45, .18), .9), (.1, pluck(Fs5 - 12, .45, .2), .8)]), .3),
}


def write(name, y):
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'cue.wav'
        with wave.open(str(wav), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(np.clip(y * 32767, -32768, 32767).astype('<i2').tobytes())
        for ext, codec in [('ogg', ['-c:a', 'libvorbis', '-q:a', '4']), ('mp3', ['-c:a', 'libmp3lame', '-b:a', '96k'])]:
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav), *codec, str(OUT / f'{name}.{ext}')], check=True)


def main():
    for name, make in CUES.items():
        write(name, make())
    lines = ['Sweet Shoe Atelier — UI sound effects, CC0 1.0 public domain.',
             'Original compositions generated by dev/build-elegant-sfx.py (pure sine partials, no samples).',
             'License: https://creativecommons.org/publicdomain/zero/1.0/', '']
    lines += [f'{n}.ogg / {n}.mp3 <- original composition (CC0)' for n in CUES]
    (OUT / 'LICENSE.txt').write_text('\n'.join(lines) + '\n')
    print('PASS:', len(CUES), 'cues')


if __name__ == '__main__':
    main()
