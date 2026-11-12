#!/usr/bin/env python3
"""Künstliche Scans für die Tests des Pakets Leerseiten (dms #997) – ohne Bibliotheken, immer dieselben Bytes.

    python3 tests/scans.py <ordner>

Schreibt <ordner>/scans.pdf: ein beidseitiger Scan, A4, Graustufen mit 100 dpi, Papier leicht grau und verrauscht wie
aus einem Einzugsscanner. Inhalte sind erfunden (Blöcke statt Text, keine Namen, keine Anschriften). Die Seiten:

  1  Vorderseite eines Briefs (Textzeilen)                       → Inhalt
  2  leere Rückseite                                             → leer
  3  leere Rückseite mit Lochung (zwei Löcher) und Schatten       → leer
  4  fast leer: Bleistiftnotiz (kleine Schleife und Strich)       → Inhalt, bei „streng“ leer
  5  fast leer: Eingangsstempel                                  → Inhalt
  6  Rückseite mit durchscheinender Schrift (gespiegelt, blass)   → Inhalt bei „vorsichtig“, sonst leer
  7  leer mit Staub (einzelne Punkte)                            → leer
  8  zweite Seite eines Briefs (wenige Zeilen unten)             → Inhalt

Dazu <ordner>/leer.pdf (eine leere Seite) für „ganz leer“ und <ordner>/brief.pdf (zwei Seiten Inhalt).
"""
import math
import sys
import zlib
from pathlib import Path

DPI = 100
B, H = 827, 1169  # A4 mit 100 dpi
MM = DPI / 25.4


class Zufall:
    """Kleiner fester Zufall (LCG), damit die Dateien immer gleich sind."""

    def __init__(self, s: int):
        self.s = s

    def zahl(self) -> float:
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF


def papier(z: Zufall, ton: int = 244) -> bytearray:
    """Papier mit leichtem Rauschen (±3) und etwas dunklerem Rand oben (Einzug)."""
    px = bytearray(B * H)
    for y in range(H):
        grund = ton - (4 if y < 8 else 0)
        for x in range(B):
            px[y * B + x] = max(0, min(255, grund + int(z.zahl() * 7) - 3))
    return px


def rechteck(px: bytearray, x0: float, y0: float, b: float, h: float, wert: int):
    for y in range(max(0, int(y0)), min(H, int(y0 + h))):
        for x in range(max(0, int(x0)), min(B, int(x0 + b))):
            px[y * B + x] = min(px[y * B + x], wert)


def kreis(px: bytearray, cx: float, cy: float, r: float, wert: int):
    for y in range(max(0, int(cy - r)), min(H, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(B, int(cx + r) + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px[y * B + x] = wert


def linie(px: bytearray, punkte: list[tuple[float, float]], dicke: float, wert: int):
    for (xa, ya), (xb, yb) in zip(punkte, punkte[1:]):
        n = int(max(abs(xb - xa), abs(yb - ya)) * 2) + 1
        for i in range(n + 1):
            x, y = xa + (xb - xa) * i / n, ya + (yb - ya) * i / n
            rechteck(px, x - dicke / 2, y - dicke / 2, dicke, dicke, wert)


def zeilen(px: bytearray, z: Zufall, y0_mm: float, anzahl: int, wert: int, gespiegelt: bool = False):
    """Textzeilen als Wortblöcke: 2,5 mm hoch, Wörter 4–22 mm lang, 6 mm Zeilenabstand."""
    for i in range(anzahl):
        y = (y0_mm + i * 6) * MM
        x = 25 * MM
        ende = (185 if i % 5 != 4 else 120) * MM
        while x < ende:
            lang = (4 + z.zahl() * 18) * MM
            if gespiegelt:
                rechteck(px, B - x - lang, y, lang, 2.5 * MM, wert)
            else:
                rechteck(px, x, y, lang, 2.5 * MM, wert)
            x += lang + 2 * MM


def seiten(z: Zufall) -> list[bytearray]:
    s = []
    # 1 Vorderseite eines Briefs
    p = papier(z)
    rechteck(p, 25 * MM, 20 * MM, 60 * MM, 12 * MM, 60)  # Briefkopf
    zeilen(p, z, 60, 6, 40)
    zeilen(p, z, 110, 18, 40)
    s.append(p)
    # 2 leere Rückseite
    s.append(papier(z))
    # 3 Lochung (Löcher dunkel – der Deckel des Scanners ist schwarz) und Schatten am rechten Rand
    p = papier(z)
    for cy in (148.5 - 40, 148.5 + 40):
        kreis(p, 12 * MM, cy * MM, 3 * MM, 25)
    rechteck(p, B - 4, 0, 4, H, 90)
    s.append(p)
    # 4 Bleistiftnotiz: kleine Schleife („ok“) und ein kurzer Strich darunter, grau
    p = papier(z)
    cx, cy = 150 * MM, 60 * MM
    schleife = [(cx + 3 * MM * math.cos(t / 10), cy + 2.5 * MM * math.sin(t / 10)) for t in range(0, 63)]
    linie(p, schleife, 1.6, 150)
    linie(p, [(cx + 5 * MM, cy - 3 * MM), (cx + 5 * MM, cy + 3 * MM), (cx + 9 * MM, cy - 2 * MM)], 1.6, 150)
    linie(p, [(cx - 4 * MM, cy + 5 * MM), (cx + 12 * MM, cy + 5.5 * MM)], 1.6, 160)
    s.append(p)
    # 5 Eingangsstempel: Rahmen 45 × 18 mm mit zwei Zeilen
    p = papier(z)
    x0, y0 = 130 * MM, 30 * MM
    for (a, b, c, d) in ((0, 0, 45, 0.6), (0, 17.4, 45, 0.6), (0, 0, 0.6, 18), (44.4, 0, 0.6, 18)):
        rechteck(p, x0 + a * MM, y0 + b * MM, c * MM, d * MM, 110)
    rechteck(p, x0 + 4 * MM, y0 + 4 * MM, 37 * MM, 3 * MM, 120)
    rechteck(p, x0 + 10 * MM, y0 + 10 * MM, 25 * MM, 3 * MM, 120)
    s.append(p)
    # 6 durchscheinende Schrift: gespiegelt, sehr blass (Kontrast etwa 25)
    p = papier(z)
    zeilen(p, z, 60, 6, 219, gespiegelt=True)
    zeilen(p, z, 110, 18, 219, gespiegelt=True)
    s.append(p)
    # 7 Staub: einzelne dunkle Punkte, je 1 Bildpunkt
    p = papier(z)
    for _ in range(25):
        x, y = int(40 + z.zahl() * (B - 80)), int(40 + z.zahl() * (H - 80))
        p[y * B + x] = 90
    s.append(p)
    # 8 zweite Seite: drei Zeilen und ein Gruß
    p = papier(z)
    zeilen(p, z, 30, 3, 40)
    rechteck(p, 25 * MM, 60 * MM, 40 * MM, 2.5 * MM, 40)
    s.append(p)
    return s


def pdf(bilder: list[bytearray]) -> bytes:
    """PDF mit einem Graustufenbild (Flate) je Seite, A4."""
    objekte: list[bytes] = []
    seiten_ids = []
    n = 3
    for _ in bilder:
        seiten_ids.append(n)
        n += 3
    objekte.append(b'<< /Type /Catalog /Pages 2 0 R >>')
    objekte.append(b'<< /Type /Pages /Kids [' + b' '.join(f'{i} 0 R'.encode() for i in seiten_ids) + f'] /Count {len(bilder)} >>'.encode())
    for i, px in zip(seiten_ids, bilder):
        inhalt = b'q 595.28 0 0 841.89 0 0 cm /Bild Do Q'
        daten = zlib.compress(bytes(px), 9)
        objekte.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Resources << /XObject << /Bild {i + 1} 0 R >> >> /Contents {i + 2} 0 R >>'.encode())
        objekte.append(f'<< /Type /XObject /Subtype /Image /Width {B} /Height {H} /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode /Length {len(daten)} >>\nstream\n'.encode() + daten + b'\nendstream')
        objekte.append(f'<< /Length {len(inhalt)} >>\nstream\n'.encode() + inhalt + b'\nendstream')
    aus = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    lagen = []
    for k, o in enumerate(objekte, 1):
        lagen.append(len(aus))
        aus += f'{k} 0 obj\n'.encode() + o + b'\nendobj\n'
    xref = len(aus)
    aus += f'xref\n0 {len(objekte) + 1}\n0000000000 65535 f \n'.encode()
    for l in lagen:
        aus += f'{l:010d} 00000 n \n'.encode()
    aus += f'trailer\n<< /Size {len(objekte) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    return bytes(aus)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    ziel = Path(sys.argv[1])
    ziel.mkdir(parents=True, exist_ok=True)
    s = seiten(Zufall(997))
    (ziel / 'scans.pdf').write_bytes(pdf(s))
    (ziel / 'leer.pdf').write_bytes(pdf([s[1]]))
    (ziel / 'brief.pdf').write_bytes(pdf([s[0], s[7]]))
    print(f'{ziel}/scans.pdf, leer.pdf, brief.pdf')


if __name__ == '__main__':
    main()
