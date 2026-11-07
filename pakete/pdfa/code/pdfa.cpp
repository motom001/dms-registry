// Paket PDF/A (dms-registry #29, DMS #631): legt zu Dokumenten eine Archivfassung ab – ein durchsuchbares PDF/A-2b
// mit unsichtbarer Textebene genau auf den Wörtern. Das Original bleibt unverändert das Dokument.
//
// Ablauf (ab DMS 0.149.0): Ereignis „Archivfassung erstellen“ (datei.archivfassung, erst wenn der Volltext feststeht)
// → schon vorhanden? → Wortpositionen über die API → Seiten bauen:
//   - JPEG: das Bild unverändert übernehmen (ohne EXIF/XMP-Metadaten), Ausrichtung nach EXIF;
//   - PNG: verlustfrei (Flate mit PNG-Prädiktoren), Durchsichtiges auf Weiß;
//   - PDF: jede Seite als Graustufenbild vom DMS (GET …/seiten/{nr}/scan, 300 dpi; bei langen Dokumenten weniger),
//     als JPEG – so kommt nichts aus dem Original mit, das PDF/A verbietet (JavaScript, Aktionen, externe Inhalte,
//     nicht eingebettete Schriften, Transparenz, Formularfelder: alles wird zu dem, was man sieht);
//   - TIFF und Co. (quelle lesefassung): die Lesefassung des Pakets Bildformate, wie oben;
// → darüber die Wörter → PUT /dokumente/{id}/archivfassung?sha256=…
// Kein Netz, kein Dateisystem; ICC-Profil und Schrift liegen unter code/daten/ und kommen über dms.datei.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

#include <jpeglib.h>

#include "json.h"
#include "mailsatz.h"
#include "pdfa.h"

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Weverything"
#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#define STBI_ONLY_JPEG
#define STBI_ONLY_GIF
#define STBI_NO_STDIO
#define STBI_NO_LINEAR
#define STBI_NO_HDR
#define STBI_MAX_DIMENSIONS 30000
#include "stb_image.h"
#pragma clang diagnostic pop

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
extern "C" {
DMS(api) int32_t dms_api(const char *json, int32_t len);
DMS(api_binaer) int32_t dms_api_binaer(const char *json, int32_t len, const uint8_t *body, int32_t blen);
DMS(datei) int32_t dms_datei(const char *name, int32_t len);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(void *ziel, int32_t max);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);
}

#ifndef PAKET_VERSION
#define PAKET_VERSION "0.0.0"
#endif

namespace {

enum Stufe { DEBUG = 0, INFO = 1, WARNUNG = 2, FEHLER = 3 };

// Wie im DMS: höchstens so groß und so viele Seiten nimmt es eine Archivfassung an.
constexpr size_t ARCHIV_MAX = 100u * 1024u * 1024u;
constexpr int SEITEN_MAX = 1000;
// Größer nimmt das DMS keine Quelle für eine Archivfassung an (ARCHIV_QUELLE_MAX_BYTES).
constexpr size_t QUELLE_MAX = 50u * 1024u * 1024u;
// Bilder, die das Paket dekodieren muss (PNG, CMYK-JPEG): höchstens so viele Bildpunkte (Speicher des Läufers).
constexpr size_t PUNKTE_MAX = 20u * 1000u * 1000u;
// Qualität der JPEG-Seiten (Seitenbilder von PDFs, umgerechnete JPEG).
constexpr int JPEG_QUALITAET = 80;
// Zeit je Aufruf (Zeitgrenze des Läufers: 120 s). Eine Archivfassung entsteht in einem Aufruf – ein Zwischenstand
// (das halbe PDF) passt nicht in die Fortsetzung des Läufers (höchstens 4 MB).
constexpr long ZEIT_MS = 100000;

void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }

std::vector<uint8_t> antwort() {
  std::vector<uint8_t> a((size_t)std::max(0, (int)dms_antwort_laenge()));
  if (!a.empty()) dms_antwort_lesen(a.data(), (int32_t)a.size());
  return a;
}
std::string alsText(const std::vector<uint8_t> &a, size_t max = 300) { return std::string(a.begin(), a.begin() + (long)std::min(max, a.size())); }

struct Antwort { int status; std::vector<uint8_t> body; };
Antwort get(const std::string &pfad) {
  const std::string q = "{\"methode\":\"GET\",\"pfad\":" + jsonText(pfad) + "}";
  int s = dms_api(q.data(), (int32_t)q.size());
  return {s, antwort()};
}

// Fehlermeldung des DMS ({"fehler": "…"}) bzw. der Anfang der Antwort.
std::string grundAus(const std::vector<uint8_t> &b) {
  Json j = JsonLeser::lies(reinterpret_cast<const char *>(b.data()), b.size());
  std::string f = j["fehler"].text();
  if (f.empty()) f = j["error"].text();
  return f.empty() ? alsText(b, 300) : f.substr(0, 300);
}

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

long jetztMs() {
  using namespace std::chrono;
  return (long)duration_cast<milliseconds>(steady_clock::now().time_since_epoch()).count();
}

bool datei(const std::string &name, std::vector<uint8_t> &ziel) {
  int32_t n = dms_datei(name.data(), (int32_t)name.size());
  if (n <= 0) return false;
  ziel.resize((size_t)n);
  dms_antwort_lesen(ziel.data(), n);
  return true;
}

/* ---------- JPEG schreiben (libjpeg-turbo) ---------- */

void jpegAbbruch(j_common_ptr c) {
  char t[JMSG_LENGTH_MAX];
  (*c->err->format_message)(c, t);
  log(FEHLER, std::string("JPEG schreiben: ") + t);
  abort();  // ohne setjmp/longjmp (WASI): Aufruf beenden
}

// Grau (1 Kanal) oder RGB (3 Kanäle), Zeile für Zeile aus px (dicht gepackt).
std::vector<uint8_t> jpeg(const uint8_t *px, int breite, int hoehe, int kanaele) {
  jpeg_compress_struct c;
  jpeg_error_mgr f;
  c.err = jpeg_std_error(&f);
  f.error_exit = jpegAbbruch;
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
  c.optimize_coding = TRUE;
  jpeg_start_compress(&c, TRUE);
  while (c.next_scanline < c.image_height) {
    JSAMPROW z = const_cast<JSAMPROW>(px + (size_t)c.next_scanline * (size_t)breite * (size_t)kanaele);
    jpeg_write_scanlines(&c, &z, 1);
  }
  jpeg_finish_compress(&c);
  std::vector<uint8_t> o(ziel, ziel + laenge);
  jpeg_destroy_compress(&c);
  free(ziel);
  return o;
}

/* ---------- Wortpositionen ---------- */

struct WpSeite { std::string quelle; double breite = 0, hoehe = 0; std::vector<pdfa::Wort> woerter; };
struct Wp { bool vollstaendig = false; std::string mime; std::vector<WpSeite> seiten; };

Wp liesWortpositionen(const std::vector<uint8_t> &b) {
  Wp w;
  Json j = JsonLeser::lies(reinterpret_cast<const char *>(b.data()), b.size());
  w.vollstaendig = j["vollstaendig"].wahr();
  w.mime = j["mime"].text();
  for (const Json &s : j["seiten"].l) {
    WpSeite x;
    x.quelle = s["quelle"].text();
    x.breite = s["breite"].zahl(0);
    x.hoehe = s["hoehe"].zahl(0);
    for (const Json &a : s["woerter"].l) {
      if (a.art != Json::LISTE || a.l.size() != 5 || a.l[0].art != Json::TEXT) continue;
      pdfa::Wort wort{a.l[0].text(), a.l[1].zahl(), a.l[2].zahl(), a.l[3].zahl(), a.l[4].zahl()};
      if (!(wort.b > 0) || !(wort.h > 0)) continue;
      x.woerter.push_back(std::move(wort));
    }
    w.seiten.push_back(std::move(x));
  }
  return w;
}

// Wörter eines gespeicherten Bilds (relativ zum Bild) auf die angezeigte Seite (EXIF-Ausrichtung) bringen.
std::vector<pdfa::Wort> gerichtet(std::vector<pdfa::Wort> w, int o) {
  if (o == 1) return w;
  for (pdfa::Wort &x : w) {
    double X1, Y1, X2, Y2;
    pdfa::richte(o, x.x, x.y, X1, Y1);
    pdfa::richte(o, x.x + x.b, x.y + x.h, X2, Y2);
    x.x = std::min(X1, X2); x.y = std::min(Y1, Y2); x.b = std::fabs(X2 - X1); x.h = std::fabs(Y2 - Y1);
  }
  return w;
}

/* ---------- Seiten aus Bildern ---------- */

// Seitengröße aus Bildpunkten und Auflösung: Angaben unter 100 dpi (Handyfotos schreiben 72 hinein) gelten nicht –
// dann 300 dpi, wie bei einem Scan.
double punkte(int px, double dpi) { return px * 72.0 / (dpi >= 100 && dpi <= 2400 ? dpi : 300.0); }

// pHYs eines PNG (Bildpunkte je Meter) → dpi; 0, wenn unbekannt.
double pngDpi(const std::vector<uint8_t> &b) {
  size_t i = 8;
  while (i + 12 <= b.size()) {
    uint32_t l = (uint32_t)b[i] << 24 | (uint32_t)b[i + 1] << 16 | (uint32_t)b[i + 2] << 8 | b[i + 3];
    if (i + 12 + (size_t)l > b.size()) break;
    if (!memcmp(&b[i + 4], "pHYs", 4) && l >= 9 && b[i + 16] == 1) {
      uint32_t x = (uint32_t)b[i + 8] << 24 | (uint32_t)b[i + 9] << 16 | (uint32_t)b[i + 10] << 8 | b[i + 11];
      return x * 0.0254;
    }
    if (!memcmp(&b[i + 4], "IDAT", 4)) break;
    i += 12 + l;
  }
  return 0;
}

struct Gebaut { pdfa::Seite seite; std::string wie, fehler; };

// Bildpunkte dekodieren (stb_image), Durchsichtiges auf Weiß, Grau erkennen → Seite (verlustfrei oder JPEG).
bool dekodiere(const std::vector<uint8_t> &datei, bool verlustfrei, pdfa::Bild &bild, std::string &fehler) {
  int w = 0, h = 0, n = 0;
  if (!stbi_info_from_memory(datei.data(), (int)datei.size(), &w, &h, &n)) { fehler = std::string("Bild nicht lesbar: ") + (stbi_failure_reason() ? stbi_failure_reason() : "unbekannt"); return false; }
  if ((size_t)w * (size_t)h > PUNKTE_MAX) { fehler = std::to_string(w) + " × " + std::to_string(h) + " Bildpunkte – höchstens 20 Millionen"; return false; }
  const bool alpha = n == 2 || n == 4;
  const int lese = alpha ? 4 : 3;
  unsigned char *px = stbi_load_from_memory(datei.data(), (int)datei.size(), &w, &h, &n, lese);
  if (!px) { fehler = std::string("Bild nicht lesbar: ") + (stbi_failure_reason() ? stbi_failure_reason() : "unbekannt"); return false; }
  const size_t punkte = (size_t)w * (size_t)h;
  bool grau = true;
  // Auf Weiß (wie auf Papier) und gleich auf 3 Kanäle zusammenschieben.
  for (size_t i = 0; i < punkte; i++) {
    unsigned char *q = px + i * (size_t)lese, *z = px + i * 3;
    unsigned r = q[0], g = q[1], b = q[2];
    if (alpha) {
      unsigned a = q[3];
      r = (r * a + 255 * (255 - a) + 127) / 255; g = (g * a + 255 * (255 - a) + 127) / 255; b = (b * a + 255 * (255 - a) + 127) / 255;
    }
    z[0] = (unsigned char)r; z[1] = (unsigned char)g; z[2] = (unsigned char)b;
    if (r != g || g != b) grau = false;
  }
  const int k = grau ? 1 : 3;
  if (grau) for (size_t i = 0; i < punkte; i++) px[i] = px[i * 3];
  if (verlustfrei) bild = pdfa::flate(px, w, h, k);
  else {
    bild.breite = w; bild.hoehe = h; bild.kanaele = k; bild.jpeg = true;
    bild.daten = jpeg(px, w, h, k);
  }
  stbi_image_free(px);
  if (bild.daten.empty()) { fehler = "Bild nicht packbar"; return false; }
  return true;
}

Gebaut bildSeite(std::vector<uint8_t> datei, const std::string &mime, const WpSeite &wp) {
  Gebaut g;
  pdfa::Seite &s = g.seite;
  double dpiX = 0, dpiY = 0;
  int breite = 0, hoehe = 0;
  if (mime == "image/jpeg") {
    pdfa::JpegInfo j = pdfa::jpegInfo(datei.data(), datei.size());
    if (!j.ok) { g.fehler = "kein lesbares JPEG"; return g; }
    s.orientierung = j.orientierung;
    dpiX = j.dpiX; dpiY = j.dpiY;
    breite = j.breite; hoehe = j.hoehe;
    if (pdfa::jpegDurchreichen(j)) {
      s.bild.breite = j.breite; s.bild.hoehe = j.hoehe; s.bild.kanaele = j.kanaele; s.bild.jpeg = true;
      s.bild.daten = pdfa::jpegOhneMetadaten(datei.data(), datei.size());
      g.wie = "JPEG unverändert übernommen";
    } else {
      // CMYK, 12 Bit, RGB ohne Adobe-Marke …: dekodieren und neu als JPEG (sRGB).
      if (!dekodiere(datei, false, s.bild, g.fehler)) return g;
      g.wie = "JPEG umgerechnet";
    }
  } else if (mime == "image/png") {
    dpiX = dpiY = pngDpi(datei);
    if (!dekodiere(datei, true, s.bild, g.fehler)) return g;
    breite = s.bild.breite; hoehe = s.bild.hoehe;
    g.wie = "PNG verlustfrei";
  } else {
    g.fehler = "unbekannter Bildtyp " + mime;
    return g;
  }
  std::vector<uint8_t>().swap(datei);
  // Angezeigte Seite: bei Ausrichtung 5–8 Breite und Höhe getauscht.
  const bool q = pdfa::quer(s.orientierung);
  const int bw = q ? hoehe : breite, bh = q ? breite : hoehe;
  const double dx = q ? dpiY : dpiX, dy = q ? dpiX : dpiY;
  s.breite = punkte(bw, dx);
  s.hoehe = punkte(bh, dy > 0 ? dy : dx);
  // Die Wortpositionen gelten für das gespeicherte Bild (so liefert das DMS es der Texterkennung).
  s.woerter = gerichtet(wp.woerter, s.orientierung);
  return g;
}

// PGM (P5, 8 Bit) aus GET …/seiten/{nr}/scan.
bool pgm(const std::vector<uint8_t> &b, int &w, int &h, size_t &start) {
  int mx = 0, n = 0;
  std::string kopf(b.begin(), b.begin() + (long)std::min<size_t>(b.size(), 64));
  if (sscanf(kopf.c_str(), "P5 %d %d %d%n", &w, &h, &mx, &n) != 3 || mx != 255 || w <= 0 || h <= 0) return false;
  start = (size_t)n + 1;
  return b.size() >= start + (size_t)w * (size_t)h;
}

// Auflösung der Seitenbilder: 300 dpi, bei langen Dokumenten weniger (Zeit je Aufruf, höchstens 100 MB).
int dpiFuer(int seiten) { return seiten <= 50 ? 300 : seiten <= 200 ? 200 : 150; }

/* ---------- E-Mails (dms-registry #143) ---------- */

bool endetMit(const std::string &s, const char *e) { const size_t n = strlen(e); return s.size() >= n && s.compare(s.size() - n, n, e) == 0; }

// Dateityp (wie das DMS ihn meldet) oder Endung sagen „E-Mail“; ob es wirklich eine ist, entscheidet danach der Inhalt.
bool istMail(const std::string &mime, const std::string &name) {
  const std::string m = zeichen::klein(mime.substr(0, mime.find(';'))), n = zeichen::klein(name);
  if (m == "message/rfc822" || m == "application/vnd.ms-outlook") return true;
  return (m == "application/octet-stream" || m.empty()) && (endetMit(n, ".eml") || endetMit(n, ".msg"));
}

pdfa::Angaben angabenAus(const Json &e, const std::string &sha, const std::string &werkzeug) {
  pdfa::Angaben ang;
  ang.werkzeug = werkzeug;
  const std::string erstellt = e["erstellt"].text();
  bool zeitOk = erstellt.size() >= 20 && erstellt.size() <= 30;
  for (char c : erstellt) if (!(isdigit((unsigned char)c) || c == '-' || c == ':' || c == 'T' || c == 'Z' || c == '.' || c == '+')) zeitOk = false;
  if (zeitOk) ang.erstellt = erstellt;
  ang.id = sha.substr(0, 32);
  return ang;
}

// Das fertige PDF/A ablegen (PUT /dokumente/{id}/archivfassung?sha256=…) und das Ergebnis melden.
int ablegen(const std::string &dok, const std::string &sha, std::vector<uint8_t> fertig, const std::string &meldung) {
  const std::string q = "{\"methode\":\"PUT\",\"pfad\":\"/dokumente/" + dok + "/archivfassung?sha256=" + sha + "\"}";
  int s = dms_api_binaer(q.data(), (int32_t)q.size(), fertig.data(), (int32_t)fertig.size());
  std::vector<uint8_t>().swap(fertig);
  if (s == 200) { log(INFO, "Dokument " + dok + ": " + meldung); ergebnis(meldung); return 0; }
  const std::string grund = grundAus(antwort());
  if (s == 403 || s == 404 || s == 409 || s == 413 || s == 415 || s == 422) {
    log(WARNUNG, "Dokument " + dok + ": Archivfassung nicht angenommen (HTTP " + std::to_string(s) + ") " + grund);
    ergebnis("Archivfassung nicht angenommen: " + grund);
    return 0;
  }
  log(FEHLER, "Archivfassung ablegen: HTTP " + std::to_string(s) + " " + grund);
  return 2;
}

// Bild aus einer Mail (JPEG, PNG, GIF) → fertig gepacktes Bild: JPEG möglichst unverändert, PNG verlustfrei, sonst JPEG.
bool mailBild(const std::string &d, pdfa::Bild &bild) {
  const std::vector<uint8_t> v(d.begin(), d.end());
  if (v.size() >= 3 && v[0] == 0xFF && v[1] == 0xD8) {
    pdfa::JpegInfo j = pdfa::jpegInfo(v.data(), v.size());
    if (j.ok && pdfa::jpegDurchreichen(j) && j.orientierung == 1) {
      bild.breite = j.breite; bild.hoehe = j.hoehe; bild.kanaele = j.kanaele; bild.jpeg = true;
      bild.daten = pdfa::jpegOhneMetadaten(v.data(), v.size());
      return !bild.daten.empty();
    }
  }
  std::string fehler;
  const bool png = v.size() >= 8 && !memcmp(v.data(), "\x89PNG", 4);
  const bool gif = v.size() >= 6 && !memcmp(v.data(), "GIF8", 4);
  return dekodiere(v, png || gif, bild, fehler);
}

// Zeitzone der Ablage (GET /region, DMS #726); ohne Antwort Europe/Berlin.
std::string zeitzone() {
  Antwort a = get("/region");
  if (a.status == 200) {
    Json j = JsonLeser::lies(reinterpret_cast<const char *>(a.body.data()), a.body.size());
    const std::string z = j["zeitzone"].text();
    bool ok = !z.empty() && z.size() < 64;
    for (char c : z) if (!(isalnum((unsigned char)c) || c == '/' || c == '_' || c == '-' || c == '+')) ok = false;
    if (ok) return z;
  }
  return "Europe/Berlin";
}

int email(const Json &e, const std::string &dok, const std::string &sha, const std::string &werkzeug, long start) {
  Antwort b = get("/dokumente/" + dok + "/inhalt");
  if (b.status == 404) { ergebnis("Das Dokument gibt es nicht mehr – nichts zu tun"); return 0; }
  if (b.status != 200) { log(FEHLER, "Datei holen: HTTP " + std::to_string(b.status) + " " + grundAus(b.body)); return 2; }
  if (b.body.size() > QUELLE_MAX) { ergebnis("Keine Archivfassung: Die E-Mail ist größer als 50 MB"); return 0; }
  std::string roh(b.body.begin(), b.body.end());
  std::vector<uint8_t>().swap(b.body);

  // Am Inhalt erkennen: Outlook (.msg) oder Internet-Nachricht (.eml).
  std::unique_ptr<cfb::Datei> c;
  mail::Nachricht n;
  if (cfb::erkannt((const uint8_t *)roh.data(), roh.size())) {
    c = std::make_unique<cfb::Datei>();
    if (!c->oeffne((const uint8_t *)roh.data(), roh.size()) || !mail::istMsg(*c)) { ergebnis("Keine Archivfassung: Outlook-Datei nicht lesbar" + (c->fehler.empty() ? std::string() : " (" + c->fehler + ")")); return 0; }
    n = mail::Msg(*c).lies(0, true);
  } else if (mail::istEml((const uint8_t *)roh.data(), roh.size(), true)) {
    n = mail::eml(roh);
  } else {
    ergebnis("Keine Archivfassung: Die Datei ist keine lesbare E-Mail (am Inhalt erkannt)");
    return 0;
  }

  std::vector<uint8_t> icc, glyphless, daten[4];
  static const char *DATEIEN[4] = {"noto-sans.ttf", "noto-sans-fett.ttf", "noto-sans-kursiv.ttf", "noto-sans-fettkursiv.ttf"};
  if (!datei("srgb.icc", icc) || !datei("glyphless.ttf", glyphless)) { log(FEHLER, "code/daten/srgb.icc oder glyphless.ttf fehlt im Paket"); return 3; }
  schrift::Schrift schriften[4];
  for (int i = 0; i < 4; i++) {
    if (!datei(DATEIEN[i], daten[i]) || !schriften[i].lies(std::move(daten[i]))) { log(FEHLER, std::string("Schrift code/daten/") + DATEIEN[i] + " fehlt oder ist nicht lesbar"); return 3; }
  }

  satz::Setzer setzer;
  for (int i = 0; i < 4; i++) setzer.schriften[i] = &schriften[i];
  setzer.seitenMax = SEITEN_MAX;
  mailsatz::Leser leser(setzer, zeitzone(), mailBild);
  {
    satz::Elemente el = leser.nachricht(n, 0, c.get());
    setzer.setze(el);
  }
  if (setzer.zuViel) { ergebnis("Keine Archivfassung: mehr als " + std::to_string(SEITEN_MAX) + " Seiten"); return 0; }
  if (jetztMs() - start > ZEIT_MS) { ergebnis("Keine Archivfassung: Die E-Mail ist zu lang für einen Durchgang"); return 0; }
  const std::string betreff = n.feld("Betreff");
  setzer.kopfUndFuss("E-Mail" + std::string(betreff.empty() ? "" : " · " + betreff));
  std::string().swap(roh);

  pdfa::Schreiber pdf;
  pdf.beginne(angabenAus(e, sha, werkzeug), icc, glyphless, 2 * 1024 * 1024);
  std::vector<int> schriftNr(4, 0);
  for (int i = 0; i < 4; i++) if (!schriften[i].benutzt.empty()) schriftNr[(size_t)i] = pdf.neuesObjekt();
  std::vector<int> bildNr;
  for (const pdfa::Bild &x : setzer.bilder) {
    bildNr.push_back(pdf.bild(x));
    if (pdf.o.size() > ARCHIV_MAX) { ergebnis("Keine Archivfassung: größer als 100 MB"); return 0; }
  }
  std::vector<pdfa::Bild>().swap(setzer.bilder);
  for (const satz::Seite &s : setzer.seiten) {
    std::vector<std::pair<int, int>> bilder;
    for (int i : s.bilder) bilder.push_back({i, bildNr[(size_t)i]});
    pdf.freieSeite(satz::Setzer::BREITE, satz::Setzer::HOEHE, satz::inhalt(s), schriftNr, bilder);
  }
  // Kennung der Teilmengen: sechs Buchstaben aus dem Prüfwert (je Schnitt verschieden).
  for (int i = 0; i < 4; i++) {
    if (!schriftNr[(size_t)i]) continue;
    std::string k;
    for (int j = 0; j < 6; j++) k += (char)('A' + (sha[(size_t)(j + 6 * i) % sha.size()] * 7 + j + 11 * i) % 26);
    satz::schreibeSchrift(pdf, schriftNr[(size_t)i], schriften[i], k);
  }
  const size_t seiten = pdf.seiten();
  std::vector<uint8_t> fertig = pdf.fertig();
  if (fertig.size() > ARCHIV_MAX) { ergebnis("Keine Archivfassung: " + pdfa::groesse(fertig.size()) + " – höchstens 100 MB"); return 0; }

  const mailsatz::Zaehler &z = leser.zaehler;
  std::string meldung = "PDF/A-2b, " + std::to_string(seiten) + (seiten == 1 ? " Seite, " : " Seiten, ") + pdfa::groesse(fertig.size()) + "; E-Mail mit Kopf und Text";
  if (z.bilder) meldung += ", " + std::to_string(z.bilder) + (z.bilder == 1 ? " Bild" : " Bilder");
  if (z.anhaenge) meldung += ", " + std::to_string(z.anhaenge) + (z.anhaenge == 1 ? " Anhang" : " Anhänge") + " als Liste";
  if (z.weitergeleitet) meldung += ", " + std::to_string(z.weitergeleitet) + (z.weitergeleitet == 1 ? " weitergeleitete E-Mail" : " weitergeleitete E-Mails");
  if (z.extern_) meldung += "; " + std::to_string(z.extern_) + (z.extern_ == 1 ? " externes Bild" : " externe Bilder") + " nicht geladen";
  if (z.verschluesselt) meldung += "; verschlüsselte Teile nicht lesbar";
  return ablegen(dok, sha, std::move(fertig), meldung);
}

/* ---------- Ein Ereignis ---------- */

int verarbeite(const Json &e) {
  if (e["art"].text() != "datei.archivfassung") return 0;  // z. B. paket.einstellungen_geaendert
  const long start = jetztMs();
  const Json &d = e["daten"];
  const std::string dok = d["dokument"].text(), sha = d["sha256"].text();
  if (!sichereId(dok) || !sichererSha(sha)) { ergebnis("Ereignis ohne gültiges Dokument"); return 0; }
  const std::string werkzeug = std::string("DMS-Paket PDF/A ") + e["paket"]["version"].text(PAKET_VERSION);

  // Wiederholung (das Ereignis kommt mindestens einmal): Gibt es schon unsere Archivfassung, nichts zu tun.
  if (!d["neu"].wahr()) {
    Antwort a = get("/dokumente/" + dok + "/archivfassung");
    if (a.status == 200) {
      const std::string kennung = "<xmp:CreatorTool>" + pdfa::xmlText(werkzeug) + "</xmp:CreatorTool>";
      if (std::search(a.body.begin(), a.body.end(), kennung.begin(), kennung.end()) != a.body.end()) { ergebnis("Archivfassung schon vorhanden"); return 0; }
    }
  }
  // E-Mails (#143): Das Paket setzt die Mail selbst zu Seiten – ohne Wortpositionen, ohne Volltext.
  if (istMail(d["mime"].text(), d["name"].text())) return email(e, dok, sha, werkzeug, start);
  if (!d["wortpositionen"].wahr()) {
    ergebnis("Wortpositionen fehlen – Texterkennung aktualisieren (Paket Texterkennung ab 2.2.0) und den Volltext neu erzeugen");
    return 0;
  }
  Antwort w = get("/dokumente/" + dok + "/wortpositionen");
  if (w.status == 404 || w.status == 403) { ergebnis("Wortpositionen nicht lesbar: " + grundAus(w.body)); return 0; }
  if (w.status != 200) { log(FEHLER, "Wortpositionen: HTTP " + std::to_string(w.status) + " " + grundAus(w.body)); return 2; }
  Wp wp = liesWortpositionen(w.body);
  std::vector<uint8_t>().swap(w.body);
  if (!wp.vollstaendig || wp.seiten.empty()) {
    ergebnis("Wortpositionen fehlen für einen Teil der Seiten – Texterkennung aktualisieren (Paket Texterkennung ab 2.2.0) und den Volltext neu erzeugen");
    return 0;
  }
  if ((int)wp.seiten.size() > SEITEN_MAX) { ergebnis(std::to_string(wp.seiten.size()) + " Seiten – höchstens " + std::to_string(SEITEN_MAX)); return 0; }

  std::vector<uint8_t> icc, schrift;
  if (!datei("srgb.icc", icc) || !datei("glyphless.ttf", schrift)) { log(FEHLER, "code/daten/srgb.icc oder glyphless.ttf fehlt im Paket"); return 3; }

  pdfa::Angaben ang;
  ang.werkzeug = werkzeug;
  const std::string erstellt = e["erstellt"].text();
  bool zeitOk = erstellt.size() >= 20 && erstellt.size() <= 30;
  for (char c : erstellt) if (!(isdigit((unsigned char)c) || c == '-' || c == ':' || c == 'T' || c == 'Z' || c == '.' || c == '+')) zeitOk = false;
  if (zeitOk) ang.erstellt = erstellt;
  ang.id = sha.substr(0, 32);

  const std::string mime = wp.mime;
  const bool lesefassung = d["quelle"].text() == "lesefassung";
  pdfa::Schreiber pdf;
  std::string wie;
  std::vector<std::string> hinweise;
  if (mime == "image/jpeg" || mime == "image/png") {
    Antwort b = get("/dokumente/" + dok + (lesefassung ? "/fassung" : "/inhalt"));
    if (b.status == 404) { ergebnis("Das Dokument gibt es nicht mehr – nichts zu tun"); return 0; }
    if (b.status != 200) { log(FEHLER, "Datei holen: HTTP " + std::to_string(b.status) + " " + grundAus(b.body)); return 2; }
    Gebaut g = bildSeite(std::move(b.body), mime, wp.seiten[0]);
    if (!g.fehler.empty()) { ergebnis("Keine Archivfassung: " + g.fehler); return 0; }
    pdf.beginne(ang, icc, schrift, g.seite.bild.daten.size() + 512 * 1024);
    pdf.seite(g.seite);
    wie = g.wie;
  } else if (mime == "application/pdf") {
    const int n = (int)wp.seiten.size();
    const int dpi = dpiFuer(n);
    pdf.beginne(ang, icc, schrift, std::min<size_t>(ARCHIV_MAX + 1024 * 1024, (size_t)n * 600 * 1024 + 1024 * 1024));
    for (int nr = 1; nr <= n; nr++) {
      if (jetztMs() - start > ZEIT_MS) {
        ergebnis("Keine Archivfassung: Das Dokument ist zu lang für einen Durchgang (" + std::to_string(nr - 1) + " von " + std::to_string(n) + " Seiten in " +
                 std::to_string(ZEIT_MS / 1000) + " Sekunden)");
        return 0;
      }
      // Große Seiten (Pläne, A0) liefert das DMS bei hoher Auflösung nicht: dann mit weniger.
      Antwort b{0, {}};
      int mit = dpi;
      for (int versuch : {dpi, 150, 72}) {
        if (versuch > dpi) continue;
        mit = versuch;
        b = get("/dokumente/" + dok + "/seiten/" + std::to_string(nr) + "/scan?dpi=" + std::to_string(versuch));
        if (b.status != 422) break;
      }
      if (b.status == 404 && nr == 1) { ergebnis("Das Dokument gibt es nicht mehr – nichts zu tun"); return 0; }
      if (b.status == 404 || b.status == 422) { ergebnis("Keine Archivfassung: Seite " + std::to_string(nr) + " nicht lesbar: " + grundAus(b.body)); return 0; }
      if (b.status != 200) { log(FEHLER, "Seite " + std::to_string(nr) + ": HTTP " + std::to_string(b.status) + " " + grundAus(b.body)); return 2; }
      int pw = 0, ph = 0;
      size_t ab = 0;
      if (!pgm(b.body, pw, ph, ab)) { log(FEHLER, "Seite " + std::to_string(nr) + ": kein Graustufenbild"); return 3; }
      pdfa::Seite s;
      const WpSeite &x = wp.seiten[(size_t)nr - 1];
      s.breite = x.breite > 0 ? x.breite : pw * 72.0 / mit;
      s.hoehe = x.hoehe > 0 ? x.hoehe : ph * 72.0 / mit;
      s.bild.breite = pw; s.bild.hoehe = ph; s.bild.kanaele = 1; s.bild.jpeg = true;
      s.bild.daten = jpeg(b.body.data() + ab, pw, ph, 1);
      std::vector<uint8_t>().swap(b.body);
      s.woerter = x.woerter;
      pdf.seite(s);
      if (mit != dpi) hinweise.push_back("Seite " + std::to_string(nr) + " mit " + std::to_string(mit) + " dpi");
      if (pdf.o.size() > ARCHIV_MAX) { ergebnis("Keine Archivfassung: größer als 100 MB (nach " + std::to_string(nr) + " von " + std::to_string(n) + " Seiten)"); return 0; }
    }
    wie = "Seiten als Bild mit " + std::to_string(dpi) + " dpi in Graustufen";
    if (d["formular"].wahr()) hinweise.push_back("Formularfelder eingefroren");
    if (d["extern"].wahr()) hinweise.push_back("externe Inhalte weggelassen");
  } else {
    ergebnis("Keine Archivfassung: Quelle vom Typ " + (mime.empty() ? std::string("unbekannt") : mime) + " liest das Paket nicht");
    return 0;
  }
  const size_t woerter = pdf.woerter;
  const size_t seiten = pdf.seiten();
  std::vector<uint8_t> fertig = pdf.fertig();
  if (fertig.size() > ARCHIV_MAX) { ergebnis("Keine Archivfassung: " + pdfa::groesse(fertig.size()) + " – höchstens 100 MB"); return 0; }

  const std::string q = "{\"methode\":\"PUT\",\"pfad\":\"/dokumente/" + dok + "/archivfassung?sha256=" + sha + "\"}";
  int s = dms_api_binaer(q.data(), (int32_t)q.size(), fertig.data(), (int32_t)fertig.size());
  std::string meldung = "PDF/A-2b, " + std::to_string(seiten) + (seiten == 1 ? " Seite, " : " Seiten, ") + pdfa::groesse(fertig.size()) + ", " +
                        std::to_string(woerter) + (woerter == 1 ? " Wort" : " Wörter") + " in der Textebene; " + wie;
  for (const std::string &h : hinweise) meldung += "; " + h;
  std::vector<uint8_t>().swap(fertig);
  if (s == 200) { log(INFO, "Dokument " + dok + ": " + meldung); ergebnis(meldung); return 0; }
  const std::string grund = grundAus(antwort());
  if (s == 403 || s == 404 || s == 409 || s == 413 || s == 415 || s == 422) {
    log(WARNUNG, "Dokument " + dok + ": Archivfassung nicht angenommen (HTTP " + std::to_string(s) + ") " + grund);
    ergebnis("Archivfassung nicht angenommen: " + grund);
    return 0;
  }
  log(FEHLER, "Archivfassung ablegen: HTTP " + std::to_string(s) + " " + grund);
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
