// XML lesen, so weit es für Text aus Office-Dateien reicht: Tags, Attribute, Text mit den fünf XML-Entitäten und
// Zeichenreferenzen. Eine DOCTYPE-Angabe wird übersprungen – keine eigenen Entitäten, keine externen Verweise (XXE),
// nichts wird nachgeladen.
#pragma once
#include <cstring>
#include <string>

#include "zeichen.h"

namespace xml {

struct Teil {
  enum Art { ENDE, AUF, ZU, TEXT } art = ENDE;
  std::string name;  // mit Präfix, z. B. „w:t“
  std::string attribute;
  std::string text;
  bool leer = false;  // <x/>
  // Wert eines Attributs (mit Präfix, z. B. „r:id“), Entitäten aufgelöst; leer, wenn es fehlt.
  std::string attribut(const char *n) const {
    const size_t l = strlen(n);
    for (size_t i = 0; i + l < attribute.size(); i++) {
      if ((i == 0 || attribute[i - 1] == ' ' || attribute[i - 1] == '\t' || attribute[i - 1] == '\n' || attribute[i - 1] == '\r') &&
          !attribute.compare(i, l, n)) {
        size_t j = i + l;
        while (j < attribute.size() && attribute[j] == ' ') j++;
        if (j >= attribute.size() || attribute[j] != '=') continue;
        j++;
        while (j < attribute.size() && attribute[j] == ' ') j++;
        if (j >= attribute.size() || (attribute[j] != '"' && attribute[j] != '\'')) continue;
        const char q = attribute[j];
        const size_t e = attribute.find(q, j + 1);
        if (e == std::string::npos) return "";
        return entschluesseln(attribute.data() + j + 1, e - j - 1);
      }
    }
    return "";
  }
  static std::string entschluesseln(const char *p, size_t n) {
    std::string r;
    for (size_t i = 0; i < n;) {
      if (p[i] == '&') {
        size_t l = zeichen::entitaetLesen(p + i, n - i, r);
        if (l) { i += l; continue; }
      }
      r += p[i++];
    }
    return r;
  }
};

class Leser {
  const char *p, *ende;
 public:
  Leser(const std::string &s) : p(s.data()), ende(s.data() + s.size()) {}
  Leser(const char *d, size_t n) : p(d), ende(d + n) {}

  Teil naechster() {
    Teil t;
    while (p < ende) {
      if (*p != '<') {
        const char *a = p;
        while (p < ende && *p != '<') p++;
        t.art = Teil::TEXT;
        t.text = Teil::entschluesseln(a, (size_t)(p - a));
        return t;
      }
      const size_t rest = (size_t)(ende - p);
      if (rest >= 4 && !strncmp(p, "<!--", 4)) { p = suche(p + 4, "-->"); continue; }
      if (rest >= 9 && !strncmp(p, "<![CDATA[", 9)) {
        const char *a = p + 9;
        const char *e = finde(a, "]]>");
        t.art = Teil::TEXT;
        t.text.assign(a, (size_t)(e - a));
        p = e < ende ? e + 3 : ende;
        return t;
      }
      if (rest >= 2 && p[1] == '?') { p = suche(p + 2, "?>"); continue; }
      if (rest >= 2 && p[1] == '!') {  // DOCTYPE (auch mit [ … ]): überspringen, nichts davon gilt
        int klammer = 0;
        p += 2;
        while (p < ende && (klammer > 0 || *p != '>')) { if (*p == '[') klammer++; else if (*p == ']') klammer--; p++; }
        if (p < ende) p++;
        continue;
      }
      p++;
      const bool zu = p < ende && *p == '/';
      if (zu) p++;
      const char *a = p;
      while (p < ende && *p != '>' && *p != '/' && *p != ' ' && *p != '\t' && *p != '\n' && *p != '\r') p++;
      t.name.assign(a, (size_t)(p - a));
      const char *b = p;
      char q = 0;
      while (p < ende && (q || *p != '>')) { if (q && *p == q) q = 0; else if (!q && (*p == '"' || *p == '\'')) q = *p; p++; }
      const char *e = p;
      if (e > b && e[-1] == '/') { t.leer = true; e--; }
      t.attribute.assign(b, (size_t)(e - b));
      if (p < ende) p++;
      t.art = zu ? Teil::ZU : Teil::AUF;
      return t;
    }
    t.art = Teil::ENDE;
    return t;
  }

 private:
  const char *finde(const char *a, const char *muster) const {
    const size_t l = strlen(muster);
    for (const char *x = a; x + l <= ende; x++) if (!memcmp(x, muster, l)) return x;
    return ende;
  }
  const char *suche(const char *a, const char *muster) const {
    const char *e = finde(a, muster);
    return e < ende ? e + strlen(muster) : ende;
  }
};

// Name ohne Präfix („w:t“ → „t“).
inline std::string lokal(const std::string &n) {
  size_t i = n.find(':');
  return i == std::string::npos ? n : n.substr(i + 1);
}

}  // namespace xml
