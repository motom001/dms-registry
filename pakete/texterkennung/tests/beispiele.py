#!/usr/bin/env python3
"""
Zwei erfundene Scanseiten für den Test des Moduls (tests/modul_test.mjs), mit Pillow: seite-1.pgm aufrecht, seite-2.pgm
quer gescannt (90° gedreht) – so, wie GET …/seiten/{nr}/scan sie liefert – und woerter.json mit der Lage jedes Worts
relativ zur gelieferten Seite (0…1, oben links).

    python3 tests/beispiele.py <ordner>
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ZEILEN = [
    ['Stadtwerke', 'Musterstadt'],
    ['Rechnung', 'für', 'Lena', 'Muster'],
    ['Kundennummer', '4711'],
    ['Zahlbar', 'bis', 'zum', 'Monatsende'],
]


def seite(breite=1240, hoehe=1754):
    b = Image.new('L', (breite, hoehe), 255)
    z = ImageDraw.Draw(b)
    schrift = ImageFont.load_default(size=44)
    woerter, y = [], 300
    for zeile in ZEILEN:
        x = 120
        for wort in zeile:
            l, o, r, u = z.textbbox((x, y), wort, font=schrift)
            z.text((x, y), wort, fill=0, font=schrift)
            woerter.append([wort, l / breite, o / hoehe, (r - l) / breite, (u - o) / hoehe])
            x = r + 30
        y += 110
    return b, woerter


def main(ordner: Path):
    ordner.mkdir(parents=True, exist_ok=True)
    s1, w1 = seite()
    s1.save(ordner / 'seite-1.pgm')
    s2, w2 = seite()
    # Quer gescannt: die Seite liegt um 90° gegen den Uhrzeigersinn gedreht im Bild. Ein Punkt (x, y) der aufrechten
    # Seite liegt dann bei (y, 1 − x) im gelieferten Bild.
    s2.rotate(90, expand=True).save(ordner / 'seite-2.pgm')
    w2 = [[t, y, 1 - x - b, h, b] for t, x, y, b, h in w2]
    (ordner / 'woerter.json').write_text(json.dumps([w1, w2], ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(Path(sys.argv[1]))
