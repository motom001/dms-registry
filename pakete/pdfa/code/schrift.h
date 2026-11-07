// Eine TrueType-Schrift lesen, Text damit vermessen und nur die benutzten Glyphen einbetten (Teilmenge) – für die
// Archivfassung von E-Mails (dms-registry #143). Ohne Bibliotheken, damit es sich nativ testen lässt.
//
// Die Teilmenge behält die Glyphen-Nummern (GID) der Schrift: Nicht benutzte Glyphen werden leer (Länge 0 in loca),
// benutzte und ihre Bestandteile (zusammengesetzte Glyphen) bleiben. So gilt im PDF CID = GID (CIDToGIDMap
// /Identity), und die Breiten im PDF (W) stimmen genau mit hmtx überein, wie PDF/A es verlangt. Eingebettet werden
// head, hhea, maxp, hmtx, loca, glyf, dazu name und OS/2 unverändert sowie ein neues cmap (nur benutzte Zeichen) und
// post (Fassung 3, ohne Glyphennamen). GSUB/GPOS fallen weg: kein Kerning, keine Ligaturen – der Text bleibt so
// suchbar, wie er gesetzt ist. Glyphe 0 (.notdef) wird nie benutzt (PDF/A verbietet Verweise darauf); was die Schrift
// nicht kann, zeichnet der Satz als „□“ (Rahmen), nie als „?“.
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace schrift {

inline uint16_t u16(const uint8_t *p) { return (uint16_t)(p[0] << 8 | p[1]); }
inline int16_t s16(const uint8_t *p) { return (int16_t)u16(p); }
inline uint32_t u32(const uint8_t *p) { return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3]; }
inline void w16(std::vector<uint8_t> &o, uint32_t v) { o.push_back((uint8_t)(v >> 8)); o.push_back((uint8_t)v); }
inline void w32(std::vector<uint8_t> &o, uint32_t v) { w16(o, v >> 16); w16(o, v & 0xffff); }

// Nächstes Zeichen aus UTF-8 (ungültige Bytes: U+FFFD).
inline uint32_t naechstes(const std::string &s, size_t &i) {
  const unsigned char c = (unsigned char)s[i];
  size_t n = c < 0x80 ? 1 : (c >> 5) == 6 ? 2 : (c >> 4) == 14 ? 3 : (c >> 3) == 30 ? 4 : 0;
  if (!n || i + n > s.size()) { i++; return 0xFFFD; }
  uint32_t u = n == 1 ? c : c & (0x7F >> n);
  for (size_t k = 1; k < n; k++) {
    const unsigned char f = (unsigned char)s[i + k];
    if ((f >> 6) != 2) { i++; return 0xFFFD; }
    u = u << 6 | (f & 0x3F);
  }
  i += n;
  if (u > 0x10FFFF || (u >= 0xD800 && u <= 0xDFFF)) return 0xFFFD;
  return u;
}

class Schrift {
 public:
  std::string name;          // PostScript-Name, z. B. „NotoSans-Regular“
  bool ok = false;
  int einheiten = 1000;      // unitsPerEm
  int oben = 0, unten = 0;   // Ascender, Descender (hhea, Schrifteinheiten)
  int versal = 700;          // Versalhöhe
  int16_t box[4] = {0, 0, 0, 0};
  double neigung = 0;        // Kursivwinkel
  bool fett = false, kursiv = false;
  std::set<uint16_t> benutzt;            // GIDs (ohne Bestandteile)
  std::map<uint16_t, uint32_t> zeichen;  // GID → erstes Zeichen dazu (für ToUnicode)

  bool lies(std::vector<uint8_t> datei) {
    d = std::move(datei);
    if (d.size() < 12) return false;
    const uint16_t anzahl = u16(&d[4]);
    for (uint16_t i = 0; i < anzahl; i++) {
      const size_t o = 12 + 16u * i;
      if (o + 16 > d.size()) return false;
      const std::string tag((const char *)&d[o], 4);
      const uint32_t ab = u32(&d[o + 8]), laenge = u32(&d[o + 12]);
      if ((uint64_t)ab + laenge > d.size()) return false;
      tabellen[tag] = {ab, laenge};
    }
    for (const char *t : {"head", "hhea", "maxp", "hmtx", "loca", "glyf", "cmap"}) if (!tabellen.count(t)) return false;
    const uint8_t *head = tab("head");
    einheiten = u16(head + 18);
    for (int k = 0; k < 4; k++) box[k] = s16(head + 36 + 2 * k);
    langeLoca = s16(head + 50) == 1;
    const uint8_t *hhea = tab("hhea");
    oben = s16(hhea + 4); unten = s16(hhea + 6);
    metriken = u16(hhea + 34);
    glyphen = u16(tab("maxp") + 4);
    if (!metriken || !glyphen || einheiten < 16) return false;
    if (tabellen.count("OS/2") && tabellen["OS/2"].second >= 90) {
      const uint8_t *os2 = tab("OS/2");
      if (u16(os2) >= 2) versal = s16(os2 + 88);
      const uint16_t gewicht = u16(os2 + 4);
      fett = gewicht >= 600;
      kursiv = (u16(os2 + 62) & 1) != 0;
    }
    if (tabellen.count("post") && tabellen["post"].second >= 8) neigung = (int32_t)u32(tab("post") + 4) / 65536.0;
    if (neigung != 0) kursiv = true;
    name = psName();
    ok = leseCmap();
    return ok;
  }

  // GID eines Zeichens (0: nicht in der Schrift).
  uint16_t gid(uint32_t u) const {
    auto i = cmap.find(u);
    return i == cmap.end() ? 0 : i->second;
  }
  // Vorschub einer Glyphe in 1/1000 em.
  double breite(uint16_t g) const {
    if (g >= glyphen) return 0;
    const uint8_t *h = tab("hmtx");
    const uint16_t i = g < metriken ? g : (uint16_t)(metriken - 1);
    return u16(h + 4u * i) * 1000.0 / einheiten;
  }
  // Breite eines Texts in pt (ohne Zeichen, die die Schrift nicht hat – die misst der Satz selbst).
  double breite(const std::string &t, double groesse) const {
    double b = 0;
    for (size_t i = 0; i < t.size();) b += breite(gid(naechstes(t, i)));
    return b * groesse / 1000.0;
  }
  void merke(uint16_t g, uint32_t u) {
    if (!g) return;
    benutzt.insert(g);
    zeichen.emplace(g, u);
  }

  // Die Teilmenge als TrueType-Datei (siehe oben).
  std::vector<uint8_t> teilmenge() const {
    // Benutzte Glyphen mit allen Bestandteilen (zusammengesetzte Glyphen, begrenzte Tiefe).
    std::set<uint16_t> alle(benutzt.begin(), benutzt.end());
    std::vector<uint16_t> offen(benutzt.begin(), benutzt.end());
    for (size_t runde = 0; !offen.empty() && runde < 100000; runde++) {
      const uint16_t g = offen.back();
      offen.pop_back();
      for (uint16_t k : bestandteile(g)) if (k < glyphen && alle.insert(k).second) offen.push_back(k);
    }
    std::vector<uint8_t> glyf, loca;
    for (uint32_t g = 0; g < glyphen; g++) {
      w32(loca, (uint32_t)glyf.size());
      if (!alle.count((uint16_t)g)) continue;
      uint32_t a, e;
      if (!lage((uint16_t)g, a, e)) continue;
      const uint8_t *q = tab("glyf");
      glyf.insert(glyf.end(), q + a, q + e);
      while (glyf.size() % 4) glyf.push_back(0);
    }
    w32(loca, (uint32_t)glyf.size());
    std::vector<uint8_t> head(tab("head"), tab("head") + 54);
    head[8] = head[9] = head[10] = head[11] = 0;  // checkSumAdjustment, unten neu
    head[50] = 0; head[51] = 1;                  // indexToLocFormat: lang
    std::map<std::string, std::vector<uint8_t>> t;
    t["head"] = head;
    t["hhea"] = kopie("hhea");
    t["maxp"] = kopie("maxp");
    t["hmtx"] = kopie("hmtx");
    t["loca"] = loca;
    t["glyf"] = glyf;
    t["cmap"] = neueCmap();
    std::vector<uint8_t> post;
    w32(post, 0x00030000);
    const uint8_t *alt = tabellen.count("post") ? tab("post") : nullptr;
    for (int k = 4; k < 32; k++) post.push_back(alt && tabellen.at("post").second >= 32 ? alt[k] : 0);
    t["post"] = post;
    if (tabellen.count("name")) t["name"] = kopie("name");
    if (tabellen.count("OS/2")) t["OS/2"] = kopie("OS/2");
    return datei(t);
  }

 private:
  std::vector<uint8_t> d;
  std::map<std::string, std::pair<uint32_t, uint32_t>> tabellen;
  std::map<uint32_t, uint16_t> cmap;
  bool langeLoca = false;
  uint16_t metriken = 0, glyphen = 0;

  const uint8_t *tab(const char *t) const { return &d[tabellen.at(t).first]; }
  uint32_t tabLaenge(const char *t) const { return tabellen.at(t).second; }
  std::vector<uint8_t> kopie(const char *t) const { return std::vector<uint8_t>(tab(t), tab(t) + tabLaenge(t)); }

  bool lage(uint16_t g, uint32_t &a, uint32_t &e) const {
    if (g >= glyphen) return false;
    const uint8_t *l = tab("loca");
    const uint32_t n = tabLaenge("loca");
    if (langeLoca) {
      if (4u * g + 8 > n) return false;
      a = u32(l + 4u * g); e = u32(l + 4u * g + 4);
    } else {
      if (2u * g + 4 > n) return false;
      a = 2u * u16(l + 2u * g); e = 2u * u16(l + 2u * g + 2);
    }
    return a <= e && e <= tabLaenge("glyf");
  }

  std::vector<uint16_t> bestandteile(uint16_t g) const {
    std::vector<uint16_t> r;
    uint32_t a, e;
    if (!lage(g, a, e) || e - a < 10) return r;
    const uint8_t *p = tab("glyf") + a, *ende = tab("glyf") + e;
    if (s16(p) >= 0) return r;  // einfache Glyphe
    p += 10;
    for (int n = 0; n < 64 && p + 4 <= ende; n++) {
      const uint16_t f = u16(p), k = u16(p + 2);
      r.push_back(k);
      p += 4 + ((f & 1) ? 4 : 2);
      if (f & 8) p += 2; else if (f & 0x40) p += 4; else if (f & 0x80) p += 8;
      if (!(f & 0x20)) break;
    }
    return r;
  }

  bool leseCmap() {
    const uint8_t *c = tab("cmap");
    const uint32_t n = tabLaenge("cmap");
    if (n < 4) return false;
    const uint16_t anzahl = u16(c + 2);
    uint32_t f4 = 0, f12 = 0;
    for (uint16_t i = 0; i < anzahl && 4 + 8u * i + 8 <= n; i++) {
      const uint16_t plattform = u16(c + 4 + 8 * i), kodierung = u16(c + 6 + 8 * i);
      const uint32_t ab = u32(c + 8 + 8 * i);
      if (ab + 4 > n) continue;
      const uint16_t format = u16(c + ab);
      if (format == 12 && ((plattform == 3 && kodierung == 10) || plattform == 0)) f12 = ab;
      if (format == 4 && ((plattform == 3 && kodierung == 1) || plattform == 0)) f4 = ab;
    }
    if (f12) {
      const uint8_t *q = c + f12;
      const uint32_t gruppen = u32(q + 12);
      for (uint32_t i = 0; i < gruppen && f12 + 16 + 12u * (i + 1) <= n; i++) {
        const uint32_t a = u32(q + 16 + 12 * i), e = u32(q + 20 + 12 * i), g = u32(q + 24 + 12 * i);
        for (uint32_t u = a; u <= e && u <= 0x10FFFF && u - a < 0x10000; u++) if (g + (u - a) < glyphen) cmap[u] = (uint16_t)(g + (u - a));
      }
      return !cmap.empty();
    }
    if (!f4) return false;
    const uint8_t *q = c + f4;
    const uint16_t segmente = u16(q + 6) / 2;
    const uint8_t *ende = q + 14, *anfang = ende + 2u * segmente + 2, *delta = anfang + 2u * segmente, *versatz = delta + 2u * segmente;
    if (f4 + 16 + 8u * segmente > n) return false;
    for (uint16_t s = 0; s < segmente; s++) {
      const uint16_t e = u16(ende + 2 * s), a = u16(anfang + 2 * s), dl = u16(delta + 2 * s), v = u16(versatz + 2 * s);
      for (uint32_t u = a; u <= e && u != 0xFFFF; u++) {
        uint16_t g;
        if (!v) g = (uint16_t)(u + dl);
        else {
          const size_t o = (size_t)(versatz - c) + 2u * s + v + 2u * (u - a);
          if (o + 2 > n) continue;
          g = u16(c + o);
          if (g) g = (uint16_t)(g + dl);
        }
        if (g && g < glyphen) cmap[u] = g;
      }
    }
    return !cmap.empty();
  }

  std::string psName() const {
    if (!tabellen.count("name")) return "Schrift";
    const uint8_t *n = tab("name");
    const uint32_t laenge = tabLaenge("name");
    const uint16_t anzahl = u16(n + 2), speicher = u16(n + 4);
    for (uint16_t i = 0; i < anzahl && 6 + 12u * (i + 1) <= laenge; i++) {
      const uint8_t *r = n + 6 + 12 * i;
      if (u16(r + 6) != 6) continue;  // PostScript-Name
      const uint16_t plattform = u16(r), l = u16(r + 8), o = u16(r + 10);
      if ((uint32_t)speicher + o + l > laenge) continue;
      std::string s;
      const uint8_t *p = n + speicher + o;
      for (uint16_t k = 0; k < l; k += plattform == 3 || plattform == 0 ? 2 : 1) {
        const char ch = (char)(plattform == 3 || plattform == 0 ? p[k + 1] : p[k]);
        if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '-') s += ch;
      }
      if (!s.empty()) return s;
    }
    return "Schrift";
  }

  // cmap (Format 4, Windows Unicode BMP) nur mit den benutzten Zeichen.
  std::vector<uint8_t> neueCmap() const {
    std::vector<std::pair<uint16_t, uint16_t>> paare;  // Zeichen → GID
    for (auto &z : zeichen) if (z.second < 0xFFFF) paare.push_back({(uint16_t)z.second, z.first});
    std::sort(paare.begin(), paare.end());
    paare.erase(std::unique(paare.begin(), paare.end(), [](auto &a, auto &b) { return a.first == b.first; }), paare.end());
    const uint16_t seg = (uint16_t)(paare.size() + 1);
    std::vector<uint8_t> f;
    w16(f, 4); w16(f, 0); w16(f, 0);  // Format, Länge (unten), Sprache
    uint16_t such = 1, stufe = 0;
    while (such * 2 <= seg) { such = (uint16_t)(such * 2); stufe++; }
    w16(f, seg * 2u); w16(f, such * 2u); w16(f, stufe); w16(f, seg * 2u - such * 2u);
    for (auto &p : paare) w16(f, p.first);
    w16(f, 0xFFFF);
    w16(f, 0);
    for (auto &p : paare) w16(f, p.first);
    w16(f, 0xFFFF);
    for (auto &p : paare) w16(f, (uint16_t)(p.second - p.first));
    w16(f, 1);
    for (size_t i = 0; i < seg; i++) w16(f, 0);
    f[2] = (uint8_t)(f.size() >> 8); f[3] = (uint8_t)f.size();
    std::vector<uint8_t> c;
    w16(c, 0); w16(c, 1); w16(c, 3); w16(c, 1); w32(c, 12);
    c.insert(c.end(), f.begin(), f.end());
    return c;
  }

  static uint32_t pruefsumme(const std::vector<uint8_t> &t) {
    uint32_t s = 0;
    for (size_t i = 0; i < t.size(); i += 4) {
      uint32_t w = 0;
      for (size_t k = 0; k < 4; k++) w = w << 8 | (i + k < t.size() ? t[i + k] : 0);
      s += w;
    }
    return s;
  }

  static std::vector<uint8_t> datei(const std::map<std::string, std::vector<uint8_t>> &t) {
    const uint16_t n = (uint16_t)t.size();
    uint16_t such = 1, stufe = 0;
    while (such * 2 <= n) { such = (uint16_t)(such * 2); stufe++; }
    std::vector<uint8_t> o;
    w32(o, 0x00010000); w16(o, n); w16(o, such * 16u); w16(o, stufe); w16(o, n * 16u - such * 16u);
    size_t ab = 12 + 16u * n, headAb = 0;
    for (auto &x : t) {  // std::map: nach Tag sortiert, wie verlangt
      o.insert(o.end(), x.first.begin(), x.first.end());
      w32(o, pruefsumme(x.second)); w32(o, (uint32_t)ab); w32(o, (uint32_t)x.second.size());
      if (x.first == "head") headAb = ab;
      ab += (x.second.size() + 3) & ~(size_t)3;
    }
    for (auto &x : t) {
      o.insert(o.end(), x.second.begin(), x.second.end());
      while (o.size() % 4) o.push_back(0);
    }
    const uint32_t anpassung = 0xB1B0AFBAu - pruefsumme(o);
    o[headAb + 8] = (uint8_t)(anpassung >> 24); o[headAb + 9] = (uint8_t)(anpassung >> 16);
    o[headAb + 10] = (uint8_t)(anpassung >> 8); o[headAb + 11] = (uint8_t)anpassung;
    return o;
  }
};

}  // namespace schrift
