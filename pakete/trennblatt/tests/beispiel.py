#!/usr/bin/env python3
"""Beispiel-PDFs für die Tests (erfundene Briefe, keine echten Daten) – nur Standardbibliothek, für die
„gescannte“ Fassung zusätzlich pdftoppm (Poppler, wie im DMS).

    python3 tests/beispiel.py <ordner>

Legt an:
  sammelscan.pdf           Brief A · Trennblatt · Brief B (Archivnummer-Aufkleber DMS-ASN:A-000123) · Trennblatt · Brief C
  sammelscan-gescannt.pdf  dasselbe beidseitig gescannt: nach jedem Trennblatt seine leere Rückseite, Brief C mit zwei
                           Seiten; jede Seite als Bild (300 dpi), leicht schief, grauer Hintergrund, Staub
  ohne-trennblatt.pdf      Brief A · Brief B (mit Aufkleber) – nichts zu teilen
"""
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / 'vorlage'))
from pdf import A4, MM, Seite, code128b, schreibe  # noqa: E402
from trennblatt import trennblatt  # noqa: E402

ASN = 'A-000123'


def brief(absender: str, betreff: str, seite: int = 1, asn: str | None = None) -> Seite:
    s = Seite()
    b, h = A4
    x = 25 * MM
    s.text(x, h - 30 * MM, 9, f'{absender} · Musterweg 1 · 12345 Musterstadt', grau=0.3)
    s.text(x, h - 50 * MM, 11, 'Familie Beispiel')
    s.text(x, h - 55 * MM, 11, 'Beispielstraße 7')
    s.text(x, h - 60 * MM, 11, '01234 Beispielhausen')
    s.text(x, h - 85 * MM, 12, betreff + (f' (Seite {seite})' if seite > 1 else ''), fett=True)
    zufall = random.Random(betreff + str(seite))
    woerter = 'Sehr geehrte Damen und Herren hiermit erhalten Sie die Unterlagen zu Ihrem Vertrag Bitte prüfen Sie die Angaben ' \
              'und überweisen Sie den Betrag bis zum Monatsende Für Rückfragen stehen wir Ihnen gern zur Verfügung'.split()
    y = h - 100 * MM
    for _ in range(22):
        s.text(x, y, 10.5, ' '.join(zufall.choice(woerter) for _ in range(12)))
        y -= 6 * MM
    s.text(x, 40 * MM, 10.5, 'Mit freundlichen Grüßen')
    s.text(x, 30 * MM, 10.5, absender)
    if asn:
        # Aufkleber 48,5 × 25,4 mm wie aus dem DMS (Werkbank → Nummernkreise): Modul so breit, wie es passt.
        w, hh = 48.5 * MM, 25.4 * MM
        x0, y0 = b - 20 * MM - w, h - 45 * MM
        breiten = code128b('DMS-ASN:' + asn)
        modul = min((w - 4 * MM) / (sum(breiten) + 20), 0.5 * MM)
        s.rahmen(x0, y0, w, hh, grau=0.7, staerke=0.3)
        s.barcode(x0 + (w - (sum(breiten) + 20) * modul) / 2 + 10 * modul, y0 + 11 + 3 * MM, 'DMS-ASN:' + asn, modul, hh - 11 - 5 * MM)
        s.text(x0 + w / 2 - 15, y0 + 2 * MM, 11, asn, fett=True)
    return s


def leer() -> Seite:
    return Seite()


def sammelscan() -> list[Seite]:
    return [brief('Stadtwerke Beispiel', 'Jahresabrechnung Strom'), trennblatt(),
            brief('Versicherung Muster AG', 'Beitragsrechnung', asn=ASN), trennblatt(),
            brief('Praxis Dr. Beispiel', 'Rechnung')]


def gescannt_vorlage() -> list[Seite]:
    return [brief('Stadtwerke Beispiel', 'Jahresabrechnung Strom'), trennblatt(), leer(),
            brief('Versicherung Muster AG', 'Beitragsrechnung', asn=ASN), trennblatt(), leer(),
            brief('Praxis Dr. Beispiel', 'Rechnung'), brief('Praxis Dr. Beispiel', 'Rechnung', seite=2)]


def pgm(pfad: Path) -> tuple[int, int, bytes]:
    d = pfad.read_bytes()
    teile = d.split(maxsplit=4)
    return int(teile[1]), int(teile[2]), teile[4][: int(teile[1]) * int(teile[2])]


def schief(w: int, h: int, px: bytes, winkel_grad: float, weiss: int) -> bytes:
    """Kleine Drehung als zwei Scherungen (zeilen- und spaltenweise verschieben) – schnell genug ohne Fremdpakete."""
    import math
    t = math.tan(math.radians(winkel_grad))
    zeilen = bytearray()
    for y in range(h):
        d = round((y - h / 2) * t)
        z = px[y * w:(y + 1) * w]
        z = (bytes([weiss]) * d + z[:w - d]) if d >= 0 else (z[-d:] + bytes([weiss]) * -d)
        zeilen += z
    aus = bytearray(w * h)
    for x in range(w):
        d = round(-(x - w / 2) * t)
        sp = bytes(zeilen[x::w])
        sp = (bytes([weiss]) * d + sp[:h - d]) if d >= 0 else (sp[-d:] + bytes([weiss]) * -d)
        aus[x::w] = sp
    return bytes(aus)


def scanne(seiten: list[Seite], ordner: Path) -> list[Seite]:
    """Seiten wie ein Einzugsscanner: gerastert (300 dpi), schief, grauer Hintergrund, Staub."""
    dpi = 300
    zufall = random.Random(16)
    with tempfile.TemporaryDirectory() as tmp:
        q = Path(tmp) / 'q.pdf'
        q.write_bytes(schreibe(seiten))
        subprocess.run(['pdftoppm', '-gray', '-r', str(dpi), str(q), str(Path(tmp) / 's')], check=True)
        bilder = sorted(Path(tmp).glob('s-*.pgm'))
        aus = []
        grau = bytes(min(255, 20 + v * 218 // 255) for v in range(256))  # Papier grau, Schwarz nicht ganz schwarz
        for i, p in enumerate(bilder):
            w, h, px = pgm(p)
            px = schief(w, h, px.translate(grau), (-1.6, 2.2, -0.7, 1.1, -2.5, 0.4, 1.8, -1.2)[i % 8], 238)
            px = bytearray(px)
            for _ in range(w * h // 2500):  # Staub und Fussel
                pos = zufall.randrange(w * h)
                px[pos] = zufall.choice((25, 60, 120))
            s = Seite()
            s.bild(0, 0, A4[0], A4[1], w, h, bytes(px))
            aus.append(s)
        return aus


def main():
    ziel = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / 'sammelscan.pdf').write_bytes(schreibe(sammelscan(), 'Sammelscan'))
    (ziel / 'ohne-trennblatt.pdf').write_bytes(schreibe([sammelscan()[0], sammelscan()[2]], 'Ohne Trennblatt'))
    (ziel / 'sammelscan-gescannt.pdf').write_bytes(schreibe(scanne(gescannt_vorlage(), ziel), 'Sammelscan gescannt'))
    print(ziel)


if __name__ == '__main__':
    main()
