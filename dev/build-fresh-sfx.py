#!/usr/bin/env python3
"""Compose every UI cue for Sweet Shoe Atelier: fresh, soft, low-register.

Replaces dev/build-elegant-sfx.py, whose high glass bells (A6-D7) read as a
sharp "ding-ding-ding". Every cue here sits roughly an octave lower and uses
rounded timbres:
  wood   a soft marimba knock (fundamental + the bar's 4x partial, fast decay)
  drop   a water-drop / bubble pop: a sine that glides gently upward
  felt   a felted pluck: warm fundamental, quick-fading upper partials
No noise, no stacked high arpeggios: taps are one note, rewards at most a
short gentle interval or a slow broken chord. D major, so cues belong together.
A gentle low-pass (3.4 kHz) keeps every cue round. Original, CC0.
Writes assets/sfx/<name>.ogg / .mp3 and LICENSE.txt.  usage: python3 dev/build-fresh-sfx.py
"""
import subprocess, tempfile, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/sfx'
SR = 44100


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


D4, E4, Fs4, A4, B4, D5, E5, Fs5, A5, B5, D6 = 62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t / decay), t


def wood(note, dur=.35, decay=.09):
    """Soft marimba knock: round, short, no ring."""
    n = int(dur * SR); e, t = env(n, .003, decay); f = hz(note)
    y = np.sin(2 * np.pi * f * t) + .22 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t / .02)
    return y * e


def drop(note, dur=.22, rise=.35):
    """Water-drop pop: a sine gliding upward and fading fast."""
    n = int(dur * SR); e, t = env(n, .002, .05)
    f = hz(note) * (1 + rise * (1 - np.exp(-t / .04)))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * e


def felt(note, dur=1.0, decay=.4):
    """Felted pluck: warm and mellow, upper partials fade almost at once."""
    n = int(dur * SR); e, t = env(n, .006, decay); f = hz(note)
    y = (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / .08)
         + .08 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / .04))
    return y * e


def mix(total, parts):
    y = np.zeros(int(total * SR))
    for start, sig, g in parts:
        i = int(start * SR); j = min(len(y), i + len(sig)); y[i:j] += g * sig[:j - i]
    return y


def room(y, taps=((.07, .16), (.15, .07))):
    out = np.concatenate([y, np.zeros(int(.25 * SR))])
    for d, g in taps:
        k = int(d * SR); out[k:k + len(y)] += g * y
    return out


def soften(y, cutoff=3400):
    a = np.exp(-2 * np.pi * cutoff / SR); b = 1 - a; out = np.empty_like(y); s = 0.0
    for i, v in enumerate(y):
        s = b * v + a * s; out[i] = s
    return out


def finish(y, peak):
    y = soften(y); n = int(.03 * SR); y[-n:] *= np.linspace(1, 0, n)
    return y / (np.abs(y).max() + 1e-9) * peak


CUES = {
    # buttons and selection: one soft note each
    'tap':     lambda: finish(wood(A4, .25, .06), .42),
    'switch':  lambda: finish(wood(D5, .25, .055), .36),
    'pick':    lambda: finish(drop(Fs4), .4),
    'drop':    lambda: finish(wood(D4, .3, .07), .42),
    'error':   lambda: finish(mix(.45, [(0, felt(Fs4, .4, .12), .9), (.11, felt(D4, .4, .14), .8)]), .28),
    # making things
    'spawn':   lambda: finish(room(drop(A4, .25, .3)), .45),
    'merge':   lambda: finish(room(mix(.6, [(0, wood(D5, .4, .1), .9), (.06, felt(A4, .55, .25), .6)])), .52),
    'sparkle': lambda: finish(room(mix(.4, [(0, drop(D5, .2, .25), .6), (.08, drop(Fs5, .2, .2), .45)])), .36),
    'coin':    lambda: finish(mix(.35, [(0, wood(A5, .3, .07), .8), (.05, wood(D6, .25, .05), .35)]), .38),
    # packing and showing
    'box':     lambda: finish(room(mix(.45, [(0, wood(A4, .35, .08), 1), (.08, wood(Fs4, .35, .09), .8)])), .48),
    'ribbon':  lambda: finish(room(mix(.6, [(i * .07, felt(n, .45, .18), .6) for i, n in enumerate([D5, E5, Fs5])])), .42),
    'tryon':   lambda: finish(room(mix(1.2, [(0, felt(D4, 1.1, .6), .7), (.09, felt(A4, 1.0, .5), .5), (.18, felt(Fs5, .9, .45), .32)])), .48),
    # rewards: a slow, warm broken chord, never a high run
    'delivery':lambda: finish(room(mix(1.0, [(i * .1, felt(n, .9, .4), .75) for i, n in enumerate([D4, Fs4, A4, D5])])), .55),
    'level':   lambda: finish(room(mix(1.6, [(i * .11, felt(n, 1.2, .5), .6) for i, n in enumerate([D4, Fs4, A4, B4, D5])] + [(.6, felt(Fs5, 1.0, .5), .25)])), .55),
    'unlock':  lambda: finish(room(mix(1.2, [(0, felt(A4, 1.0, .45), .7), (.12, felt(D5, 1.0, .45), .6), (.24, drop(Fs5, .25, .2), .3)])), .5),
}


def write(name, y):
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'cue.wav'
        with wave.open(str(wav), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(np.clip(y * 32767, -32768, 32767).astype('<i2').tobytes())
        for ext, codec in [('ogg', ['-c:a', 'libvorbis', '-q:a', '4']), ('mp3', ['-c:a', 'libmp3lame', '-b:a', '96k'])]:
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav), *codec, str(OUT / f'{name}.{ext}')], check=True)


def centroid(y):
    s = np.abs(np.fft.rfft(y)); f = np.fft.rfftfreq(len(y), 1 / SR)
    return float((s * f).sum() / (s.sum() + 1e-9))


def main():
    for name, make in CUES.items():
        y = make(); write(name, y)
        print(f'{name:9s} {len(y)/SR:.2f}s  brightness {centroid(y):6.0f} Hz')
    lines = ['Sweet Shoe Atelier — UI sound effects, CC0 1.0 public domain.',
             'Original compositions generated by dev/build-fresh-sfx.py (pure sine partials, no samples).',
             'License: https://creativecommons.org/publicdomain/zero/1.0/', '']
    lines += [f'{n}.ogg / {n}.mp3 <- original composition (CC0)' for n in CUES]
    (OUT / 'LICENSE.txt').write_text('\n'.join(lines) + '\n')
    print('PASS:', len(CUES), 'cues')


if __name__ == '__main__':
    main()
