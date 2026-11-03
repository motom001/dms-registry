// PDF/A-2b schreiben – ohne Bibliotheken außer zlib, damit es sich nativ testen lässt (tests/pdfa_test.cpp).
//
// Je Seite ein Bild, das die ganze Seite füllt (JPEG als DCTDecode, sonst Flate mit PNG-Prädiktoren), darüber eine
// unsichtbare Textebene (Darstellungsart 3) genau an den Wörtern: je Wort eine Textmatrix an seiner Lage, die
// Schriftgröße ist die Höhe des Worts, die Breite stellt die horizontale Skalierung (Tz) ein. Schrift: GlyphLessFont
// von Tesseract (Apache-2.0, eingebettet, alle Zeichen auf eine leere Glyphe der Breite 1/2 em), Text als UTF-16 mit
// Identity-H und ToUnicode – so findet die Suche jedes Zeichen. Dazu, was PDF/A-2b verlangt: XMP-Metadaten
// (ungefiltert, pdfaid:part 2, conformance B), OutputIntent sRGB mit eingebettetem ICC-Profil, Dokument-ID, keine
// Verschlüsselung, keine Aktionen, kein JavaScript, keine externen Verweise, keine Transparenz.
//
// Der Schreiber hängt Seite für Seite an (nie mehr als eine Seite zugleich im Speicher).
#pragma once
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include <zlib.h>

namespace pdfa {

/* ---------- Kleinigkeiten ---------- */

inline std::string zahl(double x, int stellen = 3) {
  if (!std::isfinite(x)) x = 0;
  char b[48];
  snprintf(b, sizeof b, "%.*f", stellen, x);
  std::string s = b;
  if (s.find('.') != std::string::npos) {
    while (!s.empty() && s.back() == '0') s.pop_back();
    if (!s.empty() && s.back() == '.') s.pop_back();
  }
  if (s == "-0") s = "0";
  return s;
}

inline std::vector<uint8_t> packe(const uint8_t *daten, size_t n, int stufe = 6) {
  uLongf m = compressBound((uLong)n);
  std::vector<uint8_t> o(m);
  if (compress2(o.data(), &m, daten, (uLong)n, stufe) != Z_OK) return {};
  o.resize(m);
  return o;
}

// UTF-8 → UTF-16BE als Hex für <…> Tj; ungültige Bytes werden U+FFFD. Liefert die Anzahl der 16-Bit-Codes.
inline std::string utf16hex(const std::string &s, size_t &codes) {
  static const char *H = "0123456789ABCDEF";
  std::string r;
  codes = 0;
  auto code = [&](unsigned c) { for (int k = 12; k >= 0; k -= 4) r += H[(c >> k) & 15]; codes++; };
  for (size_t i = 0; i < s.size();) {
    unsigned char c = (unsigned char)s[i];
    unsigned u = 0xFFFD;
    size_t n = c < 0x80 ? 1 : (c >> 5) == 6 ? 2 : (c >> 4) == 14 ? 3 : (c >> 3) == 30 ? 4 : 0;
    if (n == 0 || i + n > s.size()) { i++; code(0xFFFD); continue; }
    if (n == 1) u = c;
    else {
      u = c & (0x7F >> n);
      bool ok = true;
      for (size_t k = 1; k < n; k++) {
        unsigned char f = (unsigned char)s[i + k];
        if ((f >> 6) != 2) { ok = false; break; }
        u = (u << 6) | (f & 0x3F);
      }
      if (!ok || u > 0x10FFFF || (u >= 0xD800 && u <= 0xDFFF)) { i++; code(0xFFFD); continue; }
    }
    i += n;
    if (u < 0x20) continue;  // Steuerzeichen nicht in die Textebene
    if (u >= 0x10000) { u -= 0x10000; code(0xD800 | (u >> 10)); code(0xDC00 | (u & 0x3FF)); }
    else code(u);
  }
  return r;
}

/* ---------- Bilder ---------- */

// Ein Seitenbild, fertig gepackt.
struct Bild {
  int breite = 0, hoehe = 0;  // Bildpunkte
  int kanaele = 1;            // 1 (DeviceGray) oder 3 (DeviceRGB)
  bool jpeg = false;          // true: daten sind ein JPEG (DCTDecode); sonst Flate mit PNG-Prädiktoren
  std::vector<uint8_t> daten;
};

// Bildpunkte (Grau oder RGB, 8 Bit) verlustfrei packen: je Zeile der PNG-Filter (None, Sub, Up, Paeth) mit der
// kleinsten Summe – wie libpng –, dann Flate. Im PDF: /DecodeParms << /Predictor 15 … >>.
inline Bild flate(const uint8_t *px, int breite, int hoehe, int kanaele) {
  const size_t zeile = (size_t)breite * (size_t)kanaele;
  std::vector<uint8_t> roh;
  roh.reserve((zeile + 1) * (size_t)hoehe);
  std::vector<uint8_t> kandidat[4];
  for (auto &k : kandidat) k.resize(zeile);
  for (int y = 0; y < hoehe; y++) {
    const uint8_t *z = px + (size_t)y * zeile, *o = y ? z - zeile : nullptr;
    unsigned long beste = ~0ul;
    int wahl = 0;
    for (int f = 0; f < 4; f++) {
      unsigned long summe = 0;
      for (size_t i = 0; i < zeile; i++) {
        int a = i >= (size_t)kanaele ? z[i - (size_t)kanaele] : 0, b = o ? o[i] : 0, c = (o && i >= (size_t)kanaele) ? o[i - (size_t)kanaele] : 0;
        int p;
        if (f == 0) p = 0;
        else if (f == 1) p = a;
        else if (f == 2) p = b;
        else {
          int q = a + b - c, pa = std::abs(q - a), pb = std::abs(q - b), pc = std::abs(q - c);
          p = (pa <= pb && pa <= pc) ? a : pb <= pc ? b : c;
        }
        uint8_t v = (uint8_t)(z[i] - p);
        kandidat[f][i] = v;
        summe += v < 128 ? v : 256 - v;
      }
      if (summe < beste) { beste = summe; wahl = f; }
    }
    roh.push_back((uint8_t)(wahl == 3 ? 4 : wahl));
    roh.insert(roh.end(), kandidat[wahl].begin(), kandidat[wahl].end());
  }
  Bild b;
  b.breite = breite; b.hoehe = hoehe; b.kanaele = kanaele;
  b.daten = packe(roh.data(), roh.size(), 6);
  return b;
}

/* ---------- JPEG ansehen (ohne zu dekodieren) ---------- */

struct JpegInfo {
  bool ok = false;
  int breite = 0, hoehe = 0, kanaele = 0, bits = 0;
  int sof = -1;               // 0xC0, 0xC1, 0xC2 … (Art der Kodierung)
  bool adobe = false;         // APP14 „Adobe“ vorhanden
  bool rgbIds = false;        // Komponenten heißen R, G, B (kein YCbCr) – ohne Adobe-Marke deuten PDF-Leser das falsch
  int orientierung = 1;       // EXIF 1–8
  double dpiX = 0, dpiY = 0;  // aus JFIF (0 = unbekannt)
};

inline uint16_t be16(const uint8_t *p) { return (uint16_t)(p[0] << 8 | p[1]); }

// EXIF-Ausrichtung aus einem APP1-Abschnitt (ab „Exif\0\0“).
inline int exifOrientierung(const uint8_t *p, size_t n) {
  if (n < 14 || memcmp(p, "Exif\0\0", 6) != 0) return 1;
  const uint8_t *t = p + 6;
  size_t m = n - 6;
  bool le = t[0] == 'I' && t[1] == 'I';
  if (!le && !(t[0] == 'M' && t[1] == 'M')) return 1;
  auto u16 = [&](size_t o) -> unsigned { return o + 2 > m ? 0 : le ? (unsigned)(t[o] | t[o + 1] << 8) : (unsigned)(t[o] << 8 | t[o + 1]); };
  auto u32 = [&](size_t o) -> unsigned long { return o + 4 > m ? 0 : le ? (unsigned long)t[o] | (unsigned long)t[o + 1] << 8 | (unsigned long)t[o + 2] << 16 | (unsigned long)t[o + 3] << 24
                                                                        : (unsigned long)t[o] << 24 | (unsigned long)t[o + 1] << 16 | (unsigned long)t[o + 2] << 8 | (unsigned long)t[o + 3]; };
  unsigned long ifd = u32(4);
  if (ifd + 2 > m) return 1;
  unsigned anzahl = u16(ifd);
  for (unsigned i = 0; i < anzahl && ifd + 2 + 12 * (i + 1) <= m; i++) {
    size_t e = ifd + 2 + 12 * i;
    if (u16(e) == 0x0112) { unsigned v = u16(e + 8); return v >= 1 && v <= 8 ? (int)v : 1; }
  }
  return 1;
}

inline JpegInfo jpegInfo(const uint8_t *b, size_t n) {
  JpegInfo j;
  if (n < 4 || b[0] != 0xFF || b[1] != 0xD8) return j;
  size_t i = 2;
  while (i + 4 <= n) {
    if (b[i] != 0xFF) return j;
    uint8_t m = b[i + 1];
    if (m == 0xFF) { i++; continue; }
    if (m == 0xD8 || m == 0x01 || (m >= 0xD0 && m <= 0xD7)) { i += 2; continue; }
    if (m == 0xD9 || m == 0xDA) break;
    size_t l = be16(b + i + 2);
    if (l < 2 || i + 2 + l > n) return j;
    const uint8_t *s = b + i + 4;
    size_t sl = l - 2;
    if (m == 0xE0 && sl >= 12 && memcmp(s, "JFIF\0", 5) == 0) {
      unsigned einheit = s[7], x = be16(s + 8), y = be16(s + 10);
      double f = einheit == 1 ? 1 : einheit == 2 ? 2.54 : 0;
      j.dpiX = x * f; j.dpiY = y * f;
    } else if (m == 0xE1) {
      int o = exifOrientierung(s, sl);
      if (o != 1) j.orientierung = o;
    } else if (m == 0xEE && sl >= 5 && memcmp(s, "Adobe", 5) == 0) {
      j.adobe = true;
    } else if (m >= 0xC0 && m <= 0xCF && m != 0xC4 && m != 0xC8 && m != 0xCC && j.sof < 0) {
      if (sl < 6) return j;
      j.sof = m; j.bits = s[0]; j.hoehe = be16(s + 1); j.breite = be16(s + 3); j.kanaele = s[5];
      if (j.kanaele == 3 && sl >= 6 + 9) j.rgbIds = s[6] == 'R' && s[9] == 'G' && s[12] == 'B';
    }
    i += 2 + l;
  }
  j.ok = j.sof >= 0 && j.breite > 0 && j.hoehe > 0;
  return j;
}

// Lässt sich das JPEG so, wie es ist, ins PDF übernehmen? Baseline oder progressiv mit Huffman, 8 Bit, Grau oder YCbCr.
inline bool jpegDurchreichen(const JpegInfo &j) {
  return j.ok && (j.sof == 0xC0 || j.sof == 0xC1 || j.sof == 0xC2) && j.bits == 8 && (j.kanaele == 1 || (j.kanaele == 3 && !(j.rgbIds && !j.adobe)));
}

// JPEG ohne Metadaten-Abschnitte (EXIF mit Ort und Gerät, XMP, ICC, Kommentare): APP1–APP13, APP15 und COM fallen
// weg; APP0 (JFIF) und APP14 (Adobe, Farbumrechnung) bleiben. Die Bilddaten bleiben Byte für Byte gleich.
inline std::vector<uint8_t> jpegOhneMetadaten(const uint8_t *b, size_t n) {
  std::vector<uint8_t> o;
  if (n < 4 || b[0] != 0xFF || b[1] != 0xD8) return std::vector<uint8_t>(b, b + n);
  o.reserve(n);
  o.push_back(0xFF); o.push_back(0xD8);
  size_t i = 2;
  while (i + 4 <= n) {
    if (b[i] != 0xFF) return std::vector<uint8_t>(b, b + n);
    uint8_t m = b[i + 1];
    if (m == 0xFF) { i++; continue; }
    if (m == 0xDA) { o.insert(o.end(), b + i, b + n); return o; }  // ab dem ersten Scan alles unverändert
    size_t l = be16(b + i + 2);
    if (l < 2 || i + 2 + l > n) return std::vector<uint8_t>(b, b + n);
    bool weg = (m >= 0xE1 && m <= 0xED) || m == 0xEF || m == 0xFE;
    if (!weg) o.insert(o.end(), b + i, b + i + 2 + l);
    i += 2 + l;
  }
  return std::vector<uint8_t>(b, b + n);
}

/* ---------- Lage: Ausrichtung (EXIF) ---------- */

// Ein Punkt (u, v) im gespeicherten Bild (0…1, Ursprung oben links) → Lage auf der angezeigten Seite (X, Y), wie
// EXIF-Ausrichtung 1–8 es verlangt.
inline void richte(int o, double u, double v, double &X, double &Y) {
  switch (o) {
    case 2: X = 1 - u; Y = v; break;
    case 3: X = 1 - u; Y = 1 - v; break;
    case 4: X = u; Y = 1 - v; break;
    case 5: X = v; Y = u; break;
    case 6: X = 1 - v; Y = u; break;
    case 7: X = 1 - v; Y = 1 - u; break;
    case 8: X = v; Y = 1 - u; break;
    default: X = u; Y = v;
  }
}
inline bool quer(int o) { return o >= 5 && o <= 8; }

/* ---------- Seiten ---------- */

// Ein Wort: Text und Lage relativ zur angezeigten Seite (0…1, Ursprung oben links), wie GET …/wortpositionen.
struct Wort { std::string text; double x = 0, y = 0, b = 0, h = 0; };

struct Seite {
  double breite = 0, hoehe = 0;  // angezeigte Seite in pt
  int orientierung = 1;          // wie das gespeicherte Bild auf die Seite kommt (EXIF 1–8)
  Bild bild;
  std::vector<Wort> woerter;     // schon relativ zur angezeigten Seite
};

// Inhalt einer Seite: das Bild über die ganze Seite, darüber unsichtbar die Wörter.
inline std::string inhalt(const Seite &s, size_t &woerter) {
  std::string c;
  // Bildmatrix: Einheitsquadrat (s, t), t nach oben → gespeichertes Bild (u = s, v = 1 − t) → Seite.
  auto P = [&](double ss, double tt, double &px, double &py) {
    double X, Y;
    richte(s.orientierung, ss, 1 - tt, X, Y);
    px = X * s.breite; py = (1 - Y) * s.hoehe;
  };
  double e, f, ax, ay, cx, cy;
  P(0, 0, e, f); P(1, 0, ax, ay); P(0, 1, cx, cy);
  c += "q " + zahl(ax - e, 4) + " " + zahl(ay - f, 4) + " " + zahl(cx - e, 4) + " " + zahl(cy - f, 4) + " " + zahl(e, 4) + " " + zahl(f, 4) + " cm /Im0 Do Q\n";
  woerter = 0;
  std::string t;
  for (const Wort &w : s.woerter) {
    size_t codes = 0;
    std::string hex = utf16hex(w.text, codes);
    if (!codes) continue;
    double wb = w.b * s.breite, wh = w.h * s.hoehe;
    if (!(wb > 0.05) || !(wh > 0.05)) continue;
    double x = w.x * s.breite, y = (1 - w.y - w.h) * s.hoehe;
    // GlyphLessFont: jede Glyphe 1/2 em breit → Tz streckt das Wort auf seine Breite.
    double tz = 100.0 * wb / (wh * 0.5 * (double)codes);
    t += "/F1 " + zahl(wh, 2) + " Tf " + zahl(tz, 2) + " Tz 1 0 0 1 " + zahl(x, 2) + " " + zahl(y, 2) + " Tm <" + hex + "> Tj\n";
    woerter++;
  }
  if (!t.empty()) c += "BT\n3 Tr\n" + t + "ET\n";
  return c;
}

// Angaben für die XMP-Metadaten.
struct Angaben {
  std::string werkzeug;   // xmp:CreatorTool, z. B. „DMS-Paket PDF/A 1.0.0“
  std::string erstellt;   // ISO 8601 (xmp:CreateDate/ModifyDate), leer: weglassen
  std::string id;         // 32 Hex-Zeichen für /ID
};

inline std::string xmlText(const std::string &s) {
  std::string r;
  for (char c : s) {
    if (c == '&') r += "&amp;"; else if (c == '<') r += "&lt;"; else if (c == '>') r += "&gt;"; else if (c == '"') r += "&quot;";
    else if ((unsigned char)c >= 0x20 || c == '\t') r += c;
  }
  return r;
}

inline std::string xmp(const Angaben &a) {
  std::string d;
  if (!a.erstellt.empty()) d = "<xmp:CreateDate>" + xmlText(a.erstellt) + "</xmp:CreateDate><xmp:ModifyDate>" + xmlText(a.erstellt) + "</xmp:ModifyDate>";
  return "<?xpacket begin=\"\xEF\xBB\xBF\" id=\"W5M0MpCehiHzreSzNTczkc9d\"?>\n"
         "<x:xmpmeta xmlns:x=\"adobe:ns:meta/\">\n"
         "<rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\">\n"
         "<rdf:Description rdf:about=\"\" xmlns:pdfaid=\"http://www.aiim.org/pdfa/ns/id/\" xmlns:xmp=\"http://ns.adobe.com/xap/1.0/\" xmlns:pdf=\"http://ns.adobe.com/pdf/1.3/\">\n"
         "<pdfaid:part>2</pdfaid:part><pdfaid:conformance>B</pdfaid:conformance>\n"
         "<xmp:CreatorTool>" + xmlText(a.werkzeug) + "</xmp:CreatorTool>" + d + "\n"
         "<pdf:Producer>" + xmlText(a.werkzeug) + "</pdf:Producer>\n"
         "</rdf:Description>\n</rdf:RDF>\n</x:xmpmeta>\n<?xpacket end=\"w\"?>";
}

// Der Schreiber: beginne(), je Seite seite(), am Ende fertig(). Objekte: 1 Katalog, 2 Seitenbaum, 3 XMP,
// 4 ICC-Profil, 5–10 Schrift, ab 11 je Seite Seite, Inhalt, Bild.
class Schreiber {
 public:
  std::vector<uint8_t> o;
  size_t woerter = 0;

  // icc: sRGB-Profil (ICC v2), schrift: GlyphLessFont (TrueType).
  void beginne(const Angaben &a, const std::vector<uint8_t> &icc, const std::vector<uint8_t> &schrift, size_t reserve = 0) {
    if (reserve) o.reserve(reserve);
    angaben = a;
    schreib("%PDF-1.7\n%\xE2\xE3\xCF\xD3\n");
    objekt(1);
    schreib("<< /Type /Catalog /Pages 2 0 R /Metadata 3 0 R /OutputIntents [ << /Type /OutputIntent /S /GTS_PDFA1 "
            "/OutputConditionIdentifier (sRGB IEC61966-2.1) /Info (sRGB IEC61966-2.1) /DestOutputProfile 4 0 R >> ] >>\nendobj\n");
    const std::string x = xmp(a);
    objekt(3);
    strom("/Type /Metadata /Subtype /XML", std::vector<uint8_t>(x.begin(), x.end()));
    objekt(4);
    strom("/N 3", packe(icc.data(), icc.size()), true);
    // Schrift (wie Tesseract): Type0 mit Identity-H, CIDFontType2, alle CIDs → Glyphe 1.
    objekt(5);
    schreib("<< /Type /Font /Subtype /Type0 /BaseFont /GlyphLessFont /Encoding /Identity-H /DescendantFonts [6 0 R] /ToUnicode 8 0 R >>\nendobj\n");
    objekt(6);
    schreib("<< /Type /Font /Subtype /CIDFontType2 /BaseFont /GlyphLessFont /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
            "/FontDescriptor 9 0 R /DW 500 /CIDToGIDMap 7 0 R >>\nendobj\n");
    std::vector<uint8_t> karte(2 * 65536);
    for (size_t i = 1; i < karte.size(); i += 2) karte[i] = 1;
    objekt(7);
    strom("", packe(karte.data(), karte.size(), 9), true);
    const std::string cmap =
        "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n1 beginbfrange\n<0000> <FFFF> <0000>\nendbfrange\n"
        "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n";
    objekt(8);
    strom("", std::vector<uint8_t>(cmap.begin(), cmap.end()));
    objekt(9);
    schreib("<< /Type /FontDescriptor /FontName /GlyphLessFont /Flags 5 /FontBBox [0 0 500 1000] /ItalicAngle 0 /Ascent 1000 /Descent -1 "
            "/CapHeight 1000 /StemV 80 /FontFile2 10 0 R >>\nendobj\n");
    objekt(10);
    strom("/Length1 " + std::to_string(schrift.size()), packe(schrift.data(), schrift.size()), true);
  }

  void seite(const Seite &s) {
    const int nr = naechstes;
    naechstes += 3;
    kinder.push_back(nr);
    objekt(nr);
    size_t n = 0;
    const std::string c = inhalt(s, n);
    woerter += n;
    schreib("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + zahl(s.breite, 3) + " " + zahl(s.hoehe, 3) + "] /Resources << /XObject << /Im0 " +
            std::to_string(nr + 2) + " 0 R >>" + (n ? " /Font << /F1 5 0 R >>" : "") + " >> /Contents " + std::to_string(nr + 1) + " 0 R >>\nendobj\n");
    objekt(nr + 1);
    strom("", packe(reinterpret_cast<const uint8_t *>(c.data()), c.size()), true);
    objekt(nr + 2);
    const Bild &b = s.bild;
    std::string kopf = "/Type /XObject /Subtype /Image /Width " + std::to_string(b.breite) + " /Height " + std::to_string(b.hoehe) +
                       " /ColorSpace " + (b.kanaele == 3 ? "/DeviceRGB" : "/DeviceGray") + " /BitsPerComponent 8";
    if (b.jpeg) kopf += " /Filter /DCTDecode";
    else kopf += " /Filter /FlateDecode /DecodeParms << /Predictor 15 /Colors " + std::to_string(b.kanaele) + " /BitsPerComponent 8 /Columns " + std::to_string(b.breite) + " >>";
    strom(kopf, b.daten);
  }

  size_t seiten() const { return kinder.size(); }

  std::vector<uint8_t> fertig() {
    objekt(2);
    std::string k;
    for (size_t i = 0; i < kinder.size(); i++) k += (i ? " " : "") + std::to_string(kinder[i]) + " 0 R";
    schreib("<< /Type /Pages /Count " + std::to_string(kinder.size()) + " /Kids [" + k + "] >>\nendobj\n");
    const size_t xref = o.size();
    schreib("xref\n0 " + std::to_string(stellen.size() + 1) + "\n0000000000 65535 f \n");
    for (size_t st : stellen) {
      char b[24];
      snprintf(b, sizeof b, "%010zu 00000 n \n", st);
      schreib(b);
    }
    std::string id = angaben.id;
    if (id.size() != 32) id.assign(32, '0');
    schreib("trailer\n<< /Size " + std::to_string(stellen.size() + 1) + " /Root 1 0 R /ID [<" + id + "> <" + id + ">] >>\nstartxref\n" +
            std::to_string(xref) + "\n%%EOF\n");
    return std::move(o);
  }

 private:
  Angaben angaben;
  std::vector<size_t> stellen;
  std::vector<int> kinder;
  int naechstes = 11;

  void schreib(const std::string &s) { o.insert(o.end(), s.begin(), s.end()); }
  void objekt(int nr) {
    if ((size_t)nr > stellen.size()) stellen.resize((size_t)nr, 0);
    stellen[(size_t)nr - 1] = o.size();
    schreib(std::to_string(nr) + " 0 obj\n");
  }
  void strom(const std::string &kopf, const std::vector<uint8_t> &d, bool flate = false) {
    schreib("<< " + kopf + (kopf.empty() ? "" : " ") + (flate ? "/Filter /FlateDecode " : "") + "/Length " + std::to_string(d.size()) + " >>\nstream\n");
    o.insert(o.end(), d.begin(), d.end());
    schreib("\nendstream\nendobj\n");
  }
};

/* ---------- Für das Ergebnis ---------- */

// „1,2 MB“ bzw. „830 KB“.
inline std::string groesse(size_t bytes) {
  char b[32];
  if (bytes >= 1024 * 1024) snprintf(b, sizeof b, "%.1f MB", bytes / 1048576.0);
  else snprintf(b, sizeof b, "%zu KB", (bytes + 1023) / 1024);
  std::string s = b;
  for (char &c : s) if (c == '.') c = ',';
  return s;
}

}  // namespace pdfa
