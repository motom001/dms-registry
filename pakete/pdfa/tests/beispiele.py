#!/usr/bin/env python3
"""
Testdateien für das Paket PDF/A (erfunden, mit Pillow und von Hand geschriebenen PDFs) und die Prüfung der
Archivfassungen.

    python3 tests/beispiele.py erzeuge <ordner>      # Testdateien anlegen (je Datei ggf. <name>.woerter.json)
    python3 tests/beispiele.py vergleiche <ordner>   # Archivfassungen (<name>.pdfa.pdf) prüfen

<name>.woerter.json hält die Wörter, wie die Texterkennung sie dem DMS schicken würde: relativ zum gespeicherten
Bild bzw. zur Seite (0…1, Ursprung oben links). Für PDFs mit Textebene liest die Nachbildung des DMS die Wörter
selbst (pdftotext -bbox, wie das DMS mit Poppler).

Geprüft wird je Archivfassung: Seitenzahl und -größe (pdfinfo), PDF/A-Kennung in den XMP-Metadaten, keine Fehler
(qpdf --check, wenn da) und dass jedes Wort mit seiner Lage in der Textebene steht (pdftotext -bbox) – höchstens
1,5 pt daneben. Die Konformität prüft veraPDF (tests/verapdf.sh).
"""
import io
import json
import re
import shutil
import subprocess
import sys
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ZEILEN = [
    'Stadtwerke Musterstadt',
    'Rechnung Nr. 2026-1147 für Lena Muster',
    'Kundennummer 4711-0815',
    'Grundpreis Strom 12,50 € Arbeitspreis 0,32 €/kWh',
    'Größe Übergabe Äpfel ßüöä',
]


def brief(breite, hoehe, farbe=True, zeilen=ZEILEN):
    """Eine erfundene Briefseite mit Text; liefert Bild und Wörter (relativ, oben links)."""
    b = Image.new('RGB', (breite, hoehe), 'white')
    z = ImageDraw.Draw(b)
    groesse = max(12, hoehe // 45)
    schrift = ImageFont.load_default(size=groesse)
    if farbe:
        z.rectangle([breite * 7 // 10, hoehe // 20, breite * 9 // 10, hoehe // 20 + breite // 6], fill=(30, 90, 170))
    woerter = []
    y = hoehe // 6
    for zeile in zeilen:
        x = breite // 10
        for wort in zeile.split(' '):
            l, o, r, u = z.textbbox((x, y), wort, font=schrift)
            z.text((x, y), wort, fill=(20, 20, 20), font=schrift)
            woerter.append([wort, l / breite, o / hoehe, (r - l) / breite, (u - o) / hoehe])
            x = r + groesse // 2
        y += groesse * 2
    return b, woerter


def speichere_woerter(pfad: Path, seiten):
    pfad.write_text(json.dumps(seiten, ensure_ascii=False), encoding='utf-8')


def text_pdf(seiten, pfad: Path, extra_katalog=''):
    """Ein PDF mit Textebene (Helvetica, WinAnsi) – wie eine Online-Rechnung. seiten: Liste von Zeilenlisten."""
    objekte = []

    def obj(s):
        objekte.append(s)
        return len(objekte)

    katalog = obj(None)
    baum = obj(None)
    schrift = obj('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    kinder = []
    for zeilen in seiten:
        teile = ['0.12 0.35 0.67 rg 400 760 120 50 re f 0 g BT /F1 14 Tf']
        y = 700
        for zeile in zeilen:
            t = zeile.encode('cp1252').replace(b'\\', b'\\\\').replace(b'(', b'\\(').replace(b')', b'\\)').decode('latin-1')
            teile.append(f'1 0 0 1 60 {y} Tm ({t}) Tj')
            y -= 28
        teile.append('ET')
        inhalt = '\n'.join(teile).encode('latin-1')
        c = obj(b'<< /Length %d >>\nstream\n' % len(inhalt) + inhalt + b'\nendstream')
        kinder.append(obj(f'<< /Type /Page /Parent {baum} 0 R /MediaBox [0 0 595.28 841.89] /Resources << /Font << /F1 {schrift} 0 R >> >> /Contents {c} 0 R >>'))
    objekte[baum - 1] = f'<< /Type /Pages /Count {len(kinder)} /Kids [' + ' '.join(f'{k} 0 R' for k in kinder) + '] >>'
    objekte[katalog - 1] = f'<< /Type /Catalog /Pages {baum} 0 R {extra_katalog}>>'
    out = io.BytesIO()
    out.write(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    stellen = []
    for i, o in enumerate(objekte, 1):
        stellen.append(out.tell())
        out.write(f'{i} 0 obj\n'.encode())
        out.write(o if isinstance(o, bytes) else o.encode('latin-1'))
        out.write(b'\nendobj\n')
    x = out.tell()
    out.write(f'xref\n0 {len(objekte) + 1}\n0000000000 65535 f \n'.encode())
    for s in stellen:
        out.write(f'{s:010d} 00000 n \n'.encode())
    out.write(f'trailer\n<< /Size {len(objekte) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n'.encode())
    pfad.write_bytes(out.getvalue())


def erzeuge(ordner: Path):
    global AUSGABE
    ordner.mkdir(parents=True, exist_ok=True)
    AUSGABE = ordner
    # Foto eines Briefs (Farbe, JPEG mit 72 dpi wie vom Handy) – das JPEG kommt unverändert ins PDF/A.
    b, w = brief(1240, 1754)
    b.save(ordner / 'foto.jpg', quality=88, dpi=(72, 72))
    speichere_woerter(ordner / 'foto.jpg.woerter.json', [w])
    # Hochkant fotografiert, quer gespeichert: EXIF-Ausrichtung 6. Die Wörter gelten (wie im DMS) für das gespeicherte
    # Bild – also für das quer liegende.
    gedreht = b.rotate(90, expand=True)  # gegen den Uhrzeigersinn: so speichert eine Kamera „Ausrichtung 6“
    exif = Image.Exif()
    exif[0x0112] = 6
    gedreht.save(ordner / 'exif6.jpg', quality=85, exif=exif.tobytes())
    speichere_woerter(ordner / 'exif6.jpg.woerter.json', [[[t, y, 1 - x - bb, h, bb] for t, x, y, bb, h in w]])
    # CMYK-JPEG (aus manchem Grafikprogramm): wird umgerechnet.
    b2, w2 = brief(620, 877)
    b2.convert('CMYK').save(ordner / 'cmyk.jpg', quality=90, dpi=(150, 150))
    speichere_woerter(ordner / 'cmyk.jpg.woerter.json', [w2])
    # Bildschirmfoto mit Durchsichtigem (PNG, RGBA) und Graustufen-PNG mit 300 dpi.
    b3, w3 = brief(800, 600)
    a = b3.convert('RGBA')
    ImageDraw.Draw(a).rectangle([0, 0, 120, 90], fill=(0, 0, 0, 0))
    a.save(ordner / 'durchsichtig.png')
    speichere_woerter(ordner / 'durchsichtig.png.woerter.json', [w3])
    b4, w4 = brief(1240, 1754, farbe=False)
    b4.convert('L').save(ordner / 'grau.png', dpi=(150, 150))
    speichere_woerter(ordner / 'grau.png.woerter.json', [w4])
    # Online-Rechnung: zwei Seiten mit Textebene (die Wörter liest die Nachbildung des DMS aus dem PDF).
    text_pdf([ZEILEN, ['Seite 2', 'Zahlbar bis 30.11.2026 an Stadtwerke Musterstadt', 'Vielen Dank, Jonas Beispiel']], ordner / 'rechnung.pdf')
    # Mit JavaScript beim Öffnen und einem Verweis ins Netz: kommt beides nicht mit.
    text_pdf([ZEILEN], ordner / 'extern.pdf', '/OpenAction << /S /JavaScript /JS (app.alert\\(1\\)) >> ')
    # Gescanntes PDF (nur Bilder), zwei Seiten; die Wörter kommen von der „Texterkennung“.
    s1, ws1 = brief(1240, 1754, farbe=False)
    s2, ws2 = brief(1240, 1754, farbe=False, zeilen=['Anlage zur Rechnung', 'Herr Özdemir Hausmeisterdienst'])
    s1.convert('L').save(ordner / 'scan.pdf', save_all=True, append_images=[s2.convert('L')], resolution=150)
    speichere_woerter(ordner / 'scan.pdf.woerter.json', [ws1, ws2])
    # Ein langes Dokument: 60 Seiten mit Textebene (ab 51 Seiten 200 dpi).
    text_pdf([[f'Kontoauszug Seite {i}', 'Petra Beispiel Girokonto'] for i in range(1, 61)], ordner / 'lang.pdf')

    # Was in jeder Archivfassung stehen muss: Seiten (pt) und Wörter (pt, oben links) auf der angezeigten Seite.
    def bild(name, w, breite, hoehe, dpi):
        bw, bh = breite * 72 / dpi, hoehe * 72 / dpi
        erwarte(name, [(bw, bh)], [(1, t, x * bw, y * bh, b * bw, h * bh) for t, x, y, b, h in w])
    bild('foto.jpg', w, 1240, 1754, 300)    # 72 dpi gilt nicht → 300 dpi
    bild('exif6.jpg', w, 1240, 1754, 300)   # aufgerichtet wie angezeigt
    bild('cmyk.jpg', w2, 620, 877, 150)
    bild('durchsichtig.png', w3, 800, 600, 300)
    bild('grau.png', w4, 1240, 1754, 150)
    sw, sh = 1240 * 72 / 150, 1754 * 72 / 150
    erwarte('scan.pdf', [(sw, sh)] * 2, [(i, t, x * sw, y * sh, b * sw, h * sh) for i, ws in ((1, ws1), (2, ws2)) for t, x, y, b, h in ws])
    for name in ('rechnung.pdf', 'extern.pdf', 'lang.pdf'):
        erwarte(name, seiten_im_pdf(ordner / name), [(s, t, x, y, x2 - x, y2 - y) for s, t, x, y, x2, y2 in woerter_im_pdf(ordner / name)])


def erwarte(name, seiten, woerter):
    global AUSGABE
    (AUSGABE / f'{name}.erwartet.json').write_text(json.dumps({'seiten': seiten, 'woerter': woerter}, ensure_ascii=False), encoding='utf-8')


AUSGABE = Path('.')


def befehl(*a) -> str:
    return subprocess.run(a, capture_output=True, text=True, check=True).stdout


def woerter_im_pdf(pfad: Path):
    """[(seite, text, xMin, yMin, xMax, yMax)] in pt (oben links) – mit pdftotext -bbox."""
    html = subprocess.run(['pdftotext', '-bbox', str(pfad), '-'], capture_output=True, text=True, check=True).stdout
    out, seite = [], 0
    for zeile in html.splitlines():
        if '<page ' in zeile:
            seite += 1
        m = re.search(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*)</word>', zeile)
        if m:
            t = m.group(5).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
            out.append((seite, t, *map(float, m.group(1, 2, 3, 4))))
    return out


def seiten_im_pdf(pfad: Path):
    info = befehl('pdfinfo', '-f', '1', '-l', '9999', str(pfad))
    return [tuple(map(float, m.groups())) for m in re.finditer(r'Page\s+\d+ size:\s+([\d.]+) x ([\d.]+) pts', info)]


def vergleiche(ordner: Path) -> int:
    fehler = 0

    def pruefe(name, ok, mehr=''):
        nonlocal fehler
        print(('✓ ' if ok else '✗ ') + name + ('' if ok else f' – {mehr}'))
        if not ok:
            fehler += 1

    for erwartet in sorted(ordner.glob('*.erwartet.json')):
        name = erwartet.name[:-len('.erwartet.json')]
        e = json.loads(erwartet.read_text(encoding='utf-8'))
        pdf = ordner / f'{name}.pdfa.pdf'
        if not pdf.exists():
            pruefe(f'{name}: Archivfassung da', False, 'fehlt')
            continue
        roh = pdf.read_bytes()
        pruefe(f'{name}: PDF/A-2b-Kennung in den XMP-Metadaten', b'<pdfaid:part>2</pdfaid:part><pdfaid:conformance>B</pdfaid:conformance>' in roh)
        pruefe(f'{name}: nichts aus dem Original, das nachlädt oder ausführt', not re.search(rb'/JavaScript|/OpenAction|/URI|/Launch|/AA\b', roh))
        if shutil.which('qpdf'):
            r = subprocess.run(['qpdf', '--check', str(pdf)], capture_output=True, text=True)
            pruefe(f'{name}: qpdf --check', r.returncode == 0, r.stdout[-300:] + r.stderr[-300:])
        seiten = seiten_im_pdf(pdf)
        pruefe(f'{name}: {len(e["seiten"])} Seite(n)', len(seiten) == len(e['seiten']), f'{len(seiten)} Seiten')
        for i, (soll, ist) in enumerate(zip(e['seiten'], seiten), 1):
            pruefe(f'{name}: Seite {i} {soll[0]:.0f} × {soll[1]:.0f} pt', abs(soll[0] - ist[0]) < 1 and abs(soll[1] - ist[1]) < 1, f'{ist[0]:.1f} × {ist[1]:.1f}')
        gefunden = woerter_im_pdf(pdf)
        fehlt, daneben = [], []
        for s, t, x, y, b, h in e['woerter']:
            kandidaten = [g for g in gefunden if g[0] == s and g[1] == t]
            if not kandidaten:
                fehlt.append(f'S. {s} „{t}“')
                continue
            ab = min(max(abs(g[2] - x), abs(g[3] - y), abs(g[4] - (x + b)), abs(g[5] - (y + h))) for g in kandidaten)
            if ab > 1.5:
                daneben.append(f'S. {s} „{t}“ {ab:.1f} pt')
        pruefe(f'{name}: alle {len(e["woerter"])} Wörter in der Textebene', not fehlt, ', '.join(fehlt[:8]))
        pruefe(f'{name}: Wörter genau an ihrer Stelle (höchstens 1,5 pt)', not daneben, ', '.join(daneben[:8]))
    return fehler


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('erzeuge', 'vergleiche'):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == 'erzeuge':
        erzeuge(Path(sys.argv[2]))
    else:
        sys.exit(1 if vergleiche(Path(sys.argv[2])) else 0)
