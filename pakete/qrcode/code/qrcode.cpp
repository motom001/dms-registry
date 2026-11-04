// QR-Code lesen als Paket für Ablago (dms-registry #53): Visitenkarte mit vCard → Vorschläge für „Aus Dokument
// ausfüllen“ (Schnittstelle dms:erkennen, DMS #511).
//
// Ablauf: Ablago ruft dms_aktion mit { aktion: "dms:erkennen", schema, text, dokumente, einstellungen } → das Paket
// holt die Seiten der genannten Dokumente als Graustufenbild (GET /dokumente/{id}/seiten/{nr}/scan) → sucht
// QR-Codes (quirc) → liest die erste vCard → antwortet mit { vorschlaege: { feld: { wert, sicherheit, fundstelle } } }
// für die Felder des Schemas, deren Art (x-dms-erkennung) es kennt.
// Ohne vCard antwortet das Paket mit einem Fehler und dem Grund (z. B. „QR-Code mit Internetadresse gefunden, keine
// Visitenkarte“) – dann nimmt Ablago die eingebaute Erkennung aus dem Text. Andere QR-Inhalte (Internetadresse,
// GiroCode, Text) wertet das Paket nicht aus. Fotos in der vCard übernimmt es nie.
// Kein Netz, kein Dateisystem. Eingelesene Werte sind fremde Daten: jeder Wert ist begrenzt, Ablago prüft danach
// jeden Wert gegen die Feldart.
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "json.h"
extern "C" {
#include "quirc.h"
}

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
extern "C" {
DMS(api) int32_t dms_api(const char *json, int32_t len);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(char *ziel, int32_t max);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);
}

namespace {

enum Stufe { DEBUG = 0, INFO = 1, WARNUNG = 2, FEHLER = 3 };
const size_t WERT_MAX = 300;       // längster übernommener Wert (Zeichen in Bytes, UTF-8 nicht zerschnitten)
const size_t ZEILEN_MAX = 200;     // höchstens so viele Zeilen je vCard
const int DOKUMENTE_MAX = 3;       // höchstens so viele Dokumente je Aufruf
const int BILD_MAX = 9000;         // Kantenlänge eines Seitenbilds (größer: verkleinern)

void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }
std::string zahl(long n) { return std::to_string(n); }

std::string antwort() {
  std::string a((size_t)dms_antwort_laenge(), '\0');
  if (!a.empty()) dms_antwort_lesen(a.data(), (int32_t)a.size());
  return a;
}

struct Antwort { int status; std::string body; };

Antwort api(const std::string &methode, const std::string &pfad) {
  std::string q = "{\"methode\":" + jsonText(methode) + ",\"pfad\":" + jsonText(pfad) + "}";
  int s = dms_api(q.data(), (int32_t)q.size());
  return {s, antwort()};
}

bool sichereId(const std::string &id) {
  if (id.empty() || id.size() > 64) return false;
  for (char c : id) if (!(isalnum((unsigned char)c) || c == '-')) return false;
  return true;
}

/* ---------- Text-Helfer ---------- */

std::string ohneRand(const std::string &s) {
  size_t a = s.find_first_not_of(" \t\r\n"), e = s.find_last_not_of(" \t\r\n");
  return a == std::string::npos ? "" : s.substr(a, e - a + 1);
}

std::string gross(std::string s) { for (char &c : s) c = (char)toupper((unsigned char)c); return s; }

bool gueltigesUtf8(const std::string &s) {
  for (size_t i = 0; i < s.size();) {
    unsigned char c = (unsigned char)s[i];
    int n = c < 0x80 ? 0 : (c >> 5) == 6 ? 1 : (c >> 4) == 14 ? 2 : (c >> 3) == 30 ? 3 : -1;
    if (n < 0 || i + n >= s.size() + (n ? 0 : 1)) return false;
    for (int k = 1; k <= n; k++) if (i + k >= s.size() || ((unsigned char)s[i + k] & 0xc0) != 0x80) return false;
    i += (size_t)n + 1;
  }
  return true;
}

/** Latin-1 nach UTF-8 (ältere vCards ohne UTF-8). */
std::string latin1(const std::string &s) {
  std::string r;
  for (unsigned char c : s) { if (c < 0x80) r += (char)c; else { r += (char)(0xc0 | (c >> 6)); r += (char)(0x80 | (c & 0x3f)); } }
  return r;
}

/** Steuerzeichen raus, auf WERT_MAX kürzen, ohne ein UTF-8-Zeichen zu zerschneiden. */
std::string sauber(const std::string &s) {
  std::string r;
  for (unsigned char c : s) r += (c < 0x20 || c == 0x7f) ? ' ' : (char)c;
  r = ohneRand(r);
  if (r.size() > WERT_MAX) { size_t n = WERT_MAX; while (n > 0 && ((unsigned char)r[n] & 0xc0) == 0x80) n--; r = ohneRand(r.substr(0, n)); }
  return r;
}

/* ---------- vCard (2.1, 3.0, 4.0) ---------- */

struct Zeile { std::string name; std::vector<std::string> typen; std::string wert; std::string roh; };

std::string qpDekodieren(const std::string &s) {
  std::string r;
  auto hex = [](char c) { return isdigit((unsigned char)c) ? c - '0' : (toupper((unsigned char)c) - 'A' + 10); };
  for (size_t i = 0; i < s.size(); i++) {
    if (s[i] == '=' && i + 2 < s.size() && isxdigit((unsigned char)s[i + 1]) && isxdigit((unsigned char)s[i + 2])) {
      r += (char)(hex(s[i + 1]) * 16 + hex(s[i + 2])); i += 2;
    } else r += s[i];
  }
  return r;
}

/** Komponenten eines strukturierten Werts (N, ADR, ORG) an „;“ trennen, „\;“ bleibt Text. */
std::vector<std::string> teile(const std::string &s, char trenner = ';') {
  std::vector<std::string> r(1);
  for (size_t i = 0; i < s.size(); i++) {
    if (s[i] == '\\' && i + 1 < s.size()) { r.back() += s[i]; r.back() += s[++i]; continue; }
    if (s[i] == trenner) { if (r.size() >= 16) break; r.emplace_back(); } else r.back() += s[i];
  }
  return r;
}

std::string entschluesseln(const std::string &s) {
  std::string r;
  for (size_t i = 0; i < s.size(); i++) {
    if (s[i] == '\\' && i + 1 < s.size()) {
      char c = s[++i];
      r += (c == 'n' || c == 'N') ? ' ' : c;  // Zeilenumbruch im Wert wird Leerzeichen
    } else r += s[i];
  }
  return r;
}

/** vCard in Zeilen zerlegen; leer, wenn es keine ist. */
std::vector<Zeile> vcard(std::string text) {
  std::vector<Zeile> aus;
  if (!gueltigesUtf8(text)) text = latin1(text);
  // Zeilen trennen, gefaltete Zeilen (Leerzeichen/Tab am Anfang) wieder anfügen; 2.1: „=“ am Ende bei Quoted-Printable.
  std::vector<std::string> zeilen;
  std::string akt;
  size_t i = 0;
  while (i <= text.size()) {
    size_t e = text.find('\n', i);
    if (e == std::string::npos) e = text.size();
    std::string z = text.substr(i, e - i);
    if (!z.empty() && z.back() == '\r') z.pop_back();
    if (!zeilen.empty() && !z.empty() && (z[0] == ' ' || z[0] == '\t')) zeilen.back() += z.substr(1);
    else if (!zeilen.empty() && !zeilen.back().empty() && zeilen.back().back() == '=' && gross(zeilen.back()).find("QUOTED-PRINTABLE") != std::string::npos) { zeilen.back().pop_back(); zeilen.back() += z; }
    else zeilen.push_back(z);
    if (zeilen.size() > ZEILEN_MAX) break;
    i = e + 1;
  }
  bool drin = false, ende = false;
  for (const std::string &z : zeilen) {
    size_t dp = z.find(':');
    if (dp == std::string::npos) continue;
    std::string kopf = z.substr(0, dp), wert = z.substr(dp + 1);
    std::vector<std::string> p = teile(kopf, ';');
    std::string name = gross(ohneRand(p[0]));
    size_t punkt = name.find('.');
    if (punkt != std::string::npos) name = name.substr(punkt + 1);  // Gruppe „item1.TEL“
    if (name == "BEGIN" && gross(ohneRand(wert)) == "VCARD") { drin = true; continue; }
    if (name == "END" && gross(ohneRand(wert)) == "VCARD") { ende = true; break; }
    if (!drin) continue;
    Zeile zl; zl.name = name; zl.roh = z;
    bool qp = false;
    for (size_t k = 1; k < p.size(); k++) {
      std::string pa = gross(ohneRand(p[k]));
      std::string w = pa;
      size_t gl = pa.find('=');
      if (gl != std::string::npos) {
        std::string pn = pa.substr(0, gl); w = pa.substr(gl + 1);
        if (pn == "ENCODING") { if (w == "QUOTED-PRINTABLE") qp = true; continue; }
        if (pn != "TYPE") continue;
      }
      if (w == "QUOTED-PRINTABLE") { qp = true; continue; }
      for (std::string t : teile(w, ',')) {
        t = ohneRand(t);
        if (!t.empty() && t.front() == '"') t.erase(0, 1);
        if (!t.empty() && t.back() == '"') t.pop_back();
        if (!t.empty()) zl.typen.push_back(t);
      }
    }
    if (qp) { wert = qpDekodieren(wert); if (!gueltigesUtf8(wert)) wert = latin1(wert); }
    zl.wert = wert;
    aus.push_back(zl);
  }
  if (!drin || !ende) aus.clear();
  return aus;
}

bool hatTyp(const Zeile &z, const char *t) { for (const std::string &x : z.typen) if (x == t) return true; return false; }

/* ---------- QR-Codes in einem Seitenbild ---------- */

bool pgm(const std::string &b, int &w, int &h, size_t &start) {
  size_t p = 0;
  auto feld = [&](std::string &aus) {
    while (p < b.size()) {
      if (b[p] == '#') { while (p < b.size() && b[p] != '\n') p++; continue; }
      if (!isspace((unsigned char)b[p])) break;
      p++;
    }
    aus.clear();
    while (p < b.size() && !isspace((unsigned char)b[p]) && aus.size() < 12) aus += b[p++];
  };
  std::string a, bw, bh, mx;
  feld(a); feld(bw); feld(bh); feld(mx);
  if (a != "P5" || mx != "255") return false;
  w = atoi(bw.c_str()); h = atoi(bh.c_str());
  if (w <= 0 || h <= 0 || w > 20000 || h > 20000) return false;
  start = p + 1;
  return b.size() >= start + (size_t)w * (size_t)h;
}

/** Alle lesbaren QR-Codes eines Graustufenbilds (bei großen Bildern zusätzlich halb so groß). */
std::vector<std::string> qrCodes(const unsigned char *px, int w, int h) {
  std::vector<std::string> aus;
  std::vector<unsigned char> klein;
  for (int stufe = 0; stufe < 3 && aus.empty(); stufe++) {
    int f = 1 << stufe;  // 1, 2, 4
    if (stufe > 0 && (w / f < 200 || h / f < 200)) break;
    if (w / f > BILD_MAX || h / f > BILD_MAX) continue;
    int bw = w / f, bh = h / f;
    const unsigned char *quelle = px;
    if (f > 1) {
      klein.assign((size_t)bw * bh, 0);
      for (int y = 0; y < bh; y++) for (int x = 0; x < bw; x++) {
        unsigned s = 0;
        for (int dy = 0; dy < f; dy++) for (int dx = 0; dx < f; dx++) s += px[(size_t)(y * f + dy) * w + (x * f + dx)];
        klein[(size_t)y * bw + x] = (unsigned char)(s / (unsigned)(f * f));
      }
      quelle = klein.data();
    }
    struct quirc *q = quirc_new();
    if (!q) break;
    if (quirc_resize(q, bw, bh) < 0) { quirc_destroy(q); break; }
    uint8_t *ziel = quirc_begin(q, nullptr, nullptr);
    memcpy(ziel, quelle, (size_t)bw * bh);
    quirc_end(q);
    int n = quirc_count(q);
    for (int k = 0; k < n && k < 8; k++) {
      struct quirc_code code;
      struct quirc_data data;
      quirc_extract(q, k, &code);
      quirc_decode_error_t e = quirc_decode(&code, &data);
      if (e == QUIRC_ERROR_DATA_ECC) { quirc_flip(&code); e = quirc_decode(&code, &data); }  // gespiegelt fotografiert
      if (e == QUIRC_SUCCESS && data.payload_len > 0) aus.emplace_back((const char *)data.payload, (size_t)data.payload_len);
    }
    quirc_destroy(q);
  }
  return aus;
}

std::string artVon(const std::string &inhalt) {
  std::string g = gross(inhalt.substr(0, 16));
  if (g.compare(0, 11, "BEGIN:VCARD") == 0) return "Visitenkarte";
  if (g.compare(0, 4, "BCD\n") == 0 || g.compare(0, 5, "BCD\r\n") == 0) return "GiroCode";
  if (g.compare(0, 7, "HTTP://") == 0 || g.compare(0, 8, "HTTPS://") == 0) return "Internetadresse";
  if (g.compare(0, 6, "MECARD") == 0) return "MeCard";
  return "Text";
}

/* ---------- vCard → Vorschläge ---------- */

struct Vorschlag { std::string wert; std::string fundstelle; };

/** Erster Wert einer Eigenschaft, optional mit Typ; ohne Typangabe bevorzugt der Wert ohne die ausgeschlossenen Typen. */
const Zeile *erste(const std::vector<Zeile> &v, const char *name, const char *mitTyp = nullptr, std::vector<const char *> ohne = {}) {
  for (const Zeile &z : v) {
    if (z.name != name || ohneRand(z.wert).empty()) continue;
    if (mitTyp && !hatTyp(z, mitTyp)) continue;
    bool raus = false;
    for (const char *o : ohne) if (hatTyp(z, o)) raus = true;
    if (!raus) return &z;
  }
  return nullptr;
}

std::string telefon(std::string w) {
  w = ohneRand(w);
  if (w.compare(0, 4, "tel:") == 0 || w.compare(0, 4, "TEL:") == 0) w = w.substr(4);
  size_t sem = w.find(';');  // tel:+49…;ext=12
  if (sem != std::string::npos) w = w.substr(0, sem);
  return w;
}

std::string fund(const Zeile &z) {
  std::string r = "QR-Code (vCard): " + sauber(z.roh);
  return r.size() > 480 ? r.substr(0, 480) : r;
}

/** Strasse „Musterweg 12a“ → { „Musterweg“, „12a“ }. */
void strasseTeilen(const std::string &s, std::string &strasse, std::string &nr) {
  std::string t = ohneRand(s);
  size_t sp = t.find_last_of(' ');
  if (sp != std::string::npos && sp + 1 < t.size() && isdigit((unsigned char)t[sp + 1])) { strasse = ohneRand(t.substr(0, sp)); nr = t.substr(sp + 1); }
  else { strasse = t; nr.clear(); }
}

std::string zahlText(const std::string &s) {
  std::string r;
  for (char c : s) if (isdigit((unsigned char)c)) r += c;
  return r;
}

/** Vorschläge für die Felder des Schemas; Felder ohne bekannte Art bleiben leer. */
std::string vorschlaege(const std::vector<Zeile> &v, const Json &schema, int &anzahl) {
  const Json &props = schema["properties"];
  bool personTyp = false;
  for (auto &p : props.o) { std::string a = p.second["x-dms-erkennung"].text(); if (a == "vorname" || a == "nachname") personTyp = true; }

  const Zeile *n = erste(v, "N"), *fn = erste(v, "FN"), *org = erste(v, "ORG"), *titel = erste(v, "TITLE"), *rolle = erste(v, "ROLE");
  const Zeile *mail = erste(v, "EMAIL"), *url = erste(v, "URL"), *adr = erste(v, "ADR", "WORK");
  if (!adr) adr = erste(v, "ADR");
  const Zeile *mobil = erste(v, "TEL", "CELL"), *fax = erste(v, "TEL", "FAX");
  const Zeile *tel = erste(v, "TEL", "WORK", {"CELL", "FAX"});
  if (!tel) tel = erste(v, "TEL", nullptr, {"CELL", "FAX"});

  std::vector<std::string> name = n ? teile(n->wert) : std::vector<std::string>{};
  std::string nachname = name.size() > 0 ? entschluesseln(name[0]) : "", vorname = name.size() > 1 ? entschluesseln(name[1]) : "";
  if (fn && (vorname.empty() || nachname.empty())) {
    std::string voll = entschluesseln(fn->wert);
    size_t sp = ohneRand(voll).find_last_of(' ');
    if (sp != std::string::npos) { if (vorname.empty()) vorname = ohneRand(voll).substr(0, sp); if (nachname.empty()) nachname = ohneRand(voll).substr(sp + 1); }
    else if (nachname.empty()) nachname = voll;
  }
  std::vector<std::string> a = adr ? teile(adr->wert) : std::vector<std::string>{};
  auto adrTeil = [&](size_t i) { return i < a.size() ? entschluesseln(a[i]) : std::string(); };
  std::string strasse, hausnr;
  strasseTeilen(adrTeil(2), strasse, hausnr);
  bool hatHausnrFeld = false;
  for (auto &p : props.o) if (p.second["x-dms-erkennung"].text() == "hausnummer") hatHausnrFeld = true;
  if (!hatHausnrFeld) { strasse = ohneRand(adrTeil(2)); }

  std::string aus = "{";
  anzahl = 0;
  for (auto &p : props.o) {
    const Json &f = p.second;
    std::string art = f["x-dms-erkennung"].text(), typ = f["x-dms-feldtyp"].text();
    Vorschlag s;
    auto nimm = [&](const std::string &w, const Zeile *z) { if (z && !ohneRand(w).empty()) { s.wert = sauber(w); s.fundstelle = fund(*z); } };
    if (art == "vorname") nimm(vorname, n ? n : fn);
    else if (art == "nachname") nimm(nachname, n ? n : fn);
    else if (art == "name") {
      if (personTyp) continue;
      if (org) nimm(entschluesseln(teile(org->wert)[0]), org); else if (fn) nimm(entschluesseln(fn->wert), fn);
    }
    else if (art == "funktion") { if (titel) nimm(entschluesseln(titel->wert), titel); else if (rolle) nimm(entschluesseln(rolle->wert), rolle); }
    else if (art == "email" && mail) nimm(entschluesseln(mail->wert), mail);
    else if (art == "internet" && url) nimm(entschluesseln(url->wert), url);
    else if (art == "telefon" && tel) nimm(telefon(entschluesseln(tel->wert)), tel);
    else if (art == "mobil" && mobil) nimm(telefon(entschluesseln(mobil->wert)), mobil);
    else if (art == "fax" && fax) nimm(telefon(entschluesseln(fax->wert)), fax);
    else if (art == "strasse" && adr) nimm(strasse, adr);
    else if (art == "hausnummer" && adr) nimm(hausnr, adr);
    else if (art == "ort" && adr) nimm(adrTeil(3), adr);
    else if (art == "plz" && adr) nimm(adrTeil(5), adr);
    if (s.wert.empty()) continue;
    // Länge nach Schema (maxLength) – sonst verwirft Ablago den Wert.
    double ml = f["properties"]["wert"]["maxLength"].zahl(0);
    if (ml > 0 && s.wert.size() > (size_t)ml) continue;
    std::string wertJson;
    if (typ == "zahl") { std::string z = zahlText(s.wert); if (z.empty() || z.size() > 12) continue; wertJson = std::to_string(atoll(z.c_str())); }  // wie die eingebaute Erkennung: PLZ als Zahl
    else if (typ == "text" || typ.empty()) wertJson = jsonText(s.wert);
    else continue;  // Datum, Betrag, Auswahl, Verweis: kommen in einer vCard nicht vor
    if (anzahl) aus += ",";
    aus += jsonText(p.first) + ":{\"wert\":" + wertJson + ",\"sicherheit\":\"hoch\",\"fundstelle\":" + jsonText(s.fundstelle) + "}";
    anzahl++;
  }
  return aus + "}";
}

/* ---------- Aktion dms:erkennen ---------- */

int erkenne(const Json &e) {
  const Json &einst = e["einstellungen"];
  int dpi = (int)einst["dpi"].zahl(300);
  if (dpi < 150 || dpi > 400) dpi = 300;
  int maxSeiten = (int)einst["max_seiten"].zahl(2);
  if (maxSeiten < 1 || maxSeiten > 20) maxSeiten = 2;

  const Json &doks = e["dokumente"];
  if (doks.art != Json::LISTE || doks.l.empty()) { ergebnis("Kein Dokument mitgegeben – den QR-Code liest das Paket nur aus Dokumenten."); return 1; }

  std::vector<std::string> gefunden;
  int dokumente = 0, seiten = 0;
  for (const Json &d : doks.l) {
    if (dokumente >= DOKUMENTE_MAX) break;
    std::string id = d.text();
    if (!sichereId(id)) continue;
    dokumente++;
    Antwort info = api("GET", "/dokumente/" + id + "/seiten");
    int anzahl = info.status == 200 ? (int)JsonLeser::lies(info.body.data(), info.body.size())["anzahl"].zahl(1) : 1;
    if (anzahl < 1) anzahl = 1;
    for (int nr = 1; nr <= anzahl && nr <= maxSeiten; nr++) {
      Antwort bild = api("GET", "/dokumente/" + id + "/seiten/" + zahl(nr) + "/scan?dpi=" + zahl(dpi));
      if (bild.status != 200) { log(INFO, "Dokument " + id + " Seite " + zahl(nr) + ": kein Seitenbild (" + zahl(bild.status) + ")"); break; }
      int w, h; size_t start;
      if (!pgm(bild.body, w, h, start)) { log(WARNUNG, "Dokument " + id + " Seite " + zahl(nr) + ": Seitenbild nicht lesbar"); continue; }
      seiten++;
      for (std::string &c : qrCodes((const unsigned char *)bild.body.data() + start, w, h)) gefunden.push_back(c);
      for (const std::string &c : gefunden) if (artVon(c) == "Visitenkarte") goto fertig;
    }
  }
fertig:
  for (const std::string &c : gefunden) {
    if (artVon(c) != "Visitenkarte") continue;
    std::vector<Zeile> v = vcard(c);
    if (v.empty()) continue;
    int anzahl = 0;
    std::string vs = vorschlaege(v, e["schema"], anzahl);
    if (!anzahl) { ergebnis("Visitenkarte im QR-Code gefunden, aber keines der Felder passt dazu."); return 1; }
    log(INFO, "Visitenkarte im QR-Code: " + zahl(anzahl) + (anzahl == 1 ? " Feld" : " Felder"));
    ergebnis("{\"vorschlaege\":" + vs + "}");
    return 0;
  }
  if (!gefunden.empty()) {
    std::string arten;
    for (const std::string &c : gefunden) { std::string a = artVon(c); if (arten.find(a) == std::string::npos) arten += (arten.empty() ? "" : ", ") + a; }
    log(INFO, "QR-Code gefunden (" + arten + "), keine Visitenkarte");
    ergebnis("QR-Code gefunden (" + arten + "), aber keine Visitenkarte – Ablago liest den Text");
    return 1;
  }
  ergebnis("Kein QR-Code gefunden (" + zahl(seiten) + (seiten == 1 ? " Seite" : " Seiten") + " geprüft) – Ablago liest den Text");
  return 1;
}

char *eingang = nullptr;

}  // namespace

extern "C" {

__attribute__((export_name("dms_puffer"))) char *dms_puffer(int32_t n) {
  free(eingang);
  eingang = static_cast<char *>(malloc((size_t)n + 1));
  if (eingang) eingang[n] = 0;
  return eingang;
}

/** Ereignisse abonniert das Paket nicht. */
__attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *, int32_t) { return 0; }

__attribute__((export_name("dms_aktion"))) int32_t dms_aktion(char *json, int32_t len) {
  Json e = JsonLeser::lies(json, (size_t)len);
  std::string a = e["aktion"].text();
  if (a == "dms:erkennen") return erkenne(e);
  log(WARNUNG, "Unbekannte Aktion");
  ergebnis("Diese Aktion kennt das Paket nicht.");
  return 1;
}

}
