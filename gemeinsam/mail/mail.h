// E-Mails zerlegen: .eml (Internet-Nachricht nach RFC 5322 mit MIME) und .msg (Outlook, Compound File).
// Gemeinsamer Quellcode der Pakete „Office und E-Mail“ (Volltext) und „PDF/A“ (Archivfassung, dms-registry #143):
// Beide lesen Mails mit genau diesem Zerleger, nur was sie daraus machen, unterscheidet sich.
//
// Ergebnis ist eine Nachricht mit Kopf (Von, An, Cc, Datum, Betreff) und Blöcken in der Reihenfolge der Mail: Text,
// HTML, Alternativen (Klartext und reiche Fassung), Anhänge (auch Bilder mit Content-ID für cid:-Verweise),
// eingebettete Nachrichten und verschlüsselte Teile. Nichts wird ausgeführt oder nachgeladen; der Zerleger liest nur
// Bytes. Anhänge und eingebettete Mails zerlegt der Aufrufer bei Bedarf selbst weiter (mit Tiefe, höchstens TIEFE_MAX).
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <utility>
#include <vector>

#include "cfb.h"
#include "zeichen.h"

namespace mail {

constexpr int TIEFE_MAX = 3;      // E-Mail im Anhang einer E-Mail im Anhang …
constexpr int MIME_TIEFE_MAX = 12;

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

/* ---------- Zeit ---------- */

// Tage seit 1970-01-01 für ein Datum (Howard Hinnant, days_from_civil).
inline int64_t tageSeit1970(int64_t j, unsigned m, unsigned t) {
  j -= m <= 2;
  const int64_t era = (j >= 0 ? j : j - 399) / 400;
  const unsigned yoe = (unsigned)(j - era * 400);
  const unsigned doy = (153 * (m > 2 ? m - 3 : m + 9) + 2) / 5 + t - 1;
  const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  return era * 146097 + (int64_t)doe - 719468;
}

// „Date:“ nach RFC 5322 (auch alte Formen: zweistellige Jahre, Zonennamen) → Sekunden seit 1970 (UTC).
inline bool datumLesen(const std::string &w, int64_t &sekunden) {
  static const char *MONATE[] = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"};
  std::vector<std::string> t;
  std::string cur;
  int klammer = 0;
  for (char c : w) {
    if (c == '(') { klammer++; continue; }
    if (c == ')') { if (klammer) klammer--; continue; }
    if (klammer) continue;
    if (c == ' ' || c == '\t' || c == ',') { if (!cur.empty()) t.push_back(cur); cur.clear(); }
    else cur += c;
  }
  if (!cur.empty()) t.push_back(cur);
  size_t i = 0;
  if (i < t.size() && !t[i].empty() && !(t[i][0] >= '0' && t[i][0] <= '9')) i++;  // Wochentag
  if (i + 2 >= t.size()) return false;
  const int tag = atoi(t[i].c_str());
  int monat = 0;
  const std::string mn = zeichen::klein(t[i + 1].substr(0, 3));
  for (int m = 0; m < 12; m++) if (mn == MONATE[m]) monat = m + 1;
  int64_t jahr = atoi(t[i + 2].c_str());
  if (!monat || tag < 1 || tag > 31) return false;
  if (t[i + 2].size() <= 2) jahr += jahr < 50 ? 2000 : 1900;
  else if (t[i + 2].size() == 3) jahr += 1900;
  int hh = 0, mm = 0, ss = 0;
  if (i + 3 < t.size()) {
    if (sscanf(t[i + 3].c_str(), "%d:%d:%d", &hh, &mm, &ss) < 2) return false;
  }
  if (hh < 0 || hh > 23 || mm < 0 || mm > 59 || ss < 0 || ss > 60) return false;
  int versatz = 0;  // Minuten östlich von UTC
  if (i + 4 < t.size()) {
    const std::string z = t[i + 4];
    if ((z[0] == '+' || z[0] == '-') && z.size() >= 5) {
      const int v = atoi(z.c_str() + 1);
      versatz = (v / 100) * 60 + v % 100;
      if (z[0] == '-') versatz = -versatz;
    } else {
      static const struct { const char *n; int m; } zonen[] = {{"ut", 0}, {"utc", 0}, {"gmt", 0}, {"z", 0}, {"est", -300}, {"edt", -240}, {"cst", -360}, {"cdt", -300},
                                                              {"mst", -420}, {"mdt", -360}, {"pst", -480}, {"pdt", -420}, {"cet", 60}, {"cest", 120}, {"met", 60}, {"mest", 120}};
      const std::string k = zeichen::klein(z);
      for (auto &x : zonen) if (k == x.n) versatz = x.m;
    }
  }
  sekunden = tageSeit1970(jahr, (unsigned)monat, (unsigned)tag) * 86400 + hh * 3600 + mm * 60 + ss - (int64_t)versatz * 60;
  return true;
}

// FILETIME (100 ns seit 1601) → Sekunden seit 1970.
inline int64_t filetimeSekunden(uint64_t ft) { return (int64_t)(ft / 10000000ull) - 11644473600ll; }

// FILETIME → „JJJJ-MM-TT HH:MM UTC“ (so zeigt der Volltext das Datum einer Outlook-Nachricht).
inline std::string filetime(uint64_t ft) {
  if (!ft) return "";
  int64_t sek = filetimeSekunden(ft);
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

/* ---------- Das Ergebnis ---------- */

struct Block {
  enum Art { TEXT, HTML, ALTERNATIVE, ANHANG, NACHRICHT, VERSCHLUESSELT };
  Art art = TEXT;
  std::string text;                   // TEXT, HTML: Inhalt in UTF-8 (HTML noch mit Tags)
  std::vector<Block> schlicht, reich; // ALTERNATIVE: Klartext-Fassung bzw. reiche Fassung (HTML, sonst die letzte)
  // ANHANG und NACHRICHT:
  std::string name;                   // Dateiname (kann leer sein)
  std::string typ;                    // Content-Type bzw. bei .msg der MIME-Typ des Anhangs (klein)
  std::string cid;                    // Content-ID ohne <> (für cid:-Verweise in HTML)
  std::string daten;                  // Inhalt (dekodiert); bei NACHRICHT die eingebettete Mail
  bool eingebettet = false;           // inline (z. B. Bild im HTML), kein Anhang im Sinne der Absenderin
  int32_t msgOrdner = -1;             // .msg: eingebettete Outlook-Nachricht (Ordner im Compound File)
};

struct Nachricht {
  // Kopf zum Anzeigen: „Von“, „An“, „Cc“, „Datum“, „Betreff“ – nur, was es gibt, in dieser Reihenfolge.
  std::vector<std::pair<std::string, std::string>> kopf;
  int64_t zeit = 0;                   // Sekunden seit 1970 (UTC), wenn zeitOk
  bool zeitOk = false;
  std::vector<Block> bloecke;
  bool verschluesselt = false;
  std::string feld(const char *n) const {
    for (auto &f : kopf) if (f.first == n) return f.second;
    return "";
  }
};

/* ---------- MIME (.eml) ---------- */

inline void teil(const Kopf &k, const std::string &koerper, std::vector<Block> &aus, Nachricht &n, int mime);

inline std::vector<std::pair<Kopf, std::string>> mehrteilig(const std::string &koerper, const std::string &grenze) {
  std::vector<std::pair<Kopf, std::string>> teile;
  const std::string trenner = "--" + grenze;
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
  return teile;
}

inline void teil(const Kopf &k, const std::string &koerper, std::vector<Block> &aus, Nachricht &n, int mime) {
  const std::string ct = k.wert("content-type");
  std::string typ = ct.empty() ? "text/plain" : feldOhneParameter(ct);
  const std::string dispo = k.wert("content-disposition");
  std::string name = parameter(dispo, "filename");
  if (name.empty()) name = parameter(ct, "name");
  const std::string art = feldOhneParameter(dispo);
  const bool anhang = art == "attachment" || (!name.empty() && typ.compare(0, 5, "text/") != 0) || (!name.empty() && art != "inline");

  if (typ == "multipart/encrypted" || typ == "application/pkcs7-mime" || typ == "application/x-pkcs7-mime") {
    n.verschluesselt = true;
    Block b;
    b.art = Block::VERSCHLUESSELT;
    aus.push_back(std::move(b));
    return;
  }
  if (typ.compare(0, 10, "multipart/") == 0) {
    const std::string grenze = parameter(ct, "boundary");
    if (grenze.empty() || mime >= MIME_TIEFE_MAX) {
      Block b;
      b.art = Block::TEXT;
      b.text = zeichen::heile(koerper);
      aus.push_back(std::move(b));
      return;
    }
    std::vector<std::pair<Kopf, std::string>> teile = mehrteilig(koerper, grenze);
    if (typ == "multipart/alternative") {
      // Klartext und reiche Fassung (HTML, sonst die letzte – nach RFC 2046 die bevorzugte).
      int schlicht = -1, reich = -1;
      for (size_t i = 0; i < teile.size(); i++) {
        const std::string t = feldOhneParameter(teile[i].first.wert("content-type"));
        if (schlicht < 0 && t == "text/plain") schlicht = (int)i;
        if (reich < 0 && t == "text/html") reich = (int)i;
      }
      if (reich < 0 && !teile.empty() && (int)teile.size() - 1 != schlicht) reich = (int)teile.size() - 1;
      Block b;
      b.art = Block::ALTERNATIVE;
      if (schlicht >= 0) teil(teile[(size_t)schlicht].first, teile[(size_t)schlicht].second, b.schlicht, n, mime + 1);
      if (reich >= 0) teil(teile[(size_t)reich].first, teile[(size_t)reich].second, b.reich, n, mime + 1);
      if (b.schlicht.empty() && b.reich.empty()) return;
      aus.push_back(std::move(b));
      return;
    }
    for (auto &t : teile) teil(t.first, t.second, aus, n, mime + 1);
    return;
  }
  std::string daten = transferDekodieren(koerper, k.wert("content-transfer-encoding"));
  if (typ == "message/rfc822" && !anhang) {
    Block b;
    b.art = Block::NACHRICHT;
    b.typ = typ;
    b.daten = std::move(daten);
    aus.push_back(std::move(b));
    return;
  }
  if (anhang || (typ.compare(0, 5, "text/") != 0 && typ != "message/rfc822")) {
    Block b;
    b.art = Block::ANHANG;
    b.name = name;
    b.typ = typ;
    std::string cid = k.wert("content-id");
    while (!cid.empty() && (cid.front() == '<' || cid.front() == ' ')) cid.erase(0, 1);
    while (!cid.empty() && (cid.back() == '>' || cid.back() == ' ')) cid.pop_back();
    b.cid = cid;
    b.eingebettet = !cid.empty() && art != "attachment";
    b.daten = std::move(daten);
    aus.push_back(std::move(b));
    return;
  }
  const std::string cs = parameter(ct, "charset");
  Block b;
  b.art = typ == "text/html" ? Block::HTML : Block::TEXT;
  b.text = zeichen::nachUtf8(daten, cs.empty() ? "utf-8" : cs);
  aus.push_back(std::move(b));
}

// Eine Internet-Nachricht (.eml) zerlegen.
inline Nachricht eml(const std::string &t) {
  Nachricht n;
  size_t kb = 0;
  Kopf k = kopfLesen(t, kb);
  static const char *felder[][2] = {{"from", "Von"}, {"to", "An"}, {"cc", "Cc"}, {"date", "Datum"}, {"subject", "Betreff"}};
  for (auto &f : felder) {
    const std::string w = k.wert(f[0]);
    if (!w.empty()) n.kopf.push_back({f[1], kopfText(w)});
  }
  const std::string datum = k.wert("date");
  if (!datum.empty()) n.zeitOk = datumLesen(datum, n.zeit);
  teil(k, t.substr(kb), n.bloecke, n, 0);
  return n;
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

/* ---------- Outlook (.msg) ---------- */

// Ist das Compound File eine Outlook-Nachricht?
inline bool istMsg(const cfb::Datei &c) { return c.finde(0, "__properties_version1.0") >= 0; }

class Msg {
  const cfb::Datei &c;
 public:
  explicit Msg(const cfb::Datei &d) : c(d) {}

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
  uint64_t filetimeWert(uint32_t ordner, bool wurzel) const {
    std::string p;
    int32_t i = c.finde(ordner, "__properties_version1.0");
    if (i < 0 || !c.strom((uint32_t)i, p)) return 0;
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
    return ft;
  }

  // Die Nachricht in einem Ordner (0: die Datei selbst; sonst eine eingebettete).
  Nachricht lies(uint32_t ordner, bool wurzel) const {
    Nachricht n;
    std::string von = text(ordner, "0C1A"), mail = text(ordner, "5D01");
    if (mail.empty()) mail = text(ordner, "0C1F");
    if (!mail.empty() && mail.find('@') != std::string::npos) von += (von.empty() ? "" : " ") + std::string("<") + mail + ">";
    std::string an = text(ordner, "0E04"), cc = text(ordner, "0E03");
    if (an.empty()) {  // Empfänger aus den Empfänger-Ordnern
      for (uint32_t k : c.kinder(ordner)) {
        if (c.eintraege[k].typ != 1 || c.eintraege[k].name.compare(0, 19, "__recip_version1.0_") != 0) continue;
        std::string nm = text(k, "3001"), a = text(k, "39FE");
        if (a.empty()) a = text(k, "3003");
        an += (an.empty() ? "" : "; ") + nm + (a.empty() || a == nm ? "" : " <" + a + ">");
      }
    }
    const uint64_t ft = filetimeWert(ordner, wurzel);
    if (ft) { n.zeit = filetimeSekunden(ft); n.zeitOk = true; }
    const std::pair<const char *, std::string> kopf[] = {{"Von", von}, {"An", an}, {"Cc", cc}, {"Datum", filetime(ft)}, {"Betreff", text(ordner, "0037")}};
    for (auto &f : kopf) if (!f.second.empty()) n.kopf.push_back({f.first, f.second});
    // Text: HTML, wenn vorhanden (die Fassung, die Outlook zeigt), dazu der Klartext als Alternative.
    Block b;
    b.art = Block::ALTERNATIVE;
    std::string inhalt = text(ordner, "1000");
    if (!inhalt.empty()) { Block t; t.art = Block::TEXT; t.text = inhalt; b.schlicht.push_back(std::move(t)); }
    std::string h;
    if (binaer(ordner, "1013", h) || !(h = text(ordner, "1013")).empty()) { Block t; t.art = Block::HTML; t.text = zeichen::heile(h); b.reich.push_back(std::move(t)); }
    if (!b.schlicht.empty() || !b.reich.empty()) n.bloecke.push_back(std::move(b));
    // Anhänge
    for (uint32_t k : c.kinder(ordner)) {
      if (c.eintraege[k].typ != 1 || c.eintraege[k].name.compare(0, 20, "__attach_version1.0_") != 0) continue;
      Block a;
      a.art = Block::ANHANG;
      a.name = text(k, "3707");
      if (a.name.empty()) a.name = text(k, "3704");
      if (a.name.empty()) a.name = text(k, "3001");
      a.typ = zeichen::klein(text(k, "370E"));
      a.cid = text(k, "3712");
      a.eingebettet = !a.cid.empty();
      if (!binaer(k, "3701", a.daten)) {
        const int32_t e = c.finde(k, "__substg1.0_3701000D");  // eingebettete Nachricht
        if (e >= 0 && c.eintraege[(size_t)e].typ == 1) { a.msgOrdner = e; a.typ = "application/vnd.ms-outlook"; a.eingebettet = false; }
      }
      n.bloecke.push_back(std::move(a));
    }
    return n;
  }
};

}  // namespace mail
