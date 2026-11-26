// Kleiner JSON-Leser für die Eingaben des DMS (ohne Ausnahmen, ohne Abhängigkeiten).
#pragma once
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <memory>
#include <string>
#include <vector>

struct Json {
  enum Art { NUL, BOOL, ZAHL, TEXT, LISTE, OBJEKT } art = NUL;
  bool b = false;
  double z = 0;
  std::string t;
  std::vector<Json> l;
  std::map<std::string, Json> o;

  const Json &operator[](const char *k) const {
    static const Json leer;
    if (art != OBJEKT) return leer;
    auto i = o.find(k);
    return i == o.end() ? leer : i->second;
  }
  std::string text(const char *standard = "") const { return art == TEXT ? t : standard; }
  bool wahr(bool standard = false) const { return art == BOOL ? b : standard; }
  double zahl(double standard = 0) const { return art == ZAHL ? z : standard; }
};

class JsonLeser {
  const char *p, *ende;
  int tiefe = 0;
  bool fehler = false;
  void leer() { while (p < ende && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) p++; }
  static void utf8(std::string &s, unsigned c) {
    if (c < 0x80) s += (char)c;
    else if (c < 0x800) { s += (char)(0xc0 | c >> 6); s += (char)(0x80 | (c & 0x3f)); }
    else if (c < 0x10000) { s += (char)(0xe0 | c >> 12); s += (char)(0x80 | (c >> 6 & 0x3f)); s += (char)(0x80 | (c & 0x3f)); }
    else { s += (char)(0xf0 | c >> 18); s += (char)(0x80 | (c >> 12 & 0x3f)); s += (char)(0x80 | (c >> 6 & 0x3f)); s += (char)(0x80 | (c & 0x3f)); }
  }
  unsigned hex4() {
    if (ende - p < 4) { fehler = true; return 0; }
    unsigned v = 0;
    for (int i = 0; i < 4; i++) {
      char c = *p++; v <<= 4;
      if (c >= '0' && c <= '9') v |= c - '0'; else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10; else if (c >= 'A' && c <= 'F') v |= c - 'A' + 10; else fehler = true;
    }
    return v;
  }
  std::string zeichenkette() {
    std::string s;
    p++;
    while (p < ende && *p != '"') {
      if (*p == '\\' && p + 1 < ende) {
        p++;
        char c = *p++;
        switch (c) {
          case 'n': s += '\n'; break; case 't': s += '\t'; break; case 'r': s += '\r'; break;
          case 'b': s += '\b'; break; case 'f': s += '\f'; break;
          case 'u': {
            unsigned u = hex4();
            if (u >= 0xd800 && u < 0xdc00 && ende - p >= 6 && p[0] == '\\' && p[1] == 'u') { p += 2; unsigned v = hex4(); u = 0x10000 + ((u - 0xd800) << 10) + (v - 0xdc00); }
            utf8(s, u);
            break;
          }
          default: s += c;
        }
      } else s += *p++;
    }
    if (p >= ende) fehler = true; else p++;
    return s;
  }
  Json wert() {
    Json j;
    leer();
    if (p >= ende || ++tiefe > 64) { fehler = true; return j; }
    if (*p == '{') {
      j.art = Json::OBJEKT; p++; leer();
      if (p < ende && *p == '}') { p++; tiefe--; return j; }
      while (!fehler) {
        leer();
        if (p >= ende || *p != '"') { fehler = true; break; }
        std::string k = zeichenkette(); leer();
        if (p >= ende || *p != ':') { fehler = true; break; }
        p++;
        j.o[k] = wert(); leer();
        if (p < ende && *p == ',') { p++; continue; }
        if (p < ende && *p == '}') { p++; break; }
        fehler = true;
      }
    } else if (*p == '[') {
      j.art = Json::LISTE; p++; leer();
      if (p < ende && *p == ']') { p++; tiefe--; return j; }
      while (!fehler) {
        j.l.push_back(wert()); leer();
        if (p < ende && *p == ',') { p++; continue; }
        if (p < ende && *p == ']') { p++; break; }
        fehler = true;
      }
    } else if (*p == '"') { j.art = Json::TEXT; j.t = zeichenkette(); }
    else if (ende - p >= 4 && !strncmp(p, "true", 4)) { j.art = Json::BOOL; j.b = true; p += 4; }
    else if (ende - p >= 5 && !strncmp(p, "false", 5)) { j.art = Json::BOOL; p += 5; }
    else if (ende - p >= 4 && !strncmp(p, "null", 4)) { p += 4; }
    else {
      char *e; std::string zahl(p, (size_t)std::min<long>(ende - p, 64));
      j.z = strtod(zahl.c_str(), &e);
      if (e == zahl.c_str()) fehler = true; else { j.art = Json::ZAHL; p += e - zahl.c_str(); }
    }
    tiefe--;
    return j;
  }
 public:
  // Liest JSON; bei Fehlern ein leeres Objekt.
  static Json lies(const char *text, size_t n) {
    JsonLeser l; l.p = text; l.ende = text + n;
    Json j = l.wert();
    return l.fehler ? Json{} : j;
  }
};

// Text als JSON-Zeichenkette (mit Anführungszeichen).
inline std::string jsonText(const std::string &s) {
  std::string r = "\"";
  for (unsigned char c : s) {
    switch (c) {
      case '"': r += "\\\""; break; case '\\': r += "\\\\"; break; case '\n': r += "\\n"; break;
      case '\r': r += "\\r"; break; case '\t': r += "\\t"; break; case '\f': r += "\\f"; break;
      default:
        if (c < 0x20) { char b[8]; snprintf(b, sizeof b, "\\u%04x", c); r += b; } else r += (char)c;
    }
  }
  return r + "\"";
}
