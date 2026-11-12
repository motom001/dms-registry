#!/usr/bin/env python3
"""
Testdateien für das Paket PDF/A (erfunden, mit Pillow und von Hand geschriebenen PDFs) und die Prüfung der
Archivfassungen.

    python3 tests/beispiele.py erzeuge <ordner>      # Testdateien anlegen (je Datei ggf. <name>.woerter.json)
    python3 tests/beispiele.py vergleiche <ordner>   # Archivfassungen (<name>.pdfa.pdf) prüfen

<name>.woerter.json hält die Wörter, wie die Texterkennung sie dem DMS schicken würde: relativ zum gespeicherten
Bild bzw. zur Seite (0…1, Ursprung oben links). Für PDFs mit Textebene liest die Nachbildung des DMS die Wörter
selbst (pdftotext -bbox, wie das DMS mit Poppler).

E-Mails (dms-registry #143) erzeugt mails() nur mit der Python-Standardbibliothek (email) – Outlook-Dateien (.msg) mit dem
Compound-File-Schreiber aus den Tests des Pakets „Office und E-Mail“, das denselben Mail-Zerleger nutzt. Was in den
Seiten einer Mail stehen muss, prüft tests/modul_test.mjs (pdftotext, pdffonts, pdfimages).

Geprüft wird je Archivfassung: Seitenzahl und -größe (pdfinfo), PDF/A-Kennung in den XMP-Metadaten, keine Fehler
(qpdf --check, wenn da) und dass jedes Wort mit seiner Lage in der Textebene steht (pdftotext -bbox) – höchstens
1,5 pt daneben. Die Konformität prüft veraPDF (tests/verapdf.sh).
"""
import importlib.util
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

from email.message import EmailMessage
from email.policy import SMTP

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
    # Farbiger Scan (registry #189): Seite 1 mit blauem Logo, Seite 2 grau – nur Seite 1 kommt in Farbe ins PDF/A.
    f1, wf1 = brief(1240, 1754)
    f2, wf2 = brief(1240, 1754, farbe=False, zeilen=['Seite 2 ohne Farbe', 'Petra Beispiel'])
    f1.save(ordner / 'farbe.pdf', save_all=True, append_images=[f2], resolution=150)
    speichere_woerter(ordner / 'farbe.pdf.woerter.json', [wf1, wf2])
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
    erwarte('farbe.pdf', [(sw, sh)] * 2, [(i, t, x * sw, y * sh, b * sw, h * sh) for i, ws in ((1, wf1), (2, wf2)) for t, x, y, b, h in ws])
    mails(ordner)
    for name in ('rechnung.pdf', 'extern.pdf', 'lang.pdf'):
        erwarte(name, seiten_im_pdf(ordner / name), [(s, t, x, y, x2 - x, y2 - y) for s, t, x, y, x2, y2 in woerter_im_pdf(ordner / name)])


def office_beispiele():
    """Die Testhilfen des Pakets Office und E-Mail (Compound File für .msg)."""
    pfad = Path(__file__).resolve().parents[2] / 'office_email' / 'tests' / 'beispiele.py'
    spec = importlib.util.spec_from_file_location('office_beispiele', pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def png(breite, hoehe, farbe=(30, 90, 170)):
    b = Image.new('RGB', (breite, hoehe), 'white')
    z = ImageDraw.Draw(b)
    z.rectangle([breite // 8, hoehe // 8, breite * 7 // 8, hoehe * 7 // 8], fill=farbe)
    z.text((breite // 6, hoehe // 3), 'Logo', fill='white', font=ImageFont.load_default(size=max(10, hoehe // 4)))
    o = io.BytesIO()
    b.save(o, 'PNG')
    return o.getvalue()


def jpeg(breite, hoehe):
    b, _ = brief(breite, hoehe)
    o = io.BytesIO()
    b.save(o, 'JPEG', quality=80)
    return o.getvalue()


def kopf(m, betreff, von='Stadtwerke Musterstadt <service@example.org>', an='Lena Muster <lena@example.org>', datum='Mon, 02 Nov 2026 10:15:00 +0100', cc=None):
    m['From'] = von
    m['To'] = an
    if cc:
        m['Cc'] = cc
    m['Date'] = datum
    m['Subject'] = betreff
    return m


HTML = '''<!DOCTYPE html><html><head><title>TITELTEXT</title><style>body{font-family:Arial}</style><script>SKRIPTINHALT()</script>
<link rel="stylesheet" href="https://example.org/stil.css"></head><body>
<img src="cid:logo@example.org" width="120" height="40" alt="Logo">
<h1>Ihre Rechnung November</h1>
<p>Guten Tag Frau Muster,<br>anbei Ihre Rechnung. <b>Fällig am 15.11.2026</b>, <i>bitte pünktlich</i>.</p>
<table border="1"><tr><th>Posten</th><th>Betrag</th></tr><tr><td>Grundpreis</td><td>12,50 €</td></tr><tr><td>Arbeitspreis</td><td>71,50 €</td></tr></table>
<ul><li>Erster Punkt</li><li>Zweiter Punkt</li></ul><ol><li>Schritt eins</li><li>Schritt zwei</li></ol>
<p>Mehr im <a href="https://example.org/portal">Kundenportal</a> oder per <a href="mailto:service@example.org">E-Mail</a>.</p>
<blockquote>Zitierter Absatz aus Ihrer Nachricht.</blockquote>
<img src="https://tracker.example.net/bild.png" width="300" height="80" alt="Werbung">
<img src="https://tracker.example.net/p.gif" width="1" height="1">
<form action="https://example.org/abschicken"><input type="text" value="FORMULARWERT"><button>Senden</button></form>
</body></html>'''


def mails(ordner: Path):
    """Die Test-E-Mails (alles erfunden): nur Standardbibliothek."""
    # Reine Text-Mail mit Zitat, langer Adresse und einem sehr langen Wort.
    m = kopf(EmailMessage(policy=SMTP), 'Ihre Abschlagszahlung ab Dezember')
    m.set_content('Hallo Lena,\n\nIhr monatlicher Abschlag ändert sich ab 01.12.2026 auf 84,00 €. Bitte prüfen Sie die Angaben in Ihrem Kundenportal: '
                  'https://example.org/kundenportal/vertraege/4711-0815/abschlag?ansicht=uebersicht&jahr=2026\n\n'
                  '    Vertragskonto: 4711-0815\n    Zähler:        1ESY1160123456\n\n'
                  '> Am 28.10.2026 schrieb Lena Muster:\n> Bitte den Abschlag anpassen.\n>> Ältere Nachricht ganz unten.\n\n'
                  'Donaudampfschifffahrtsgesellschaftskapitänswitwenrentenversicherungsanstaltsverwaltungsvorschriftenergänzungsbeilage\n\n'
                  'Freundliche Grüße\nIhre Stadtwerke\n-- \nStadtwerke Musterstadt · Kundenservice\n')
    (ordner / 'text.eml').write_bytes(m.as_bytes())

    # HTML-Mail: Alternative mit Klartext und HTML mit cid:-Bild, externem Bild, Zählpixel, Tabelle, Liste, Link, Skript.
    m = kopf(EmailMessage(policy=SMTP), 'Ihre Rechnung November', cc='Tom Muster <tom@example.org>')
    m.set_content('Klartext-Fassung: Ihre Rechnung November.\n')
    m.add_alternative(HTML, subtype='html')
    m.get_payload()[1].add_related(png(240, 80), maintype='image', subtype='png', cid='<logo@example.org>')
    (ordner / 'html.eml').write_bytes(m.as_bytes())

    # Mit Anhängen (PDF, Word, Foto) – die Inhalte kommen nicht in die Archivfassung.
    m = kopf(EmailMessage(policy=SMTP), 'Unterlagen zum Mietvertrag', von='Herr Özdemir <hausverwaltung@example.org>')
    m.set_content('Hallo Lena,\nanbei die Unterlagen.\n')
    m.add_attachment(b'%PDF-1.4\n%ANHANGINHALT\n', maintype='application', subtype='pdf', filename='Mietvertrag.pdf')
    m.add_attachment(b'PK\x03\x04' + b'\0' * 2000, maintype='application', subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', filename='Hausordnung.docx')
    m.add_attachment(jpeg(400, 560), maintype='image', subtype='jpeg', filename='Zählerstand.jpg')
    (ordner / 'anhaenge.eml').write_bytes(m.as_bytes())

    # Weitergeleitet: vier Ebenen tief – gesetzt werden drei, die vierte steht nur noch als Anhang in der Liste.
    innen = None
    for ebene in (4, 3, 2, 1):
        x = kopf(EmailMessage(policy=SMTP), f'Ebene {ebene}: Ablesetermin', von=f'Absender{ebene} <a{ebene}@example.org>', datum=f'Mon, 0{ebene} Nov 2026 08:00:00 +0000')
        x.set_content(f'Text der Ebene {ebene}.\n')
        if innen is not None:
            x.add_attachment(innen)
        innen = x
    m = kopf(EmailMessage(policy=SMTP), 'WG: Ablesetermin', von='Jonas Muster <jonas@example.org>')
    m.set_content('Siehe unten.\n')
    m.add_attachment(innen)
    (ordner / 'weitergeleitet.eml').write_bytes(m.as_bytes())

    # Windows-1252 im Text, ISO-8859-1 und Base64 im Kopf.
    t = 'Sehr geehrte Damen und Herren,\r\nder Betrag von 1.250 € wird „am Monatsende“ fällig – Grüße.\r\n'.encode('cp1252')
    roh = (b'From: =?ISO-8859-1?Q?J=FCrgen_M=FCller?= <juergen@example.org>\r\nTo: lena@example.org\r\nDate: Tue, 3 Nov 2026 09:00:00 GMT\r\n'
           b'Subject: =?UTF-8?B?w5xiZXJ3ZWlzdW5n?= =?ISO-8859-1?Q?_f=FCr_Oktober?=\r\nMIME-Version: 1.0\r\nContent-Type: text/plain; charset=windows-1252\r\n'
           b'Content-Transfer-Encoding: 8bit\r\n\r\n' + t)
    (ordner / 'latin1.eml').write_bytes(roh)

    # Kyrillisch, Griechisch – und Zeichen, die die Schrift nicht hat (Rahmen statt Fragezeichen).
    m = kopf(EmailMessage(policy=SMTP), 'Привет из Москвы', von='Ирина Петрова <irina@example.org>', datum='Wed, 04 Nov 2026 12:00:00 +0300')
    m.set_content('Здравствуйте, Лена!\nΚαλημέρα από την Αθήνα.\nPfeil → und Schriftzeichen 漢字 ohne Glyphe.\n')
    (ordner / 'kyrillisch.eml').write_bytes(m.as_bytes())

    # Lang: mehrere Seiten (Kopf- und Fußzeile mit „Seite x von y“).
    m = kopf(EmailMessage(policy=SMTP), 'Protokoll der Eigentümerversammlung', datum='Sat, 01 Aug 2026 18:30:00 +0200')
    m.set_content('\n\n'.join(f'Punkt {i}: ' + 'Die Versammlung beschließt einstimmig, die Fassade im kommenden Jahr streichen zu lassen. ' * 6 for i in range(1, 60)))
    (ordner / 'lang.eml').write_bytes(m.as_bytes())

    # Outlook (.msg): HTML-Text, ein Anhang und eine eingebettete Nachricht.
    o = office_beispiele()
    eig = bytearray(32)
    eig += struct.pack('<IIQ', 0x0E060040, 0, (1793611800 + 11644473600) * 10000000)  # 2026-11-02 09:30 UTC
    eingebettet = {'__properties_version1.0': bytes(24), '__substg1.0_0037001F': o.u('Eingebettet: Angebot alt'),
                   '__substg1.0_1000001F': o.u('Text der eingebetteten Nachricht.')}
    (ordner / 'outlook.msg').write_bytes(o.cfb({
        '__properties_version1.0': bytes(eig),
        '__substg1.0_0037001F': o.u('Angebot Dachrinne – Petra'),
        '__substg1.0_0C1A001F': o.u('Petra Sommer'),
        '__substg1.0_5D01001F': o.u('petra@example.org'),
        '__substg1.0_1000001F': o.u('Klartext des Angebots.'),
        '__substg1.0_10130102': '<html><body><p>Hallo Markus,</p><p>anbei das <b>Angebot</b> über 1.250 €.</p></body></html>'.encode(),
        '__recip_version1.0_#00000000': {'__substg1.0_3001001F': o.u('Markus Weber'), '__substg1.0_39FE001F': o.u('markus@example.org')},
        '__attach_version1.0_#00000000': {'__substg1.0_3707001F': o.u('Angebot.pdf'), '__substg1.0_37010102': b'%PDF-1.4\n'},
        '__attach_version1.0_#00000001': {'__substg1.0_3707001F': o.u('Altes Angebot.msg'), '__substg1.0_3701000D': eingebettet},
    }))


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
