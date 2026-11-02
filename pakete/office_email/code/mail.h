// Text aus E-Mails: .eml (Internet-Nachricht nach RFC 5322 mit MIME) und .msg (Outlook, Compound File).
// Kopf (Von, An, Cc, Datum, Betreff), Text der Nachricht (Klartext bevorzugt, sonst HTML ohne Tags), Namen der
// Anhänge – und der Text von Anhängen, die das Paket selbst liest (Office, Text, weitere E-Mails; begrenzte Tiefe).
// Nichts wird ausgeführt: kein Skript aus HTML, keine Links, keine Bilder, nichts aus dem Netz.
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "cfb.h"
#include "zeichen.h"

namespace mail {

struct Ergebnis {
  std::string fehler;
  int anhaenge = 0;
  bool verschluesselt = false;
};

constexpr int TIEFE_MAX = 3;      // E-Mail im Anhang einer E-Mail im Anhang …
constexpr int MIME_TIEFE_MAX = 12;

}  // namespace mail

// Text eines Anhangs, wenn das Paket den Typ liest (erkennen.h). Liefert, ob etwas gelesen wurde.
inline bool anhangText(const std::string &name, const std::string &daten, zeichen::Sammler &s, int tiefe);

namespace mail {

/* ---------- Kopfzeilen ---------- */

// RFC 2047: =?charset?B|Q?…?= – Leerraum zwischen zwei kodierten Wörtern fällt weg.
inline std::string kopfText(const std::string &w) {
  std::string r, zwischen;
  bool zuletztKodiert = false;
  for (size_t i = 0; i < w.size();) {
    if (w.compare(i, 2, "=?") == 0) {
      size_t a = w.find('?', i + 2);
      size_t b = a == std::string::npos ? a : w.find('?', a + 1);
      size_t e = b == std::string::npos ? b : w.find("?=", b + 1);
      if (e != std::string::npos && b == a + 2) {
        std::string cs = w.substr(i + 2, a - i - 2);
        const size_t stern = cs.find('*');
        if (stern != std::string::npos) cs.resize(stern);
        const char art = (char)(w[a + 1] | 0x20);
        const std::string roh = w.substr(b + 1, e - b - 1);
        const std::string bytes = art == 'b' ? zeichen::base64(roh.data(), roh.size()) : zeichen::quotedPrintable(roh.data(), roh.size(), true);
        if (!zuletztKodiert) r += zwischen;
        zwischen.clear();
        r += zeichen::nachUtf8(bytes, cs);
        zuletztKodiert = true;
        i = e + 2;
        continue;
      }
    }
    if (w[i] == ' ' || w[i] == '\t') { zwischen += ' '; i++; continue; }
    r += zwischen; zwischen.clear();
    zuletztKodiert = false;
    r += w[i++];
  }
  return zeichen::heile(r + zwischen);
}

struct Kopf {
  std::vector<std::pair<std::string, std::string>> felder;  // Name klein, Wert (ungefaltet, roh)
  std::string wert(const char *n) const {
    for (auto &f : felder) if (f.first == n) return f.second;
    return "";
  }
};

// Kopf und Körper trennen (erste Leerzeile); Folgezeilen gehören zum Feld davor.
inline Kopf kopfLesen(const std::string &t, size_t &koerper) {
  Kopf k;
  size_t i = 0;
  if (t.compare(0, 5, "From ") == 0) {  // Trennzeile aus einem mbox-Postfach
    i = t.find('\n');
    i = i == std::string::npos ? t.size() : i + 1;
  }
  while (i < t.size()) {
    size_t e = t.find('\n', i);
    if (e == std::string::npos) e = t.size();
    std::string z = t.substr(i, e - i);
    if (!z.empty() && z.back() == '\r') z.pop_back();
    i = e + 1;
    if (z.empty()) break;
    if ((z[0] == ' ' || z[0] == '\t') && !k.felder.empty()) { k.felder.back().second += " " + z.substr(z.find_first_not_of(" \t")); continue; }
    const size_t d = z.find(':');
    if (d == std::string::npos || d == 0) continue;
    std::string wert = z.substr(d + 1);
    const size_t a = wert.find_first_not_of(" \t");
    k.felder.push_back({zeichen::klein(z.substr(0, d)), a == std::string::npos ? "" : wert.substr(a)});
  }
  koerper = std::min(i, t.size());
  return k;
}

// Parameter eines Felds wie Content-Type (auch RFC 2231: name*=utf-8''…, name*0=…).
inline std::string parameter(const std::string &feld, const std::string &name) {
  std::string ergebnis, teile;
  bool kodiert = false;
  std::string cs;
  size_t i = feld.find(';');
  while (i != std::string::npos && i < feld.size()) {
    i++;
    while (i < feld.size() && (feld[i] == ' ' || feld[i] == '\t')) i++;
    const size_t gleich = feld.find('=', i);
    if (gleich == std::string::npos) break;
    std::string n = zeichen::klein(feld.substr(i, gleich - i));
    while (!n.empty() && n.back() == ' ') n.pop_back();
    size_t j = gleich + 1;
    while (j < feld.size() && feld[j] == ' ') j++;
    std::string w;
    if (j < feld.size() && feld[j] == '"') {
      j++;
      while (j < feld.size() && feld[j] != '"') { if (feld[j] == '\\' && j + 1 < feld.size()) j++; w += feld[j++]; }
      j = feld.find(';', j);
    } else {
      size_t e = feld.find(';', j);
      w = feld.substr(j, e == std::string::npos ? std::string::npos : e - j);
      while (!w.empty() && (w.back() == ' ' || w.back() == '\t')) w.pop_back();
      j = e;
    }
    i = j;
    if (n == name) ergebnis = w;
    else if (n.compare(0, name.size() + 1, name + "*") == 0) {
      // name* oder name*0, name*1*, …: zusammensetzen; mit * am Ende prozentkodiert, im ersten Teil „charset'sprache'“.
      const bool pk = n.back() == '*';
      if (pk && cs.empty() && teile.empty()) {
        const size_t a = w.find('\''), b = a == std::string::npos ? a : w.find('\'', a + 1);
        if (b != std::string::npos) { cs = w.substr(0, a); w = w.substr(b + 1); }
      }
      if (pk) {
        kodiert = true;
        std::string x;
        for (size_t k = 0; k < w.size(); k++) {
          if (w[k] == '%' && k + 2 < w.size() && zeichen::hexwert(w[k + 1]) >= 0 && zeichen::hexwert(w[k + 2]) >= 0) { x += (char)(zeichen::hexwert(w[k + 1]) << 4 | zeichen::hexwert(w[k + 2])); k += 2; }
          else x += w[k];
        }
        w = x;
      }
      teile += w;
    }
  }
  if (!teile.empty()) return kodiert ? zeichen::nachUtf8(teile, cs.empty() ? "utf-8" : cs) : teile;
  return kopfText(ergebnis);
}

inline std::string feldOhneParameter(const std::string &f) {
  std::string r = zeichen::klein(f.substr(0, f.find(';')));
  while (!r.empty() && (r.back() == ' ' || r.back() == '\t')) r.pop_back();
  return r;
}

inline std::string transferDekodieren(const std::string &k, const std::string &kodierung) {
  const std::string c = zeichen::klein(kodierung);
  if (c.find("base64") != std::string::npos) return zeichen::base64(k.data(), k.size());
  if (c.find("quoted-printable") != std::string::npos) return zeichen::quotedPrintable(k.data(), k.size());
  return k;
}

/* ---------- MIME ---------- */

inline void nachricht(const std::string &t, zeichen::Sammler &s, Ergebnis &e, int tiefe, int mime);

inline void kopfZeigen(const Kopf &k, zeichen::Sammler &s) {
  static const char *felder[][2] = {{"from", "Von"}, {"to", "An"}, {"cc", "Cc"}, {"date", "Datum"}, {"subject", "Betreff"}};
  for (auto &f : felder) {
    const std::string w = k.wert(f[0]);
    if (w.empty()) continue;
    s.text(std::string(f[1]) + ": " + kopfText(w));
    s.zeile();
  }
  s.absatz();
}

inline void teil(const Kopf &k, const std::string &koerper, zeichen::Sammler &s, Ergebnis &e, int tiefe, int mime) {
  if (s.voll) return;
  const std::string ct = k.wert("content-type");
  std::string typ = ct.empty() ? "text/plain" : feldOhneParameter(ct);
  const std::string dispo = k.wert("content-disposition");
  std::string name = parameter(dispo, "filename");
  if (name.empty()) name = parameter(ct, "name");
  const bool anhang = feldOhneParameter(dispo) == "attachment" || (!name.empty() && typ.compare(0, 5, "text/") != 0) || (!name.empty() && feldOhneParameter(dispo) != "inline");

  if (typ == "multipart/encrypted" || typ == "application/pkcs7-mime" || typ == "application/x-pkcs7-mime") {
    e.verschluesselt = true;
    s.absatz(); s.text("(verschlüsselter Inhalt)"); s.zeile();
    return;
  }
  if (typ.compare(0, 10, "multipart/") == 0) {
    const std::string grenze = parameter(ct, "boundary");
    if (grenze.empty() || mime >= MIME_TIEFE_MAX) { s.text(koerper); return; }
    const std::string trenner = "--" + grenze;
    std::vector<std::pair<Kopf, std::string>> teile;
    size_t p = koerper.find(trenner);
    while (p != std::string::npos) {
      size_t a = p + trenner.size();
      if (koerper.compare(a, 2, "--") == 0) break;
      a = koerper.find('\n', a);
      if (a == std::string::npos) break;
      a++;
      size_t b = koerper.find("\n" + trenner, a);
      std::string inhalt = koerper.substr(a, b == std::string::npos ? std::string::npos : b - a + 1);
      size_t kb = 0;
      Kopf tk = kopfLesen(inhalt, kb);
      teile.push_back({tk, inhalt.substr(kb)});
      if (b == std::string::npos) break;
      p = b + 1;
    }
    if (typ == "multipart/alternative") {
      // Eine Fassung genügt: Klartext, sonst HTML, sonst die letzte.
      int wahl = -1;
      for (size_t i = 0; i < teile.size(); i++) if (feldOhneParameter(teile[i].first.wert("content-type")) == "text/plain") { wahl = (int)i; break; }
      if (wahl < 0) for (size_t i = 0; i < teile.size(); i++) if (feldOhneParameter(teile[i].first.wert("content-type")) == "text/html") { wahl = (int)i; break; }
      if (wahl < 0 && !teile.empty()) wahl = (int)teile.size() - 1;
      if (wahl >= 0) teil(teile[(size_t)wahl].first, teile[(size_t)wahl].second, s, e, tiefe, mime + 1);
      return;
    }
    for (auto &t : teile) { teil(t.first, t.second, s, e, tiefe, mime + 1); s.zeile(); }
    return;
  }
  std::string daten = transferDekodieren(koerper, k.wert("content-transfer-encoding"));
  if (typ == "message/rfc822" && !anhang) {
    s.absatz();
    if (tiefe < TIEFE_MAX) nachricht(daten, s, e, tiefe + 1, mime + 1);
    return;
  }
  if (anhang || (typ.compare(0, 5, "text/") != 0 && typ != "message/rfc822")) {
    e.anhaenge++;
    s.absatz();
    s.text("Anhang: " + (!name.empty() ? name : typ == "message/rfc822" ? std::string("E-Mail") : typ));
    s.zeile();
    if (tiefe < TIEFE_MAX) anhangText(typ == "message/rfc822" ? "anhang.eml" : name, daten, s, tiefe + 1);
    return;
  }
  const std::string cs = parameter(ct, "charset");
  const std::string text = zeichen::nachUtf8(daten, cs.empty() ? "utf-8" : cs);
  if (typ == "text/html") zeichen::html(text, s);
  else s.text(text);
  s.zeile();
}

inline void nachricht(const std::string &t, zeichen::Sammler &s, Ergebnis &e, int tiefe, int mime) {
  size_t kb = 0;
  Kopf k = kopfLesen(t, kb);
  kopfZeigen(k, s);
  teil(k, t.substr(kb), s, e, tiefe, mime);
}

// Sieht der Anfang aus wie eine Internet-Nachricht (Kopfzeilen mit From/Date/Subject/Received …)?
// `hinweis`: Dateityp oder Endung sagen „E-Mail“ – dann genügt ein bekanntes Kopffeld (etwa nur Content-Type).
inline bool istEml(const uint8_t *d, size_t n, bool hinweis = false) {
  std::string t((const char *)d, std::min<size_t>(n, 16384));
  if (t.compare(0, 5, "From ") == 0) t.erase(0, std::min(t.size(), t.find('\n') + 1));
  size_t kb = 0;
  Kopf k = kopfLesen(t, kb);
  int bekannt = 0;
  for (auto &f : k.felder)
    if (f.first == "from" || f.first == "date" || f.first == "subject" || f.first == "to" || f.first == "received" || f.first == "message-id" || f.first == "mime-version" || f.first == "return-path" || f.first == "content-type")
      bekannt++;
  // Die erste Zeile muss ein Kopffeld sein (sonst ist es Text, der irgendwo „From:“ enthält).
  const size_t d1 = t.find(':'), z1 = t.find('\n');
  if (d1 == std::string::npos || (z1 != std::string::npos && d1 > z1) || t.find(' ') < d1) return false;
  return bekannt >= (hinweis ? 1 : 2) && kb > 0;
}

inline Ergebnis eml(const std::string &t, zeichen::Sammler &s, int tiefe = 0) {
  Ergebnis e;
  nachricht(t, s, e, tiefe, 0);
  return e;
}

/* ---------- Outlook (.msg) ---------- */

// FILETIME (100 ns seit 1601) → „JJJJ-MM-TT HH:MM UTC“
inline std::string filetime(uint64_t ft) {
  if (!ft) return "";
  int64_t sek = (int64_t)(ft / 10000000ull) - 11644473600ll;
  int64_t tage = sek / 86400, rest = sek % 86400;
  if (rest < 0) { rest += 86400; tage--; }
  // Tage seit 1970 → Datum (Howard Hinnant, civil_from_days)
  tage += 719468;
  const int64_t era = (tage >= 0 ? tage : tage - 146096) / 146097;
  const unsigned doe = (unsigned)(tage - era * 146097);
  const unsigned yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  const unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
  const unsigned mp = (5 * doy + 2) / 153;
  const unsigned tag = doy - (153 * mp + 2) / 5 + 1, monat = mp < 10 ? mp + 3 : mp - 9;
  const int64_t jahr = (int64_t)yoe + era * 400 + (monat <= 2);
  char b[40];
  snprintf(b, sizeof b, "%04lld-%02u-%02u %02lld:%02lld UTC", (long long)jahr, monat, tag, (long long)(rest / 3600), (long long)(rest % 3600 / 60));
  return b;
}

class Msg {
  cfb::Datei &c;
 public:
  explicit Msg(cfb::Datei &d) : c(d) {}

  // Text-Eigenschaft (Unicode 001F, sonst 8 Bit 001E) eines Ordners, z. B. „0037“ (Betreff).
  std::string text(uint32_t ordner, const char *id) const {
    std::string roh;
    int32_t i = c.finde(ordner, std::string("__substg1.0_") + id + "001F");
    if (i >= 0 && c.strom((uint32_t)i, roh)) {
      std::string t = zeichen::utf16le((const uint8_t *)roh.data(), roh.size());
      while (!t.empty() && t.back() == '\0') t.pop_back();
      return t;
    }
    i = c.finde(ordner, std::string("__substg1.0_") + id + "001E");
    if (i >= 0 && c.strom((uint32_t)i, roh)) {
      while (!roh.empty() && roh.back() == '\0') roh.pop_back();
      return zeichen::heile(roh);
    }
    return "";
  }
  bool binaer(uint32_t ordner, const char *id, std::string &aus) const {
    int32_t i = c.finde(ordner, std::string("__substg1.0_") + id + "0102");
    return i >= 0 && c.strom((uint32_t)i, aus);
  }
  // Zeit aus dem Eigenschaftenstrom (fester Teil): Kopf 32 Bytes in der Nachricht, 24 in eingebetteten; je Eintrag 16.
  std::string zeit(uint32_t ordner, bool wurzel) const {
    std::string p;
    int32_t i = c.finde(ordner, "__properties_version1.0");
    if (i < 0 || !c.strom((uint32_t)i, p)) return "";
    uint64_t ft = 0;
    for (size_t o = wurzel ? 32 : 24; o + 16 <= p.size(); o += 16) {
      const uint8_t *q = (const uint8_t *)p.data() + o;
      const uint32_t tag = (uint32_t)q[0] | (uint32_t)q[1] << 8 | (uint32_t)q[2] << 16 | (uint32_t)q[3] << 24;
      if ((tag & 0xffff) != 0x0040) continue;
      const uint32_t id = tag >> 16;
      uint64_t w = 0;
      for (int k = 7; k >= 0; k--) w = w << 8 | q[8 + k];
      if (id == 0x0E06) { ft = w; break; }  // Zustellzeit
      if (id == 0x0039 && !ft) ft = w;      // Sendezeit
    }
    return filetime(ft);
  }

  void lies(uint32_t ordner, zeichen::Sammler &s, Ergebnis &e, int tiefe, bool wurzel) const {
    std::string von = text(ordner, "0C1A"), mail = text(ordner, "5D01");
    if (mail.empty()) mail = text(ordner, "0C1F");
    if (!mail.empty() && mail.find('@') != std::string::npos) von += (von.empty() ? "" : " ") + std::string("<") + mail + ">";
    std::string an = text(ordner, "0E04"), cc = text(ordner, "0E03");
    if (an.empty()) {  // Empfänger aus den Empfänger-Ordnern
      for (uint32_t k : c.kinder(ordner)) {
        if (c.eintraege[k].typ != 1 || c.eintraege[k].name.compare(0, 19, "__recip_version1.0_") != 0) continue;
        std::string n = text(k, "3001"), a = text(k, "39FE");
        if (a.empty()) a = text(k, "3003");
        an += (an.empty() ? "" : "; ") + n + (a.empty() || a == n ? "" : " <" + a + ">");
      }
    }
    const std::pair<const char *, std::string> kopf[] = {{"Von", von}, {"An", an}, {"Cc", cc}, {"Datum", zeit(ordner, wurzel)}, {"Betreff", text(ordner, "0037")}};
    for (auto &f : kopf) if (!f.second.empty()) { s.text(std::string(f.first) + ": " + f.second); s.zeile(); }
    s.absatz();
    std::string inhalt = text(ordner, "1000");
    if (!inhalt.empty()) s.text(inhalt);
    else {
      std::string h;
      if (binaer(ordner, "1013", h) || !(h = text(ordner, "1013")).empty()) zeichen::html(zeichen::heile(h), s);
    }
    s.zeile();
    // Anhänge
    for (uint32_t k : c.kinder(ordner)) {
      if (s.voll) break;
      if (c.eintraege[k].typ != 1 || c.eintraege[k].name.compare(0, 20, "__attach_version1.0_") != 0) continue;
      e.anhaenge++;
      std::string name = text(k, "3707");
      if (name.empty()) name = text(k, "3704");
      if (name.empty()) name = text(k, "3001");
      s.absatz();
      s.text("Anhang: " + (name.empty() ? std::string("ohne Namen") : name));
      s.zeile();
      if (tiefe >= TIEFE_MAX) continue;
      std::string daten;
      if (binaer(k, "3701", daten)) anhangText(name, daten, s, tiefe + 1);
      else {
        const int32_t eingebettet = c.finde(k, "__substg1.0_3701000D");  // eingebettete Nachricht
        if (eingebettet >= 0 && c.eintraege[(size_t)eingebettet].typ == 1) lies((uint32_t)eingebettet, s, e, tiefe + 1, false);
      }
    }
  }
};

}  // namespace mail
