// Reine Logik der Ergänzung „Fahrzeuge: Abruf beim KBA“ (dms-registry #278) – ohne Host-Funktionen, nativ testbar
// (tests/kba_test.cpp): SHA-256 und Base64 für das Captcha (Altcha), Zerlegen des Links aus dem QR-Code, Abbilden des
// Digitalen Untersuchungsberichts (DUB, XKfz 6.1 Type.DigitalerUntersuchungsbericht) und des elektronischen CoC (IVI 1.x
// und 2.0, EUCARIS) auf die Felder des Pakets Fahrzeuge. Grundregel: nur leere Felder füllen; was schon anders
// eingetragen ist, bleibt und steht als Hinweis in der Meldung.
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cctype>
#include <cstdlib>
#include <algorithm>
#include <string>
#include <vector>

#include "json.h"

namespace kba {

/* ---------- SHA-256 (FIPS 180-4) ---------- */

struct Sha256 {
  uint32_t h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
  uint8_t puffer[64];
  size_t n = 0;
  uint64_t laenge = 0;
  static uint32_t ror(uint32_t x, int r) { return (x >> r) | (x << (32 - r)); }
  void block(const uint8_t *p) {
    static const uint32_t k[64] = {
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
        0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
        0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
        0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};
    uint32_t w[64];
    for (int i = 0; i < 16; i++) w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 | (uint32_t)p[4 * i + 2] << 8 | p[4 * i + 3];
    for (int i = 16; i < 64; i++) {
      uint32_t s0 = ror(w[i - 15], 7) ^ ror(w[i - 15], 18) ^ (w[i - 15] >> 3), s1 = ror(w[i - 2], 17) ^ ror(w[i - 2], 19) ^ (w[i - 2] >> 10);
      w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
    for (int i = 0; i < 64; i++) {
      uint32_t t1 = hh + (ror(e, 6) ^ ror(e, 11) ^ ror(e, 25)) + ((e & f) ^ (~e & g)) + k[i] + w[i];
      uint32_t t2 = (ror(a, 2) ^ ror(a, 13) ^ ror(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
      hh = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
    }
    h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
  }
  void dazu(const void *daten, size_t len) {
    const uint8_t *p = static_cast<const uint8_t *>(daten);
    laenge += len;
    while (len--) { puffer[n++] = *p++; if (n == 64) { block(puffer); n = 0; } }
  }
  std::string hex() {
    uint64_t bits = laenge * 8;
    uint8_t eins = 0x80, null = 0;
    dazu(&eins, 1);
    while (n != 56) dazu(&null, 1);
    for (int i = 7; i >= 0; i--) { uint8_t b = (uint8_t)(bits >> (8 * i)); dazu(&b, 1); }
    static const char *z = "0123456789abcdef";
    std::string r;
    for (uint32_t x : h)
      for (int i = 28; i >= 0; i -= 4) r += z[(x >> i) & 15];
    return r;
  }
};
inline std::string sha256(const std::string &s) { Sha256 h; h.dazu(s.data(), s.size()); return h.hex(); }

inline std::string base64(const std::string &s) {
  static const char *a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  std::string r;
  size_t i = 0;
  for (; i + 2 < s.size(); i += 3) {
    uint32_t v = (uint8_t)s[i] << 16 | (uint8_t)s[i + 1] << 8 | (uint8_t)s[i + 2];
    r += a[v >> 18]; r += a[(v >> 12) & 63]; r += a[(v >> 6) & 63]; r += a[v & 63];
  }
  if (i + 1 == s.size()) { uint32_t v = (uint8_t)s[i] << 16; r += a[v >> 18]; r += a[(v >> 12) & 63]; r += "=="; }
  else if (i + 2 == s.size()) { uint32_t v = (uint8_t)s[i] << 16 | (uint8_t)s[i + 1] << 8; r += a[v >> 18]; r += a[(v >> 12) & 63]; r += a[(v >> 6) & 63]; r += '='; }
  return r;
}

/* ---------- Altcha (Rechenaufgabe statt Bilderrätsel) ---------- */

// Die Aufgabe: die Zahl n (0 … maxnumber), für die SHA-256(salt + n) = challenge ist. Rückgabe -1, wenn es keine gibt.
inline long altcha_zahl(const std::string &salt, const std::string &challenge, long max) {
  // Den Zustand nach dem Salt nur einmal rechnen, wenn er volle Blöcke füllt – reicht hier: kurze Salts.
  char z[24];
  for (long i = 0; i <= max; i++) {
    int l = snprintf(z, sizeof z, "%ld", i);
    Sha256 h;
    h.dazu(salt.data(), salt.size());
    h.dazu(z, (size_t)l);
    if (h.hex() == challenge) return i;
  }
  return -1;
}
// Antwort für das Formular: Base64 von {algorithm, challenge, number, salt, signature, took}.
inline std::string altcha_antwort(const Json &aufgabe, long zahl, long ms) {
  return base64("{\"algorithm\":" + jsonText(aufgabe["algorithm"].text("SHA-256")) + ",\"challenge\":" + jsonText(aufgabe["challenge"].text()) +
                ",\"number\":" + std::to_string(zahl) + ",\"salt\":" + jsonText(aufgabe["salt"].text()) +
                ",\"signature\":" + jsonText(aufgabe["signature"].text()) + ",\"took\":" + std::to_string(ms) + "}");
}

/* ---------- Link aus dem QR-Code ---------- */

struct DubSchluessel { std::string suchid, bericht, kennnummer; };

inline std::string klein(std::string s) { for (char &c : s) if (c >= 'A' && c <= 'Z') c = (char)(c - 'A' + 'a'); return s; }
inline std::string url_dekodieren(const std::string &s) {
  std::string r;
  for (size_t i = 0; i < s.size(); i++) {
    if (s[i] == '+') r += ' ';
    else if (s[i] == '%' && i + 2 < s.size() && isxdigit((unsigned char)s[i + 1]) && isxdigit((unsigned char)s[i + 2])) {
      r += (char)strtol(s.substr(i + 1, 2).c_str(), nullptr, 16); i += 2;
    } else r += s[i];
  }
  return r;
}
inline std::string trimmen(const std::string &s) {
  size_t a = s.find_first_not_of(" \t\r\n"), b = s.find_last_not_of(" \t\r\n");
  return a == std::string::npos ? "" : s.substr(a, b - a + 1);
}
inline bool ist_suchid(const std::string &s) {
  if (s.size() != 12) return false;
  for (char c : s) if (!((c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z'))) return false;
  return true;
}
// Den Aufbau des Links legt das KBA fest; wir lesen alle Parameter nach „?“ und „#“ und erkennen sie am Namen. Fehlt
// die Such-ID, nehmen wir eine Zeichenfolge aus 12 Großbuchstaben und Ziffern (Format laut XKfz Type.DUBSuchID).
// Beobachteter Aufbau (Thomas, 27.11.2026): https://www.kba-online.de/dub/#/zugriffsdaten/<Such-ID>/<Prüfberichtsnummer>/<Kennnummer>
inline DubSchluessel link_zerlegen(const std::string &link) {
  DubSchluessel d;
  size_t z = klein(link).find("zugriffsdaten/");
  if (z != std::string::npos) {
    std::vector<std::string> teile;
    std::string rest = link.substr(z + 14);
    size_t i = 0;
    while (i <= rest.size() && teile.size() < 3) {
      size_t e = rest.find_first_of("/?#&", i);
      if (e == std::string::npos) e = rest.size();
      teile.push_back(trimmen(url_dekodieren(rest.substr(i, e - i))));
      if (e >= rest.size() || rest[e] != '/') break;
      i = e + 1;
    }
    if (teile.size() == 3 && !teile[0].empty() && !teile[1].empty() && !teile[2].empty()) {
      d.suchid = teile[0]; d.bericht = teile[1]; d.kennnummer = teile[2];
      return d;
    }
  }
  size_t start = link.find_first_of("?#");
  std::string rest = start == std::string::npos ? "" : link.substr(start + 1);
  size_t i = 0;
  while (i <= rest.size()) {
    size_t e = rest.find_first_of("&?#;", i);
    if (e == std::string::npos) e = rest.size();
    std::string teil = rest.substr(i, e - i);
    size_t gl = teil.find('=');
    if (gl != std::string::npos) {
      std::string k = klein(url_dekodieren(teil.substr(0, gl))), v = trimmen(url_dekodieren(teil.substr(gl + 1)));
      if (k.find("/") != std::string::npos) k = k.substr(k.rfind('/') + 1);
      if (!v.empty()) {
        if (k.find("such") != std::string::npos || k == "id" || k == "dub") { if (d.suchid.empty()) d.suchid = v; }
        else if (k.find("bericht") != std::string::npos || k == "pbn" || k == "nr") { if (d.bericht.empty()) d.bericht = v; }
        else if (k.find("kenn") != std::string::npos || k.find("institution") != std::string::npos || k.find("zdk") != std::string::npos || k == "ki" || k == "ui") { if (d.kennnummer.empty()) d.kennnummer = v; }
      }
    }
    i = e + 1;
  }
  if (d.suchid.empty()) {
    for (size_t p = 0; p + 12 <= link.size(); p++) {
      std::string t = link.substr(p, 12);
      bool rand_links = p == 0 || !isalnum((unsigned char)link[p - 1]), rand_rechts = p + 12 == link.size() || !isalnum((unsigned char)link[p + 12]);
      if (rand_links && rand_rechts && ist_suchid(t)) { d.suchid = t; break; }
    }
  }
  return d;
}

/* ---------- Ergebnis sammeln: nur leere Felder füllen ---------- */

struct Ergebnis {
  std::vector<std::pair<std::string, std::string>> felder;  // Schlüssel → JSON-Wert
  std::vector<std::string> abweichend;                        // „Kilometerstand: laut KBA 55120, eingetragen 55000“
  std::vector<std::string> notizen;                           // weitere Hinweise für die Meldung
  int gleich = 0;

  static bool leer(const Json &w) {
    return w.art == Json::NUL || (w.art == Json::TEXT && trimmen(w.t).empty()) || (w.art == Json::LISTE && w.l.empty());
  }
  static std::string anzeige(const Json &w) {
    switch (w.art) {
      case Json::TEXT: return w.t;
      case Json::BOOL: return w.b ? "ja" : "nein";
      case Json::ZAHL: { char b[32]; snprintf(b, sizeof b, "%g", w.z); return b; }
      case Json::OBJEKT: if (w["betrag"].art == Json::ZAHL) { char b[32]; snprintf(b, sizeof b, "%.2f €", w["betrag"].z); return b; } return "…";
      default: return "…";
    }
  }
  // Setzt key auf neu (JSON), wenn das Feld leer ist; sonst vergleicht es und merkt Abweichungen.
  void setze(const Json &werte, const std::string &key, const std::string &name, const std::string &neu_json) {
    Json neu = JsonLeser::lies(neu_json.data(), neu_json.size());
    const Json &alt = werte[key.c_str()];
    if (leer(neu)) return;
    if (leer(alt)) { felder.push_back({key, neu_json}); return; }
    bool gleich_ = false;
    if (alt.art == Json::TEXT && neu.art == Json::TEXT) gleich_ = klein(trimmen(alt.t)) == klein(trimmen(neu.t));
    else if (alt.art == Json::ZAHL && neu.art == Json::ZAHL) gleich_ = alt.z == neu.z;
    else if (alt.art == Json::BOOL && neu.art == Json::BOOL) gleich_ = alt.b == neu.b;
    else if (alt.art == Json::OBJEKT && neu.art == Json::OBJEKT) gleich_ = alt["betrag"].zahl(-1) == neu["betrag"].zahl(-2);
    if (gleich_) { gleich++; return; }
    abweichend.push_back(name + ": laut KBA " + anzeige(neu) + ", eingetragen " + anzeige(alt));
  }
  void text(const Json &werte, const std::string &key, const std::string &name, const std::string &t) { if (!trimmen(t).empty()) setze(werte, key, name, jsonText(trimmen(t))); }
  void zahl(const Json &werte, const std::string &key, const std::string &name, double z) { if (z > 0) { char b[32]; snprintf(b, sizeof b, "%.10g", z); setze(werte, key, name, b); } }
  void ja_nein(const Json &werte, const std::string &key, const std::string &name, const Json &b) { if (b.art == Json::BOOL) setze(werte, key, name, b.b ? "true" : "false"); }

  std::string felder_json() const {
    std::string r = "{";
    for (size_t i = 0; i < felder.size(); i++) r += (i ? "," : "") + jsonText(felder[i].first) + ":" + felder[i].second;
    return r + "}";
  }
  // Meldung höchstens etwa 1900 Zeichen (Ablago kürzt bei 2000).
  std::string meldung(const std::string &kopf) const {
    std::string m = kopf;
    if (felder.empty() && abweichend.empty()) m += " Alle Angaben waren schon eingetragen.";
    else if (felder.empty()) m += " Keine leeren Felder gefüllt.";
    else m += " " + std::to_string(felder.size()) + (felder.size() == 1 ? " Feld" : " Felder") + " eingetragen.";
    if (!abweichend.empty()) {
      m += " Nicht überschrieben, weil schon anders eingetragen:";
      for (const auto &a : abweichend) m += "\n• " + a;
    }
    for (const auto &n : notizen) m += "\n" + n;
    if (m.size() > 1900) m = m.substr(0, 1890) + " …";
    return m;
  }
};

/* ---------- Datum ---------- */

// „MMJJJJ“ → „JJJJ-MM-01“
inline std::string monat_jahr(const std::string &s) {
  if (s.size() != 6) return "";
  for (char c : s) if (c < '0' || c > '9') return "";
  return s.substr(2, 4) + "-" + s.substr(0, 2) + "-01";
}

/* ---------- Digitaler Untersuchungsbericht → Hauptuntersuchung ---------- */

inline std::string ergebnis_auswahl(const std::string &t0) {
  std::string t = klein(t0);
  if (t.find("unmittelbar") != std::string::npos) return "unmittelbare Verkehrsgefährdung";
  if (t.find("verkehrsunsicher") != std::string::npos) return "verkehrsunsicher";
  if (t.find("gef\xc3\xa4hrlich") != std::string::npos || t.find("gefahrlich") != std::string::npos) return "gefährliche Mängel";
  if (t.find("erheblich") != std::string::npos) return "erhebliche Mängel";
  if (t.find("gering") != std::string::npos) return "geringe Mängel";
  if (t.find("ohne") != std::string::npos || t == "hinweise") return "ohne Mängel";
  return "";  // „mit festgestellten Mängeln“ sagt nicht, welche Stufe – dann lieber leer lassen
}

// Ein Mangel als Zeile: „erheblich: Bremsscheibe vorn verschlissen (1.2.1)“. Die Feldnamen der Antwort sind nicht
// dokumentiert – wir nehmen Einstufung, Text und Code, wo wir sie finden.
inline std::string mangel_zeile(const Json &m) {
  std::string einstufung, text, code;
  for (const auto &kv : m.o) {
    std::string k = klein(kv.first);
    std::string v = kv.second.art == Json::TEXT ? trimmen(kv.second.t) : kv.second.art == Json::OBJEKT ? trimmen(kv.second["name"].text()) : "";
    if (v.empty()) continue;
    if (k.find("einstufung") != std::string::npos) einstufung = v;
    else if (k.find("code") != std::string::npos) { if (code.empty()) code = v; }
    else if (text.empty() || v.size() > text.size()) text = v;
  }
  std::string z = einstufung.empty() ? "" : einstufung + ": ";
  z += text.empty() ? code : text + (code.empty() ? "" : " (" + code + ")");
  return z;
}
inline void liste_sammeln(const Json &j, std::vector<const Json *> &aus) {
  if (j.art == Json::LISTE) { for (const Json &x : j.l) aus.push_back(&x); return; }
  if (j.art == Json::OBJEKT) for (const auto &kv : j.o) if (kv.second.art == Json::LISTE) for (const Json &x : kv.second.l) aus.push_back(&x);
}

inline Ergebnis dub_abbilden(const Json &r, const Json &werte) {
  Ergebnis e;
  const std::string art = r["artDerUntersuchung"]["code"].text();
  e.text(werte, "art_untersuchung", "Art der Untersuchung", art == "HU" ? "Hauptuntersuchung" : art == "SP" ? "Sicherheitsprüfung" : "");
  const std::string typ = r["typDerUntersuchung"]["code"].text();
  e.text(werte, "typ_untersuchung", "Untersuchung", typ == "1" ? "Erstuntersuchung" : typ == "2" ? "Nachuntersuchung" : "");
  const std::string zeit = r["zeitpunktUntersuchung"].text();
  if (zeit.size() >= 10) e.text(werte, "geprueft_am", "Geprüft am", zeit.substr(0, 10));
  e.text(werte, "pruefbericht_nr", "Prüfbericht-Nr.", r["berichtsnummer"].text());
  e.zahl(werte, "kilometerstand", "Kilometerstand", r["kilometerstand"].zahl(0));
  e.text(werte, "ergebnis", "Ergebnis", ergebnis_auswahl(r["untersuchungsergebnis"].text()));
  e.ja_nein(werte, "pruefplakette", "Prüfplakette zugeteilt", r["entscheidungZuteilungPruefplakettePruefmarke"]);
  e.ja_nein(werte, "wiedervorfuehrung", "Wiedervorführung angeordnet", r["anordnungWiedervorfuehrpflicht"]);
  e.text(werte, "naechste_hu", "Nächste HU", monat_jahr(r["naechsteHauptuntersuchung"].text()));
  e.text(werte, "naechste_sp", "Nächste Sicherheitsprüfung", monat_jahr(r["naechsteSicherheitspruefung"].text()));
  // Mängel und Hinweise zu einem Text (#278): je Mangel eine Zeile, darunter „Hinweise:“.
  std::vector<const Json *> maengel, hinweise;
  liste_sammeln(r["maengel"], maengel);
  liste_sammeln(r["hinweise"], hinweise);
  std::string m;
  for (const Json *x : maengel) { std::string z = x->art == Json::TEXT ? x->t : mangel_zeile(*x); if (!z.empty()) m += (m.empty() ? "" : "\n") + z; }
  std::string h;
  for (const Json *x : hinweise) { std::string z = trimmen(x->text()); if (!z.empty()) h += "\n" + z; }
  if (!h.empty()) m += (m.empty() ? "" : "\n") + std::string("Hinweise:") + h;
  if (m.size() > 900) m = m.substr(0, 890) + " …";
  e.text(werte, "maengel", "Mängel und Hinweise", m);
  // Kosten: Summe aller Beträge unter gebuehrenEntgelte.
  std::vector<const Json *> posten;
  liste_sammeln(r["gebuehrenEntgelte"], posten);
  double summe = 0;
  for (const Json *p : posten) summe += (*p)["betrag"].zahl(0);
  if (summe > 0) { char b[64]; snprintf(b, sizeof b, "{\"betrag\":%.2f,\"waehrung\":\"EUR\"}", summe); e.setze(werte, "kosten", "Kosten", b); }
  // Fahrzeugdaten laut Bericht – die Automatisierung des Pakets bringt sie ans Fahrzeug, wo sie fehlen.
  std::string hsn = r["schluesselHersteller"].text();
  while (!hsn.empty() && hsn.size() < 4) hsn = "0" + hsn;
  e.text(werte, "hsn", "HSN", hsn);
  e.text(werte, "tsn", "TSN", r["schluesselTyp"].text().substr(0, 3));
  e.zahl(werte, "zul_gesamtmasse", "Zulässige Gesamtmasse", r["zulaessigeGesamtmasse"].zahl(0));
  const std::string stelle = trimmen(r["schluesselnummerUeberwachungsinstitutionOderZDK"]["name"].text(r["nameDerUeberwachungsinstitutionOderZDK"].text().c_str()));
  if (!stelle.empty() && Ergebnis::leer(werte["pruefstelle"])) e.notizen.push_back("Prüfstelle laut KBA: " + stelle + " – bitte unter „Prüfstelle“ auswählen.");
  return e;
}

/* ---------- Kleiner XML-Leser für den elektronischen CoC ---------- */

struct Knoten {
  std::string name, text;  // Name ohne Namensraum-Präfix
  std::vector<Knoten> kinder;
  const Knoten *kind(const char *n) const { for (const auto &k : kinder) if (k.name == n) return &k; return nullptr; }
  void alle(const char *n, std::vector<const Knoten *> &aus) const {
    if (name == n) aus.push_back(this);
    for (const auto &k : kinder) k.alle(n, aus);
  }
  const Knoten *erstes(const char *n) const { if (name == n) return this; for (const auto &k : kinder) if (auto *f = k.erstes(n)) return f; return nullptr; }
  std::string wert(const char *n) const { const Knoten *k = erstes(n); return k ? trimmen(k->text) : ""; }
};

struct XmlLeser {
  const char *p, *ende;
  bool fehler = false;
  static std::string entitaeten(const std::string &s) {
    std::string r;
    for (size_t i = 0; i < s.size(); i++) {
      if (s[i] != '&') { r += s[i]; continue; }
      size_t e = s.find(';', i);
      if (e == std::string::npos) { r += s[i]; continue; }
      std::string n = s.substr(i + 1, e - i - 1);
      if (n == "amp") r += '&'; else if (n == "lt") r += '<'; else if (n == "gt") r += '>'; else if (n == "quot") r += '"'; else if (n == "apos") r += '\'';
      else if (!n.empty() && n[0] == '#') {
        long c = n.size() > 1 && (n[1] == 'x' || n[1] == 'X') ? strtol(n.c_str() + 2, nullptr, 16) : strtol(n.c_str() + 1, nullptr, 10);
        if (c < 0x80) r += (char)c;
        else if (c < 0x800) { r += (char)(0xC0 | (c >> 6)); r += (char)(0x80 | (c & 63)); }
        else { r += (char)(0xE0 | (c >> 12)); r += (char)(0x80 | ((c >> 6) & 63)); r += (char)(0x80 | (c & 63)); }
      } else r += s.substr(i, e - i + 1);
      i = e;
    }
    return r;
  }
  void ueberspringen() {
    for (;;) {
      while (p < ende && isspace((unsigned char)*p)) p++;
      if (ende - p >= 2 && p[0] == '<' && (p[1] == '?' || p[1] == '!')) {
        const char *e = ende - p >= 4 && !strncmp(p, "<!--", 4) ? strstr(p, "-->") : static_cast<const char *>(memchr(p, '>', (size_t)(ende - p)));
        if (!e) { p = ende; return; }
        p = e + (e[0] == '-' ? 3 : 1);
      } else return;
    }
  }
  Knoten element(int tiefe) {
    Knoten k;
    if (tiefe > 64 || p >= ende || *p != '<') { fehler = true; return k; }
    p++;
    const char *n = p;
    while (p < ende && !isspace((unsigned char)*p) && *p != '>' && *p != '/') p++;
    k.name.assign(n, p);
    size_t dp = k.name.find(':');
    if (dp != std::string::npos) k.name = k.name.substr(dp + 1);
    const char *gt = static_cast<const char *>(memchr(p, '>', (size_t)(ende - p)));
    if (!gt) { fehler = true; p = ende; return k; }
    bool leer = gt[-1] == '/';
    p = gt + 1;
    if (leer) return k;
    std::string text;
    while (p < ende && !fehler) {
      if (*p != '<') { const char *t = p; while (p < ende && *p != '<') p++; text.append(t, p); continue; }
      if (ende - p >= 2 && p[1] == '/') { const char *e = static_cast<const char *>(memchr(p, '>', (size_t)(ende - p))); p = e ? e + 1 : ende; break; }
      if (ende - p >= 9 && !strncmp(p, "<![CDATA[", 9)) { const char *e = strstr(p, "]]>"); if (!e) { p = ende; break; } text.append(p + 9, e); p = e + 3; continue; }
      if (ende - p >= 2 && (p[1] == '!' || p[1] == '?')) { ueberspringen(); continue; }
      k.kinder.push_back(element(tiefe + 1));
    }
    k.text = entitaeten(text);
    return k;
  }
  static Knoten lies(const std::string &s) {
    XmlLeser l{s.data(), s.data() + s.size()};
    l.ueberspringen();
    Knoten k = l.element(0);
    if (l.fehler) k = Knoten{};
    return k;
  }
};

/* ---------- Elektronischer CoC (IVI 1.x und 2.0) → Fahrzeug ---------- */

inline double zahl_aus(const std::string &s) { return s.empty() ? 0 : strtod(s.c_str(), nullptr); }
inline std::string kraftstoff(int code, bool elektro) {
  std::string k = code >= 10 && code < 20 ? "Benzin" : code >= 20 && code < 30 ? "Diesel" : code == 30 ? "Autogas (LPG)" : code >= 40 && code < 45 ? "Erdgas (CNG)" : code == 50 ? "Wasserstoff" : code == 95 ? "Elektro" : code > 0 ? "Sonstige" : "";
  if (elektro && k == "Benzin") return "Hybrid Benzin/Elektro";
  if (elektro && k == "Diesel") return "Hybrid Diesel/Elektro";
  return k;
}
// „EURO 5“ → „Euro 5“
inline std::string euro(std::string s) {
  s = trimmen(s);
  if (klein(s).rfind("euro", 0) == 0) s = "Euro" + s.substr(4);
  return s;
}
// Version des Datensatzes: „1.8.2“, „2.0“ …
inline std::string ivi_version(const Knoten &w) {
  std::string v = w.wert("IviVersionNumberXsd");
  return v.empty() ? w.wert("VersionNumberXsd") : v;
}

struct IviBekannt { int haupt = 0; };
inline Ergebnis ivi_abbilden(const Knoten &w, const Json &werte, const std::string &fin) {
  Ergebnis e;
  const std::string version = ivi_version(w);
  const bool zwei = !version.empty() && version[0] == '2';
  const std::string vin = w.wert("VehicleIdentificationNumber");
  if (!fin.empty() && !vin.empty() && klein(vin) != klein(fin)) { e.notizen.push_back("Der Datensatz gehört zu einer anderen FIN – nichts übernommen."); return e; }
  if (!version.empty() && version[0] != '1' && version[0] != '2')
    e.notizen.push_back("Das KBA liefert ein neueres Datenformat (" + version + ") – übernommen wurde, was das Paket kennt. Bitte das Paket aktualisieren.");
  // HSN/TSN: nur als deutsche Ergänzung in IVI 1.x (TechnicalAdditionalDataGroup); in 2.0 nicht vorgesehen.
  std::string hsn = w.wert("CodeOfManufacturer");
  if (!hsn.empty()) { while (hsn.size() < 4) hsn = "0" + hsn; e.text(werte, "hsn", "HSN", hsn); }
  std::string tsn = w.wert("CodeOfType");
  if (!tsn.empty()) e.text(werte, "tsn", "TSN", tsn.substr(0, 3));
  e.text(werte, "typgenehmigung", "Typgenehmigung", w.wert("TypeApprovalNumber"));
  double hub = zahl_aus(w.wert("EngineCapacity"));
  if (hub > 0) e.zahl(werte, "hubraum", "Hubraum", (double)(long)(hub + 0.5));
  // Kraftstoff: 1.x FuelCode, 2.0 EnergySource; elektrisch: ElectricEngineIndicator (1.x) bzw. Energiequelle 95 (2.0).
  std::vector<const Knoten *> quellen;
  w.alle(zwei ? "EnergySource" : "FuelCode", quellen);
  int haupt = 0; bool strom = klein(w.wert("ElectricEngineIndicator")) == "y";
  for (const Knoten *q : quellen) { int c = atoi(q->text.c_str()); if (c == 95) strom = true; else if (!haupt) haupt = c; }
  if (!haupt && strom) haupt = 95;
  e.text(werte, "kraftstoff", "Kraftstoff", kraftstoff(haupt, strom && haupt != 95));
  e.text(werte, "emissionsklasse", "Emissionsklasse", euro(w.wert(zwei ? "ExhaustEmissionLevel" : "ExhaustEmissionLevelEuro")));
  double co2 = 0;
  for (const char *n : {"WltpCo2Combined", "WltpCo2WeightedCombined", "WLTPCombinedCO2", "WLTPWeightedCombinedCO2", "TypeVIICo2", "TestprocTypeVIICO2", "CombinedCO2"})
    if ((co2 = zahl_aus(w.wert(n))) > 0) break;
  if (co2 > 0) e.zahl(werte, "co2", "CO₂", (double)(long)(co2 + 0.5));
  e.zahl(werte, "zul_gesamtmasse", "Zulässige Gesamtmasse", zahl_aus(w.wert(zwei ? "TechnicallyPermissibleMaximumLadenMass" : "TechnPermMaxLadenMass")));
  // Anhängelast: Gruppe mit Bremsart (BRK, HDB, INB, PNB, PNH = gebremst, UNB = ungebremst) und Masse.
  double gebremst = 0, ungebremst = 0;
  std::vector<const Knoten *> gruppen;
  w.alle("TowingBrakedTypeTrailGroup", gruppen);
  w.alle("BrakedTypeTrailGroup", gruppen);
  for (const Knoten *g : gruppen) {
    std::string bremse = g->wert("BrakedTypeTrail");
    if (bremse.empty()) bremse = g->wert("BrakedTypeTrailCode");
    double m = std::max(zahl_aus(g->wert("TechnicallyPermissibleMaximumTowableMass")), zahl_aus(g->wert("TechPermMaxTowMassTrailer")));
    if (m <= 0 || bremse.empty()) continue;
    if (bremse == "UNB") ungebremst = std::max(ungebremst, m); else gebremst = std::max(gebremst, m);
  }
  e.zahl(werte, "anhaengelast_gebremst", "Anhängelast gebremst", gebremst);
  e.zahl(werte, "anhaengelast_ungebremst", "Anhängelast ungebremst", ungebremst);
  double stuetz = std::max(zahl_aus(w.wert("TechnicallyPermissibleMaximumStaticVerticalMassCouplingPoint")), zahl_aus(w.wert("TechPermMaxStatVertMassCouplPt")));
  e.zahl(werte, "stuetzlast", "Stützlast", stuetz);
  // Reifen: je Achse die Größe mit Last- und Geschwindigkeitsindex, dazu Alternativen aus den Bemerkungen.
  std::string reifen;
  std::vector<const Knoten *> achsen;
  w.alle("AxleGroup", achsen);
  for (const Knoten *a : achsen) {
    std::vector<const Knoten *> rs;
    a->alle("TyreAxleGroup", rs);
    for (const Knoten *r : rs) {
      std::string groesse = r->wert("TyreSize");
      if (groesse.empty()) continue;
      std::string z = "Achse " + a->wert("AxleNumber") + ": " + groesse;
      std::string li = r->wert("LoadCapacityIndexSingleWheel"), sp = r->wert("SpeedCategorySymbol");
      if (!li.empty() || !sp.empty()) z += " " + li + sp;
      if (reifen.find(z) == std::string::npos) reifen += (reifen.empty() ? "" : "\n") + z;
    }
  }
  std::vector<const Knoten *> bemerkungen;
  w.alle("Remarks", bemerkungen);
  w.alle("Remark", bemerkungen);
  for (const Knoten *b : bemerkungen) {
    std::string t = b->text;
    size_t i = 0;
    while (i < t.size()) {
      size_t e2 = t.find('*', i);
      if (e2 == std::string::npos) e2 = t.size();
      std::string s = trimmen(t.substr(i, e2 - i));
      // „Zu 6.18.1.1. Achse1: …“ – der Verweis auf die Nummer im CoC-Muster hilft im Laden nicht.
      if (klein(s).rfind("zu ", 0) == 0) {
        size_t a = s.find_first_not_of("0123456789.", 3);
        if (a != std::string::npos && a > 3) s = trimmen(s.substr(a));
      }
      while (s.find("  ") != std::string::npos) s.replace(s.find("  "), 2, " ");
      bool reifenartig = false;
      for (size_t k = 0; k + 4 < s.size(); k++) if (isdigit((unsigned char)s[k]) && s[k + 1] != '/' && s.find('/', k) != std::string::npos && isdigit((unsigned char)s[std::min(s.size() - 1, s.find('/', k) + 1)])) { reifenartig = klein(s).find("achse") != std::string::npos; break; }
      if (reifenartig && reifen.size() + s.size() < 900) reifen += (reifen.empty() ? "" : "\n") + s;
      i = e2 + 1;
    }
  }
  e.text(werte, "reifengroessen", "Zulässige Reifengrößen", reifen);
  return e;
}

}  // namespace kba
