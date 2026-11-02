// Ausgabe des Pakets Bildformate ohne Bibliotheken – damit sie sich nativ testen lässt (tests/ausgabe_test.cpp):
// Bildart bestimmen (Schwarzweiß, Graustufen, Farbe), Schwarzweiß in 1 Bit packen und ein PDF aus fertig
// gepackten Seitenbildern zusammensetzen (JPEG als DCTDecode, sonst FlateDecode).
#pragma once
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

namespace ausgabe {

enum class Art { SCHWARZWEISS, GRAU, FARBE };

// Bildpunkte als RGBA (8 Bit je Kanal, Zeile für Zeile). Durchsichtiges kommt auf Weiß (wie auf Papier).
inline void aufWeiss(std::vector<uint8_t> &rgba) {
  for (size_t i = 0; i + 3 < rgba.size(); i += 4) {
    unsigned a = rgba[i + 3];
    if (a == 255) continue;
    for (int k = 0; k < 3; k++) rgba[i + k] = (uint8_t)((rgba[i + k] * a + 255 * (255 - a) + 127) / 255);
    rgba[i + 3] = 255;
  }
}

inline Art bildart(const std::vector<uint8_t> &rgba) {
  bool grau = true, sw = true;
  for (size_t i = 0; i + 3 < rgba.size(); i += 4) {
    uint8_t r = rgba[i], g = rgba[i + 1], b = rgba[i + 2];
    if (r != g || g != b) { grau = false; sw = false; break; }
    if (r != 0 && r != 255) sw = false;
  }
  return sw ? Art::SCHWARZWEISS : grau ? Art::GRAU : Art::FARBE;
}

// Ein Kanal (Grau) bzw. drei (RGB) aus RGBA.
inline std::vector<uint8_t> kanaele(const std::vector<uint8_t> &rgba, int n) {
  std::vector<uint8_t> o;
  o.reserve(rgba.size() / 4 * (size_t)n);
  for (size_t i = 0; i + 3 < rgba.size(); i += 4) {
    if (n == 1) o.push_back(rgba[i]);
    else { o.push_back(rgba[i]); o.push_back(rgba[i + 1]); o.push_back(rgba[i + 2]); }
  }
  return o;
}

// Schwarzweiß als 1 Bit je Bildpunkt (PDF DeviceGray: 0 = schwarz, 1 = weiß), Zeilen auf ganze Bytes aufgefüllt.
inline std::vector<uint8_t> einBit(const std::vector<uint8_t> &rgba, int breite, int hoehe) {
  const size_t zeile = ((size_t)breite + 7) / 8;
  std::vector<uint8_t> o(zeile * (size_t)hoehe, 0);
  for (int y = 0; y < hoehe; y++)
    for (int x = 0; x < breite; x++)
      if (rgba[((size_t)y * (size_t)breite + (size_t)x) * 4] >= 128) o[(size_t)y * zeile + (size_t)x / 8] |= (uint8_t)(0x80 >> (x % 8));
  return o;
}

// Eine Seite des PDFs: das Bild (schon gepackt) und seine Größe in Bildpunkten und dpi.
struct Seite {
  int breite = 0, hoehe = 0;
  double dpiX = 300, dpiY = 300;
  bool jpeg = false;   // true: daten sind ein JPEG (DCTDecode); sonst mit zlib gepackte Bildpunkte (FlateDecode)
  int kanaele = 1;     // 1 (Grau) oder 3 (RGB)
  int bits = 8;        // 8, bei Schwarzweiß 1
  std::vector<uint8_t> daten;
};

// Seitengröße in pt: Bildpunkte × 72 / dpi (ohne Angabe gilt 300 dpi, siehe README).
inline double punkte(int px, double dpi) { return px * 72.0 / (dpi > 0 ? dpi : 300.0); }

inline std::string zahl(double x) {
  char b[32];
  snprintf(b, sizeof b, "%.2f", x);
  std::string s = b;
  while (!s.empty() && s.back() == '0') s.pop_back();
  if (!s.empty() && s.back() == '.') s.pop_back();
  return s;
}

// PDF 1.4 mit je einem Bild pro Seite, das die ganze Seite füllt. Objekte: 1 Katalog, 2 Seitenbaum, dann je Seite
// Seite, Inhalt, Bild. Querverweistabelle mit den echten Byte-Stellen.
inline std::vector<uint8_t> pdf(const std::vector<Seite> &seiten) {
  std::vector<uint8_t> o;
  std::vector<size_t> stellen;
  auto schreib = [&](const std::string &s) { o.insert(o.end(), s.begin(), s.end()); };
  auto objekt = [&](int nr) { if ((size_t)nr > stellen.size()) stellen.resize((size_t)nr); stellen[(size_t)nr - 1] = o.size(); schreib(std::to_string(nr) + " 0 obj\n"); };
  schreib("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n");
  objekt(1);
  schreib("<< /Type /Catalog /Pages 2 0 R >>\nendobj\n");
  objekt(2);
  std::string kinder;
  for (size_t i = 0; i < seiten.size(); i++) kinder += (i ? " " : "") + std::to_string(3 + 3 * i) + " 0 R";
  schreib("<< /Type /Pages /Count " + std::to_string(seiten.size()) + " /Kids [" + kinder + "] >>\nendobj\n");
  for (size_t i = 0; i < seiten.size(); i++) {
    const Seite &s = seiten[i];
    const int nr = 3 + 3 * (int)i;
    const std::string w = zahl(punkte(s.breite, s.dpiX)), h = zahl(punkte(s.hoehe, s.dpiY));
    objekt(nr);
    schreib("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + w + " " + h + "] /Resources << /XObject << /Im0 " +
            std::to_string(nr + 2) + " 0 R >> >> /Contents " + std::to_string(nr + 1) + " 0 R >>\nendobj\n");
    const std::string inhalt = "q " + w + " 0 0 " + h + " 0 0 cm /Im0 Do Q\n";
    objekt(nr + 1);
    schreib("<< /Length " + std::to_string(inhalt.size()) + " >>\nstream\n" + inhalt + "endstream\nendobj\n");
    objekt(nr + 2);
    schreib("<< /Type /XObject /Subtype /Image /Width " + std::to_string(s.breite) + " /Height " + std::to_string(s.hoehe) +
            " /ColorSpace " + (s.kanaele == 3 ? "/DeviceRGB" : "/DeviceGray") + " /BitsPerComponent " + std::to_string(s.bits) +
            " /Filter " + (s.jpeg ? "/DCTDecode" : "/FlateDecode") + " /Length " + std::to_string(s.daten.size()) + " >>\nstream\n");
    o.insert(o.end(), s.daten.begin(), s.daten.end());
    schreib("\nendstream\nendobj\n");
  }
  const size_t xref = o.size();
  schreib("xref\n0 " + std::to_string(stellen.size() + 1) + "\n0000000000 65535 f \n");
  for (size_t st : stellen) {
    char b[24];
    snprintf(b, sizeof b, "%010zu 00000 n \n", st);
    schreib(b);
  }
  schreib("trailer\n<< /Size " + std::to_string(stellen.size() + 1) + " /Root 1 0 R >>\nstartxref\n" + std::to_string(xref) + "\n%%EOF\n");
  return o;
}

// Dateityp am Inhalt (nicht am Namen): tiff, webp, gif, bmp – sonst leer.
inline std::string dateityp(const uint8_t *b, size_t n) {
  if (n >= 4 && ((b[0] == 'I' && b[1] == 'I' && b[2] == 42 && b[3] == 0) || (b[0] == 'M' && b[1] == 'M' && b[2] == 0 && b[3] == 42))) return "tiff";
  if (n >= 4 && ((b[0] == 'I' && b[1] == 'I' && b[2] == 43 && b[3] == 0) || (b[0] == 'M' && b[1] == 'M' && b[2] == 0 && b[3] == 43))) return "tiff"; // BigTIFF
  if (n >= 12 && b[0] == 'R' && b[1] == 'I' && b[2] == 'F' && b[3] == 'F' && b[8] == 'W' && b[9] == 'E' && b[10] == 'B' && b[11] == 'P') return "webp";
  if (n >= 6 && b[0] == 'G' && b[1] == 'I' && b[2] == 'F' && b[3] == '8' && (b[4] == '7' || b[4] == '9') && b[5] == 'a') return "gif";
  if (n >= 14 && b[0] == 'B' && b[1] == 'M') return "bmp";
  return "";
}

// „1,2 MB“ bzw. „830 KB“ für das Ergebnis.
inline std::string groesse(size_t bytes) {
  char b[32];
  if (bytes >= 1024 * 1024) snprintf(b, sizeof b, "%.1f MB", bytes / 1048576.0);
  else snprintf(b, sizeof b, "%zu KB", (bytes + 1023) / 1024);
  std::string s = b;
  for (char &c : s) if (c == '.') c = ',';
  return s;
}

}  // namespace ausgabe
