// Test des PDF-Schreibers (code/pdfa.h) ohne WebAssembly: UTF-16, JPEG-Kopf, Metadaten entfernen, Ausrichtung,
// Textebene und Aufbau der Datei (Querverweise zeigen auf ihre Objekte); dazu die Teilmenge einer Schrift (schrift.h).
//
//   c++ -std=c++17 -I code tests/pdfa_test.cpp -lz -o /tmp/pdfa_test && /tmp/pdfa_test code/daten [ausgabe.pdf]
#include <fstream>
#include <iostream>
#include <iterator>

#include "pdfa.h"
#include "schrift.h"

static int fehler = 0;
static void pruefe(const std::string &name, bool ok) {
  std::cout << (ok ? "ok   " : "FEHL ") << name << "\n";
  if (!ok) fehler++;
}

static std::vector<uint8_t> lies(const std::string &pfad) {
  std::ifstream f(pfad, std::ios::binary);
  return std::vector<uint8_t>(std::istreambuf_iterator<char>(f), {});
}

int main(int argc, char **argv) {
  const std::string daten = argc > 1 ? argv[1] : "code/daten";
  size_t n = 0;
  pruefe("UTF-16: ASCII", pdfa::utf16hex("Ab", n) == "00410062" && n == 2);
  pruefe("UTF-16: Umlaut", pdfa::utf16hex("\xC3\xA4", n) == "00E4" && n == 1);
  pruefe("UTF-16: Euro", pdfa::utf16hex("\xE2\x82\xAC", n) == "20AC" && n == 1);
  pruefe("UTF-16: außerhalb der BMP als Ersatzpaar", pdfa::utf16hex("\xF0\x9F\x98\x80", n) == "D83DDE00" && n == 2);
  pruefe("UTF-16: kaputtes UTF-8 wird U+FFFD", pdfa::utf16hex("\xC3", n) == "FFFD" && n == 1);
  pruefe("UTF-16: Steuerzeichen fallen weg", pdfa::utf16hex("a\x01" "b", n) == "00610062" && n == 2);
  pruefe("Zahl ohne Nullen", pdfa::zahl(12.5000) == "12.5" && pdfa::zahl(3.0) == "3" && pdfa::zahl(-0.0001) == "0");

  // Ein erfundener JPEG-Kopf: SOI, APP0 JFIF 300 dpi, APP1 EXIF (Ausrichtung 6), COM, SOF0 3 Komponenten, SOS …
  std::vector<uint8_t> j = {0xFF, 0xD8,
                            0xFF, 0xE0, 0x00, 0x10, 'J', 'F', 'I', 'F', 0, 1, 1, 1, 0x01, 0x2C, 0x01, 0x2C, 0, 0,
                            0xFF, 0xE1, 0x00, 0x22, 'E', 'x', 'i', 'f', 0, 0, 'M', 'M', 0, 42, 0, 0, 0, 8, 0, 1, 0x01, 0x12, 0, 3, 0, 0, 0, 1, 0, 6, 0, 0, 0, 0, 0, 0,
                            0xFF, 0xFE, 0x00, 0x05, 'h', 'i', '!',
                            0xFF, 0xC0, 0x00, 0x11, 8, 0x01, 0xE0, 0x02, 0x80, 3, 1, 0x22, 0, 2, 0x11, 1, 3, 0x11, 1,
                            0xFF, 0xDA, 0x00, 0x02, 0x12, 0x34, 0xFF, 0xD9};
  pdfa::JpegInfo ji = pdfa::jpegInfo(j.data(), j.size());
  pruefe("JPEG: Größe 640 × 480", ji.ok && ji.breite == 640 && ji.hoehe == 480 && ji.kanaele == 3 && ji.bits == 8);
  pruefe("JPEG: 300 dpi aus JFIF", ji.dpiX == 300 && ji.dpiY == 300);
  pruefe("JPEG: EXIF-Ausrichtung 6", ji.orientierung == 6);
  pruefe("JPEG: Baseline lässt sich durchreichen", pdfa::jpegDurchreichen(ji));
  std::vector<uint8_t> ohne = pdfa::jpegOhneMetadaten(j.data(), j.size());
  pruefe("JPEG: ohne EXIF und Kommentar, Rest gleich", ohne.size() == j.size() - 36 - 7 && ohne[2] == 0xFF && ohne[3] == 0xE0 && ohne[20] == 0xFF && ohne[21] == 0xC0 && ohne.back() == 0xD9);
  pdfa::JpegInfo cmyk = ji;
  cmyk.kanaele = 4;
  pruefe("JPEG: CMYK nicht durchreichen", !pdfa::jpegDurchreichen(cmyk));
  pdfa::JpegInfo arith = ji;
  arith.sof = 0xC9;
  pruefe("JPEG: arithmetisch kodiert nicht durchreichen", !pdfa::jpegDurchreichen(arith));

  double X, Y;
  pdfa::richte(6, 0, 0, X, Y);
  bool r6 = X == 1 && Y == 0;
  pdfa::richte(6, 1, 0, X, Y);
  r6 = r6 && X == 1 && Y == 1;
  pruefe("Ausrichtung 6: oben links → oben rechts, oben rechts → unten rechts", r6);
  pdfa::richte(8, 0, 0, X, Y);
  pruefe("Ausrichtung 8: oben links → unten links", X == 0 && Y == 1);
  pdfa::richte(3, 0.25, 0.1, X, Y);
  pruefe("Ausrichtung 3: gedreht um 180°", X == 0.75 && std::fabs(Y - 0.9) < 1e-12);

  // Graustufenbild 40 × 30 mit Verlauf, verlustfrei.
  std::vector<uint8_t> px(40 * 30);
  for (int y = 0; y < 30; y++) for (int x = 0; x < 40; x++) px[(size_t)y * 40 + (size_t)x] = (uint8_t)(x * 6 + y);
  pdfa::Bild b = pdfa::flate(px.data(), 40, 30, 1);
  {
    std::vector<uint8_t> roh(41 * 30);
    uLongf m = roh.size();
    bool ok = uncompress(roh.data(), &m, b.daten.data(), b.daten.size()) == Z_OK && m == 41 * 30;
    // Zurückrechnen (PNG-Filter je Zeile) und vergleichen.
    std::vector<uint8_t> zur(40 * 30);
    for (int y = 0; ok && y < 30; y++) {
      int f = roh[(size_t)y * 41];
      for (int x = 0; x < 40; x++) {
        int a = x ? zur[(size_t)y * 40 + x - 1] : 0, o = y ? zur[(size_t)(y - 1) * 40 + x] : 0, c = (x && y) ? zur[(size_t)(y - 1) * 40 + x - 1] : 0;
        int p = f == 0 ? 0 : f == 1 ? a : f == 2 ? o : 0;
        if (f == 4) { int q = a + o - c, pa = std::abs(q - a), pb = std::abs(q - o), pc = std::abs(q - c); p = (pa <= pb && pa <= pc) ? a : pb <= pc ? o : c; }
        zur[(size_t)y * 40 + x] = (uint8_t)(roh[(size_t)y * 41 + 1 + x] + p);
      }
    }
    pruefe("Flate mit PNG-Prädiktoren: verlustfrei", ok && zur == px);
  }

  std::vector<uint8_t> icc = lies(daten + "/srgb.icc"), schrift = lies(daten + "/glyphless.ttf");
  pruefe("Daten: ICC-Profil und Schrift da", icc.size() > 128 && schrift.size() > 100);

  pdfa::Schreiber s;
  pdfa::Angaben a{"DMS-Paket PDF/A Test", "2026-11-03T10:00:00Z", std::string(32, 'a')};
  s.beginne(a, icc, schrift);
  pdfa::Seite seite;
  seite.breite = 595.28; seite.hoehe = 841.89; seite.bild = b;
  seite.woerter = {{"Stromrechnung", 0.1, 0.05, 0.3, 0.02}, {"Kundennummer", 0.1, 0.1, 0.25, 0.015}, {"Gr\xC3\xBC\xC3\x9F" "e", 0.5, 0.5, 0.1, 0.02}, {"", 0.1, 0.1, 0.1, 0.1}};
  s.seite(seite);
  pdfa::Seite zwei = seite;
  zwei.orientierung = 6; zwei.breite = 300; zwei.hoehe = 400; zwei.woerter.clear();
  s.seite(zwei);
  pruefe("Wörter in der Textebene (leere nicht)", s.woerter == 3);
  std::vector<uint8_t> pdf = s.fertig();
  const std::string t(pdf.begin(), pdf.end());
  pruefe("Kopf %PDF-1.7 mit Binärkommentar", t.rfind("%PDF-1.7\n%\xE2\xE3\xCF\xD3\n", 0) == 0);
  pruefe("XMP ungefiltert mit pdfaid", t.find("/Type /Metadata /Subtype /XML /Length") != std::string::npos && t.find("<pdfaid:part>2</pdfaid:part><pdfaid:conformance>B</pdfaid:conformance>") != std::string::npos);
  pruefe("OutputIntent sRGB", t.find("/S /GTS_PDFA1") != std::string::npos && t.find("/DestOutputProfile 4 0 R") != std::string::npos);
  pruefe("Dokument-ID", t.find("/ID [<" + std::string(32, 'a') + ">") != std::string::npos);
  pruefe("Keine Aktionen, kein JavaScript", t.find("/JavaScript") == std::string::npos && t.find("/OpenAction") == std::string::npos && t.find("/AA") == std::string::npos);
  pruefe("Zwei Seiten", t.find("/Type /Pages /Count 2") != std::string::npos);
  pruefe("Seite 2 ohne Schrift in den Ressourcen", t.find("/Im0 16 0 R >> >>") != std::string::npos);
  // Querverweise: jede Stelle zeigt auf „<n> 0 obj“.
  size_t x = t.rfind("startxref\n");
  size_t xref = (size_t)atol(t.c_str() + x + 10);
  bool xok = t.compare(xref, 5, "xref\n") == 0;
  size_t p = t.find('\n', xref + 5) + 1;  // „0 <anzahl>“
  int anzahl = atoi(t.c_str() + xref + 7);
  p = t.find('\n', p) + 1;                // Eintrag 0
  for (int i = 1; xok && i < anzahl; i++, p += 20) {
    size_t stelle = (size_t)atol(t.c_str() + p);
    xok = t.compare(stelle, std::to_string(i).size() + 6, std::to_string(i) + " 0 obj") == 0 && t.compare(p + 16, 3, " n ") == 0;
  }
  pruefe("Querverweise zeigen auf ihre Objekte (" + std::to_string(anzahl - 1) + ")", xok && anzahl == 17);
  pruefe("Ende mit %%EOF", t.size() > 6 && t.compare(t.size() - 6, 6, "%%EOF\n") == 0);

  // Schrift für E-Mails (#143): lesen, vermessen, Teilmenge – und die Teilmenge lässt sich wieder lesen.
  schrift::Schrift noto;
  const bool gelesen = noto.lies(lies(daten + "/noto-sans.ttf"));
  pruefe("Noto Sans gelesen", gelesen && noto.einheiten == 1000 && noto.name == "NotoSans-Regular");
  if (gelesen) {
    pruefe("Zeichen in der Schrift: A, ä, Ж, Ω, €", noto.gid('A') && noto.gid(0xE4) && noto.gid(0x416) && noto.gid(0x3A9) && noto.gid(0x20AC));
    pruefe("Zeichen ohne Glyphe: GID 0 (nie benutzt)", noto.gid(0x6F22) == 0);
    const std::string hallo = "Hallo Köln";
    pruefe("Breite eines Texts", noto.breite(hallo, 10) > 40 && noto.breite(hallo, 10) < 60);
    for (size_t i = 0; i < hallo.size();) { const uint32_t u = schrift::naechstes(hallo, i); noto.merke(noto.gid(u), u); }
    noto.merke(0, 0x6F22);
    pruefe("Glyphe 0 wird nicht gemerkt", !noto.benutzt.count(0));
    const std::vector<uint8_t> teil = noto.teilmenge();
    schrift::Schrift wieder;
    pruefe("Teilmenge: TrueType, kleiner als die Schrift", teil.size() > 12 && teil[0] == 0 && teil[1] == 1 && teil.size() < lies(daten + "/noto-sans.ttf").size() / 4);
    pruefe("Teilmenge lässt sich lesen, gleiche GIDs und Breiten", wieder.lies(teil) && wieder.gid('H') == noto.gid('H') && wieder.breite(wieder.gid(0xF6)) == noto.breite(noto.gid(0xF6)));
  }

  if (argc > 2) {
    std::ofstream o(argv[2], std::ios::binary);
    o.write(reinterpret_cast<const char *>(pdf.data()), (std::streamsize)pdf.size());
  }
  return fehler ? 1 : 0;
}
