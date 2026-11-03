// Wortpositionen für die Archivfassung (DMS #631, dms-registry #29): die Lage jedes erkannten Worts, so wie das DMS sie
// mit dem Volltext annimmt – je Wort [Text, x, y, b, h] relativ zur Seite, wie GET …/seiten/{nr}/scan sie liefert
// (0…1, Ursprung oben links). Hat das Paket die Seite zum Lesen gedreht, rechnet es die Lage hierher zurück.
// Ohne Tesseract, damit es sich nativ testen lässt (tests/woerter_test.cpp).
#pragma once
#include <algorithm>
#include <cstdio>
#include <string>

#include "json.h"

namespace woerter {

// Ein Wort, wie Tesseract es liefert: Text (UTF-8) und Kasten in Bildpunkten des gelesenen Bilds.
struct Kasten { int links = 0, oben = 0, rechts = 0, unten = 0; };

// Kasten im gedrehten Bild (pixRotateOrth: viertel Umdrehungen im Uhrzeigersinn) → Kasten im ungedrehten Bild der
// Breite W und Höhe H.
inline Kasten zurueck(int vierteln, int W, int H, Kasten k) {
  switch (((vierteln % 4) + 4) % 4) {
    case 1: return {k.oben, H - k.rechts, k.unten, H - k.links};
    case 2: return {W - k.rechts, H - k.unten, W - k.links, H - k.oben};
    case 3: return {W - k.unten, k.links, W - k.oben, k.rechts};
    default: return k;
  }
}

// Höchstens so viele UTF-16-Einheiten je Wort nimmt das DMS (WORT_MAX_LAENGE).
constexpr size_t WORT_MAX = 200;

// Text kürzen, bis er in höchstens max UTF-16-Einheiten passt (ganze Zeichen); Leerraum an den Rändern weg.
inline std::string gekuerzt(const std::string &s, size_t max = WORT_MAX) {
  size_t a = 0, e = s.size();
  while (a < e && (unsigned char)s[a] <= ' ') a++;
  while (e > a && (unsigned char)s[e - 1] <= ' ') e--;
  std::string r;
  size_t einheiten = 0;
  for (size_t i = a; i < e;) {
    unsigned char c = (unsigned char)s[i];
    size_t n = c < 0x80 ? 1 : (c >> 5) == 6 ? 2 : (c >> 4) == 14 ? 3 : (c >> 3) == 30 ? 4 : 1;
    if (i + n > e) break;
    const size_t u = n == 4 ? 2 : 1;
    if (einheiten + u > max) break;
    if (c < 0x20) { i++; continue; }  // Steuerzeichen (auch \f) gehören nicht in ein Wort
    r.append(s, i, n);
    einheiten += u;
    i += n;
  }
  return r;
}

inline std::string zahl5(double v) {
  char b[24];
  snprintf(b, sizeof b, "%.5f", v);
  std::string s = b;
  while (s.size() > 1 && s.back() == '0') s.pop_back();
  if (s.back() == '.') s.pop_back();
  return s;
}

// Ein Wort als JSON [Text, x, y, b, h] relativ zum Bild W × H – oder leer, wenn es nichts taugt (kein Text, kein Kasten).
inline std::string json(const std::string &text, Kasten k, int W, int H) {
  const std::string t = gekuerzt(text);
  if (t.empty() || W <= 0 || H <= 0) return "";
  const int l = std::clamp(k.links, 0, W), r = std::clamp(k.rechts, 0, W), o = std::clamp(k.oben, 0, H), u = std::clamp(k.unten, 0, H);
  if (r <= l || u <= o) return "";
  const double x = (double)l / W, y = (double)o / H, b = (double)(r - l) / W, h = (double)(u - o) / H;
  return "[" + jsonText(t) + "," + zahl5(x) + "," + zahl5(y) + "," + zahl5(b) + "," + zahl5(h) + "]";
}

}  // namespace woerter
