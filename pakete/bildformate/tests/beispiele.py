#!/usr/bin/env python3
"""
Testbilder für das Paket Bildformate (erfunden, mit Pillow erzeugt) und der Vergleich der Fassungen mit ihnen.

    python3 tests/beispiele.py erzeuge <ordner>      # Testbilder anlegen
    python3 tests/beispiele.py vergleiche <ordner>   # Fassungen (<name>.fassung) mit den Testbildern vergleichen

Vergleich: Die Bilder im PDF holt pdfimages heraus, die Seitengröße pdfinfo; PNG und JPEG liest Pillow. Schwarzweiß und PNG müssen genau stimmen, JPEG höchstens im Mittel um 3 bis 4 von 255 abweichen.
"""
import io
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageStat


def brief(breite, hoehe, modus='L', farbe=False):
    """Eine erfundene Briefseite: Kopf, Zeilen als Balken, ein Kasten."""
    b = Image.new('RGB', (breite, hoehe), 'white')
    z = ImageDraw.Draw(b)
    z.rectangle([breite // 10, hoehe // 12, breite // 2, hoehe // 12 + hoehe // 40], fill=(30, 60, 160) if farbe else 'black')
    for i in range(12):
        y = hoehe // 5 + i * hoehe // 30
        z.rectangle([breite // 10, y, breite * (6 + i % 3) // 10, y + hoehe // 120], fill='black')
    z.text((breite // 10, hoehe * 3 // 4), 'Stadtwerke Musterstadt - Rechnung 2026-11', fill='black')
    if farbe:
        z.ellipse([breite * 7 // 10, hoehe // 15, breite * 9 // 10, hoehe // 15 + breite // 5], fill=(200, 40, 40))
    return b.convert(modus) if modus != 'RGB' else b


def erzeuge(ordner: Path):
    ordner.mkdir(parents=True, exist_ok=True)
    # Zwei Seiten Schwarzweiß (CCITT G4) mit 200 dpi – wie ein Dokumentenscanner.
    s1, s2 = brief(1654, 2339, '1'), brief(1654, 2339, '1').rotate(180)
    s1.save(ordner / 'scan-g4.tif', compression='group4', dpi=(200, 200), save_all=True, append_images=[s2])
    brief(800, 600, 'RGB', farbe=True).save(ordner / 'farbe-lzw.tif', compression='tiff_lzw', dpi=(300, 300))
    brief(640, 480, 'RGB', farbe=True).save(ordner / 'farbe-jpeg.tif', compression='jpeg', dpi=(150, 150))
    brief(500, 300, 'L').save(ordner / 'grau-ohne-dpi.tif')
    # Auflösung in Zentimetern (118,11 Punkte/cm = 300 dpi).
    brief(600, 400, 'L').save(ordner / 'grau-cm.tif', compression='packbits', dpi=(300, 300), resolution_unit=3,
                              tiffinfo={282: 118.11, 283: 118.11, 296: 3})
    brief(640, 480, 'RGB', farbe=True).save(ordner / 'foto.webp', quality=90)
    a = brief(320, 240, 'RGB', farbe=True).convert('RGBA')
    ImageDraw.Draw(a).rectangle([0, 0, 80, 60], fill=(0, 0, 0, 0))  # durchsichtige Ecke → weiß
    a.save(ordner / 'durchsichtig.webp', lossless=True)
    g1, g2 = brief(300, 200, 'P', farbe=True), brief(300, 200, 'P', farbe=True).rotate(90)
    g1.save(ordner / 'animiert.gif', save_all=True, append_images=[g2], duration=500, loop=0)
    brief(400, 300, 'RGB', farbe=True).save(ordner / 'grafik.bmp')
    brief(300, 200, 'L').save(ordner / 'grau.bmp')
    # Kaputt: abgeschnittenes TIFF; kein Bild: ein PNG mit der Endung .tif.
    daten = (ordner / 'farbe-lzw.tif').read_bytes()
    (ordner / 'kaputt.tif').write_bytes(daten[:len(daten) // 3])
    p = io.BytesIO()
    brief(100, 100, 'L').save(p, 'PNG')
    (ordner / 'kein-tiff.tif').write_bytes(p.getvalue())


def weiss(b: Image.Image) -> Image.Image:
    if b.mode in ('RGBA', 'LA', 'P'):
        b = b.convert('RGBA')
        h = Image.new('RGBA', b.size, 'white')
        h.alpha_composite(b)
        return h.convert('RGB')
    return b.convert('RGB')


def abweichung(a: Image.Image, b: Image.Image) -> float:
    if a.size != b.size:
        return 999.0
    return sum(ImageStat.Stat(ImageChops.difference(weiss(a), weiss(b))).mean) / 3


def seiten_aus_pdf(pdf: Path):
    """Die Seitenbilder genau so, wie sie im PDF stecken (pdfimages), und die Seitengrößen in pt (pdfinfo)."""
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(['pdfimages', '-png', str(pdf), f'{t}/s'], check=True)
        bilder = [Image.open(p).copy() for p in sorted(Path(t).glob('s-*.png'))]
    info = subprocess.run(['pdfinfo', '-f', '1', '-l', '1000', str(pdf)], check=True, capture_output=True, text=True).stdout
    groessen = [tuple(float(x) for x in z.split(':')[1].split('pts')[0].split(' x ')) for z in info.splitlines() if z.startswith('Page') and 'size' in z]
    return bilder, groessen


def vergleiche(ordner: Path) -> int:
    fehler = 0

    def pruefe(name, wert, grenze):
        nonlocal fehler
        ok = wert <= grenze
        fehler += 0 if ok else 1
        print(f"{'✓' if ok else '✗'} {name}: mittlere Abweichung {wert:.2f} (höchstens {grenze})")

    # TIFF → PDF: Bild je Seite wie im TIFF, Seitengröße = Bildpunkte × 72 / dpi (ohne Angabe 300 dpi).
    for datei, dpi, grenze in [('scan-g4.tif', 200, 0), ('farbe-lzw.tif', 300, 3), ('farbe-jpeg.tif', 150, 4),
                               ('grau-ohne-dpi.tif', 300, 4), ('grau-cm.tif', 300, 4)]:
        f = ordner / f'{datei}.fassung'
        if not f.exists():
            print(f'✗ {datei}: keine Fassung'); fehler += 1; continue
        seiten, groessen = seiten_aus_pdf(f)
        original = Image.open(ordner / datei)
        anzahl = getattr(original, 'n_frames', 1)
        if len(seiten) != anzahl:
            print(f'✗ {datei}: {len(seiten)} statt {anzahl} Seiten'); fehler += 1; continue
        for i, s in enumerate(seiten):
            original.seek(i)
            pruefe(f'{datei} Seite {i + 1}', abweichung(s, original), grenze)
            soll = (original.width * 72 / dpi, original.height * 72 / dpi)
            if max(abs(groessen[i][0] - soll[0]), abs(groessen[i][1] - soll[1])) > 0.01:
                print(f'✗ {datei} Seite {i + 1}: {groessen[i]} pt statt {soll}'); fehler += 1
    for datei, grenze in [('foto.webp', 3), ('durchsichtig.webp', 3), ('animiert.gif', 0), ('grafik.bmp', 0), ('grau.bmp', 0)]:
        f = ordner / f'{datei}.fassung'
        if not f.exists():
            print(f'✗ {datei}: keine Fassung'); fehler += 1; continue
        original = Image.open(ordner / datei)
        original.seek(0)
        pruefe(datei, abweichung(Image.open(f), original), grenze)
    return fehler


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('erzeuge', 'vergleiche'):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == 'erzeuge':
        erzeuge(Path(sys.argv[2]))
    else:
        sys.exit(1 if vergleiche(Path(sys.argv[2])) else 0)
