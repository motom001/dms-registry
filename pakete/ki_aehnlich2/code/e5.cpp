/*
 * KI lokal – Ähnlichkeit Stufe 2 (DMS-Paket-ABI 1): wie „KI lokal – Ähnlichkeit“, aber mit dem Transformer
 * multilingual-e5-small (intfloat, MIT) statt eines statischen Modells – genauer bei „Wohin gehört das?“ und vor allem
 * bei der Suche (dms-registry #242/#243), dafür deutlich mehr Rechenzeit je Dokument.
 *
 * Modell: BERT mit 12 Schichten, 384 breit, 12 Köpfe, 1536 im Zwischenschritt; Gewichte als int8 mit einem Maßstab
 * je Zeile, Aktivierungen je Wortteil auf int8 gerundet (wie die dynamische Quantisierung von onnxruntime).
 * Tokenizer: SentencePiece/Unigram von XLM-RoBERTa (Normalisierung NFKC, Metaspace „▁“), Wortliste auf lateinische,
 * griechische und kyrillische Schrift gekürzt. Höchstens 256 Wortteile je Text (mit <s> und </s>); e5 erwartet
 * „query: “ vor einem Suchbegriff und „passage: “ vor einem Dokument.
 * Die Daten (code/daten/) entstehen beim Bau mit umwandeln.py.
 *
 * Ereignis volltext.fertig → GET /dokumente/{id}/volltext → Vektor („passage“) → PUT /dokumente/{id}/vektor
 * Aktion  dms:vektor { text, art? } → Ergebnis { modell, vektor, schwelle } (leerer Text: nur modell und schwelle).
 *         art „suche“ → „query: “, „dokument“ → „passage: “ (DMS #1706, ab 0.331.0); ohne art: kurz = Suchbegriff.
 * Aktion  dms:klassifizieren { typen, aehnliche } wie in KI lokal – Ähnlichkeit 1.2.0, Schwellen für dieses Modell.
 */
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include "json.h"
#ifdef __wasm_simd128__
#include <wasm_simd128.h>
#endif

#ifdef ABLAGO_NATIV
// Für Tests auf dem Rechner (tests/nativ.cpp stellt diese Funktionen bereit).
extern "C" int32_t dms_api(const char *, int32_t);
extern "C" int32_t dms_datei(const char *, int32_t);
extern "C" int32_t dms_antwort_laenge();
extern "C" int32_t dms_antwort_lesen(char *, int32_t);
extern "C" int32_t dms_ergebnis(const char *, int32_t);
extern "C" int32_t dms_log(int32_t, const char *, int32_t);
#else
#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
extern "C" DMS(api) int32_t dms_api(const char *, int32_t);
extern "C" DMS(datei) int32_t dms_datei(const char *, int32_t);
extern "C" DMS(antwort_laenge) int32_t dms_antwort_laenge();
extern "C" DMS(antwort_lesen) int32_t dms_antwort_lesen(char *, int32_t);
extern "C" DMS(ergebnis) int32_t dms_ergebnis(const char *, int32_t);
extern "C" DMS(log) int32_t dms_log(int32_t, const char *, int32_t);
#endif

static const char *MODELL_NAME = "multilingual-e5-small";
/** Ab dieser Ähnlichkeit (Kosinus) zeigt Ablago ein Dokument als ähnlich. e5 liegt höher als statische Modelle: Die
 *  Schwellen entsprechen über die Verteilung am Satz „Lebensläufe“ denen von KI lokal – Ähnlichkeit (0,45 / 0,7 / 0,85). */
static const double SCHWELLE = 0.85;
static const double AEHNLICH = 0.88;
static const double KLASS_NAH = 0.965;
/** Höchstens so viele Wortteile je Text, mit <s> und </s> (gemessen: 256 kosten gegenüber 512 fast nichts). */
static const size_t WORTTEILE_MAX = 256;
/** Ohne Angabe der Art gilt ein Text bis zu dieser Länge (Bytes) als Suchbegriff. */
static const size_t SUCHE_MAX = 200;

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
static uint16_t u16(const char *p) { uint16_t v; memcpy(&v, p, 2); return v; }

/** Matrix int8 [zeilen × spalten] mit einem Maßstab je Zeile, dazu Verschiebung (float32 je Zeile). */
struct Matrix { const float *massstab; const int8_t *w; const float *b; uint32_t zeilen, spalten; };
struct Schicht { Matrix q, k, v, o, rein, raus; const float *ln1g, *ln1b, *ln2g, *ln2b; };

struct Modell {
  uint32_t woerter = 0, breite = 0, schichten = 0, zwischen = 0, positionen = 0, unk = 0;
  std::vector<char> roh, vokRoh, normRoh;
  const float *wortMassstab = nullptr; const int8_t *wortWerte = nullptr;
  const float *pos = nullptr, *typ0 = nullptr, *ln0g = nullptr, *ln0b = nullptr;
  std::vector<Schicht> s;
  // Vokabular: Zeiger, Längen, Bewertungen, Hashtabelle (offene Adressierung, Nummer + 1).
  std::vector<const char *> stueck; std::vector<uint16_t> laenge; std::vector<float> bewertung;
  std::vector<uint32_t> tabelle; uint32_t maske = 0; float unkBewertung = 0; size_t laengstes = 0;
  // Normalisierung: sortierte Zeichen mit Ersetzung, Paare Buchstabe + Akzent.
  std::vector<uint32_t> normZeichen; std::vector<const char *> normText; std::vector<uint16_t> normLaenge;
  const char *paare = nullptr; uint32_t paarAnzahl = 0;
  std::string fehler;

  static uint32_t hash(const char *p, size_t n) { uint32_t h = 2166136261u; for (size_t i = 0; i < n; i++) { h ^= (uint8_t)p[i]; h *= 16777619u; } return h; }

  bool matrix(size_t &pos, uint32_t zeilen, uint32_t spalten, Matrix &m) {
    size_t groesse = (size_t)zeilen * 4 + (size_t)zeilen * spalten + (size_t)zeilen * 4;
    if (pos + groesse > roh.size()) return false;
    m.massstab = (const float *)(roh.data() + pos); pos += (size_t)zeilen * 4;
    m.w = (const int8_t *)(roh.data() + pos); pos += (size_t)zeilen * spalten;
    m.b = (const float *)(roh.data() + pos); pos += (size_t)zeilen * 4;
    m.zeilen = zeilen; m.spalten = spalten;
    return true;
  }
  const float *floats(size_t &pos, size_t n) {
    if (pos + n * 4 > roh.size()) return nullptr;
    const float *p = (const float *)(roh.data() + pos); pos += n * 4; return p;
  }

  bool laden() {
    if (!lade("modell.dat", roh) || roh.size() < 28 || memcmp(roh.data(), "DMSE", 4) || u32(roh.data() + 4) != 1) { fehler = "daten/modell.dat fehlt oder ist kein Modell"; return false; }
    woerter = u32(roh.data() + 8); breite = u32(roh.data() + 12); schichten = u32(roh.data() + 16);
    zwischen = u32(roh.data() + 20); positionen = u32(roh.data() + 24);
    if (breite != 384 || breite % 32 || zwischen % 16 || positionen < WORTTEILE_MAX) { fehler = "daten/modell.dat: unerwartete Maße"; return false; }
    size_t p = 28;
    if (p + (size_t)woerter * (4 + breite) > roh.size()) { fehler = "daten/modell.dat zu kurz"; return false; }
    wortMassstab = (const float *)(roh.data() + p); p += (size_t)woerter * 4;
    wortWerte = (const int8_t *)(roh.data() + p); p += (size_t)woerter * breite;
    pos = floats(p, (size_t)positionen * breite); typ0 = floats(p, breite); ln0g = floats(p, breite); ln0b = floats(p, breite);
    s.resize(schichten);
    for (Schicht &x : s) {
      if (!matrix(p, breite, breite, x.q) || !matrix(p, breite, breite, x.k) || !matrix(p, breite, breite, x.v) || !matrix(p, breite, breite, x.o)) { fehler = "daten/modell.dat zu kurz"; return false; }
      x.ln1g = floats(p, breite); x.ln1b = floats(p, breite);
      if (!matrix(p, zwischen, breite, x.rein) || !matrix(p, breite, zwischen, x.raus)) { fehler = "daten/modell.dat zu kurz"; return false; }
      x.ln2g = floats(p, breite); x.ln2b = floats(p, breite);
    }
    if (!x_ok(p)) { fehler = "daten/modell.dat hat die falsche Größe"; return false; }

    if (!lade("vokabular.dat", vokRoh) || vokRoh.size() < 16 || memcmp(vokRoh.data(), "DMSW", 4) || u32(vokRoh.data() + 8) != woerter) { fehler = "daten/vokabular.dat fehlt oder passt nicht"; return false; }
    unk = u32(vokRoh.data() + 12);
    size_t q = 16; float kleinste = 0;
    for (uint32_t i = 0; i < woerter; i++) {
      if (q + 6 > vokRoh.size()) { fehler = "daten/vokabular.dat zu kurz"; return false; }
      float b; memcpy(&b, vokRoh.data() + q, 4); uint16_t n = u16(vokRoh.data() + q + 4); q += 6;
      if (q + n > vokRoh.size()) { fehler = "daten/vokabular.dat zu kurz"; return false; }
      stueck.push_back(vokRoh.data() + q); laenge.push_back(n); bewertung.push_back(b); q += n;
      if (i > 3 && b < kleinste) kleinste = b;
      laengstes = std::max(laengstes, (size_t)n);
    }
    unkBewertung = kleinste - 10.0f;  // wie Unigram in tokenizers: kleinste Bewertung minus 10
    uint32_t groesse = 1; while (groesse < woerter * 2) groesse <<= 1;
    tabelle.assign(groesse, 0); maske = groesse - 1;
    for (uint32_t i = 4; i < woerter; i++) {  // <s>, <pad>, </s>, <unk> nie aus dem Text
      uint32_t h = hash(stueck[i], laenge[i]) & maske;
      while (tabelle[h]) h = (h + 1) & maske;
      tabelle[h] = i + 1;
    }

    if (!lade("normal.dat", normRoh) || normRoh.size() < 16 || memcmp(normRoh.data(), "DMSN", 4)) { fehler = "daten/normal.dat fehlt"; return false; }
    uint32_t n = u32(normRoh.data() + 8); paarAnzahl = u32(normRoh.data() + 12);
    size_t r = 16;
    for (uint32_t i = 0; i < n; i++) {
      if (r + 6 > normRoh.size()) { fehler = "daten/normal.dat zu kurz"; return false; }
      normZeichen.push_back(u32(normRoh.data() + r)); uint16_t l = u16(normRoh.data() + r + 4); r += 6;
      normText.push_back(normRoh.data() + r); normLaenge.push_back(l); r += l;
    }
    if (r + (size_t)paarAnzahl * 12 != normRoh.size()) { fehler = "daten/normal.dat hat die falsche Größe"; return false; }
    paare = normRoh.data() + r;
    return true;
  }
  bool x_ok(size_t p) const { return p == roh.size() && pos && typ0 && ln0g && ln0b; }

  int32_t nummer(const char *p, size_t n) const {
    uint32_t h = hash(p, n) & maske;
    while (uint32_t x = tabelle[h]) {
      uint32_t i = x - 1;
      if (laenge[i] == n && !memcmp(stueck[i], p, n)) return (int32_t)i;
      h = (h + 1) & maske;
    }
    return -1;
  }
  /** Ersetzung eines Zeichens; nullptr = bleibt. */
  bool ersetzung(uint32_t cp, const char *&t, uint16_t &l) const {
    auto it = std::lower_bound(normZeichen.begin(), normZeichen.end(), cp);
    if (it == normZeichen.end() || *it != cp) return false;
    size_t i = (size_t)(it - normZeichen.begin()); t = normText[i]; l = normLaenge[i]; return true;
  }
  /** Buchstabe + Akzent → zusammengesetztes Zeichen, sonst 0. */
  uint32_t paar(uint32_t a, uint32_t b) const {
    uint32_t lo = 0, hi = paarAnzahl;
    while (lo < hi) {
      uint32_t m = (lo + hi) / 2; const char *e = paare + (size_t)m * 12; uint32_t x = u32(e), y = u32(e + 4);
      if (a < x || (a == x && b < y)) hi = m; else if (a > x || b > y) lo = m + 1; else return u32(e + 8);
    }
    return 0;
  }
};

/* ---------- Tokenizer ---------- */

static void utf8(std::string &s, uint32_t c) {
  if (c < 0x80) s += (char)c;
  else if (c < 0x800) { s += (char)(0xC0 | (c >> 6)); s += (char)(0x80 | (c & 0x3F)); }
  else if (c < 0x10000) { s += (char)(0xE0 | (c >> 12)); s += (char)(0x80 | ((c >> 6) & 0x3F)); s += (char)(0x80 | (c & 0x3F)); }
  else { s += (char)(0xF0 | (c >> 18)); s += (char)(0x80 | ((c >> 12) & 0x3F)); s += (char)(0x80 | ((c >> 6) & 0x3F)); s += (char)(0x80 | (c & 0x3F)); }
}
static uint32_t naechstes(const char *t, size_t n, size_t &i) {
  uint8_t c = (uint8_t)t[i++];
  if (c < 0x80) return c;
  int k = c >= 0xF0 ? 3 : c >= 0xE0 ? 2 : c >= 0xC0 ? 1 : -1;
  if (k < 0 || i + (size_t)k > n) return 0xFFFD;
  uint32_t v = c & (0x3F >> k);
  for (int j = 0; j < k; j++) { uint8_t d = (uint8_t)t[i]; if ((d & 0xC0) != 0x80) return 0xFFFD; v = (v << 6) | (d & 0x3F); i++; }
  return v;
}
static size_t zeichenLaenge(uint8_t c) { return c < 0x80 ? 1 : c >= 0xF0 ? 4 : c >= 0xE0 ? 3 : c >= 0xC0 ? 2 : 1; }

/** Unigram (Viterbi) für ein Wort mit „▁“ am Anfang; unbekannte Zeichen werden zu <unk>, aufeinanderfolgende zu einem. */
static void unigram(const Modell &m, const std::string &w, std::vector<uint32_t> &ids) {
  size_t n = w.size();
  std::vector<float> best(n + 1, -1e30f); std::vector<int32_t> id(n + 1, -1); std::vector<size_t> von(n + 1, 0);
  best[0] = 0;
  for (size_t a = 0; a < n; a = a + zeichenLaenge((uint8_t)w[a])) {
    if (best[a] <= -1e29f) continue;
    bool einzeln = false;
    size_t e = a, zeichen = 0;
    while (e < n && e - a < m.laengstes) {
      e += zeichenLaenge((uint8_t)w[e]); zeichen++;
      if (e > n) break;
      int32_t i = m.nummer(w.data() + a, e - a);
      if (i >= 0) {
        if (zeichen == 1) einzeln = true;
        float s = best[a] + m.bewertung[(size_t)i];
        if (s > best[e]) { best[e] = s; id[e] = i; von[e] = a; }
      }
    }
    if (!einzeln) {
      size_t z = a + zeichenLaenge((uint8_t)w[a]); if (z > n) z = n;
      float s = best[a] + m.unkBewertung;
      if (s > best[z]) { best[z] = s; id[z] = (int32_t)m.unk; von[z] = a; }
    }
  }
  std::vector<uint32_t> r;
  for (size_t e = n; e > 0; e = von[e]) r.push_back((uint32_t)id[e]);
  for (size_t i = r.size(); i-- > 0;) {
    if (r[i] == m.unk && !ids.empty() && ids.back() == m.unk) continue;
    ids.push_back(r[i]);
  }
}

/** Text → Wortteile mit <s> … </s>, höchstens WORTTEILE_MAX; Normalisierung wie der Tokenizer von XLM-RoBERTa. */
static std::vector<uint32_t> tokens(const Modell &m, const std::string &text) {
  std::vector<uint32_t> ids{0};  // <s>
  const size_t grenze = WORTTEILE_MAX - 1;
  std::string norm;  // normalisierter Text des laufenden Abschnitts
  std::string wort = "\xE2\x96\x81";  // „▁“: add_prefix_space
  uint32_t vorher = 0;
  bool leer = false;  // letztes Zeichen war ein Leerzeichen (mehrere werden zu einem)
  auto schluss = [&]() { if (wort.size() > 3) unigram(m, wort, ids); wort = "\xE2\x96\x81"; };
  auto zeichen = [&](uint32_t c) {
    if (c == ' ') { if (leer) return; leer = true; schluss(); return; }
    leer = false; utf8(wort, c);
  };
  for (size_t i = 0; i < text.size() && ids.size() < grenze;) {
    uint32_t c = naechstes(text.data(), text.size(), i);
    if (c >= 0x300 && c < 0x370 && vorher) {
      if (uint32_t z = m.paar(vorher, c)) {  // zusammensetzen: letztes Zeichen im Wort ersetzen
        size_t k = wort.size(); while (k > 3 && ((uint8_t)wort[k - 1] & 0xC0) == 0x80) k--; if (k > 3) k--;
        wort.resize(k); utf8(wort, z); vorher = z; continue;
      }
    }
    const char *t; uint16_t l;
    if (m.ersetzung(c, t, l)) {
      for (size_t j = 0; j < l;) zeichen(naechstes(t, l, j));
    } else zeichen(c);
    vorher = (c == ' ' || leer) ? 0 : c;
  }
  if (ids.size() < grenze) { if (leer) unigram(m, wort, ids); else schluss(); }  // Leerraum am Ende: ein „▁“ wie im Tokenizer
  if (ids.size() > grenze) ids.resize(grenze);
  ids.push_back(2);  // </s>
  (void)norm;
  return ids;
}

/* ---------- Transformer ---------- */

/** int8-Skalarprodukt über n Werte (n Vielfaches von 16). */
static int32_t punkt(const int8_t *a, const int8_t *b, uint32_t n) {
#ifdef __wasm_simd128__
  v128_t s = wasm_i32x4_splat(0);
  for (uint32_t i = 0; i < n; i += 16) {
    v128_t x = wasm_v128_load(a + i), y = wasm_v128_load(b + i);
    s = wasm_i32x4_add(s, wasm_i32x4_dot_i16x8(wasm_i16x8_extend_low_i8x16(x), wasm_i16x8_extend_low_i8x16(y)));
    s = wasm_i32x4_add(s, wasm_i32x4_dot_i16x8(wasm_i16x8_extend_high_i8x16(x), wasm_i16x8_extend_high_i8x16(y)));
  }
  return wasm_i32x4_extract_lane(s, 0) + wasm_i32x4_extract_lane(s, 1) + wasm_i32x4_extract_lane(s, 2) + wasm_i32x4_extract_lane(s, 3);
#else
  int32_t s = 0;
  for (uint32_t i = 0; i < n; i++) s += (int32_t)a[i] * b[i];
  return s;
#endif
}

/** Zeilen von x (L × spalten, float) je Zeile auf int8 runden. */
static void runden(const float *x, uint32_t L, uint32_t spalten, std::vector<int8_t> &q, std::vector<float> &f) {
  q.resize((size_t)L * spalten); f.resize(L);
  for (uint32_t t = 0; t < L; t++) {
    const float *r = x + (size_t)t * spalten; float m = 0;
    for (uint32_t k = 0; k < spalten; k++) m = std::max(m, std::fabs(r[k]));
    float s = m > 0 ? m / 127.0f : 1.0f; f[t] = s; float inv = 1.0f / s;
    for (uint32_t k = 0; k < spalten; k++) { float v = std::nearbyint(r[k] * inv); q[(size_t)t * spalten + k] = (int8_t)(v > 127 ? 127 : v < -127 ? -127 : v); }
  }
}

/** y (L × zeilen) = x · Wᵀ + b. */
static void lineare(const Matrix &W, const std::vector<int8_t> &xq, const std::vector<float> &xf, uint32_t L, float *y) {
  for (uint32_t o = 0; o < W.zeilen; o++) {
    const int8_t *w = W.w + (size_t)o * W.spalten; float sw = W.massstab[o], b = W.b[o];
    for (uint32_t t = 0; t < L; t++) y[(size_t)t * W.zeilen + o] = (float)punkt(xq.data() + (size_t)t * W.spalten, w, W.spalten) * sw * xf[t] + b;
  }
}

static void norm(float *x, uint32_t L, uint32_t d, const float *g, const float *b) {
  for (uint32_t t = 0; t < L; t++) {
    float *r = x + (size_t)t * d; double m = 0, v = 0;
    for (uint32_t k = 0; k < d; k++) m += r[k];
    m /= d;
    for (uint32_t k = 0; k < d; k++) { double z = r[k] - m; v += z * z; }
    float inv = (float)(1.0 / std::sqrt(v / d + 1e-12));
    for (uint32_t k = 0; k < d; k++) r[k] = (float)((r[k] - m) * inv) * g[k] + b[k];
  }
}

/** Vektor (384, Länge 1) aus Wortteilen: BERT vorwärts, Mittelwert über alle Wortteile. */
static std::vector<float> vorwaerts(const Modell &m, const std::vector<uint32_t> &ids) {
  const uint32_t L = (uint32_t)ids.size(), d = m.breite, h = 12, dk = d / h, z = m.zwischen;
  std::vector<float> x((size_t)L * d), q((size_t)L * d), k((size_t)L * d), v((size_t)L * d), a((size_t)L * d), y((size_t)L * d), mitte((size_t)L * z), p(L);
  std::vector<int8_t> xq; std::vector<float> xf;
  for (uint32_t t = 0; t < L; t++) {
    const int8_t *w = m.wortWerte + (size_t)ids[t] * d; float s = m.wortMassstab[ids[t]];
    for (uint32_t j = 0; j < d; j++) x[(size_t)t * d + j] = w[j] * s + m.pos[(size_t)t * d + j] + m.typ0[j];
  }
  norm(x.data(), L, d, m.ln0g, m.ln0b);
  const float skala = 1.0f / std::sqrt((float)dk);
  for (const Schicht &s : m.s) {
    runden(x.data(), L, d, xq, xf);
    lineare(s.q, xq, xf, L, q.data()); lineare(s.k, xq, xf, L, k.data()); lineare(s.v, xq, xf, L, v.data());
    for (uint32_t kopf = 0; kopf < h; kopf++) {
      const uint32_t o = kopf * dk;
      for (uint32_t i = 0; i < L; i++) {
        const float *qi = q.data() + (size_t)i * d + o; float mx = -1e30f;
        for (uint32_t j = 0; j < L; j++) { const float *kj = k.data() + (size_t)j * d + o; float s2 = 0; for (uint32_t c = 0; c < dk; c++) s2 += qi[c] * kj[c]; p[j] = s2 * skala; mx = std::max(mx, p[j]); }
        float summe = 0; for (uint32_t j = 0; j < L; j++) { p[j] = std::exp(p[j] - mx); summe += p[j]; }
        float *ai = a.data() + (size_t)i * d + o; for (uint32_t c = 0; c < dk; c++) ai[c] = 0;
        for (uint32_t j = 0; j < L; j++) { const float *vj = v.data() + (size_t)j * d + o; float g = p[j] / summe; for (uint32_t c = 0; c < dk; c++) ai[c] += g * vj[c]; }
      }
    }
    runden(a.data(), L, d, xq, xf); lineare(s.o, xq, xf, L, y.data());
    for (size_t i = 0; i < x.size(); i++) x[i] += y[i];
    norm(x.data(), L, d, s.ln1g, s.ln1b);
    runden(x.data(), L, d, xq, xf); lineare(s.rein, xq, xf, L, mitte.data());
    for (float &e : mitte) e = 0.5f * e * (1.0f + std::erf(e * 0.70710678f));  // GELU
    runden(mitte.data(), L, z, xq, xf); lineare(s.raus, xq, xf, L, y.data());
    for (size_t i = 0; i < x.size(); i++) x[i] += y[i];
    norm(x.data(), L, d, s.ln2g, s.ln2b);
  }
  std::vector<double> mittel(d, 0.0);
  for (uint32_t t = 0; t < L; t++) for (uint32_t j = 0; j < d; j++) mittel[j] += x[(size_t)t * d + j];
  double n = 0; for (double e : mittel) n += e * e;
  n = std::sqrt(n);
  std::vector<float> r(d);
  for (uint32_t j = 0; j < d; j++) r[j] = n > 0 ? (float)(mittel[j] / n) : 0.0f;
  return r;
}

static std::vector<float> vektor(const Modell &m, const std::string &text, bool suche, size_t *anzahl = nullptr) {
  std::vector<uint32_t> ids = tokens(m, std::string(suche ? "query: " : "passage: ") + text);
  if (anzahl) *anzahl = ids.size();
  return vorwaerts(m, ids);
}

static std::string modellKennung() { char b[96]; snprintf(b, sizeof b, "%s/384-int8-%u", MODELL_NAME, (unsigned)WORTTEILE_MAX); return b; }
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
  if (text.size() > 20000) text.resize(20000);  // 256 Wortteile brauchen nie mehr
  if (text.empty()) { ergebnis("ohne Volltext"); return 0; }
  Modell m;
  if (!m.laden()) { log(3, m.fehler); return 2; }
  size_t n = 0;
  std::vector<float> v = vektor(m, text, false, &n);
  std::string body = "{\"methode\":\"PUT\",\"pfad\":\"/dokumente/" + id + "/vektor\",\"body\":{\"modell\":" + jsonText(modellKennung()) + ",\"vektor\":" + zahlen(v) + "}}";
  Antwort p = api(body);
  if (p.status == 404) { ergebnis("Dokument gibt es nicht mehr"); return 0; }
  if (p.status != 200) { log(2, "Vektor nicht gespeichert: HTTP " + std::to_string(p.status) + " " + p.text.substr(0, 200)); return 1; }
  ergebnis("Vektor gespeichert (" + std::to_string(n) + " Wortteile)");
  return 0;
}

/* ---------- Wohin gehört das? (wie KI lokal – Ähnlichkeit 1.2.0, Schwellen dieses Modells) ---------- */

static const size_t KLASS_MAX = 3;
static const size_t KLASS_JE_TYP = 3;
static const double KLASS_GROESSE = 0.15;

static double naehe(double s) { return std::max(0.0, std::min(1.0, (s - SCHWELLE) / (KLASS_NAH - SCHWELLE))); }

static std::string naeheInWorten(double s, int n, const std::string &typ) {
  std::string wie = s >= KLASS_NAH ? "Sehr ähnlich" : s >= AEHNLICH ? "Ähnlich" : "Entfernt ähnlich";
  return wie + (n == 1 ? " zu einer Mappe in " : " zu " + std::to_string(n) + " Mappen in ") + typ;
}

static int32_t klassifiziere(const Json &e) {
  struct Typ { std::string id, name; double mappen = 0; std::vector<double> s; double punkte = 0; };
  std::vector<Typ> typen;
  for (const Json &t : e["typen"].l) {
    std::string id = t["id"].text(), name = t["name"].text();
    if (!id.empty() && !name.empty()) typen.push_back({id, name.substr(0, 80), std::max(0.0, t["anzahl"].zahl(0))});
  }
  int gesamt = 0;
  for (const Json &a : e["aehnliche"].l) {
    std::string typ = a["typ"].text();
    double s = a["aehnlichkeit"].zahl(-2);
    if (s < -1 || s > 1) continue;
    for (Typ &t : typen) if (t.id == typ) { t.s.push_back(s); gesamt++; break; }
  }
  if (!gesamt) { ergebnis("{\"typen\":[]}"); return 0; }
  double summeMappen = 0; int mitAnzahl = 0;
  for (const Typ &t : typen) if (!t.s.empty() && t.mappen > 0) { summeMappen += t.mappen; mitAnzahl++; }
  double mittel = mitAnzahl ? summeMappen / mitAnzahl : 0;
  std::vector<Typ *> rang;
  for (Typ &t : typen) {
    if (t.s.empty()) continue;
    std::sort(t.s.begin(), t.s.end(), std::greater<double>());
    double gewicht = 1;
    for (size_t i = 0; i < t.s.size() && i < KLASS_JE_TYP; i++, gewicht /= 2) t.punkte += gewicht * naehe(t.s[i]) * naehe(t.s[i]);
    if (mittel > 0 && t.mappen > mittel) t.punkte *= std::pow(mittel / t.mappen, KLASS_GROESSE);
    if (t.punkte > 0) rang.push_back(&t);
  }
  if (rang.empty()) { ergebnis("{\"typen\":[]}"); return 0; }
  std::sort(rang.begin(), rang.end(), [](const Typ *a, const Typ *b) { return a->punkte != b->punkte ? a->punkte > b->punkte : a->s[0] > b->s[0]; });
  double summe = 0;
  for (const Typ *t : rang) summe += t->punkte;
  std::string r = "{\"typen\":[";
  for (size_t i = 0; i < rang.size() && i < KLASS_MAX; i++) {
    const Typ &t = *rang[i];
    double s = std::min(0.95, naehe(t.s[0]) * t.punkte / summe);
    int nah = 0;
    for (double x : t.s) if (x >= t.s[0] - 0.01) nah++;
    std::string grund = naeheInWorten(t.s[0], nah, t.name);
    char b[64];
    snprintf(b, sizeof b, "%.2f", s);
    r += std::string(i ? "," : "") + "{\"typ\":" + jsonText(t.id) + ",\"sicherheit\":" + b + ",\"begruendung\":" + jsonText(grund) + "}";
  }
  ergebnis(r + "]}");
  return 0;
}

extern "C" __attribute__((export_name("dms_aktion"))) int32_t dms_aktion(char *json, int32_t len) {
  Json e = JsonLeser::lies(json, (size_t)len);
  if (e["aktion"].text() == "dms:klassifizieren") return klassifiziere(e);
  if (e["aktion"].text() != "dms:vektor") { ergebnis("Dieses Paket hat keine Aktionen."); return 0; }
  char s[32]; snprintf(s, sizeof s, "%.3f", SCHWELLE);
  std::string text = e["text"].text();
  std::string aus = "{\"modell\":" + jsonText(modellKennung()) + ",\"schwelle\":" + s;
  if (!text.empty()) {
    Modell m;
    if (!m.laden()) { log(3, m.fehler); ergebnis(m.fehler); return 2; }
    std::string art = e["art"].text();
    bool suche = art == "suche" || (art != "dokument" && text.size() <= SUCHE_MAX);
    if (text.size() > 20000) text.resize(20000);
    aus += ",\"vektor\":" + zahlen(vektor(m, text, suche));
  }
  ergebnis(aus + "}");
  return 0;
}

#ifdef ABLAGO_NATIV
// Für tests/nativ.cpp: Wortteile und Vektor ohne die Schnittstelle.
std::vector<uint32_t> test_tokens(const std::string &t) { static Modell m; static bool g = m.laden(); (void)g; return tokens(m, t); }
std::vector<float> test_vektor(const std::string &t) { static Modell m; static bool g = m.laden(); (void)g; return vorwaerts(m, tokens(m, t)); }
#endif
