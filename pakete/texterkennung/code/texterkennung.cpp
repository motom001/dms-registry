// Texterkennung als Paket für das DMS (dms-registry #23, #47): Tesseract als WebAssembly.
//
// Ablauf (ab DMS 0.133.0): Ereignis „Volltext fertig“ vom Kern → entscheiden (ohne Text immer; mit Text nur bei
// „Vorhandenen Volltext verwerfen und neu erkennen“ oder ausdrücklich `neu`) → Seiten als Graustufenbild über die
// API holen → Lage und Schrift erkennen (osd), Seite aufrichten → Tesseract, bei „Automatisch“ mit Spracherkennung
// und zweitem Durchgang → Volltext per API zurückschreiben. Lange Dokumente abschnittsweise: nach etwa einer Minute
// antwortet das Modul mit {"weiter": …} und der Läufer ruft es gleich wieder auf.
// Kein Netz, kein Dateisystem; die Sprachdaten liegen im Paket (code/daten/*.traineddata) bzw. in Zusatzpaketen
// texterkennung_<sprache> und kommen über dms.datei.
#include <leptonica/allheaders.h>
#include <tesseract/baseapi.h>
#include <tesseract/osdetect.h>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

#include "json.h"
#include "sprache.h"

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
extern "C" {
DMS(api) int32_t dms_api(const char *json, int32_t len);
DMS(datei) int32_t dms_datei(const char *name, int32_t len);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(char *ziel, int32_t max);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);
}

namespace {

enum Stufe { DEBUG = 0, INFO = 1, WARNUNG = 2, FEHLER = 3 };

// Ein Aufruf arbeitet höchstens so lange und gibt dann mit „weiter“ ab (Zeitgrenze des Läufers: 120 s).
constexpr long ABSCHNITT_MS = 60000;
// Ab dieser Sicherheit von osd wird eine Seite gedreht (bei wenig Text meldet osd Werte um 2–5).
constexpr float DREHUNG_SICHER = 2.0f;

void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }

std::string antwort() {
  std::string a((size_t)dms_antwort_laenge(), '\0');
  if (!a.empty()) dms_antwort_lesen(a.data(), (int32_t)a.size());
  return a;
}

struct Antwort { int status; std::string body; };

Antwort api(const std::string &methode, const std::string &pfad, const std::string &body = "") {
  std::string q = "{\"methode\":" + jsonText(methode) + ",\"pfad\":" + jsonText(pfad) + (body.empty() ? "" : ",\"body\":" + body) + "}";
  int s = dms_api(q.data(), (int32_t)q.size());
  return {s, antwort()};
}

// Ids kommen vom DMS; trotzdem nur harmlose Zeichen in Pfade lassen.
bool sichereId(const std::string &id) {
  if (id.empty() || id.size() > 64) return false;
  for (char c : id) if (!(isalnum((unsigned char)c) || c == '-')) return false;
  return true;
}

long jetztMs() {
  using namespace std::chrono;
  return (long)duration_cast<milliseconds>(steady_clock::now().time_since_epoch()).count();
}

/* ---------- Sprachdaten ---------- */

// Eine geladene Sprache (je Aufruf einmal). Deutsch und Englisch liegen im Paket, weitere in Zusatzpaketen.
struct Sprache {
  std::vector<char> daten;
  std::unique_ptr<tesseract::TessBaseAPI> api;
};
std::map<std::string, std::unique_ptr<Sprache>> geladen;
std::set<std::string> fehlen;

// Datei aus dem Paket oder einem Zusatzpaket (<paket>/<datei>); leer, wenn es sie nicht gibt.
bool datei(const std::string &name, std::vector<char> &ziel) {
  int32_t n = dms_datei(name.data(), (int32_t)name.size());
  if (n <= 0) return false;
  ziel.resize((size_t)n);
  dms_antwort_lesen(ziel.data(), n);
  return true;
}

// Sprache laden (Kennung wie deu, fra); null, wenn die Sprachdaten fehlen – dann steht sie in `fehlen`.
tesseract::TessBaseAPI *sprache(const std::string &k) {
  auto i = geladen.find(k);
  if (i != geladen.end()) return i->second ? i->second->api.get() : nullptr;
  auto s = std::make_unique<Sprache>();
  bool da = datei(k + ".traineddata", s->daten) || datei("texterkennung_" + k + "/" + k + ".traineddata", s->daten);
  if (!da) { fehlen.insert(k); geladen[k] = nullptr; return nullptr; }
  s->api = std::make_unique<tesseract::TessBaseAPI>();
  if (s->api->Init(s->daten.data(), (int)s->daten.size(), k.c_str(), tesseract::OEM_LSTM_ONLY, nullptr, 0, nullptr, nullptr, false, nullptr)) {
    log(FEHLER, "Tesseract startet nicht mit " + k + ".traineddata");
    geladen[k] = nullptr;
    return nullptr;
  }
  s->api->SetPageSegMode(tesseract::PSM_AUTO);
  tesseract::TessBaseAPI *a = s->api.get();
  geladen[k] = std::move(s);
  return a;
}

// Lage und Schrift (osd.traineddata, alte Tesseract-Erkennung).
std::unique_ptr<tesseract::TessBaseAPI> osdApi;
std::vector<char> osdDaten;
bool osdVersucht = false;
tesseract::TessBaseAPI *osd() {
  if (osdVersucht) return osdApi.get();
  osdVersucht = true;
  if (!datei("osd.traineddata", osdDaten)) { log(WARNUNG, "osd.traineddata fehlt – Seiten werden nicht gedreht"); return nullptr; }
  osdApi = std::make_unique<tesseract::TessBaseAPI>();
  if (osdApi->Init(osdDaten.data(), (int)osdDaten.size(), "osd", tesseract::OEM_TESSERACT_ONLY, nullptr, 0, nullptr, nullptr, false, nullptr)) {
    log(WARNUNG, "Lageerkennung (osd) startet nicht – Seiten werden nicht gedreht");
    osdApi.reset();
    return nullptr;
  }
  osdApi->SetPageSegMode(tesseract::PSM_OSD_ONLY);
  return osdApi.get();
}

/* ---------- Bilder ---------- */

struct PixWeg { void operator()(Pix *p) const { pixDestroy(&p); } };
using PixPtr = std::unique_ptr<Pix, PixWeg>;

// PGM (P5, 8 Bit) aus der Antwort des DMS als Leptonica-Bild.
PixPtr pgm(const std::string &b) {
  int w = 0, h = 0, mx = 0, n = 0;
  if (sscanf(b.c_str(), "P5 %d %d %d%n", &w, &h, &mx, &n) != 3 || mx != 255 || w <= 0 || h <= 0) return nullptr;
  size_t start = (size_t)n + 1;
  if (b.size() < start + (size_t)w * (size_t)h) return nullptr;
  Pix *p = pixCreate(w, h, 8);
  if (!p) return nullptr;
  l_uint32 *daten = pixGetData(p);
  int wpl = pixGetWpl(p);
  const unsigned char *q = reinterpret_cast<const unsigned char *>(b.data()) + start;
  for (int y = 0; y < h; y++) {
    l_uint32 *zeile = daten + (size_t)y * wpl;
    for (int x = 0; x < w; x++) SET_DATA_BYTE(zeile, x, q[(size_t)y * w + x]);
  }
  return PixPtr(p);
}

struct Lesung { std::string text; int sicherheit = -1; };

Lesung lies(tesseract::TessBaseAPI *a, Pix *bild, int dpi) {
  a->SetImage(bild);
  a->SetSourceResolution(dpi);
  std::unique_ptr<char[]> t(a->GetUTF8Text());
  Lesung r{t ? t.get() : "", a->MeanTextConf()};
  a->Clear();
  return r;
}

/* ---------- Ein Dokument ---------- */

// Stand eines Dokuments, auch über mehrere Aufrufe hinweg (in „weiter“).
struct Stand {
  int seite = 1;            // nächste Seite
  std::string text;         // bisher erkannt
  std::string sprachen;     // z. B. „deu“ oder „deu+eng“ (bei „Deutsch und Englisch“: je Seite die sicherere)
  bool entschieden = false; // Sprache bei „Automatisch“ festgelegt
  int versuche = 0;         // Seiten, die zur Sprachwahl gelesen wurden
  int gedreht = 0;
  std::string zweiter;      // Hinweis auf einen zweiten Durchgang
};

std::vector<std::string> teile(const std::string &s) {
  std::vector<std::string> r;
  size_t a = 0;
  while (a <= s.size()) {
    size_t b = s.find('+', a);
    if (b == std::string::npos) b = s.size();
    if (b > a) r.push_back(s.substr(a, b - a));
    a = b + 1;
  }
  return r;
}

// Eine Seite mit den Sprachen des Stands lesen: je Sprache ein Durchgang, die sicherere Lesung gilt.
Lesung liesMit(const std::string &sprachen, Pix *bild, int dpi) {
  Lesung beste;
  for (const std::string &k : teile(sprachen)) {
    tesseract::TessBaseAPI *a = sprache(k);
    if (!a) continue;
    Lesung l = lies(a, bild, dpi);
    if (l.sicherheit > beste.sicherheit) beste = l;
  }
  return beste;
}

// Lage und Schrift einer Seite; dreht sie bei Bedarf (gedreht = true).
PixPtr richteAuf(PixPtr bild, int dpi, bool &gedreht, std::string &schrift) {
  gedreht = false;
  tesseract::TessBaseAPI *o = osd();
  if (!o) return bild;
  o->SetImage(bild.get());
  o->SetSourceResolution(dpi);
  int grad = 0; float sicher = 0, schriftSicher = 0; const char *name = nullptr;
  bool ok = o->DetectOrientationScript(&grad, &sicher, &name, &schriftSicher);
  o->Clear();
  if (!ok) return bild;
  if (name && schriftSicher >= 1) schrift = name;
  // grad: Lage der Seite; aufrichten im Uhrzeigersinn um (360 − grad).
  int drehen = (360 - grad) % 360;
  if (drehen == 0 || sicher < DREHUNG_SICHER) return bild;
  Pix *neu = pixRotateOrth(bild.get(), drehen / 90);
  if (!neu) return bild;
  gedreht = true;
  return PixPtr(neu);
}

bool typErlaubt(const Json &einstellungen, const std::string &mappe) {
  const Json &liste = einstellungen["typen"];
  if (liste.art != Json::LISTE || liste.l.empty()) return true;
  if (!sichereId(mappe)) return false;
  Antwort a = api("GET", "/mappen/" + mappe);
  if (a.status != 200) { log(WARNUNG, "Mappe nicht lesbar (HTTP " + std::to_string(a.status) + ")"); return false; }
  std::string typ = JsonLeser::lies(a.body.data(), a.body.size())["typId"].text();
  for (const Json &e : liste.l) if (e["typ"].text() == typ) return true;
  return false;
}

std::string seitenText(int n) { return std::to_string(n) + (n == 1 ? " Seite" : " Seiten"); }

std::string fehlendText() {
  if (fehlen.empty()) return "";
  std::string s;
  for (const std::string &k : fehlen) s += (s.empty() ? "" : ", ") + k + " (Zusatzpaket texterkennung_" + k + ")";
  return s;
}

int verarbeite(const Json &e) {
  const std::string art = e["art"].text();
  if (art != "volltext.fertig") return 0; // z. B. paket.einstellungen_geaendert: nichts zu tun
  const Json &d = e["daten"];
  const Json &einst = e["einstellungen"];
  const std::string dok = d["dokument"].text();
  if (!sichereId(dok)) return 0;
  // Nur, was der Kern gelesen hat – nicht den Text anderer Pakete oder der API (und nie den eigenen).
  if (d["quelle"].text() != "kern") { ergebnis("Volltext kam nicht vom DMS selbst – nichts zu tun"); return 0; }
  const std::string mime = d["mime"].text();
  if (mime != "application/pdf" && mime != "image/jpeg" && mime != "image/png") { ergebnis("kein PDF, JPEG oder PNG"); return 0; }

  const Json &weiter = d["weiter"];
  const bool fortsetzung = weiter.art == Json::OBJEKT;
  // Text aus dem PDF bleibt – außer „verwerfen“ ist an oder jemand will ausdrücklich neu erzeugen. Bei gemischten
  // PDFs (Textseiten und gescannte Seiten) erkennt das Paket dann nur die Seiten ohne Text und hängt sie an.
  const bool behalten = d["text"].wahr() && !einst["verwerfen"].wahr(false) && !d["neu"].wahr();
  std::vector<int> nurSeiten;
  if (behalten) for (const Json &x : d["seitenOhneText"].l) if (x.art == Json::ZAHL && x.zahl() >= 1) nurSeiten.push_back((int)x.zahl());
  if (!fortsetzung) {
    if (behalten && nurSeiten.empty()) { ergebnis("Text aus dem PDF bleibt"); return 0; }
    if (!typErlaubt(einst, d["mappe"].text())) { ergebnis("Mappentyp nicht gewählt"); return 0; }
  }

  // Sprache wie in manifest.yaml: Automatisch, Deutsch, Englisch oder beide (je Seite die sicherere Lesung).
  const std::string wahl = einst["sprache"].text("Automatisch");
  const bool automatisch = wahl == "Automatisch";
  Stand s;
  if (fortsetzung) {
    s.seite = std::max(1, (int)weiter["seite"].zahl(1));
    s.text = weiter["text"].text();
    s.sprachen = weiter["sprachen"].text();
    s.entschieden = weiter["entschieden"].wahr();
    s.versuche = (int)weiter["versuche"].zahl(0);
    s.gedreht = (int)weiter["gedreht"].zahl(0);
    s.zweiter = weiter["zweiter"].text();
    for (const Json &k : weiter["fehlen"].l) fehlen.insert(k.text());
  }
  if (s.sprachen.empty()) s.sprachen = wahl == "Englisch" ? "eng" : wahl == "Deutsch und Englisch" ? "deu+eng" : "deu";
  if (!automatisch) s.entschieden = true;
  for (const std::string &k : teile(s.sprachen)) if (!sprache(k)) { log(FEHLER, "Sprachdaten fehlen im Paket: " + k); return 2; }
  const bool drehen = einst["drehen"].wahr(true);

  const int dpi = std::clamp((int)einst["dpi"].zahl(300), 150, 400);
  const int maxSeiten = std::clamp((int)einst["max_seiten"].zahl(100), 1, 1000);
  // Welche Seiten: alle (bis zur ersten, die es nicht gibt) oder bei gemischten PDFs nur die ohne Text.
  // s.seite zählt die Stelle in dieser Folge (ab 1), nicht die Seitennummer.
  const bool liste = !nurSeiten.empty();
  const int letzte = liste ? (int)nurSeiten.size() : maxSeiten;
  const int gesamt = liste ? letzte : d["seiten"].art == Json::ZAHL ? std::min((int)d["seiten"].zahl(), maxSeiten) : 0;
  const long start = jetztMs();
  bool ende = false;
  int pos = s.seite;
  for (; pos <= letzte; pos++) {
    // Abschnittsweise: Zeit für diesen Aufruf um – Stand mitgeben, der Läufer ruft gleich wieder auf.
    if (pos > s.seite && jetztMs() - start > ABSCHNITT_MS) break;
    const int nr = liste ? nurSeiten[(size_t)pos - 1] : pos;
    Antwort b = api("GET", "/dokumente/" + dok + "/seiten/" + std::to_string(nr) + "/scan?dpi=" + std::to_string(dpi));
    if (b.status == 404) { ende = true; break; } // keine weitere Seite
    if (b.status != 200) { log(FEHLER, "Seite " + std::to_string(nr) + ": HTTP " + std::to_string(b.status) + " " + b.body.substr(0, 200)); return 3; }
    PixPtr bild = pgm(b.body);
    if (!bild) { log(FEHLER, "Seite " + std::to_string(nr) + ": kein Graustufenbild"); return 3; }
    pixSetResolution(bild.get(), dpi, dpi); // sonst rät Tesseract (osd: „Invalid resolution 0 dpi“)
    b.body.clear();
    std::string schrift;
    bool gedreht = false;
    PixPtr aufrecht = drehen ? richteAuf(PixPtr(pixClone(bild.get())), dpi, gedreht, schrift) : PixPtr(pixClone(bild.get()));
    // Andere Schrift (z. B. Kyrillisch): passende Sprache gleich mitnehmen, wenn sie da ist.
    if (automatisch && !s.entschieden && s.versuche == 0) {
      std::string passend = spracheFuerSchrift(schrift, s.sprachen, [](const std::string &k) { return sprache(k) != nullptr; });
      if (!passend.empty()) s.sprachen = passend + "+" + s.sprachen;
    }
    Lesung l = liesMit(s.sprachen, aufrecht.get(), dpi);
    if (gedreht) {
      // Unsicher nach dem Drehen? Dann auch ungedreht – die bessere Lesung gilt.
      Lesung u = l.sicherheit < 60 ? liesMit(s.sprachen, bild.get(), dpi) : Lesung{};
      if (u.sicherheit > l.sicherheit) l = u; else s.gedreht++;
    }
    // Sprache bei „Automatisch“ (wie im DMS #395): nach der ersten Seite mit Text, höchstens drei Versuche. Anders als
    // früher im DMS auch dann ein zweiter Durchgang, wenn Tesseract sich sicher war: Der erste Durchgang liest nur
    // Deutsch, und Tesseract hält eine französische Seite auf Deutsch gelesen oft für sicher (Akzente fehlen dann).
    // Es gilt die sicherere Lesung; das kostet nur bei Dokumenten in anderen Sprachen einen Durchgang mehr.
    if (!s.entschieden) {
      s.versuche++;
      ErkannteSprache erkannt = erkenneSprache(s.text + "\n" + l.text);
      s.entschieden = !erkannt.sprache.empty() || s.versuche >= 3;
      const std::vector<std::string> bisher = teile(s.sprachen);
      if (!erkannt.sprache.empty() && erkannt.konfidenz >= 0.5 && std::find(bisher.begin(), bisher.end(), erkannt.sprache) == bisher.end()) {
        if (sprache(erkannt.sprache)) {
          Lesung zwei = liesMit(erkannt.sprache, aufrecht.get(), dpi);
          s.zweiter = "zweiter Durchgang mit " + erkannt.sprache + ": Sicherheit " + std::to_string(zwei.sicherheit) + " statt " + std::to_string(l.sicherheit) + " %";
          if (zwei.sicherheit > l.sicherheit) { s.sprachen = erkannt.sprache; l = zwei; } else s.zweiter += ", erster blieb";
        }
        s.entschieden = true;
      }
    }
    if (!s.text.empty()) s.text += "\n\n";
    s.text += l.text;
    log(DEBUG, "Seite " + std::to_string(nr) + ": " + std::to_string(l.text.size()) + " Zeichen, Sicherheit " + std::to_string(l.sicherheit) + " % (" + s.sprachen + (gedreht ? ", gedreht" : "") + ")");
  }
  if (liste && pos > letzte) ende = true;
  const int seiten = pos - 1;
  if (!ende && pos <= letzte) {
    std::string f = "[";
    for (const std::string &k : fehlen) f += (f.size() > 1 ? "," : "") + jsonText(k);
    f += "]";
    std::string fort = "Seite " + std::to_string(seiten) + (gesamt ? " von " + std::to_string(gesamt) : "");
    ergebnis("{\"weiter\":{\"seite\":" + std::to_string(pos) + ",\"text\":" + jsonText(s.text) + ",\"sprachen\":" + jsonText(s.sprachen) +
             ",\"entschieden\":" + (s.entschieden ? "true" : "false") + ",\"versuche\":" + std::to_string(s.versuche) + ",\"gedreht\":" + std::to_string(s.gedreht) +
             ",\"zweiter\":" + jsonText(s.zweiter) + ",\"fehlen\":" + f + ",\"fortschritt\":" + jsonText(fort) + "}}");
    return 0;
  }
  if (seiten == 0) { ergebnis("keine Seiten"); return 0; }

  // Gemischt: Text aus dem PDF vorn, die erkannten Seiten dahinter (für die Suche zählt die Reihenfolge nicht).
  std::string volltext = s.text;
  int alleSeiten = seiten;
  if (liste) {
    Antwort v = api("GET", "/dokumente/" + dok + "/volltext");
    if (v.status != 200) { log(FEHLER, "Volltext lesen: HTTP " + std::to_string(v.status)); return 4; }
    const Json j = JsonLeser::lies(v.body.data(), v.body.size());
    volltext = j["text"].text() + "\n\n" + s.text;
    alleSeiten = std::max(seiten, (int)d["seiten"].zahl(seiten));
  }
  Antwort r = api("PUT", "/dokumente/" + dok + "/volltext", "{\"text\":" + jsonText(volltext) + ",\"seiten\":" + std::to_string(alleSeiten) + "}");
  if (r.status != 200) { log(FEHLER, "Volltext schreiben: HTTP " + std::to_string(r.status) + " " + r.body.substr(0, 200)); return 4; }
  std::string meldung = seitenText(seiten) + (liste ? " ohne Text erkannt" : "") + ", " + std::to_string(s.text.size()) + " Zeichen, " + s.sprachen;
  if (s.gedreht) meldung += ", " + seitenText(s.gedreht) + " gedreht";
  if (!s.zweiter.empty()) meldung += ", " + s.zweiter;
  if (!liste && seiten == maxSeiten && !ende) meldung += " (Grenze erreicht)";
  if (!fehlen.empty()) { meldung += " – Sprachdaten fehlen: " + fehlendText(); log(WARNUNG, "Sprachdaten fehlen: " + fehlendText()); }
  log(INFO, "Dokument " + dok + ": " + meldung);
  ergebnis(meldung);
  return 0;
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
  setMsgSeverity(L_SEVERITY_NONE); // Leptonica-Meldungen (fehlende Bildformate) nicht ins Protokoll
  return verarbeite(JsonLeser::lies(json, (size_t)n));
}

}
