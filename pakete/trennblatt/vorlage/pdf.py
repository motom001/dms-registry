"""Kleiner PDF-Schreiber ohne Fremdpakete – für das Trennblatt zum Ausdrucken und die Beispiel-PDFs der Tests.

Kann: A4-Seiten, Text in Helvetica (WinAnsi, also mit Umlauten), gefüllte Rechtecke, Code 128 (Zeichensatz B)
und Graustufenbilder. Die Ausgabe ist bei gleicher Eingabe Byte für Byte gleich (keine Zeitstempel).
"""
import zlib

MM = 72 / 25.4
A4 = (210 * MM, 297 * MM)

# Strich-/Lückenbreiten der Werte 0–105, 106 = Stopp – dieselbe Tabelle wie im DMS (Aufkleber) und in code/barcode.c.
MUSTER = (
    '212222 222122 222221 121223 121322 131222 122213 122312 132212 221213 221312 231212 112232 122132 122231 113222 '
    '123122 123221 223211 221132 221231 213212 223112 312131 311222 321122 321221 312212 322112 322211 212123 212321 '
    '232121 111323 131123 131321 112313 132113 132311 211313 231113 231311 112133 112331 132131 113123 113321 133121 '
    '313121 211331 231131 213113 213311 213131 311123 311321 331121 312113 312311 332111 314111 221411 431111 111224 '
    '111422 121124 121421 141122 141221 112214 112412 122114 122411 142112 142211 241211 221114 413111 241112 134111 '
    '111242 121142 121241 114212 124112 124211 411212 421112 421211 212141 214121 412121 111143 111341 131141 114113 '
    '114311 411113 411311 113141 114131 311141 411131 211412 211214 211232 2331112'
).split()


def code128b(text: str) -> list[int]:
    """Breiten (Module) von Strichen und Lücken, mit Strich beginnend, ohne Ruhezonen."""
    if not text or any(not 32 <= ord(c) <= 126 for c in text):
        raise ValueError('Code 128 B: nur druckbare ASCII-Zeichen')
    werte = [ord(c) - 32 for c in text]
    pruef = (104 + sum(w * (i + 1) for i, w in enumerate(werte))) % 103
    return [int(z) for w in [104, *werte, pruef, 106] for z in MUSTER[w]]


def _text(s: str) -> bytes:
    b = s.encode('cp1252')
    return b'(' + b.replace(b'\\', b'\\\\').replace(b'(', b'\\(').replace(b')', b'\\)') + b')'


class Seite:
    def __init__(self, breite: float = A4[0], hoehe: float = A4[1]):
        self.breite, self.hoehe = breite, hoehe
        self.inhalt: list[bytes] = []
        self.bilder: list[tuple[int, int, bytes]] = []

    def text(self, x: float, y: float, groesse: float, s: str, fett: bool = False, grau: float = 0):
        """Text ab (x, y) in Punkten, y von unten."""
        self.inhalt.append(b'BT %.3f g /%s %.2f Tf %.2f %.2f Td %s Tj ET' % (grau, b'F2' if fett else b'F1', groesse, x, y, _text(s)))

    def rechteck(self, x: float, y: float, w: float, h: float, grau: float = 0):
        self.inhalt.append(b'%.3f g %.3f %.3f %.3f %.3f re f' % (grau, x, y, w, h))

    def rahmen(self, x: float, y: float, w: float, h: float, grau: float = 0, staerke: float = 0.5, strich: float = 0):
        muster = b'[%.2f %.2f] 0 d' % (strich, strich) if strich else b'[] 0 d'
        self.inhalt.append(b'%.3f G %.2f w %s %.3f %.3f %.3f %.3f re S' % (grau, staerke, muster, x, y, w, h))

    def barcode(self, x: float, y: float, text: str, modul: float, hoehe: float, drehung: int = 0):
        """Code 128 B; (x, y) = linke untere Ecke der Striche, modul und hoehe in Punkten; drehung 0 oder 90 (Grad)."""
        pos = 0.0
        for i, b in enumerate(code128b(text)):
            if i % 2 == 0:
                if drehung == 90:
                    self.rechteck(x, y + pos * modul, hoehe, b * modul)
                else:
                    self.rechteck(x + pos * modul, y, b * modul, hoehe)
            pos += b

    def bild(self, x: float, y: float, w: float, h: float, breite: int, hoehe: int, pixel: bytes):
        """Graustufenbild (8 Bit, zeilenweise von oben) auf die Fläche w × h."""
        n = len(self.bilder)
        self.bilder.append((breite, hoehe, pixel))
        self.inhalt.append(b'q %.3f 0 0 %.3f %.3f %.3f cm /Im%d Do Q' % (w, h, x, y, n))


def code128_breite(text: str, modul: float) -> float:
    return sum(code128b(text)) * modul


def schreibe(seiten: list[Seite], titel: str = '') -> bytes:
    objekte: list[bytes] = []

    def neu(inhalt: bytes) -> int:
        objekte.append(inhalt)
        return len(objekte)

    katalog = neu(b'')
    baum = neu(b'')
    f1 = neu(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    f2 = neu(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
    kinder = []
    for s in seiten:
        bilder = []
        for (b, h, px) in s.bilder:
            daten = zlib.compress(px, 9)
            bilder.append(neu(b'<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray /BitsPerComponent 8 '
                              b'/Filter /FlateDecode /Length %d >>\nstream\n' % (b, h, len(daten)) + daten + b'\nendstream'))
        strom = zlib.compress(b'\n'.join(s.inhalt), 9)
        inhalt = neu(b'<< /Length %d /Filter /FlateDecode >>\nstream\n' % len(strom) + strom + b'\nendstream')
        xobj = b' /XObject << ' + b' '.join(b'/Im%d %d 0 R' % (i, o) for i, o in enumerate(bilder)) + b' >>' if bilder else b''
        kinder.append(neu(b'<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] /Contents %d 0 R '
                          b'/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >>%s >> >>' % (baum, s.breite, s.hoehe, inhalt, f1, f2, xobj)))
    objekte[baum - 1] = b'<< /Type /Pages /Count %d /Kids [%s] >>' % (len(kinder), b' '.join(b'%d 0 R' % k for k in kinder))
    objekte[katalog - 1] = b'<< /Type /Catalog /Pages %d 0 R >>' % baum
    info = neu(b'<< /Title %s /Producer (DMS-Paket Trennblatt) >>' % _text(titel)) if titel else None

    aus = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    lagen = []
    for i, o in enumerate(objekte, 1):
        lagen.append(len(aus))
        aus += b'%d 0 obj\n' % i + o + b'\nendobj\n'
    xref = len(aus)
    aus += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objekte) + 1)
    for p in lagen:
        aus += b'%010d 00000 n \n' % p
    aus += b'trailer\n<< /Size %d /Root %d 0 R%s >>\nstartxref\n%d\n%%%%EOF\n' % (
        len(objekte) + 1, katalog, b' /Info %d 0 R' % info if info else b'', xref)
    return bytes(aus)
