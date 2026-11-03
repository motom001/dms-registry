// Test der Wortpositionen (code/woerter.h), nativ übersetzt von code/bauen.sh.
#include <cstdio>
#include <string>
#include "woerter.h"

static int fehler = 0;
static void pruefe(bool ok, const char *was) { std::printf("%s %s\n", ok ? "ok" : "FEHLER", was); if (!ok) fehler++; }

static bool gleich(woerter::Kasten a, woerter::Kasten b) { return a.links == b.links && a.oben == b.oben && a.rechts == b.rechts && a.unten == b.unten; }

// Wie pixRotateOrth: ein Punkt des ungedrehten Bilds (W × H) nach v viertel Umdrehungen im Uhrzeigersinn.
static void drehe(int v, int W, int H, int x, int y, int &x2, int &y2) {
  if (v == 1) { x2 = H - y; y2 = x; } else if (v == 2) { x2 = W - x; y2 = H - y; } else if (v == 3) { x2 = y; y2 = W - x; } else { x2 = x; y2 = y; }
}

int main() {
  const int W = 1000, H = 1400;
  const woerter::Kasten k{100, 200, 300, 240};
  pruefe(gleich(woerter::zurueck(0, W, H, k), k), "Ungedreht: unverändert");
  for (int v = 1; v <= 3; v++) {
    int a, b, c, d;
    drehe(v, W, H, k.links, k.oben, a, b);
    drehe(v, W, H, k.rechts, k.unten, c, d);
    woerter::Kasten g{std::min(a, c), std::min(b, d), std::max(a, c), std::max(b, d)};
    char t[64];
    std::snprintf(t, sizeof t, "%d viertel Umdrehung(en): zurückgerechnet", v);
    pruefe(gleich(woerter::zurueck(v, W, H, g), k), t);
  }
  pruefe(woerter::json("Rechnung", k, W, H) == "[\"Rechnung\",0.1,0.14286,0.2,0.02857]", "JSON relativ, 5 Stellen");
  pruefe(woerter::json("  ", k, W, H).empty(), "Leeres Wort fällt weg");
  pruefe(woerter::json("x", {10, 10, 10, 20}, W, H).empty(), "Kasten ohne Breite fällt weg");
  pruefe(woerter::json("x", {-5, 10, 1200, 20}, W, H) == "[\"x\",0,0.00714,1,0.00714]", "Kasten auf das Bild begrenzt");
  pruefe(woerter::gekuerzt(std::string(250, 'a')).size() == 200, "Langes Wort auf 200 Zeichen gekürzt");
  std::string emoji;
  for (int i = 0; i < 101; i++) emoji += "\xF0\x9F\x98\x80";
  pruefe(woerter::gekuerzt(emoji).size() == 100 * 4, "Zeichen außerhalb der BMP zählen doppelt");
  pruefe(woerter::gekuerzt(" Gr\xC3\xBC\xC3\x9F" "e\f ") == "Gr\xC3\xBC\xC3\x9F" "e", "Umlaute bleiben, Ränder und Seitenvorschub weg");
  return fehler ? 1 : 0;
}
