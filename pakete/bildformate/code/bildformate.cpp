// Paket Bildformate (dms-registry #48, DMS #577): wandelt Bilder, die das DMS nicht selbst lesen kann, in eine
// Fassung, die es kennt – TIFF (auch mehrseitig) in ein PDF, WebP in ein JPEG, GIF und BMP in ein PNG.
//
// Ablauf (ab DMS 0.137.0): Ereignis „Datei umwandeln“ (datei.umwandeln) → Originaldatei über die API holen →
// Dateityp am Inhalt erkennen → lesen (libtiff, libwebp, stb_image) → PDF, JPEG oder PNG schreiben →
// PUT /dokumente/{id}/fassung?sha256=… Das Original bleibt unverändert; Vorschaubild und Volltext macht das DMS
// aus der Fassung (Textebene bzw. Paket Texterkennung). Kein Netz, kein Dateisystem.
#include <algorithm>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include <jpeglib.h>
#include <tiffio.h>
#include <webp/decode.h>
#include <zlib.h>

#include "ausgabe.h"

static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__, "libtiff-RGBA wird als Bytes R, G, B, A gelesen");
#include "json.h"

// stb: GIF und BMP lesen, PNG schreiben (PNG mit zlib statt des eigenen, schwächeren Packers).
static unsigned char *zlibPacken(unsigned char *daten, int laenge, int *aus, int stufe);
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Weverything"
#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_GIF
#define STBI_ONLY_BMP
#define STBI_NO_STDIO
#define STBI_NO_LINEAR
#define STBI_NO_HDR
#define STBI_MAX_DIMENSIONS 30000
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#define STBI_WRITE_NO_STDIO
#define STBIW_ZLIB_COMPRESS zlibPacken
#include "stb_image_write.h"
#pragma clang diagnostic pop

static unsigned char *zlibPacken(unsigned char *daten, int laenge, int *aus, int stufe) {
  (void)stufe;
  uLongf n = compressBound((uLong)laenge);
  unsigned char *o = (unsigned char *)STBIW_MALLOC(n);
  if (!o || compress2(o, &n, daten, (uLong)laenge, 6) != Z_OK) { STBIW_FREE(o); *aus = 0; return nullptr; }
  *aus = (int)n;
  return o;
}

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
extern "C" {
DMS(api) int32_t dms_api(const char *json, int32_t len);
DMS(api_binaer) int32_t dms_api_binaer(const char *json, int32_t len, const uint8_t *body, int32_t blen);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(void *ziel, int32_t max);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);
}

namespace {

enum Stufe { DEBUG = 0, INFO = 1, WARNUNG = 2, FEHLER = 3 };

// Höchstens so viele Bildpunkte je Seite (RGBA: 4 Bytes je Punkt; A3 mit 400 dpi sind gut 31 Millionen).
constexpr size_t PUNKTE_MAX = 36u * 1000u * 1000u;
// So groß darf die Fassung werden (wie im DMS).
constexpr size_t FASSUNG_MAX = 50u * 1024u * 1024u;
constexpr int JPEG_QUALITAET = 90;

void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }

std::vector<uint8_t> antwort() {
  std::vector<uint8_t> a((size_t)dms_antwort_laenge());
  if (!a.empty()) dms_antwort_lesen(a.data(), (int32_t)a.size());
  return a;
}
std::string antwortText() { std::vector<uint8_t> a = antwort(); return std::string(a.begin(), a.end()); }

bool sichereId(const std::string &id) {
  if (id.empty() || id.size() > 64) return false;
  for (char c : id) if (!(isalnum((unsigned char)c) || c == '-')) return false;
  return true;
}
bool sichererSha(const std::string &s) {
  if (s.size() != 64) return false;
  for (char c : s) if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
  return true;
}

/* ---------- Ein Bild als RGBA ---------- */

struct Bild {
  int breite = 0, hoehe = 0;
  double dpiX = 0, dpiY = 0;  // 0 = unbekannt
  std::vector<uint8_t> rgba;
};

/* ---------- Schreiben: JPEG, PNG, Seiten für das PDF ---------- */

struct JpegFehler { jpeg_error_mgr basis; };
void jpegAbbruch(j_common_ptr c) {
  char t[JMSG_LENGTH_MAX];
  (*c->err->format_message)(c, t);
  log(FEHLER, std::string("JPEG schreiben: ") + t);
  abort();  // ohne setjmp/longjmp (WASI): Aufruf beenden
}

// JPEG in Grau (1 Kanal) oder Farbe (3 Kanäle) aus RGBA – Zeile für Zeile, ohne zweite Kopie des Bilds.
std::vector<uint8_t> jpeg(const std::vector<uint8_t> &rgba, int breite, int hoehe, int kanaele, double dpiX, double dpiY) {
  jpeg_compress_struct c;
  JpegFehler f;
  c.err = jpeg_std_error(&f.basis);
  f.basis.error_exit = jpegAbbruch;
  jpeg_create_compress(&c);
  unsigned char *ziel = nullptr;
  unsigned long laenge = 0;
  jpeg_mem_dest(&c, &ziel, &laenge);
  c.image_width = (JDIMENSION)breite;
  c.image_height = (JDIMENSION)hoehe;
  c.input_components = kanaele;
  c.in_color_space = kanaele == 3 ? JCS_RGB : JCS_GRAYSCALE;
  jpeg_set_defaults(&c);
  jpeg_set_quality(&c, JPEG_QUALITAET, TRUE);
  if (dpiX > 0 && dpiY > 0) { c.density_unit = 1; c.X_density = (UINT16)(dpiX + 0.5); c.Y_density = (UINT16)(dpiY + 0.5); }
  jpeg_start_compress(&c, TRUE);
  std::vector<uint8_t> zeile((size_t)breite * (size_t)kanaele);
  while (c.next_scanline < c.image_height) {
    const uint8_t *q = rgba.data() + (size_t)c.next_scanline * (size_t)breite * 4;
    for (int x = 0; x < breite; x++)
      for (int k = 0; k < kanaele; k++) zeile[(size_t)x * (size_t)kanaele + (size_t)k] = q[(size_t)x * 4 + (size_t)k];
    JSAMPROW z = zeile.data();
    jpeg_write_scanlines(&c, &z, 1);
  }
  jpeg_finish_compress(&c);
  std::vector<uint8_t> o(ziel, ziel + laenge);
  jpeg_destroy_compress(&c);
  free(ziel);
  return o;
}

void anhaengen(void *ctx, void *daten, int n) {
  auto *o = static_cast<std::vector<uint8_t> *>(ctx);
  o->insert(o->end(), static_cast<uint8_t *>(daten), static_cast<uint8_t *>(daten) + n);
}

// PNG (Grau oder RGB) – verlustfrei, für GIF und BMP (Grafiken, Bildschirmfotos).
std::vector<uint8_t> png(const Bild &b) {
  const int n = ausgabe::bildart(b.rgba) == ausgabe::Art::FARBE ? 3 : 1;
  std::vector<uint8_t> px = ausgabe::kanaele(b.rgba, n), o;
  stbi_write_png_to_func(anhaengen, &o, b.breite, b.hoehe, n, px.data(), b.breite * n);
  return o;
}

// Eine Seite fürs PDF: Schwarzweiß als 1 Bit (verlustfrei, klein), sonst JPEG in Grau oder Farbe.
ausgabe::Seite seite(const Bild &b) {
  ausgabe::Seite s;
  s.breite = b.breite; s.hoehe = b.hoehe;
  s.dpiX = b.dpiX > 0 ? b.dpiX : 300; s.dpiY = b.dpiY > 0 ? b.dpiY : s.dpiX;
  const ausgabe::Art art = ausgabe::bildart(b.rgba);
  if (art == ausgabe::Art::SCHWARZWEISS) {
    std::vector<uint8_t> bits = ausgabe::einBit(b.rgba, b.breite, b.hoehe);
    uLongf n = compressBound((uLong)bits.size());
    s.daten.resize(n);
    compress2(s.daten.data(), &n, bits.data(), (uLong)bits.size(), 9);
    s.daten.resize(n);
    s.bits = 1;
  } else {
    s.kanaele = art == ausgabe::Art::FARBE ? 3 : 1;
    s.daten = jpeg(b.rgba, b.breite, b.hoehe, s.kanaele, s.dpiX, s.dpiY);
    s.jpeg = true;
  }
  return s;
}

/* ---------- Lesen ---------- */

std::string tiffMeldung;
void tiffFehler(const char *modul, const char *fmt, va_list ap) {
  char t[300];
  vsnprintf(t, sizeof t, fmt, ap);
  tiffMeldung = std::string(modul ? modul : "TIFF") + ": " + t;
}
void tiffWarnung(const char *, const char *, va_list) {}

// TIFF aus dem Speicher (libtiff liest über diese Funktionen statt aus einer Datei).
struct Speicher { const uint8_t *daten; toff_t laenge, pos; };
tmsize_t tLesen(thandle_t h, void *ziel, tmsize_t n) {
  auto *s = static_cast<Speicher *>(h);
  if (s->pos >= s->laenge) return 0;
  toff_t k = std::min<toff_t>((toff_t)n, s->laenge - s->pos);
  memcpy(ziel, s->daten + s->pos, (size_t)k);
  s->pos += k;
  return (tmsize_t)k;
}
tmsize_t tSchreiben(thandle_t, void *, tmsize_t) { return 0; }
toff_t tSuchen(thandle_t h, toff_t off, int woher) {
  auto *s = static_cast<Speicher *>(h);
  toff_t neu = woher == SEEK_SET ? off : woher == SEEK_CUR ? s->pos + off : s->laenge + off;
  s->pos = neu;
  return neu;
}
int tSchliessen(thandle_t) { return 0; }
toff_t tGroesse(thandle_t h) { return static_cast<Speicher *>(h)->laenge; }
int tKarte(thandle_t, void **, toff_t *) { return 0; }
void tKarteWeg(thandle_t, void *, toff_t) {}

double dpi(TIFF *t, ttag_t tag) {
  float v = 0;
  uint16_t einheit = RESUNIT_INCH;
  if (!TIFFGetField(t, tag, &v) || !(v > 0)) return 0;
  TIFFGetFieldDefaulted(t, TIFFTAG_RESOLUTIONUNIT, &einheit);
  double d = einheit == RESUNIT_CENTIMETER ? v * 2.54 : einheit == RESUNIT_NONE ? 0 : v;
  return d >= 50 && d <= 2400 ? d : 0;  // Unsinnige Angaben übergehen (dann 300 dpi)
}

struct Gelesen { std::vector<ausgabe::Seite> seiten; int gesamt = 0; std::string fehler; };

// Alle Seiten (Verzeichnisse) eines TIFF bis max, je Seite gleich gepackt – so liegt nie mehr als ein Bild offen.
Gelesen tiffLesen(const std::vector<uint8_t> &datei, int max) {
  Gelesen g;
  tiffMeldung.clear();
  TIFFSetErrorHandler(tiffFehler);
  TIFFSetWarningHandler(tiffWarnung);
  Speicher sp{datei.data(), (toff_t)datei.size(), 0};
  TIFF *t = TIFFClientOpen("datei.tif", "rm", &sp, tLesen, tSchreiben, tSuchen, tSchliessen, tGroesse, tKarte, tKarteWeg);
  if (!t) { g.fehler = tiffMeldung.empty() ? "kein lesbares TIFF" : tiffMeldung; return g; }
  do {
    g.gesamt++;
    if ((int)g.seiten.size() >= max) continue;
    uint32_t w = 0, h = 0;
    TIFFGetField(t, TIFFTAG_IMAGEWIDTH, &w);
    TIFFGetField(t, TIFFTAG_IMAGELENGTH, &h);
    if (!w || !h || (size_t)w * h > PUNKTE_MAX) { g.fehler = "Seite " + std::to_string(g.gesamt) + ": " + std::to_string(w) + " × " + std::to_string(h) + " Bildpunkte – höchstens 36 Millionen je Seite"; break; }
    Bild b;
    b.breite = (int)w; b.hoehe = (int)h;
    b.dpiX = dpi(t, TIFFTAG_XRESOLUTION); b.dpiY = dpi(t, TIFFTAG_YRESOLUTION);
    if (!b.dpiY) b.dpiY = b.dpiX;
    // libtiff liefert je Punkt ein uint32 mit R, G, B, A in den Bytes 0–3 (Little Endian wie WebAssembly):
    // also gleich in den RGBA-Speicher lesen, ohne zweite Kopie.
    b.rgba.resize((size_t)w * h * 4);
    if (!TIFFReadRGBAImageOriented(t, w, h, reinterpret_cast<uint32_t *>(b.rgba.data()), ORIENTATION_TOPLEFT, 0)) {
      g.fehler = "Seite " + std::to_string(g.gesamt) + ": " + (tiffMeldung.empty() ? "nicht lesbar" : tiffMeldung);
      break;
    }
    ausgabe::aufWeiss(b.rgba);
    g.seiten.push_back(seite(b));
  } while (TIFFReadDirectory(t));
  TIFFClose(t);
  return g;
}

bool webpLesen(const std::vector<uint8_t> &datei, Bild &b, std::string &fehler) {
  int w = 0, h = 0;
  if (!WebPGetInfo(datei.data(), datei.size(), &w, &h)) { fehler = "kein lesbares WebP"; return false; }
  if ((size_t)w * (size_t)h > PUNKTE_MAX) { fehler = std::to_string(w) + " × " + std::to_string(h) + " Bildpunkte – höchstens 36 Millionen"; return false; }
  b.rgba.resize((size_t)w * (size_t)h * 4);
  if (!WebPDecodeRGBAInto(datei.data(), datei.size(), b.rgba.data(), b.rgba.size(), w * 4)) { fehler = "WebP nicht lesbar (z. B. beschädigt)"; return false; }
  b.breite = w; b.hoehe = h;
  ausgabe::aufWeiss(b.rgba);
  return true;
}

// GIF (erstes Bild einer Animation) und BMP mit stb_image.
bool stbLesen(const std::vector<uint8_t> &datei, Bild &b, std::string &fehler) {
  int w = 0, h = 0, n = 0;
  if (!stbi_info_from_memory(datei.data(), (int)datei.size(), &w, &h, &n)) { fehler = stbi_failure_reason() ? stbi_failure_reason() : "nicht lesbar"; return false; }
  if ((size_t)w * (size_t)h > PUNKTE_MAX) { fehler = std::to_string(w) + " × " + std::to_string(h) + " Bildpunkte – höchstens 36 Millionen"; return false; }
  unsigned char *px = stbi_load_from_memory(datei.data(), (int)datei.size(), &w, &h, &n, 4);
  if (!px) { fehler = stbi_failure_reason() ? stbi_failure_reason() : "nicht lesbar"; return false; }
  b.breite = w; b.hoehe = h;
  b.rgba.assign(px, px + (size_t)w * (size_t)h * 4);
  stbi_image_free(px);
  ausgabe::aufWeiss(b.rgba);
  return true;
}

/* ---------- Ein Ereignis ---------- */

const char *NAMEN[][2] = {{"tiff", "TIFF"}, {"webp", "WebP"}, {"gif", "GIF"}, {"bmp", "BMP"}};
std::string name(const std::string &art) {
  for (auto &n : NAMEN) if (art == n[0]) return n[1];
  return art;
}

int verarbeite(const Json &e) {
  if (e["art"].text() != "datei.umwandeln") return 0;  // z. B. paket.einstellungen_geaendert
  const Json &d = e["daten"];
  const std::string dok = d["dokument"].text(), sha = d["sha256"].text();
  if (!sichereId(dok) || !sichererSha(sha)) { ergebnis("Ereignis ohne gültiges Dokument"); return 0; }
  const int maxSeiten = std::max(1, std::min(1000, (int)e["einstellungen"]["max_seiten"].zahl(200)));

  std::string q = "{\"methode\":\"GET\",\"pfad\":\"/dokumente/" + dok + "/inhalt\"}";
  int s = dms_api(q.data(), (int32_t)q.size());
  if (s == 404) { ergebnis("Das Dokument gibt es nicht mehr – nichts zu tun"); return 0; }
  if (s != 200) { log(FEHLER, "Datei holen: HTTP " + std::to_string(s) + " " + antwortText().substr(0, 200)); return 1; }
  std::vector<uint8_t> datei = antwort();
  const std::string art = ausgabe::dateityp(datei.data(), datei.size());
  if (art.empty()) { ergebnis("Kein TIFF, WebP, GIF oder BMP (am Inhalt erkannt) – nichts umgewandelt"); return 0; }

  std::vector<uint8_t> fassung;
  std::string was, fehler;
  if (art == "tiff") {
    Gelesen g = tiffLesen(datei, maxSeiten);
    if (!g.fehler.empty() || g.seiten.empty()) fehler = g.fehler.empty() ? "keine Seite" : g.fehler;
    else {
      std::vector<uint8_t>().swap(datei);
      fassung = ausgabe::pdf(g.seiten);
      was = std::to_string(g.seiten.size()) + (g.seiten.size() == 1 ? " Seite" : " Seiten") + " → PDF";
      if (g.gesamt > (int)g.seiten.size()) was += " (nur die ersten " + std::to_string(g.seiten.size()) + " von " + std::to_string(g.gesamt) + ")";
    }
  } else {
    Bild b;
    bool ok = art == "webp" ? webpLesen(datei, b, fehler) : stbLesen(datei, b, fehler);
    std::vector<uint8_t>().swap(datei);
    if (ok && art == "webp") {
      // WebP sind meist Fotos: JPEG (Grau oder Farbe). GIF und BMP sind eher Grafiken: verlustfrei als PNG.
      const int n = ausgabe::bildart(b.rgba) == ausgabe::Art::FARBE ? 3 : 1;
      fassung = jpeg(b.rgba, b.breite, b.hoehe, n, 0, 0);
      was = std::to_string(b.breite) + " × " + std::to_string(b.hoehe) + " → JPEG";
    } else if (ok) {
      fassung = png(b);
      was = std::to_string(b.breite) + " × " + std::to_string(b.hoehe) + " → PNG";
    }
  }
  if (!fehler.empty() || fassung.empty()) {
    // Eine kaputte Datei wird beim nächsten Versuch nicht besser: kein Fehlercode, aber die Meldung am Dokument.
    const std::string m = name(art) + " lässt sich nicht lesen: " + (fehler.empty() ? "unbekannter Fehler" : fehler);
    log(WARNUNG, "Dokument " + dok + ": " + m);
    ergebnis(m);
    return 0;
  }
  if (fassung.size() > FASSUNG_MAX) {
    const std::string m = name(art) + ": Die Fassung wäre " + ausgabe::groesse(fassung.size()) + " groß – höchstens 50 MB";
    log(WARNUNG, "Dokument " + dok + ": " + m);
    ergebnis(m);
    return 0;
  }

  q = "{\"methode\":\"PUT\",\"pfad\":\"/dokumente/" + dok + "/fassung?sha256=" + sha + "\"}";
  s = dms_api_binaer(q.data(), (int32_t)q.size(), fassung.data(), (int32_t)fassung.size());
  const std::string meldung = name(art) + ", " + was + ", " + ausgabe::groesse(fassung.size());
  if (s == 200) { log(INFO, "Dokument " + dok + ": " + meldung); ergebnis(meldung); return 0; }
  const std::string grund = antwortText().substr(0, 300);
  // Neue Version, Dokument weg oder nicht (mehr) zuständig: nichts zu wiederholen.
  if (s == 409 || s == 404 || s == 403 || s == 413 || s == 415 || s == 422) {
    log(WARNUNG, "Dokument " + dok + ": Fassung nicht angenommen (HTTP " + std::to_string(s) + ") " + grund);
    ergebnis("Fassung nicht angenommen: " + grund);
    return 0;
  }
  log(FEHLER, "Fassung schreiben: HTTP " + std::to_string(s) + " " + grund);
  return 2;
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

__attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *json, int32_t n) {
  return verarbeite(JsonLeser::lies(json, (size_t)n));
}

}
