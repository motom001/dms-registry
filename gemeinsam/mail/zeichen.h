// Zeichen und Text: UTF-8, Zeichensätze von E-Mails (Latin-1, Windows-1252, UTF-16), Base64, Quoted-Printable,
// HTML zu Text und ein Sammler, der den Volltext begrenzt und Leerraum ordnet. Ohne Bibliotheken.
#pragma once
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

namespace zeichen {

inline void utf8(std::string &s, uint32_t c) {
  if (c == 0 || (c >= 0xd800 && c < 0xe000) || c > 0x10ffff) c = 0xfffd;
  if (c < 0x80) s += (char)c;
  else if (c < 0x800) { s += (char)(0xc0 | c >> 6); s += (char)(0x80 | (c & 0x3f)); }
  else if (c < 0x10000) { s += (char)(0xe0 | c >> 12); s += (char)(0x80 | (c >> 6 & 0x3f)); s += (char)(0x80 | (c & 0x3f)); }
  else { s += (char)(0xf0 | c >> 18); s += (char)(0x80 | (c >> 12 & 0x3f)); s += (char)(0x80 | (c >> 6 & 0x3f)); s += (char)(0x80 | (c & 0x3f)); }
}

// Windows-1252: 0x80–0x9F (sonst wie Latin-1).
inline uint32_t cp1252(uint8_t b) {
  static const uint16_t t[32] = {0x20ac, 0xfffd, 0x201a, 0x0192, 0x201e, 0x2026, 0x2020, 0x2021, 0x02c6, 0x2030, 0x0160, 0x2039, 0x0152, 0xfffd, 0x017d, 0xfffd,
                                 0xfffd, 0x2018, 0x2019, 0x201c, 0x201d, 0x2022, 0x2013, 0x2014, 0x02dc, 0x2122, 0x0161, 0x203a, 0x0153, 0xfffd, 0x017e, 0x0178};
  return b >= 0x80 && b < 0xa0 ? t[b - 0x80] : b;
}

// Länge einer gültigen UTF-8-Folge ab p (0, wenn ungültig).
inline size_t utf8Folge(const uint8_t *p, size_t n) {
  uint8_t c = p[0];
  if (c < 0x80) return 1;
  size_t l = c >= 0xc2 && c < 0xe0 ? 2 : c >= 0xe0 && c < 0xf0 ? 3 : c >= 0xf0 && c < 0xf5 ? 4 : 0;
  if (!l || l > n) return 0;
  for (size_t i = 1; i < l; i++) if ((p[i] & 0xc0) != 0x80) return 0;
  if (l == 3 && ((c == 0xe0 && p[1] < 0xa0) || (c == 0xed && p[1] >= 0xa0))) return 0;
  if (l == 4 && ((c == 0xf0 && p[1] < 0x90) || (c == 0xf4 && p[1] >= 0x90))) return 0;
  return l;
}

inline bool istUtf8(const std::string &s) {
  const uint8_t *p = (const uint8_t *)s.data();
  for (size_t i = 0, n = s.size(); i < n;) { size_t l = utf8Folge(p + i, n - i); if (!l) return false; i += l; }
  return true;
}

// Gültiges UTF-8; ungültige Bytes gelten als Windows-1252 (häufigster Fall bei alten E-Mails und Texten).
inline std::string heile(const std::string &s) {
  std::string r;
  r.reserve(s.size());
  const uint8_t *p = (const uint8_t *)s.data();
  for (size_t i = 0, n = s.size(); i < n;) {
    size_t l = utf8Folge(p + i, n - i);
    if (l) { r.append(s, i, l); i += l; } else { utf8(r, cp1252(p[i])); i++; }
  }
  return r;
}

inline std::string klein(std::string s) {
  for (char &c : s) if (c >= 'A' && c <= 'Z') c = (char)(c - 'A' + 'a');
  return s;
}

inline std::string utf16le(const uint8_t *p, size_t n) {
  std::string r;
  for (size_t i = 0; i + 1 < n; i += 2) {
    uint32_t c = p[i] | p[i + 1] << 8;
    if (c >= 0xd800 && c < 0xdc00 && i + 3 < n) {
      uint32_t d = p[i + 2] | p[i + 3] << 8;
      if (d >= 0xdc00 && d < 0xe000) { c = 0x10000 + ((c - 0xd800) << 10) + (d - 0xdc00); i += 2; }
    }
    utf8(r, c);
  }
  return r;
}

inline std::string utf16be(const uint8_t *p, size_t n) {
  std::vector<uint8_t> v(p, p + (n & ~(size_t)1));
  for (size_t i = 0; i + 1 < v.size(); i += 2) std::swap(v[i], v[i + 1]);
  return utf16le(v.data(), v.size());
}

// Text in einem Zeichensatz (Namen wie in E-Mails) nach UTF-8. Unbekannte: gültiges UTF-8 bleibt, sonst Windows-1252.
inline std::string nachUtf8(const std::string &s, std::string cs) {
  cs = klein(cs);
  const uint8_t *p = (const uint8_t *)s.data();
  if (cs == "utf-16" || cs == "utf-16le" || cs == "unicode") {
    if (s.size() >= 2 && p[0] == 0xfe && p[1] == 0xff) return utf16be(p + 2, s.size() - 2);
    if (s.size() >= 2 && p[0] == 0xff && p[1] == 0xfe) return utf16le(p + 2, s.size() - 2);
    return utf16le(p, s.size());
  }
  if (cs == "utf-16be") return utf16be(p, s.size());
  if (cs == "iso-8859-1" || cs == "latin1" || cs == "iso_8859-1" || cs == "l1") {
    std::string r;
    for (uint8_t b : s) utf8(r, b);
    return r;
  }
  if (cs == "windows-1252" || cs == "cp1252" || cs == "iso-8859-15" || cs == "us-ascii" || cs == "ascii") {
    std::string r;
    for (uint8_t b : s) {
      uint32_t c = cp1252(b);
      if (cs == "iso-8859-15") { if (b == 0xa4) c = 0x20ac; else if (b == 0xa6) c = 0x160; else if (b == 0xa8) c = 0x161; else if (b == 0xb4) c = 0x17d; else if (b == 0xb8) c = 0x17e; else if (b == 0xbc) c = 0x152; else if (b == 0xbd) c = 0x153; else if (b == 0xbe) c = 0x178; else if (b >= 0x80 && b < 0xa0) c = b; }
      utf8(r, c);
    }
    return r;
  }
  return heile(s);
}

inline int hexwert(char c) {
  return c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1;
}

inline std::string base64(const char *p, size_t n) {
  std::string r;
  uint32_t puffer = 0;
  int bits = 0;
  for (size_t i = 0; i < n; i++) {
    char c = p[i];
    int v = c >= 'A' && c <= 'Z' ? c - 'A' : c >= 'a' && c <= 'z' ? c - 'a' + 26 : c >= '0' && c <= '9' ? c - '0' + 52 : c == '+' || c == '-' ? 62 : c == '/' || c == '_' ? 63 : -1;
    if (c == '=') break;
    if (v < 0) continue;
    puffer = puffer << 6 | (uint32_t)v;
    bits += 6;
    if (bits >= 8) { bits -= 8; r += (char)(puffer >> bits & 0xff); }
  }
  return r;
}

// Quoted-Printable; `kopf`: Variante aus RFC 2047 („_“ ist ein Leerzeichen).
inline std::string quotedPrintable(const char *p, size_t n, bool kopf = false) {
  std::string r;
  for (size_t i = 0; i < n; i++) {
    char c = p[i];
    if (c == '=' && i + 1 < n && (p[i + 1] == '\n' || p[i + 1] == '\r')) {  // weicher Zeilenumbruch
      i++;
      if (p[i] == '\r' && i + 1 < n && p[i + 1] == '\n') i++;
    } else if (c == '=' && i + 2 < n && hexwert(p[i + 1]) >= 0 && hexwert(p[i + 2]) >= 0) {
      r += (char)(hexwert(p[i + 1]) << 4 | hexwert(p[i + 2]));
      i += 2;
    } else if (kopf && c == '_') r += ' ';
    else r += c;
  }
  return r;
}

// Benannte Zeichen in HTML und XML (die häufigen; der Rest bleibt stehen).
inline uint32_t entitaet(const std::string &n) {
  static const struct { const char *n; uint16_t c; } t[] = {
      {"amp", '&'}, {"lt", '<'}, {"gt", '>'}, {"quot", '"'}, {"apos", '\''}, {"nbsp", 0xa0}, {"euro", 0x20ac}, {"copy", 0xa9},
      {"reg", 0xae}, {"sect", 0xa7}, {"deg", 0xb0}, {"para", 0xb6}, {"middot", 0xb7}, {"laquo", 0xab}, {"raquo", 0xbb}, {"shy", 0xad},
      {"auml", 0xe4}, {"ouml", 0xf6}, {"uuml", 0xfc}, {"Auml", 0xc4}, {"Ouml", 0xd6}, {"Uuml", 0xdc}, {"szlig", 0xdf},
      {"eacute", 0xe9}, {"egrave", 0xe8}, {"ecirc", 0xea}, {"aacute", 0xe1}, {"agrave", 0xe0}, {"acirc", 0xe2}, {"ccedil", 0xe7},
      {"Eacute", 0xc9}, {"oacute", 0xf3}, {"iacute", 0xed}, {"uacute", 0xfa}, {"ntilde", 0xf1}, {"ocirc", 0xf4}, {"icirc", 0xee},
      {"ndash", 0x2013}, {"mdash", 0x2014}, {"hellip", 0x2026}, {"bdquo", 0x201e}, {"ldquo", 0x201c}, {"rdquo", 0x201d},
      {"sbquo", 0x201a}, {"lsquo", 0x2018}, {"rsquo", 0x2019}, {"bull", 0x2022}, {"times", 0xd7}, {"frac12", 0xbd}, {"micro", 0xb5}};
  for (auto &e : t) if (n == e.n) return e.c;
  return 0;
}

// „&…;“ ab p[i] (p[i] == '&'); hängt das Zeichen an r und liefert die Länge, oder 0.
inline size_t entitaetLesen(const char *p, size_t n, std::string &r) {
  size_t e = 1;
  while (e < n && e < 12 && p[e] != ';') e++;
  if (e >= n || p[e] != ';') return 0;
  std::string name(p + 1, e - 1);
  uint32_t c = 0;
  if (name.size() > 1 && name[0] == '#') {
    bool hex = name[1] == 'x' || name[1] == 'X';
    for (size_t i = hex ? 2 : 1; i < name.size(); i++) {
      int v = hex ? hexwert(name[i]) : (name[i] >= '0' && name[i] <= '9' ? name[i] - '0' : -1);
      if (v < 0 || c > 0x10ffff) return 0;
      c = c * (hex ? 16 : 10) + (uint32_t)v;
    }
  } else c = entitaet(name);
  if (!c) return 0;
  utf8(r, c == 0xa0 ? ' ' : c);
  return e + 1;
}

// Sammelt den Volltext: höchstens `max` Bytes, Leerzeichen am Zeilenende weg, höchstens eine Leerzeile am Stück.
class Sammler {
  std::string t;
  size_t max;
  int umbrueche = 2;  // am Anfang keine Leerzeilen
  bool leer = false;
 public:
  bool voll = false;
  explicit Sammler(size_t m) : max(m) {}
  void zeichen(char c) {
    if (voll) return;
    if (c == '\r') return;
    if (c == '\n' || c == '\f') {
      while (!t.empty() && (t.back() == ' ' || t.back() == '\t')) t.pop_back();
      leer = false;
      if (umbrueche < 2) { t += '\n'; umbrueche++; }
      return;
    }
    if (c == ' ' || c == '\t' || (unsigned char)c < 0x20) {
      if (umbrueche == 0 && !leer) leer = true;
      return;
    }
    if (leer) { t += c == '\t' ? '\t' : ' '; leer = false; }
    umbrueche = 0;
    t += c;
    if (t.size() >= max) voll = true;
  }
  void text(const std::string &s) { for (char c : s) { if (voll) return; zeichen(c); } }
  void zeile() { zeichen('\n'); }
  void absatz() { zeichen('\n'); zeichen('\n'); }
  void tab() { if (umbrueche == 0) leer = true; }
  size_t groesse() const { return t.size(); }
  std::string fertig() {
    std::string r = heile(t);
    if (r.size() > max) {  // nicht mitten in einem Zeichen abschneiden
      size_t n = max;
      while (n > 0 && ((uint8_t)r[n] & 0xc0) == 0x80) n--;
      r.resize(n);
    }
    while (!r.empty() && (r.back() == '\n' || r.back() == ' ')) r.pop_back();
    return r;
  }
};

// HTML zu Text: Tags weg, Inhalte von script/style/head weg, Blöcke als Zeilen, Zellen mit Abstand.
inline void html(const std::string &h, Sammler &s) {
  const char *p = h.data();
  const size_t n = h.size();
  for (size_t i = 0; i < n && !s.voll;) {
    if (p[i] == '<') {
      if (i + 3 < n && !strncmp(p + i, "<!--", 4)) {
        const char *e = strstr(p + i + 4, "-->");
        i = e && (size_t)(e - p) < n ? (size_t)(e - p) + 3 : n;
        continue;
      }
      size_t j = i + 1;
      bool zu = j < n && p[j] == '/';
      if (zu) j++;
      std::string name;
      while (j < n && name.size() < 16 && ((p[j] >= 'a' && p[j] <= 'z') || (p[j] >= 'A' && p[j] <= 'Z') || (p[j] >= '0' && p[j] <= '9'))) name += p[j++];
      name = klein(name);
      size_t e = j;
      char q = 0;
      while (e < n && (q || p[e] != '>')) { if (q && p[e] == q) q = 0; else if (!q && (p[e] == '"' || p[e] == '\'')) q = p[e]; e++; }
      i = e < n ? e + 1 : n;
      if (!zu && (name == "script" || name == "style" || name == "head" || name == "title")) {
        std::string ende = "</" + name;
        size_t k = i;
        while (k < n) {
          const char *f = strchr(p + k, '<');
          if (!f || (size_t)(f - p) >= n) { k = n; break; }
          k = (size_t)(f - p);
          if (k + ende.size() <= n && klein(std::string(p + k, ende.size())) == ende) break;
          k++;
        }
        if (k >= n) continue;  // nie geschlossen: nur das Tag selbst weglassen
        const char *f = strchr(p + k, '>');
        i = f && (size_t)(f - p) < n ? (size_t)(f - p) + 1 : n;
        continue;
      }
      if (name == "br" || name == "tr" || name == "li") s.zeile();
      else if (name == "p" || name == "div" || name == "h1" || name == "h2" || name == "h3" || name == "h4" || name == "table" || name == "blockquote") s.absatz();
      else if (name == "td" || name == "th") s.tab();
      continue;
    }
    if (p[i] == '&') {
      std::string z;
      size_t l = entitaetLesen(p + i, n - i, z);
      if (l) { s.text(z); i += l; continue; }
    }
    s.zeichen(p[i] == '\n' || p[i] == '\r' ? ' ' : p[i]);
    i++;
  }
}

}  // namespace zeichen
