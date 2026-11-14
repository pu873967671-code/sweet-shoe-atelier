#!/usr/bin/env python3
"""Original UI icon set for Sweet Shoe Atelier (cute, rounded, one family).

Writes assets/icons/<name>.svg. Style: 24x24 grid, 2px rounded plum line,
one blush fill, rose for hearts/accents, a white highlight dot for shine.
Colours are baked in because the game shows icons through <img>.
usage: python3 dev/build-icons.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/icons'
LINE, BLUSH, ROSE, LILAC, GOLD, WHITE = '#5a3a52', '#ffd3e0', '#f06d98', '#ddd5f7', '#e8b75a', '#ffffff'
PEACH, CREAM, SKY, PINK = '#ffd2b8', '#fff1c7', '#cfe4ff', '#ff9fbf'

L = f'fill="none" stroke="{LINE}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
F = f'fill="{BLUSH}"'
R = f'fill="{ROSE}"'
V = f'fill="{LILAC}"'
G = f'fill="{GOLD}"'
W = f'fill="{WHITE}"'
HEART = 'M12 20.5s-7.5-4.4-7.5-10A4.2 4.2 0 0112 7.9a4.2 4.2 0 017.5 2.6c0 5.6-7.5 10-7.5 10z'


def heart(cx, cy, s):
    """Small heart centred at (cx, cy), size s."""
    return f'<path {R} d="M{cx} {cy + s * .55}s-{s * .7} -{s * .42} -{s * .7} -{s * .95}A{s * .4} {s * .4} 0 01{cx} {cy - s * .55}a{s * .4} {s * .4} 0 01{s * .7} {s * .17}c0 {s * .53}-{s * .7} {s * .95}-{s * .7} {s * .95}z"/>'


ICONS = {
    # navigation
    'atelier': f'<rect fill="{PEACH}" x="5" y="3.5" width="12" height="3.5" rx="1.5"/><rect fill="{PEACH}" x="5" y="17" width="12" height="3.5" rx="1.5"/><rect fill="{PINK}" x="7" y="7" width="8" height="10"/><path {L} d="M7 7v10M15 7v10"/><rect fill="none" stroke="{LINE}" stroke-width="2" x="5" y="3.5" width="12" height="3.5" rx="1.5"/><rect fill="none" stroke="{LINE}" stroke-width="2" x="5" y="17" width="12" height="3.5" rx="1.5"/><path fill="none" stroke="{WHITE}" stroke-width="1.4" stroke-linecap="round" d="M8.5 9l5 2M8.5 12l5 2"/><path {L} d="M19.5 3v14"/><circle fill="none" stroke="{LINE}" stroke-width="1.6" cx="19.5" cy="4.6" r=".9"/><path fill="none" stroke="{ROSE}" stroke-width="1.6" stroke-linecap="round" d="M15 12c2.5 0 4.5-2 4.5-5.5"/>',
    'clients': f'<path fill="{PEACH}" d="{HEART}"/><path {L} d="{HEART}"/><circle {W} cx="8.3" cy="10.2" r="1.1"/><circle {R} cx="9" cy="13.4" r=".9"/><circle {R} cx="15" cy="13.4" r=".9"/><path {L} d="M10.6 14.2q1.4 1.1 2.8 0"/>',
    'design': f'<path {V} d="M2.5 17.2Q2.4 14.4 6 14.1L10 13.7Q12.6 13.4 14.3 10.2L15.9 7.9Q17.4 6.1 19.2 7.3Q20.6 8.6 19.7 10.5L18.6 12.9L18.3 20.2H16.7L16.2 17.2Z"/><path {L} d="M2.5 17.2Q2.4 14.4 6 14.1L10 13.7Q12.6 13.4 14.3 10.2L15.9 7.9Q17.4 6.1 19.2 7.3Q20.6 8.6 19.7 10.5L18.6 12.9L18.3 20.2H16.7L16.2 17.2Z"/><path {L} d="M9.6 13.8q2.3 1.7 4.4-.4"/><circle {W} cx="5.6" cy="15.3" r=".9"/><path {G} d="M7 3.2l.8 1.9 1.9.8-1.9.8L7 8.6l-.8-1.9-1.9-.8 1.9-.8z"/>',
    'lookbook': f'<rect {V} x="7.5" y="4" width="12" height="15" rx="2.5" transform="rotate(9 13.5 11.5)"/><rect {F} x="4.5" y="3.5" width="12" height="15.5" rx="2.5"/><rect {L} x="4.5" y="3.5" width="12" height="15.5" rx="2.5"/><path fill="{WHITE}" d="M6.5 5.5h8v8.5h-8z"/>{heart(10.5, 9.8, 4.4)}<path {L} d="M7.5 16.5h6"/>',
    'boutique': f'<path fill="{CREAM}" d="M4.5 11h15v9h-15z"/><path {L} d="M3 10.5l2-5.5h14l2 5.5"/><path fill="{ROSE}" d="M3 10.5h18c0 1.5-1 2.3-2.3 2.3s-2.2-.8-2.2-2.3c0 1.5-1 2.3-2.2 2.3s-2.3-.8-2.3-2.3c0 1.5-1 2.3-2.2 2.3s-2.3-.8-2.3-2.3c0 1.5-1 2.3-2.2 2.3S3 12 3 10.5z"/><path {L} d="M4.5 12.5V20h15v-7.5M10 20v-4.5h4V20"/>',
    # resources and header
    'coin': f'<circle {G} cx="12" cy="12" r="8.6"/><circle fill="none" stroke="#c48d2e" stroke-width="2" cx="12" cy="12" r="8.6"/><circle fill="none" stroke="#fff3cf" stroke-width="1.3" cx="12" cy="12" r="5.8"/>{heart(12, 12.2, 5)}<circle {W} cx="8.2" cy="8.3" r="1.2"/>',
    'star': f'<path fill="#ffd970" stroke="#d99a2b" stroke-width="2" stroke-linejoin="round" d="M12 2.8l2.6 5.6 6.1.7-4.6 4.1 1.3 6-5.4-3.1-5.4 3.1 1.3-6-4.6-4.1 6.1-.7z"/><circle {W} cx="10" cy="9" r="1.1"/><circle fill="#f6a3b8" cx="9.3" cy="13" r=".9"/><circle fill="#f6a3b8" cx="14.7" cy="13" r=".9"/>',
    'gem': f'<path fill="#c9b8fb" d="M7 4h10l4 5.2-9 11L3 9.2z"/><path fill="none" stroke="#7a5cc4" stroke-width="2" stroke-linejoin="round" d="M7 4h10l4 5.2-9 11L3 9.2zM3 9.2h18M9 9.2l3 11 3-11M7 4l2 5.2L12 4l3 5.2L17 4"/><path {W} d="M8 6l1 2.4-2.8.1z"/>',
    'energy': f'<path fill="#ffe27a" d="M13.5 2.5L5 13.5h6l-1.3 8 8.3-11h-6z"/><path fill="none" stroke="#d99a2b" stroke-width="2" stroke-linejoin="round" d="M13.5 2.5L5 13.5h6l-1.3 8 8.3-11h-6z"/>',
    'heart': f'<path {R} d="{HEART}"/><path fill="none" stroke="#c94174" stroke-width="2" stroke-linejoin="round" d="{HEART}"/><circle {W} cx="8.4" cy="10.2" r="1.3"/>',
    'clock': f'<circle fill="{CREAM}" cx="12" cy="13" r="8"/><circle fill="none" stroke="{LINE}" stroke-width="2" cx="12" cy="13" r="8"/><path {L} d="M12 9v4l2.5 1.8M9 2.8h6M12 2.8v2.2"/><circle {R} cx="12" cy="13" r="1.1"/>',
    'gift': f'<rect {F} x="4" y="10" width="16" height="10.5" rx="2"/><rect fill="{BLUSH}" x="3" y="7" width="18" height="4" rx="1.5"/><path {L} d="M4 11v7.5a2 2 0 002 2h12a2 2 0 002-2V11M3 7h18v4H3zM12 7v13.5"/><path fill="{ROSE}" stroke="{LINE}" stroke-width="1.6" stroke-linejoin="round" d="M12 7C10 3.2 6.6 4 7.4 6c.4 1 2.4 1 4.6 1zM12 7c2-3.8 5.4-3 4.6-1-.4 1-2.4 1-4.6 1z"/>',
    'music': f'<path {L} d="M9.5 17.5V5.5l10-2v11"/><circle {F} cx="7" cy="17.5" r="2.7"/><circle fill="none" stroke="{LINE}" stroke-width="2" cx="7" cy="17.5" r="2.7"/><circle {F} cx="17" cy="14.5" r="2.7"/><circle fill="none" stroke="{LINE}" stroke-width="2" cx="17" cy="14.5" r="2.7"/>',
    'music-off': f'<path fill="none" stroke="#b9a7b4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M9.5 17.5V5.5l10-2v11"/><circle fill="none" stroke="#b9a7b4" stroke-width="2" cx="7" cy="17.5" r="2.7"/><circle fill="none" stroke="#b9a7b4" stroke-width="2" cx="17" cy="14.5" r="2.7"/><path {L} d="M4 4l16 16"/>',
    'pause': f'<rect {F} x="3" y="3" width="18" height="18" rx="9"/><path {L} d="M10 8.8v6.4M14 8.8v6.4"/>',
    'lock': f'<rect {V} x="5" y="10.5" width="14" height="10" rx="3"/><rect fill="none" stroke="{LINE}" stroke-width="2" x="5" y="10.5" width="14" height="10" rx="3"/><path {L} d="M8.5 10.5V8a3.5 3.5 0 017 0v2.5"/>{heart(12, 15.6, 3.2)}',
    'share': f'<path {F} d="M17 13.5v4a2.5 2.5 0 01-2.5 2.5h-8A2.5 2.5 0 014 17.5v-8A2.5 2.5 0 016.5 7h4"/><path {L} d="M17 13.5v4a2.5 2.5 0 01-2.5 2.5h-8A2.5 2.5 0 014 17.5v-8A2.5 2.5 0 016.5 7h4M14 4h6v6M20 4l-8 8"/>',
    'fitting': f'<rect {F} x="3" y="7.5" width="18" height="12.5" rx="3.5"/><rect fill="none" stroke="{LINE}" stroke-width="2" x="3" y="7.5" width="18" height="12.5" rx="3.5"/><path {L} d="M8.2 7.5l1.5-3h4.6l1.5 3"/><circle {W} cx="12" cy="13.7" r="3.6"/><circle fill="none" stroke="{LINE}" stroke-width="2" cx="12" cy="13.7" r="3.6"/><circle {R} cx="17.6" cy="10.6" r=".9"/>',
    # design categories
    'color': f'<path fill="{SKY}" d="M12 3s6.2 6.6 6.2 10.9A6.2 6.2 0 015.8 13.9C5.8 9.6 12 3 12 3z"/><path {L} d="M12 3s6.2 6.6 6.2 10.9A6.2 6.2 0 015.8 13.9C5.8 9.6 12 3 12 3z"/><circle {W} cx="9.5" cy="13.5" r="1.4"/><circle {R} cx="14.3" cy="16" r="1.4"/>',
    'material': f'<path fill="{LILAC}" d="M8 6h12v10H8z"/><path {L} d="M8 6h12v10H8"/><ellipse fill="{PINK}" cx="7" cy="11" rx="4" ry="5.5"/><ellipse fill="none" stroke="{LINE}" stroke-width="2" cx="7" cy="11" rx="4" ry="5.5"/><ellipse fill="{WHITE}" cx="7" cy="11" rx="1.4" ry="2"/><path fill="none" stroke="{WHITE}" stroke-width="1.4" stroke-linecap="round" d="M12 9h5M12 12.5h6"/><path {L} d="M8 16.5v3h12v-3.5"/>',
    'pattern': f'<circle fill="{PEACH}" cx="12" cy="12" r="8.6"/><circle fill="none" stroke="{LINE}" stroke-width="2" cx="12" cy="12" r="8.6"/>{heart(9, 9.2, 3.6)}{heart(15.4, 14.2, 3.6)}<circle {W} cx="15.4" cy="8.4" r="1.5"/><circle {W} cx="8.6" cy="15.4" r="1.5"/>',
    'strap': f'<rect fill="{LILAC}" x="2.5" y="9" width="19" height="6" rx="3"/><rect fill="none" stroke="{LINE}" stroke-width="2" x="2.5" y="9" width="19" height="6" rx="3"/><rect fill="none" stroke="{GOLD}" stroke-width="2" x="5.5" y="7.5" width="5" height="9" rx="1.6"/><path stroke="{GOLD}" stroke-width="2" stroke-linecap="round" d="M8 9.5v5"/><circle fill="{LINE}" cx="14" cy="12" r="1"/><circle fill="{LINE}" cx="17.5" cy="12" r="1"/>',
    'decoration': f'<path fill="{PINK}" d="M12 12L4 7v10zM12 12l8-5v10z"/><path {L} d="M12 12L4 7v10zM12 12l8-5v10z"/><rect fill="{ROSE}" stroke="{LINE}" stroke-width="1.6" x="10.4" y="9.8" width="3.2" height="4.4" rx="1.3"/><path {L} d="M11 14.5l-1.6 5.5M13 14.5l1.6 5.5"/>',
    'heel': f'<path {F} d="M2.5 17.2Q2.4 14.4 6 14.1L10 13.7Q12.6 13.4 14.3 10.2L15.9 7.9Q17.4 6.1 19.2 7.3Q20.6 8.6 19.7 10.5L18.6 12.9L18.3 20.2H16.7L16.2 17.2Z"/><path {L} d="M2.5 17.2Q2.4 14.4 6 14.1L10 13.7Q12.6 13.4 14.3 10.2L15.9 7.9Q17.4 6.1 19.2 7.3Q20.6 8.6 19.7 10.5L18.6 12.9L18.3 20.2H16.7L16.2 17.2Z"/><path fill="none" stroke="{ROSE}" stroke-width="2" stroke-linecap="round" d="M3.6 17.6h12.3"/><circle {W} cx="5.6" cy="15.3" r=".9"/>',
    'charm': f'<path fill="{GOLD}" stroke="{LINE}" stroke-width="1.6" stroke-linejoin="round" d="M8.5 6.5l3.5-3 3.5 3-1.2 1.5h-4.6z"/><circle fill="#fbf6ff" cx="12" cy="14" r="6.5"/><circle fill="{LILAC}" cx="13.6" cy="15.8" r="4.2"/><circle fill="#fbf6ff" cx="11.3" cy="13.2" r="4.2"/><circle fill="none" stroke="{LINE}" stroke-width="2" cx="12" cy="14" r="6.5"/><circle {W} cx="9.6" cy="11.6" r="1.8"/><circle fill="{BLUSH}" cx="14.6" cy="17" r="1.1"/>',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in ICONS.items():
        (OUT / f'{name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48">{body}</svg>\n')
    print(f'PASS: {len(ICONS)} icons -> {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
