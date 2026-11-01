#!/usr/bin/env python3
"""Erzeugt das Trennblatt zum Ausdrucken (PDF, A4) – nur mit der Standardbibliothek.

    python3 vorlage/trennblatt.py                              # vorlage/trennblatt.pdf mit DMS-TRENNEN
    python3 vorlage/trennblatt.py --text MEIN-CODE ziel.pdf    # eigener Barcode-Inhalt (Einstellung im DMS anpassen)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf import A4, MM, Seite, code128_breite, schreibe  # noqa: E402

STANDARD = 'DMS-TRENNEN'
MODUL = 0.6 * MM      # Modulbreite: liest sich schon ab 150 dpi sicher
HOEHE = 28 * MM       # hohe Striche: auch ein schief eingezogenes Blatt kreuzt jede Abtastzeile alle Striche


def trennblatt(text: str = STANDARD) -> Seite:
    s = Seite()
    b, h = A4
    links = 25 * MM
    s.rechteck(0, h - 14 * MM, b, 14 * MM)                     # schwarzer Rand oben: im Papierstapel gut zu sehen
    s.text(links, h - 42 * MM, 40, 'TRENNBLATT', fett=True)
    s.text(links, h - 52 * MM, 13, 'Hier beginnt ein neuer Brief.')
    breite = code128_breite(text, MODUL)
    x = (b - breite) / 2
    for y in (h - 100 * MM, 52 * MM):
        s.barcode(x, y, text, MODUL, HOEHE)
        s.text(x, y - 6 * MM, 10, text, grau=0.35)
    zeilen = [
        ('So geht’s', True),
        ('1. Lege ein Trennblatt zwischen je zwei Briefe (vor den ersten brauchst du keins).', False),
        ('2. Scanne den ganzen Stapel auf einmal – er kommt als eine Post ins DMS.', False),
        ('3. Das Paket „Trennblatt“ teilt den Scan an jedem Trennblatt in eigene Posts', False),
        ('    und lässt die Trennblätter weg (auch eine leere Rückseite beim beidseitigen Scan).', False),
        ('', False),
        ('Archivnummer: Klebst du einen Archivnummer-Aufkleber des DMS auf einen Brief,', False),
        ('bekommt dessen Post diese Nummer gleich mit.', False),
        ('', False),
        ('Drucken mit 100 % (nicht „an Seite anpassen“). Das Blatt kannst du immer wieder verwenden.', False),
    ]
    y = h - 128 * MM
    for t, fett in zeilen:
        if t:
            s.text(links, y, 12 if fett else 10.5, t, fett=fett, grau=0 if fett else 0.15)
        y -= 6.2 * MM
    s.text(links, 18 * MM, 8, f'Barcode (Code 128): {text}  ·  Paket „Trennblatt“ für das DMS', grau=0.45)
    return s


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--text', default=STANDARD, help=f'Inhalt des Barcodes (Standard {STANDARD})')
    a.add_argument('ziel', nargs='?', default=str(Path(__file__).resolve().parent / 'trennblatt.pdf'))
    args = a.parse_args()
    Path(args.ziel).write_bytes(schreibe([trennblatt(args.text)], 'Trennblatt'))
    print(args.ziel)


if __name__ == '__main__':
    main()
