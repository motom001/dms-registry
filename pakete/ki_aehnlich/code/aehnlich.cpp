/*
 * KI lokal – Ähnlichkeit (DMS-Paket-ABI 1): rechnet zu jedem Dokument einen Vektor aus dem Volltext und liefert
 * den Vektor eines Suchbegriffs. Das DMS speichert und vergleicht die Vektoren (Schnittstelle dms:vektoren, DMS #442).
 *
 * Modell: static-similarity-mrl-multilingual-v1 (sentence-transformers, Apache-2.0) – ein „statisches“ Embedding:
 * je Token ein fester Vektor, der Text ist der Mittelwert seiner Tokens. Kein neuronales Netz zur Laufzeit, daher
 * schnell genug für WebAssembly ohne Threads. Tokenizer: WordPiece von bert-base-multilingual-uncased.
 * Die Daten (code/daten/) entstehen beim Bau mit umwandeln.py: 256 Dimensionen (Matryoshka), 8 Bit je Wert.
 *
 * Ereignis volltext.fertig → GET /dokumente/{id}/volltext → Vektor → PUT /dokumente/{id}/vektor
 * Aktion  dms:vektor { text } → Ergebnis { modell, vektor, schwelle } (leerer Text: nur modell und schwelle)
 */
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include "json.h"

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
DMS(api) int32_t dms_api(const char *json, int32_t len);
DMS(datei) int32_t dms_datei(const char *name, int32_t len);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(char *ziel, int32_t max);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);

static const char *MODELL_NAME = "static-similarity-mrl-multilingual-v1";
/** Ab dieser Ähnlichkeit (Kosinus) zeigt das DMS ein Dokument als ähnlich. */
static const double SCHWELLE = 0.45;
/** Höchstens so viel Volltext (Bytes) fließt in den Vektor – der Anfang eines Dokuments trägt seinen Inhalt. */
static const size_t TEXT_MAX = 1000000;
/** Längere Wörter (Zeichen) sind [UNK] – wie im Tokenizer. */
static const size_t WORT_MAX = 100;

static void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
static void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }

/* ---------- Daten des Pakets ---------- */

static bool lade(const char *name, std::vector<char> &ziel) {
  int32_t n = dms_datei(name, (int32_t)strlen(name));
  if (n < 0) return false;
  ziel.resize((size_t)n);
  return dms_antwort_lesen(ziel.data(), n) == n;
}
static uint32_t u32(const char *p) { uint32_t v; memcpy(&v, p, 4); return v; }

struct Modell {
  uint32_t anzahl = 0, dim = 0, unk = 0;
  std::vector<char> roh, vokabularRoh, zeichenRoh;
  const float *massstab = nullptr;
  const int8_t *werte = nullptr;
  // Vokabular: Zeilenanfänge und eine Hashtabelle (offene Adressierung, Nummer + 1).
  std::vector<uint32_t> anfang, laenge, tabelle;
  uint32_t maske = 0;
  // Zeichen: Abbildungen (Kleinschreibung ohne Akzente) und Klassen-Bereiche.
  const char *abbildung = nullptr; uint32_t abbildungen = 0;
  const char *bereiche = nullptr; uint32_t bereichAnzahl = 0;
  uint8_t asciiKlasse[128] = {0};
  std::string fehler;

  static uint32_t hash(const char *p, size_t n) { uint32_t h = 2166136261u; for (size_t i = 0; i < n; i++) { h ^= (uint8_t)p[i]; h *= 16777619u; } return h; }

  bool laden() {
    if (!lade("modell.dat", roh) || roh.size() < 24 || memcmp(roh.data(), "DMSV", 4) || u32(roh.data() + 4) != 1) { fehler = "daten/modell.dat fehlt oder ist kein Modell"; return false; }
    anzahl = u32(roh.data() + 8); dim = u32(roh.data() + 12); unk = u32(roh.data() + 16);
    if (!dim || roh.size() != 24 + (size_t)anzahl * 4 + (size_t)anzahl * dim) { fehler = "daten/modell.dat hat die falsche Größe"; return false; }
    massstab = (const float *)(roh.data() + 24);
    werte = (const int8_t *)(roh.data() + 24 + (size_t)anzahl * 4);
    if (!lade("vokabular.txt", vokabularRoh)) { fehler = "daten/vokabular.txt fehlt"; return false; }
    for (size_t i = 0, a = 0; i < vokabularRoh.size(); i++) if (vokabularRoh[i] == '\n') { anfang.push_back((uint32_t)a); laenge.push_back((uint32_t)(i - a)); a = i + 1; }
    if (anfang.size() != anzahl || unk >= anzahl) { fehler = "daten/vokabular.txt passt nicht zum Modell"; return false; }
    uint32_t groesse = 1; while (groesse < anzahl * 2) groesse <<= 1;
    tabelle.assign(groesse, 0); maske = groesse - 1;
    for (uint32_t i = 0; i < anzahl; i++) {
      uint32_t h = hash(vokabularRoh.data() + anfang[i], laenge[i]) & maske;
      while (tabelle[h]) h = (h + 1) & maske;
      tabelle[h] = i + 1;
    }
    if (!lade("zeichen.dat", zeichenRoh) || zeichenRoh.size() < 16 || memcmp(zeichenRoh.data(), "DMSZ", 4)) { fehler = "daten/zeichen.dat fehlt"; return false; }
    abbildungen = u32(zeichenRoh.data() + 8); bereichAnzahl = u32(zeichenRoh.data() + 12);
    if (zeichenRoh.size() != 16 + (size_t)abbildungen * 20 + (size_t)bereichAnzahl * 12) { fehler = "daten/zeichen.dat hat die falsche Größe"; return false; }
    abbildung = zeichenRoh.data() + 16; bereiche = abbildung + (size_t)abbildungen * 20;
    for (uint32_t c = 0; c < 128; c++) asciiKlasse[c] = klasseLangsam(c);
    return true;
  }

  int32_t nummer(const char *p, size_t n) const {
    uint32_t h = hash(p, n) & maske;
    while (uint32_t x = tabelle[h]) {
      uint32_t i = x - 1;
      if (laenge[i] == n && !memcmp(vokabularRoh.data() + anfang[i], p, n)) return (int32_t)i;
      h = (h + 1) & maske;
    }
    return -1;
  }

  uint8_t klasseLangsam(uint32_t cp) const {
    uint32_t lo = 0, hi = bereichAnzahl;
    while (lo < hi) {
      uint32_t m = (lo + hi) / 2; const char *b = bereiche + (size_t)m * 12;
      if (cp < u32(b)) hi = m; else if (cp > u32(b + 4)) lo = m + 1; else return (uint8_t)u32(b + 8);
    }
    return 0;
  }
  uint8_t klasse(uint32_t cp) const { return cp < 128 ? asciiKlasse[cp] : klasseLangsam(cp); }

  /** Kleinschreibung ohne Akzente: n Zeichen nach aus (0 = Zeichen fällt weg); ohne Eintrag bleibt es. */
  int abbilden(uint32_t cp, uint32_t aus[3]) const {
    if (cp < 128) { aus[0] = (cp >= 'A' && cp <= 'Z') ? cp + 32 : cp; return 1; }
    uint32_t lo = 0, hi = abbildungen;
    while (lo < hi) {
      uint32_t m = (lo + hi) / 2; const char *e = abbildung + (size_t)m * 20; uint32_t c = u32(e);
      if (cp < c) hi = m; else if (cp > c) lo = m + 1;
      else { int n = (int)u32(e + 4); for (int i = 0; i < n; i++) aus[i] = u32(e + 8 + 4 * i); return n; }
    }
    aus[0] = cp; return 1;
  }
};

/* ---------- Tokenizer (BertNormalizer, BertPreTokenizer, WordPiece) ---------- */

enum { LEER = 1, STEUER = 2, SATZ = 3, CJK = 4 };

static void utf8(std::string &s, uint32_t c) {
  if (c < 0x80) s += (char)c;
  else if (c < 0x800) { s += (char)(0xc0 | c >> 6); s += (char)(0x80 | (c & 0x3f)); }
  else if (c < 0x10000) { s += (char)(0xe0 | c >> 12); s += (char)(0x80 | (c >> 6 & 0x3f)); s += (char)(0x80 | (c & 0x3f)); }
  else { s += (char)(0xf0 | c >> 18); s += (char)(0x80 | (c >> 12 & 0x3f)); s += (char)(0x80 | (c >> 6 & 0x3f)); s += (char)(0x80 | (c & 0x3f)); }
}

/** Nächstes Zeichen aus UTF-8; ungültige Bytes werden zu U+FFFD (fällt als Steuerzeichen weg). */
static uint32_t naechstes(const std::string &t, size_t &i) {
  unsigned char c = (unsigned char)t[i++];
  if (c < 0x80) return c;
  int n = c >= 0xf0 ? 3 : c >= 0xe0 ? 2 : c >= 0xc0 ? 1 : -1;
  if (n < 0 || i + n > t.size()) return 0xfffd;
  uint32_t cp = c & (0x3f >> n);
  for (int k = 0; k < n; k++) { unsigned char x = (unsigned char)t[i]; if ((x & 0xc0) != 0x80) return 0xfffd; cp = cp << 6 | (x & 0x3f); i++; }
  return cp;
}

/** WordPiece für ein Wort (UTF-8, Zeichenzahl n): längster Treffer zuerst, Fortsetzungen mit „##“; sonst [UNK]. */
static void wordpiece(const Modell &m, const std::string &wort, size_t zeichen, std::vector<uint32_t> &ids) {
  if (wort.empty()) return;
  if (zeichen > WORT_MAX) { ids.push_back(m.unk); return; }
  // Grenzen der Zeichen im Wort.
  std::vector<size_t> pos;
  for (size_t i = 0; i < wort.size();) { pos.push_back(i); naechstes(wort, i); }
  pos.push_back(wort.size());
  std::vector<uint32_t> teil;
  std::string kandidat;
  size_t start = 0;
  while (start + 1 < pos.size()) {
    int32_t gefunden = -1; size_t ende = pos.size() - 1;
    for (; ende > start; ende--) {
      kandidat.assign(start ? "##" : "");
      kandidat.append(wort, pos[start], pos[ende] - pos[start]);
      if ((gefunden = m.nummer(kandidat.data(), kandidat.size())) >= 0) break;
    }
    if (gefunden < 0) { ids.push_back(m.unk); return; }  // wie im Tokenizer: das ganze Wort ist [UNK]
    teil.push_back((uint32_t)gefunden);
    start = ende;
  }
  ids.insert(ids.end(), teil.begin(), teil.end());
}

/** Text → Token-Nummern (ohne [CLS]/[SEP], wie StaticEmbedding in sentence-transformers). */
static std::vector<uint32_t> tokens(const Modell &m, const std::string &text) {
  std::vector<uint32_t> ids;
  std::string wort; size_t zeichen = 0;
  auto schluss = [&]() { wordpiece(m, wort, zeichen, ids); wort.clear(); zeichen = 0; };
  auto einzeln = [&](uint32_t cp) { schluss(); utf8(wort, cp); zeichen = 1; schluss(); };
  size_t n = std::min(text.size(), TEXT_MAX);
  for (size_t i = 0; i < n;) {
    uint32_t cp = naechstes(text, i);
    uint8_t k = m.klasse(cp);
    if (k == STEUER) continue;
    if (k == LEER) { schluss(); continue; }
    if (k == CJK || k == SATZ) { einzeln(cp); continue; }  // eigenes Token (Satzzeichen bleiben, wie sie sind)
    uint32_t aus[3]; int a = m.abbilden(cp, aus);
    for (int j = 0; j < a; j++) {
      uint8_t ka = m.klasse(aus[j]);
      if (ka == SATZ || ka == CJK) einzeln(aus[j]);
      else if (ka == LEER) schluss();
      else if (ka != STEUER) { utf8(wort, aus[j]); zeichen++; }
    }
  }
  schluss();
  return ids;
}

/** Mittelwert der Token-Vektoren, auf Länge 1 normiert; leer, wenn der Text keine Tokens hat. */
static std::vector<float> vektor(const Modell &m, const std::string &text, size_t *anzahl = nullptr) {
  std::vector<uint32_t> ids = tokens(m, text);
  if (anzahl) *anzahl = ids.size();
  std::vector<float> v;
  if (ids.empty()) return v;
  std::vector<double> s(m.dim, 0.0);
  for (uint32_t id : ids) {
    const int8_t *w = m.werte + (size_t)id * m.dim; double f = m.massstab[id];
    for (uint32_t k = 0; k < m.dim; k++) s[k] += f * w[k];
  }
  double n = 0; for (double x : s) n += x * x;
  n = std::sqrt(n);
  if (n <= 0) return v;
  v.resize(m.dim);
  for (uint32_t k = 0; k < m.dim; k++) v[k] = (float)(s[k] / n);
  return v;
}

static std::string modellKennung(const Modell &m) { char b[96]; snprintf(b, sizeof b, "%s/%u", MODELL_NAME, (unsigned)m.dim); return b; }
static std::string zahlen(const std::vector<float> &v) {
  std::string s = "[";
  char b[32];
  for (size_t i = 0; i < v.size(); i++) { snprintf(b, sizeof b, i ? ",%.5g" : "%.5g", (double)v[i]); s += b; }
  return s + "]";
}

/* ---------- Schnittstelle zum DMS ---------- */

struct Antwort { int status; std::string text; };
static Antwort api(const std::string &q) {
  int s = dms_api(q.data(), (int32_t)q.size());
  std::string t((size_t)dms_antwort_laenge(), '\0');
  if (!t.empty()) dms_antwort_lesen(&t[0], (int32_t)t.size());
  return { s, t };
}

static char *eingang;
extern "C" __attribute__((export_name("dms_puffer"))) char *dms_puffer(int32_t n) {
  free(eingang);
  eingang = (char *)malloc((size_t)n + 1);
  if (eingang) eingang[n] = 0;
  return eingang;
}

extern "C" __attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *json, int32_t len) {
  Json e = JsonLeser::lies(json, (size_t)len);
  if (e["art"].text() != "volltext.fertig") return 0;
  std::string id = e["daten"]["dokument"].text();
  if (id.empty() || id.find_first_not_of("0123456789abcdef-") != std::string::npos) { ergebnis("keine Dokument-Id"); return 0; }
  Antwort a = api("{\"methode\":\"GET\",\"pfad\":\"/dokumente/" + id + "/volltext\"}");
  if (a.status == 404 || a.status == 403) { ergebnis("Dokument nicht (mehr) lesbar"); return 0; }
  if (a.status != 200) { log(2, "Volltext nicht geladen: HTTP " + std::to_string(a.status)); return 1; }
  std::string text = JsonLeser::lies(a.text.data(), a.text.size())["text"].text();
  a.text.clear(); a.text.shrink_to_fit();
  if (text.empty()) { ergebnis("ohne Volltext"); return 0; }
  Modell m;
  if (!m.laden()) { log(3, m.fehler); return 2; }
  size_t n = 0;
  std::vector<float> v = vektor(m, text, &n);
  if (v.empty()) { ergebnis("keine Wörter im Volltext"); return 0; }
  std::string body = "{\"methode\":\"PUT\",\"pfad\":\"/dokumente/" + id + "/vektor\",\"body\":{\"modell\":" + jsonText(modellKennung(m)) + ",\"vektor\":" + zahlen(v) + "}}";
  Antwort p = api(body);
  if (p.status == 404) { ergebnis("Dokument gibt es nicht mehr"); return 0; }
  if (p.status != 200) { log(2, "Vektor nicht gespeichert: HTTP " + std::to_string(p.status) + " " + p.text.substr(0, 200)); return 1; }
  ergebnis("Vektor gespeichert (" + std::to_string(n) + " Tokens)");
  return 0;
}

extern "C" __attribute__((export_name("dms_aktion"))) int32_t dms_aktion(char *json, int32_t len) {
  Json e = JsonLeser::lies(json, (size_t)len);
  if (e["aktion"].text() != "dms:vektor") { ergebnis("Dieses Paket hat keine Aktionen."); return 0; }
  Modell m;
  if (!m.laden()) { log(3, m.fehler); ergebnis(m.fehler); return 2; }
  char s[32]; snprintf(s, sizeof s, "%.2f", SCHWELLE);
  std::string text = e["text"].text();
  std::string aus = "{\"modell\":" + jsonText(modellKennung(m)) + ",\"schwelle\":" + s;
  if (!text.empty()) {
    std::vector<float> v = vektor(m, text);
    if (!v.empty()) aus += ",\"vektor\":" + zahlen(v);
  }
  ergebnis(aus + "}");
  return 0;
}
