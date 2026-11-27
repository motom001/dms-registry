// Barcodes als Paket für Ablago (dms-registry #294): liest QR-Codes und Strichcodes auf Dokumenten mit zxing-cpp.
//
// Zwei Aktionen:
// - dms:codes (Ablago 0.336.0, dms #1723): { aktion, datei, mime, seiten } → das Paket holt die Seitenbilder des
//   Dokuments (GET /dokumente/{id}/seiten/{nr}/scan) und antwortet mit allen lesbaren Codes
//   { codes: [{ art, inhalt, seite }] } – genau die Ausgabe der Leistung dokument.lesen.barcode@1. Welcher Code in
//   welches Feld gehört, entscheidet Ablago am Feld (Erkennungsart code mit codeart und muster).
// - dms:erkennen (DMS #511): Visitenkarte mit vCard im QR-Code → Vorschläge für „Aus Dokument ausfüllen“ (übernommen
//   aus dem Paket QR-Code lesen). Ohne vCard antwortet das Paket mit einem Fehler und dem Grund – dann nimmt Ablago
//   die eingebaute Erkennung aus dem Text. Fotos in der vCard übernimmt es nie.
//
// Namen der Arten (art, klein, ohne Satzzeichen): qr, microqr, rmqr, aztec, datamatrix, pdf417, maxicode, ean13, ean8,
// upca, upce, code39, code93, code128, itf, codabar, databar, databarexpanded, databarlimited.
// Kein Netz, kein Dateisystem. Gelesene Inhalte sind fremde Daten: begrenzt auf die Grenzen der Leistung (200 Codes,
// Inhalt bis 4000 Zeichen), gültiges UTF-8; Ablago prüft die Antwort noch einmal mit dem Schema der Leistung.
// zxing-cpp wirft intern Ausnahmen und fängt sie selbst; das Modul ist darum mit Wasm-Ausnahmen gebaut (bauen.sh).
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <chrono>
#include <climits>
#include <cstring>
#include <exception>
#include <set>
#include <string>
#include <tuple>
#include <vector>

#include "ReadBarcode.h"
#include "json.h"

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
const size_t WERT_MAX = 300;       // längster übernommener vCard-Wert (Bytes, UTF-8 nicht zerschnitten)
const size_t ZEILEN_MAX = 200;     // höchstens so viele Zeilen je vCard
const int DOKUMENTE_MAX = 3;       // dms:erkennen: höchstens so viele Dokumente je Aufruf
const int BILD_MAX = 9000;         // Kantenlänge eines Seitenbilds (größer: verkleinern)
const size_t CODES_MAX = 200;      // dokument.lesen.barcode@1: höchstens 200 Codes
const size_t INHALT_MAX = 4000;    // … Inhalt höchstens 4000 Zeichen
const int CODES_JE_SEITE = 50;     // mehr Codes sucht zxing auf einer Seite nicht
const int CODES_SEITEN_MAX = 40;   // dms:codes: höchstens so viele Seiten je Dokument
// dms:codes: keine neue Seite mehr nach so vielen Sekunden. Ablago wartet beim „Aus Dokument ausfüllen“ 30 s, im
// Hintergrund 120 s; eine A4-Seite braucht 0,3 bis 3 s. Was gelesen ist, geht in die Antwort.
const double CODES_SEKUNDEN = 22;

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

/* ---------- Seitenbild (PGM) ---------- */

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

/* ---------- Codes in einem Seitenbild ---------- */

struct Code { std::string art; std::string inhalt; int seite; int y = 0; int x = 0; };

/** Kurzer Name der Art für Ablago (dms #1723: Kleinbuchstaben und Ziffern). Leer: nicht melden. */
std::string artName(ZXing::BarcodeFormat f) {
  using F = ZXing::BarcodeFormat;
  switch (f) {
    case F::QRCode: return "qr";
    case F::MicroQRCode: return "microqr";
    case F::RMQRCode: return "rmqr";
    case F::Aztec: return "aztec";
    case F::DataMatrix: return "datamatrix";
    case F::PDF417: return "pdf417";
    case F::MaxiCode: return "maxicode";
    case F::EAN13: return "ean13";
    case F::EAN8: return "ean8";
    case F::UPCA: return "upca";
    case F::UPCE: return "upce";
    case F::Code39: return "code39";
    case F::Code93: return "code93";
    case F::Code128: return "code128";
    case F::ITF: return "itf";
    case F::Codabar: return "codabar";
    case F::DataBar: return "databar";
    case F::DataBarExpanded: return "databarexpanded";
    case F::DataBarLimited: return "databarlimited";
    default: return "";
  }
}

/** Name für Meldungen an die Person („EAN-13“, „Code 128“ …). */
std::string artAnzeige(const std::string &art) {
  if (art == "ean13") return "EAN-13";
  if (art == "ean8") return "EAN-8";
  if (art == "upca") return "UPC-A";
  if (art == "upce") return "UPC-E";
  if (art == "code39") return "Code 39";
  if (art == "code93") return "Code 93";
  if (art == "code128") return "Code 128";
  if (art == "itf") return "ITF";
  if (art == "datamatrix") return "Data Matrix";
  if (art == "pdf417") return "PDF417";
  if (art == "aztec") return "Aztec-Code";
  if (art == "maxicode") return "MaxiCode";
  if (art == "codabar") return "Codabar";
  if (art.compare(0, 7, "databar") == 0) return "GS1 DataBar";
  return art;
}

bool istQr(const std::string &art) { return art == "qr" || art == "microqr" || art == "rmqr"; }

/** Anzahl Zeichen (Codepunkte) in gültigem UTF-8. */
size_t zeichen(const std::string &s) {
  size_t n = 0;
  for (unsigned char c : s) if ((c & 0xc0) != 0x80) n++;
  return n;
}

/** Alle lesbaren Codes eines Graustufenbilds (sehr große Bilder vorher verkleinert). */
std::vector<Code> codesImBild(const unsigned char *px, int w, int h, int seite) {
  std::vector<Code> aus;
  std::vector<unsigned char> klein;
  int f = 1;
  while (w / f > BILD_MAX || h / f > BILD_MAX) f *= 2;
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
  ZXing::ReaderOptions o;
  // Alle Arten; „Any“ lässt die DX-Filmkante aus (nur auf Kleinbildfilm, sonst Fehltreffer).
  o.setFormats(ZXing::BarcodeFormat::Any);
  o.setTryHarder(true);
  o.setTryRotate(true);
  o.setTryInvert(false);
  o.setTryDownscale(true);
  o.setReturnErrors(false);
  o.setMaxNumberOfSymbols(CODES_JE_SEITE);
  try {
    ZXing::ImageView bild(quelle, bw, bh, ZXing::ImageFormat::Lum);
    for (const ZXing::Barcode &b : ZXing::ReadBarcodes(bild, o)) {
      if (!b.isValid()) continue;
      std::string art = artName(b.format());
      if (art.empty()) continue;
      // Klartext wie im Code (Zeilenumbrüche bleiben Zeilenumbrüche); nur GS1-Inhalte lesbar mit Klammern „(01)…“.
      std::string inhalt = b.text(b.contentType() == ZXing::ContentType::GS1 ? ZXing::TextMode::HRI : ZXing::TextMode::Plain);
      if (!gueltigesUtf8(inhalt)) inhalt = latin1(inhalt);
      if (inhalt.empty() || zeichen(inhalt) > INHALT_MAX) continue;  // gekürzt wäre der Inhalt falsch
      // Ecke oben links des umschließenden Rechtecks – für die Lesereihenfolge (oben nach unten, links nach rechts).
      int y = INT32_MAX, x = INT32_MAX;
      for (const auto &p : b.position()) { y = std::min(y, p.y); x = std::min(x, p.x); }
      aus.push_back({art, inhalt, seite, y * f, x * f});
    }
    // Lesereihenfolge; Codes in fast derselben Höhe (ein Zehntel der Seite) gelten als eine Zeile.
    int zeile = std::max(1, h / 10);
    std::stable_sort(aus.begin(), aus.end(), [zeile](const Code &a, const Code &b) {
      return a.y / zeile != b.y / zeile ? a.y / zeile < b.y / zeile : a.x < b.x;
    });
  } catch (const std::exception &e) {
    log(WARNUNG, std::string("Seite ") + zahl(seite) + ": Codes nicht lesbar (" + e.what() + ")");
  } catch (...) {
    log(WARNUNG, "Seite " + zahl(seite) + ": Codes nicht lesbar");
  }
  return aus;
}

/** Einstellungen: Auflösung und Seitenzahl für Visitenkarten (Grenzen wie im Manifest). */
struct Einstellungen { int dpi = 300; int maxSeiten = 2; };  // maxSeiten: nur Visitenkarten (dms:erkennen)

Einstellungen einstellungen(const Json &e) {
  Einstellungen s;
  const Json &einst = e["einstellungen"];
  s.dpi = (int)einst["dpi"].zahl(300);
  if (s.dpi < 150 || s.dpi > 400) s.dpi = 300;
  s.maxSeiten = (int)einst["max_seiten"].zahl(2);
  if (s.maxSeiten < 1 || s.maxSeiten > 20) s.maxSeiten = 2;
  return s;
}

/**
 * Seiten eines Dokuments lesen (höchstens maxSeiten), in ihrer Reihenfolge. anzahl < 1: bei Ablago nachfragen. fertig(codes) → true beendet
 * vorzeitig. Liefert die Zahl der gelesenen Seiten; -1, wenn keine Seite zu holen war.
 */
template <typename Fertig>
int seitenLesen(const std::string &id, int anzahl, int maxSeiten, const Einstellungen &s, std::vector<Code> &codes, Fertig fertig) {
  if (anzahl < 1) {
    Antwort info = api("GET", "/dokumente/" + id + "/seiten");
    anzahl = info.status == 200 ? (int)JsonLeser::lies(info.body.data(), info.body.size())["anzahl"].zahl(1) : 1;
    if (anzahl < 1) anzahl = 1;
  }
  int gelesen = 0, geholt = 0;
  for (int nr = 1; nr <= anzahl && nr <= maxSeiten; nr++) {
    Antwort bild = api("GET", "/dokumente/" + id + "/seiten/" + zahl(nr) + "/scan?dpi=" + zahl(s.dpi));
    if (bild.status != 200) { log(INFO, "Dokument " + id + " Seite " + zahl(nr) + ": kein Seitenbild (" + zahl(bild.status) + ")"); break; }
    geholt++;
    int w, h; size_t start;
    if (!pgm(bild.body, w, h, start)) { log(WARNUNG, "Dokument " + id + " Seite " + zahl(nr) + ": Seitenbild nicht lesbar"); continue; }
    gelesen++;
    for (Code &c : codesImBild((const unsigned char *)bild.body.data() + start, w, h, nr)) codes.push_back(c);
    if (fertig(codes)) break;
  }
  return geholt ? gelesen : -1;
}

/** Art eines QR-Inhalts für Meldungen. */
std::string artVon(const Code &c) {
  if (!istQr(c.art)) return artAnzeige(c.art);
  std::string g = gross(c.inhalt.substr(0, 16));
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

/* ---------- Aktion dms:codes ---------- */

int codesLesen(const Json &e) {
  std::string id = e["datei"].text();
  if (!sichereId(id)) { ergebnis("Kein gültiges Dokument mitgegeben."); return 1; }
  Einstellungen s = einstellungen(e);
  int anzahl = (int)e["seiten"].zahl(0);
  std::vector<Code> roh;
  auto start = std::chrono::steady_clock::now();
  bool zeitUm = false;
  int gelesen = seitenLesen(id, anzahl, CODES_SEITEN_MAX, s, roh, [&](const std::vector<Code> &) {
    zeitUm = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() > CODES_SEKUNDEN;
    return zeitUm;
  });
  if (gelesen < 0) { ergebnis("Keine Seite des Dokuments lesbar."); return 1; }
  if (zeitUm) log(WARNUNG, "Zeit für Codes um nach " + zahl(gelesen) + " Seiten – die übrigen Seiten bleiben ungelesen");
  // Gleiche Codes auf derselben Seite nur einmal (zxing findet manche doppelt, z. B. gedreht).
  std::set<std::tuple<std::string, std::string, int>> schon;
  std::string aus = "{\"codes\":[";
  size_t n = 0;
  for (const Code &c : roh) {
    if (n >= CODES_MAX) break;
    if (!schon.insert({c.art, c.inhalt, c.seite}).second) continue;
    aus += std::string(n ? "," : "") + "{\"art\":" + jsonText(c.art) + ",\"inhalt\":" + jsonText(c.inhalt) + ",\"seite\":" + zahl(c.seite) + "}";
    n++;
  }
  // Nur Anzahl und Arten ins Protokoll, nie Inhalte (ein Code kann ein Zugangsschlüssel sein).
  std::string arten;
  for (const auto &t : schon) if (arten.find(std::get<0>(t)) == std::string::npos) arten += (arten.empty() ? "" : ", ") + std::get<0>(t);
  log(INFO, zahl((long)n) + (n == 1 ? " Code" : " Codes") + " auf " + zahl(gelesen) + (gelesen == 1 ? " Seite" : " Seiten") + (arten.empty() ? "" : " (" + arten + ")"));
  ergebnis(aus + "]}");
  return 0;
}

/* ---------- Aktion dms:erkennen ---------- */

int erkenne(const Json &e) {
  Einstellungen s = einstellungen(e);
  const Json &doks = e["dokumente"];
  if (doks.art != Json::LISTE || doks.l.empty()) { ergebnis("Kein Dokument mitgegeben – Codes liest das Paket nur aus Dokumenten."); return 1; }

  std::vector<Code> gefunden;
  int dokumente = 0, seiten = 0;
  auto vcardDa = [](const std::vector<Code> &cs) { for (const Code &c : cs) if (artVon(c) == "Visitenkarte") return true; return false; };
  for (const Json &d : doks.l) {
    if (dokumente >= DOKUMENTE_MAX || vcardDa(gefunden)) break;
    std::string id = d.text();
    if (!sichereId(id)) continue;
    dokumente++;
    int n = seitenLesen(id, 0, s.maxSeiten, s, gefunden, vcardDa);
    if (n > 0) seiten += n;
  }
  for (const Code &c : gefunden) {
    if (artVon(c) != "Visitenkarte") continue;
    std::vector<Zeile> v = vcard(c.inhalt);
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
    for (const Code &c : gefunden) { std::string a = artVon(c); if (arten.find(a) == std::string::npos) arten += (arten.empty() ? "" : ", ") + a; }
    log(INFO, "Code gefunden (" + arten + "), keine Visitenkarte");
    ergebnis("Code gefunden (" + arten + "), aber keine Visitenkarte – Ablago liest den Text");
    return 1;
  }
  ergebnis("Kein Code gefunden (" + zahl(seiten) + (seiten == 1 ? " Seite" : " Seiten") + " geprüft) – Ablago liest den Text");
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
  if (a == "dms:codes") return codesLesen(e);
  if (a == "dms:erkennen") return erkenne(e);
  log(WARNUNG, "Unbekannte Aktion");
  ergebnis("Diese Aktion kennt das Paket nicht.");
  return 1;
}

}
