// Test der Ausgabe (code/ausgabe.h) – nativ, ohne Bibliotheken; läuft beim Bau (code/bauen.sh).
// Prüft Bildart, 1-Bit-Packen, Dateityp am Inhalt und das PDF (Seitengröße aus dpi, Querverweise an der richtigen Stelle).
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "ausgabe.h"

static int fehler = 0;
static void pruefe(bool ok, const char *was) {
  printf("%s %s\n", ok ? "ok" : "FEHLER", was);
  if (!ok) fehler++;
}

static std::vector<uint8_t> bild(std::initializer_list<uint8_t> grau) {
  std::vector<uint8_t> o;
  for (uint8_t g : grau) { o.push_back(g); o.push_back(g); o.push_back(g); o.push_back(255); }
  return o;
}

int main() {
  using namespace ausgabe;
  pruefe(bildart(bild({0, 255, 255, 0})) == Art::SCHWARZWEISS, "nur Schwarz und Weiß: Schwarzweiß");
  pruefe(bildart(bild({0, 128, 255})) == Art::GRAU, "Grautöne: Grau");
  std::vector<uint8_t> farbe = bild({0, 255});
  farbe[0] = 200;
  pruefe(bildart(farbe) == Art::FARBE, "ein farbiger Punkt: Farbe");

  std::vector<uint8_t> durchsichtig = {0, 0, 0, 0, 0, 0, 0, 255};
  aufWeiss(durchsichtig);
  pruefe(durchsichtig[0] == 255 && durchsichtig[3] == 255 && durchsichtig[4] == 0, "Durchsichtiges kommt auf Weiß");

  // 10 × 2: erste Zeile weiß, zweite schwarz; Zeilen auf ganze Bytes aufgefüllt (2 Bytes je Zeile).
  std::vector<uint8_t> sw;
  for (int i = 0; i < 10; i++) for (int k = 0; k < 4; k++) sw.push_back(255);
  for (int i = 0; i < 10; i++) { sw.push_back(0); sw.push_back(0); sw.push_back(0); sw.push_back(255); }
  std::vector<uint8_t> bits = einBit(sw, 10, 2);
  pruefe(bits.size() == 4 && bits[0] == 0xff && bits[1] == 0xc0 && bits[2] == 0 && bits[3] == 0, "1 Bit: weiß = 1, Zeilen aufgefüllt");

  const uint8_t tiff[] = {'I', 'I', 42, 0, 8, 0, 0, 0}, tiffMM[] = {'M', 'M', 0, 42, 0, 0, 0, 8};
  const uint8_t webp[] = {'R', 'I', 'F', 'F', 0, 0, 0, 0, 'W', 'E', 'B', 'P'}, gif[] = {'G', 'I', 'F', '8', '9', 'a'};
  const uint8_t bmp[] = {'B', 'M', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}, png[] = {0x89, 'P', 'N', 'G', 13, 10, 26, 10};
  pruefe(dateityp(tiff, sizeof tiff) == "tiff" && dateityp(tiffMM, sizeof tiffMM) == "tiff", "TIFF (II und MM) am Inhalt");
  pruefe(dateityp(webp, sizeof webp) == "webp" && dateityp(gif, sizeof gif) == "gif" && dateityp(bmp, sizeof bmp) == "bmp", "WebP, GIF, BMP am Inhalt");
  pruefe(dateityp(png, sizeof png).empty() && dateityp(gif, 3).empty(), "PNG und zu kurze Dateien: nichts");

  // PDF mit zwei Seiten: 2480 × 3508 bei 300 dpi = A4 (595,2 × 841,92 pt), 100 × 50 bei 72 dpi = 100 × 50 pt.
  Seite a; a.breite = 2480; a.hoehe = 3508; a.dpiX = a.dpiY = 300; a.jpeg = true; a.kanaele = 3; a.daten = {1, 2, 3};
  Seite b; b.breite = 100; b.hoehe = 50; b.dpiX = b.dpiY = 72; b.bits = 1; b.daten = {9, 9};
  std::vector<uint8_t> p = pdf({a, b});
  std::string s(p.begin(), p.end());
  pruefe(s.rfind("%PDF-1.4\n", 0) == 0 && s.size() > 20 && s.substr(s.size() - 6) == "%%EOF\n", "PDF beginnt und endet richtig");
  pruefe(s.find("/Count 2 /Kids [3 0 R 6 0 R]") != std::string::npos, "Seitenbaum mit zwei Seiten");
  pruefe(s.find("/MediaBox [0 0 595.2 841.92]") != std::string::npos, "A4 aus 300 dpi");
  pruefe(s.find("/MediaBox [0 0 100 50]") != std::string::npos, "72 dpi: ein Bildpunkt je pt");
  pruefe(s.find("/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length 3") != std::string::npos, "Farbseite als JPEG");
  pruefe(s.find("/ColorSpace /DeviceGray /BitsPerComponent 1 /Filter /FlateDecode /Length 2") != std::string::npos, "Schwarzweiß als 1 Bit");
  // Jeder Eintrag der Querverweistabelle zeigt auf „n 0 obj“.
  size_t x = s.rfind("startxref\n");
  size_t xref = (size_t)atol(s.c_str() + x + 10);
  pruefe(s.compare(xref, 5, "xref\n") == 0, "startxref zeigt auf die Tabelle");
  bool stellen = true;
  for (int nr = 1; nr <= 8; nr++) {
    size_t zeile = xref + strlen("xref\n0 9\n") + 20 * (size_t)nr;
    size_t off = (size_t)atol(s.c_str() + zeile);
    std::string kopf = std::to_string(nr) + " 0 obj";
    if (s.compare(off, kopf.size(), kopf) != 0) stellen = false;
  }
  pruefe(stellen, "Querverweise an den richtigen Stellen");
  pruefe(punkte(300, 0) == 72.0, "ohne dpi gilt 300 dpi");
  pruefe(groesse(1258291) == "1,2 MB" && groesse(2000) == "2 KB", "Größen für das Ergebnis");
  return fehler ? 1 : 0;
}
