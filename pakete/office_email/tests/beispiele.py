#!/usr/bin/env python3
"""
Testdateien für das Paket Office und E-Mail – nur mit der Standardbibliothek erzeugt, mit erfundenen Inhalten
(Persona-Namen, keine echten Adressen). Schreibt die Dateien und faelle.json (was im Volltext stehen muss bzw.
nicht stehen darf) in einen Ordner; tests/modul_test.mjs prüft das Modul damit.

    python3 tests/beispiele.py <ordner>
"""
import base64, json, struct, sys, zipfile, zlib
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
TYPEN = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>'


def rels(*eintraege):
    x = ''.join(f'<Relationship Id="{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/{t}" Target="{z}"/>' for i, t, z in eintraege)
    return f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{x}</Relationships>'


def zip_datei(teile, mimetype=None):
    from io import BytesIO
    b = BytesIO()
    with zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED) as z:
        if mimetype:
            z.writestr(zipfile.ZipInfo('mimetype'), mimetype, compress_type=zipfile.ZIP_STORED)
        for n, inhalt in teile.items():
            z.writestr(n, inhalt)
    return b.getvalue()


def docx(makros=False):
    dok = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE x [<!ENTITY boese SYSTEM "file:///etc/passwd">]>
<w:document {W}><w:body>
<w:p><w:r><w:t>Sehr geehrte Frau Petra Sommer,</w:t></w:r></w:p>
<w:p><w:r><w:t xml:space="preserve">anbei die Nebenkostenabrechnung für die Wohnung in der Lindenallee </w:t></w:r><w:r><w:t>– Grüße &amp; Dank.</w:t></w:r></w:p>
<w:p><w:r><w:t>Betrag</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>312,40 €</w:t></w:r></w:p>
<w:p><w:r><w:delText>GELOESCHTERTEXT</w:delText></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText>FELDBEFEHL</w:instrText></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Zelle-A1</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Zelle-B1</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
<w:p><w:r><mc:AlternateContent><mc:Choice Requires="wps"><w:t>Textfeld-Inhalt</w:t></mc:Choice><mc:Fallback><w:t>DOPPELT-FALLBACK</w:t></mc:Fallback></mc:AlternateContent></w:r></w:p>
<w:p><w:r><w:t>&boese;</w:t></w:r></w:p>
</w:body></w:document>'''
    teile = {'[Content_Types].xml': TYPEN, '_rels/.rels': rels(('rId1', 'officeDocument', 'word/document.xml')),
             'word/document.xml': dok,
             'word/header1.xml': f'<w:hdr {W}><w:p><w:r><w:t>Kopfzeile Hausverwaltung Özdemir</w:t></w:r></w:p></w:hdr>',
             'word/footnotes.xml': f'<w:footnotes {W}><w:footnote><w:p><w:r><w:t>Fußnote zur Abrechnung</w:t></w:r></w:p></w:footnote></w:footnotes>'}
    if makros:
        teile['word/vbaProject.bin'] = b'Attribute VB_Name = "MAKROCODE"'
    return zip_datei(teile)


def xlsx():
    wb = f'''<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" {R}><sheets>
<sheet name="Konten" sheetId="1" r:id="rId7"/><sheet name="Übersicht" sheetId="2" r:id="rId3"/></sheets></workbook>'''
    ss = '''<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="3" uniqueCount="3">
<si><t>Girokonto</t></si><si><r><t>Spar</t></r><r><t>buch</t></r><rPh><t>PHONETIK</t></rPh></si><si><t>Jonas Berger</t></si></sst>'''
    blatt1 = '''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>1523.75</v></c></row>
<row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><f>SUMME(B1)</f><v>4711</v></c><c r="C2" t="b"><v>1</v></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Inline-Zelle</t></is></c><c r="B3" t="s"><v>2</v></c></row></sheetData></worksheet>'''
    blatt2 = '''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="str"><v>Summe aller Konten</v></c></row></sheetData></worksheet>'''
    return zip_datei({'[Content_Types].xml': TYPEN, 'xl/workbook.xml': wb,
                      'xl/_rels/workbook.xml.rels': rels(('rId7', 'worksheet', 'worksheets/sheet1.xml'), ('rId3', 'worksheet', '/xl/worksheets/sheet2.xml'), ('rId9', 'sharedStrings', 'sharedStrings.xml')),
                      'xl/sharedStrings.xml': ss, 'xl/worksheets/sheet1.xml': blatt1, 'xl/worksheets/sheet2.xml': blatt2})


def pptx():
    pres = f'<p:presentation {A} {R}><p:sldIdLst><p:sldId id="256" r:id="rId3"/><p:sldId id="257" r:id="rId2"/></p:sldIdLst></p:presentation>'
    folie = lambda t: f'<p:sld {A}><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{t}</a:t></a:r><a:br/><a:r><a:t>zweite Zeile</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
    return zip_datei({'[Content_Types].xml': TYPEN, 'ppt/presentation.xml': pres,
                      'ppt/_rels/presentation.xml.rels': rels(('rId2', 'slide', 'slides/slide1.xml'), ('rId3', 'slide', 'slides/slide2.xml')),
                      'ppt/slides/slide1.xml': folie('Folie-Zwei-Inhalt'), 'ppt/slides/slide2.xml': folie('Folie-Eins-Inhalt'),
                      'ppt/slides/_rels/slide1.xml.rels': rels(('rId1', 'notesSlide', '../notesSlides/notesSlide1.xml')),
                      'ppt/notesSlides/notesSlide1.xml': f'<p:notes {A}><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Sprechernotiz Katrin</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:notes>'})


ODF_NS = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
          'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"')


def odf(art, inhalt, verschluesselt=False):
    manifest = '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"><manifest:file-entry manifest:full-path="content.xml">' + \
        ('<manifest:encryption-data/>' if verschluesselt else '') + '</manifest:file-entry></manifest:manifest>'
    content = f'<office:document-content {ODF_NS}><office:body>{inhalt}</office:body></office:document-content>'
    return zip_datei({'META-INF/manifest.xml': manifest, 'content.xml': content if not verschluesselt else zlib.compress(b'x' * 50),
                      'Basic/Standard/Module1.xml': 'MAKRO'}, mimetype=f'application/vnd.oasis.opendocument.{art}')


ODT = '''<office:text><text:h>Mietvertrag Markus Weber</text:h><text:p>Kaution<text:s text:c="3"/>900 Euro<text:tab/>fällig<text:line-break/>zum Einzug</text:p>
<text:tracked-changes><text:changed-region><text:deletion><text:p>ENTFERNTERTEXT</text:p></text:deletion></text:changed-region></text:tracked-changes>
<draw:frame><draw:image><office:binary-data>QkFTRTY0QklMRA==</office:binary-data></draw:image></draw:frame></office:text>'''
ODS = '''<office:spreadsheet><table:table table:name="Haushaltsbuch"><table:table-row><table:table-cell><text:p>Strom</text:p></table:table-cell>
<table:table-cell office:value="87.5"><text:p>87,50</text:p></table:table-cell></table:table-row></table:table></office:spreadsheet>'''
ODP = '''<office:presentation><draw:page draw:name="Seite1"><draw:frame><draw:text-box><text:p>Jahresrückblick Lena</text:p></draw:text-box></draw:frame></draw:page>
<draw:page draw:name="Seite2"><draw:frame><draw:text-box><text:p>Urlaub an der Ostsee</text:p></draw:text-box></draw:frame></draw:page></office:presentation>'''


def eml(anhang_docx):
    innen = EmailMessage()
    innen['From'] = 'Herr Özdemir <hausverwaltung@example.org>'
    innen['To'] = 'lena@example.org'
    innen['Subject'] = 'Weitergeleitet: Ablesetermin'
    innen.set_content('Der Ablesetermin ist am Dienstag.')
    m = EmailMessage(policy=SMTP)
    m['From'] = 'Jonas Berger <jonas@example.org>'
    m['To'] = 'Lena Berger <lena@example.org>'
    m['Cc'] = 'Katrin <katrin@example.net>'
    m['Date'] = 'Mon, 02 Nov 2026 10:15:00 +0100'
    m['Subject'] = 'Rechnung für März – Stromzähler'
    m.set_content('Hallo Lena,\nanbei die Rechnung für März. Grüße aus Köln\n', charset='iso-8859-1', cte='quoted-printable')
    m.add_alternative('<html><head><style>.x{}</style><script>SKRIPTINHALT()</script></head><body><p>HTML-FASSUNG</p></body></html>', subtype='html')
    m.add_attachment(anhang_docx, maintype='application', subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', filename='Rechnung März.docx')
    m.add_attachment(innen)
    m.add_attachment(b'\x89PNG\r\n\x1a\n' + b'\0' * 40, maintype='image', subtype='png', filename='zaehler.png')
    return m.as_bytes()


def eml_html():
    k = base64.encodebytes('<html><body><script>alert("SKRIPT")</script><h1>Kündigung</h1><p>Sehr geehrte Damen &amp; Herren,<br>hiermit kündige ich zum 31.12.</p><table><tr><td>Kunde</td><td>4711</td></tr></table></body></html>'.encode()).decode()
    return ('From: =?ISO-8859-1?Q?Markus_M=FCller?= <markus@example.org>\r\nTo: info@example.com\r\nSubject: =?UTF-8?B?S8O8bmRpZ3VuZw==?= =?UTF-8?Q?_Vertrag?=\r\n'
            'MIME-Version: 1.0\r\nContent-Type: text/html; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n\r\n' + k).encode()


# ---------- Compound File (OLE2) für .msg und alte Office-Dateien ----------

def cfb(baum):
    """baum: {name: bytes | dict} – Ordner als dict. Sektoren 512, Ministrom unter 4096 Bytes."""
    eintraege = []  # [name, typ, kinder-indizes, daten]

    def lege(name, wert, typ=None):
        i = len(eintraege)
        eintraege.append([name, typ or (1 if isinstance(wert, dict) else 2), [], wert if not isinstance(wert, dict) else b''])
        if isinstance(wert, dict):
            eintraege[i][2] = [lege(n, w) for n, w in wert.items()]
        return i
    lege('Root Entry', baum, typ=5)
    mini, gross = bytearray(), []
    start = {}
    for i, e in enumerate(eintraege):
        if e[1] == 2 and len(e[3]) < 4096:
            start[i] = len(mini) // 64
            mini += e[3] + b'\0' * (-len(e[3]) % 64)
    # Sektoren: Verzeichnis, MiniFAT, Ministrom, große Ströme; die FAT selbst vorne.
    ketten = []
    verz = b''
    ketten.append(('verz', (len(eintraege) * 128 + 511) // 512))
    minifat = []
    for i, e in enumerate(eintraege):
        if e[1] == 2 and len(e[3]) < 4096:
            n = (len(e[3]) + 63) // 64
            minifat += [start[i] + k + 1 for k in range(n - 1)] + [0xfffffffe] if n else []
    minifat_b = b''.join(struct.pack('<I', x) for x in minifat)
    ketten.append(('minifat', (len(minifat_b) + 511) // 512))
    ketten.append(('mini', (len(mini) + 511) // 512))
    for i, e in enumerate(eintraege):
        if e[1] == 2 and len(e[3]) >= 4096:
            ketten.append((i, (len(e[3]) + 511) // 512))
    daten_sektoren = sum(n for _, n in ketten)
    fat_sektoren = 1
    while fat_sektoren * 128 < daten_sektoren + fat_sektoren:
        fat_sektoren += 1
    fat = [0xfffffffd] * fat_sektoren
    beginn = {}
    s = fat_sektoren
    for k, n in ketten:
        beginn[k] = s if n else 0xfffffffe
        fat += [s + j + 1 for j in range(n - 1)] + ([0xfffffffe] if n else [])
        s += n
    fat += [0xffffffff] * (fat_sektoren * 128 - len(fat))
    for i, e in enumerate(eintraege):
        if e[1] == 5:
            e.append(beginn['mini'] if mini else 0xfffffffe); e.append(len(mini))
        elif e[1] == 2:
            e.append(start[i] if len(e[3]) < 4096 else beginn[i]); e.append(len(e[3]))
        else:
            e.append(0); e.append(0)
    for e in eintraege:
        name = e[0].encode('utf-16-le') + b'\0\0'
        kinder = e[2]
        # Kinder als Kette über „rechts“ (ein gültiger, wenn auch unbalancierter Baum)
        kind = kinder[0] if kinder else 0xffffffff
        rechts = 0xffffffff
        verz += name.ljust(64, b'\0') + struct.pack('<HBBIII', len(name), e[1], 1, 0xffffffff, rechts, kind) + b'\0' * 16 + b'\0' * 4 + b'\0' * 16 + struct.pack('<IQ', e[4], e[5])
    verz = bytearray(verz)
    for e in eintraege:
        for a, b in zip(e[2], e[2][1:]):
            struct.pack_into('<I', verz, a * 128 + 72, b)
    kopf = bytearray(512)
    kopf[0:8] = bytes([0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1])
    struct.pack_into('<HHHHH', kopf, 24, 0x3e, 3, 0xfffe, 9, 6)
    struct.pack_into('<IIIIIIIII', kopf, 40, 0, fat_sektoren, beginn['verz'], 0, 4096, beginn['minifat'], len(minifat_b) // 4 and (len(minifat_b) + 511) // 512, 0xfffffffe, 0)
    for k in range(109):
        struct.pack_into('<I', kopf, 76 + 4 * k, k if k < fat_sektoren else 0xffffffff)
    aus = bytearray(kopf)
    aus += b''.join(struct.pack('<I', x) for x in fat)
    teile = {'verz': bytes(verz), 'minifat': minifat_b, 'mini': bytes(mini)}
    for k, n in ketten:
        b = teile[k] if k in teile else eintraege[k][3]
        aus += b + b'\0' * (n * 512 - len(b))
    return bytes(aus)


def u(t):
    return t.encode('utf-16-le')


def msg(anhang):
    eigenschaften = bytearray(32)
    # Zustellzeit 2026-11-02 09:30 UTC als FILETIME
    ft = (1793611800 + 11644473600) * 10000000
    eigenschaften += struct.pack('<IIQ', 0x0E060040, 0, ft)
    return cfb({
        '__properties_version1.0': bytes(eigenschaften),
        '__substg1.0_0037001F': u('Angebot Dachrinne – Petra'),
        '__substg1.0_0C1A001F': u('Petra Sommer'),
        '__substg1.0_5D01001F': u('petra@example.org'),
        '__substg1.0_1000001F': u('Hallo Markus,\r\nanbei das Angebot für die Dachrinne über 1.250 €.\r\n') * 120,  # > 4096 Bytes: großer Strom
        '__recip_version1.0_#00000000': {'__substg1.0_3001001F': u('Markus Weber'), '__substg1.0_39FE001F': u('markus@example.org')},
        '__attach_version1.0_#00000000': {'__substg1.0_3707001F': u('Angebot.docx'), '__substg1.0_37010102': anhang},
    })


def rtf():
    return (r'{\rtf1\ansi\ansicpg1252\deff0{\fonttbl{\f0 SCHRIFTNAME;}}{\colortbl;\red0\green0\blue0;}'
            r'{\*\generator GENERATOR;}{\info{\title TITELINFO}}'
            r'\pard Gr\'fc\'dfe aus M\'fcnchen\par Preis 20\u8364?\par {\field{\*\fldinst HYPERLINK "FELDINST"}{\fldrslt Linktext}}\par}').encode('ascii')


def erzeuge(ordner: Path):
    ordner.mkdir(parents=True, exist_ok=True)
    d = docx()
    dateien = {
        'brief.docx': d, 'makros.docm': docx(makros=True), 'konten.xlsx': xlsx(), 'vortrag.pptx': pptx(),
        'vertrag.odt': odf('text', ODT), 'haushalt.ods': odf('spreadsheet', ODS), 'rueckblick.odp': odf('presentation', ODP),
        'geheim.odt': odf('text', ODT, verschluesselt=True),
        'post.eml': eml(d), 'kuendigung.eml': eml_html(), 'angebot.msg': msg(xlsx()),
        'brief.rtf': rtf(), 'notiz.txt': 'Notiz: Müll am Donnerstag rausstellen.\n'.encode('cp1252'),
        'notiz16.txt': '﻿Einkaufsliste: Äpfel, Brot'.encode('utf-16-le'),
        'geheim.docx': cfb({'EncryptedPackage': b'\0' * 100, 'EncryptionInfo': b'\0' * 20}),
        'umbenannt.docx': cfb({'WordDocument': b'\0' * 100}),
        'kaputt.docx': d[: len(d) // 2],
        'bombe.docx': zip_datei({'[Content_Types].xml': TYPEN, 'word/document.xml': b'<w:document>' + b' ' * (60 * 1024 * 1024) + b'</w:document>'}),
        'foto.docx': b'\xff\xd8\xff\xe0' + b'\0' * 100,
    }
    for n, b in dateien.items():
        (ordner / n).write_bytes(b)
    W_ = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    faelle = [
        # datei, mime, muss enthalten, darf nicht enthalten, Ergebnis enthält, Volltext geschrieben?
        ['brief.docx', W_, ['Sehr geehrte Frau Petra Sommer,', 'Lindenallee – Grüße & Dank.', 'Betrag 312,40 €', 'Zelle-A1 Zelle-B1', 'Textfeld-Inhalt', 'Kopfzeile Hausverwaltung Özdemir', 'Fußnote zur Abrechnung'],
         ['GELOESCHTERTEXT', 'FELDBEFEHL', 'DOPPELT-FALLBACK', 'root:'], 'Word, ', True],
        ['makros.docm', 'application/octet-stream', ['Sehr geehrte'], ['MAKROCODE'], 'Makros, nicht ausgeführt', True],
        ['konten.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', ['Konten', 'Girokonto 1523.75', 'Sparbuch 4711', 'Inline-Zelle Jonas Berger', 'Übersicht', 'Summe aller Konten'],
         ['PHONETIK', 'SUMME('], '2 Tabellenblätter', True],
        ['vortrag.pptx', '', ['Folie-Eins-Inhalt\nzweite Zeile\n\nFolie-Zwei-Inhalt', 'Sprechernotiz Katrin'], [], '2 Folien', True],
        ['vertrag.odt', 'application/vnd.oasis.opendocument.text', ['Mietvertrag Markus Weber', 'Kaution 900 Euro fällig\nzum Einzug'], ['ENTFERNTERTEXT', 'QkFTRT', 'MAKRO\n'], 'OpenDocument-Text', True],
        ['haushalt.ods', 'application/vnd.oasis.opendocument.spreadsheet', ['Haushaltsbuch', 'Strom 87,50'], [], 'OpenDocument-Tabelle', True],
        ['rueckblick.odp', 'application/vnd.oasis.opendocument.presentation', ['Jahresrückblick Lena', 'Urlaub an der Ostsee'], [], '2 Folien', True],
        ['geheim.odt', 'application/vnd.oasis.opendocument.text', [], [], 'verschlüsselt', False],
        ['post.eml', 'message/rfc822', ['Von: Jonas Berger <jonas@example.org>', 'An: Lena Berger <lena@example.org>', 'Cc: Katrin', 'Betreff: Rechnung für März – Stromzähler',
                                         'anbei die Rechnung für März. Grüße aus Köln', 'Anhang: Rechnung März.docx', 'Lindenallee – Grüße & Dank.',
                                         'Betreff: Weitergeleitet: Ablesetermin', 'Der Ablesetermin ist am Dienstag.', 'Anhang: zaehler.png'],
         ['HTML-FASSUNG', 'SKRIPTINHALT'], 'E-Mail, ', True],
        ['kuendigung.eml', '', ['Von: Markus Müller', 'Betreff: Kündigung Vertrag', 'Kündigung', 'Sehr geehrte Damen & Herren,\nhiermit kündige ich zum 31.12.', 'Kunde 4711'], ['SKRIPT', 'alert'], 'E-Mail', True],
        ['angebot.msg', 'application/vnd.ms-outlook', ['Von: Petra Sommer <petra@example.org>', 'An: Markus Weber <markus@example.org>', 'Datum: 2026-11-02 09:30 UTC',
                                                        'Betreff: Angebot Dachrinne – Petra', 'anbei das Angebot für die Dachrinne über 1.250 €.', 'Anhang: Angebot.docx', 'Girokonto 1523.75'], [], '1 Anhang', True],
        ['brief.rtf', 'application/rtf', ['Grüße aus München', 'Preis 20€', 'Linktext'], ['SCHRIFTNAME', 'GENERATOR', 'TITELINFO', 'FELDINST'], 'RTF', True],
        ['notiz.txt', 'text/plain', ['Notiz: Müll am Donnerstag rausstellen.'], [], 'Text', True],
        ['notiz16.txt', 'text/plain', ['Einkaufsliste: Äpfel, Brot'], [], 'Text', True],
        ['geheim.docx', W_, [], [], 'mit einem Passwort verschlüsselt', False],
        ['umbenannt.docx', 'application/octet-stream', [], [], 'alte Word-Format', False],
        ['kaputt.docx', W_, [], [], 'lässt sich nicht lesen', False],
        ['bombe.docx', W_, [], [], 'lässt sich nicht lesen', False],
        ['foto.docx', W_, [], [], 'nichts zu tun', False],
    ]
    (ordner / 'faelle.json').write_text(json.dumps(faelle, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    erzeuge(Path(sys.argv[1]))
