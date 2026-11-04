// Texterkennung als Paket für das DMS (dms-registry #23, #47): Tesseract als WebAssembly.
//
// Ablauf (ab DMS 0.133.0): Ereignis „Volltext fertig“ vom Kern → entscheiden (ohne Text immer; mit Text nur bei
// „Vorhandenen Volltext verwerfen und neu erkennen“ oder ausdrücklich `neu`) → Seiten als Graustufenbild über die
// API holen → Lage und Schrift erkennen (osd), Seite aufrichten → Tesseract, bei „Automatisch“ mit Spracherkennung
// je Seite, zweitem Durchgang und Mischseiten (zwei Sprachen in einem Durchgang) → Volltext mit den Sprachen je Seite
// per API zurückschreiben (ab DMS 0.139.0, motom001/dms#579), dazu die Lage jedes Worts (`woerter`, ab DMS 0.149.0 für
// die Archivfassung, motom001/dms#631 – ältere DMS übergehen das Feld). Lange Dokumente abschnittsweise: nach etwa
// einer Minute antwortet das Modul mit {"weiter": …} und der Läufer ruft es gleich wieder auf.
// Kein Netz, kein Dateisystem; die Sprachdaten liegen im Paket (code/daten/*.traineddata) bzw. in Zusatzpaketen
// texterkennung_<sprache> und kommen über dms.datei.
#include <leptonica/allheaders.h>
#include <tesseract/baseapi.h>
#include <tesseract/osdetect.h>
#include <tesseract/resultiterator.h>
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
#include "woerter.h"

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
// Mischseite (#579): Der Durchgang mit beiden Sprachen zugleich gilt nur, wenn er um mindestens so viele Prozentpunkte
// sicherer ist als der beste mit einer Sprache – dann nennt das Paket für die Seite beide Sprachen.
constexpr int MISCH_DEUTLICH = 2;
// Wortpositionen (#631) wandern mit dem Text durch die Fortsetzung (höchstens 4 MB je „weiter“). Werden sie mehr als
// das hier, schickt das Paket für die übrigen Seiten keine mehr (null) – das DMS nennt dann „Wortpositionen fehlen“.
constexpr size_t WOERTER_MAX_BYTES = 2500u * 1024u;

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

// Für Tesseract: Sprachdaten nach Dateinamen (…/fra.traineddata) – so lädt es mehrere Sprachen in einen Durchgang.
bool leser(const char *pfad, std::vector<char> *ziel) {
  std::string name(pfad ? pfad : "");
  const size_t s = name.find_last_of('/');
  if (s != std::string::npos) name = name.substr(s + 1);
  const size_t p = name.find('.');
  const std::string k = p == std::string::npos ? name : name.substr(0, p);
  if (k.empty() || k.size() > 8) return false;
  return datei(k + ".traineddata", *ziel) || datei("texterkennung_" + k + "/" + k + ".traineddata", *ziel);
}

std::vector<std::string> teile(const std::string &s);

// Sprache laden (Kennung wie deu, fra); null, wenn die Sprachdaten fehlen – dann steht sie in `fehlen`. Mit „+“
// (z. B. deu+fra, Mischseite #579) ein Durchgang mit beiden Sprachen zugleich; die Daten liest Tesseract über leser.
tesseract::TessBaseAPI *sprache(const std::string &k) {
  auto i = geladen.find(k);
  if (i != geladen.end()) return i->second ? i->second->api.get() : nullptr;
  if (k.find('+') != std::string::npos) {
    for (const std::string &t : teile(k)) if (!sprache(t)) { geladen[k] = nullptr; return nullptr; }
    auto s = std::make_unique<Sprache>();
    s->api = std::make_unique<tesseract::TessBaseAPI>();
    if (s->api->Init(nullptr, 0, k.c_str(), tesseract::OEM_LSTM_ONLY, nullptr, 0, nullptr, nullptr, false, leser)) {
      log(WARNUNG, "Tesseract startet nicht mit " + k + " – Mischseiten mit einer Sprache");
      geladen[k] = nullptr;
      return nullptr;
    }
    s->api->SetPageSegMode(tesseract::PSM_AUTO);
    tesseract::TessBaseAPI *a = s->api.get();
    geladen[k] = std::move(s);
    return a;
  }
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

// Eine Lesung: Text, Sicherheit und die Wörter mit ihrem Kasten im gelesenen Bild (Bildpunkte).
struct Wort { std::string text; woerter::Kasten k; };
struct Lesung { std::string text; int sicherheit = -1; std::vector<Wort> woerter; };

Lesung lies(tesseract::TessBaseAPI *a, Pix *bild, int dpi) {
  a->SetImage(bild);
  a->SetSourceResolution(dpi);
  std::unique_ptr<char[]> t(a->GetUTF8Text());
  Lesung r{t ? t.get() : "", a->MeanTextConf(), {}};
  // Wortpositionen (#631): je Wort Text und Kasten, wie Tesseract sie beim Lesen gefunden hat.
  std::unique_ptr<tesseract::ResultIterator> it(a->GetIterator());
  if (it) {
    do {
      if (it->Empty(tesseract::RIL_WORD)) continue;
      std::unique_ptr<char[]> w(it->GetUTF8Text(tesseract::RIL_WORD));
      Wort x;
      if (!w || !it->BoundingBox(tesseract::RIL_WORD, &x.k.links, &x.k.oben, &x.k.rechts, &x.k.unten)) continue;
      x.text = w.get();
      r.woerter.push_back(std::move(x));
    } while (it->Next(tesseract::RIL_WORD));
  }
  a->Clear();
  return r;
}

/* ---------- Ein Dokument ---------- */

// Stand eines Dokuments, auch über mehrere Aufrufe hinweg (in „weiter“).
struct Stand {
  int seite = 1;            // nächste Seite
  std::string text;         // bisher erkannt, Seiten durch Seitenvorschub (\f) getrennt
  std::string seiten;       // Sprachen je Seite (#579), durch „|“ getrennt: „deu|fra|deu+fra|“ (leer: nicht erkannt)
  std::string sprachen;     // Lesesprache(n): bei „Automatisch“ die der letzten Seite (Anfang für die nächste),
                            // sonst fest – „deu“, „eng“ oder „deu+eng“ (je Seite die sicherere Lesung)
  int gedreht = 0;
  int zweite = 0;           // Seiten mit zweitem Durchgang in einer anderen Sprache
  int misch = 0;            // Mischseiten (zwei Sprachen in einem Durchgang)
  int anzahl = 0;           // erkannte Seiten
  std::string woerter;      // Wortpositionen je erkannter Seite als JSON, durch Komma getrennt: „[[…],…],[…]“ (#631)
  bool ohneWoerter = false; // zu viele für die Fortsetzung: ab hier keine mehr (null)
};

std::vector<std::string> teileAn(const std::string &s, char z, bool leere = false) {
  std::vector<std::string> r;
  size_t a = 0;
  while (a <= s.size()) {
    size_t b = s.find(z, a);
    if (b == std::string::npos) b = s.size();
    if (b > a || leere) r.push_back(s.substr(a, b - a));
    a = b + 1;
  }
  return r;
}
std::vector<std::string> teile(const std::string &s) { return teileAn(s, '+'); }
std::string verbinde(const std::vector<std::string> &l, const std::string &z) {
  std::string r;
  for (size_t i = 0; i < l.size(); i++) { if (i) r += z; r += l[i]; } // auch leere Seiten bekommen ihren Trenner
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

// Lage und Schrift einer Seite; dreht sie bei Bedarf (gedreht = true, vierteln: viertel Umdrehungen im Uhrzeigersinn).
PixPtr richteAuf(PixPtr bild, int dpi, bool &gedreht, std::string &schrift, int &vierteln) {
  gedreht = false;
  vierteln = 0;
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
  vierteln = drehen / 90;
  return PixPtr(neu);
}

// Eine Seite bei „Automatisch“ (#579: Sprache je Seite). Erster Durchgang in der Sprache der Seite davor (am Anfang
// Deutsch; bei anderer Schrift wie Kyrillisch gleich in der passenden). Dann die Sprache(n) aus dem Text: Ist es eine
// andere, ein zweiter Durchgang in ihr – die sicherere Lesung gilt (dms-registry#47: immer, wenn ihre Sprachdaten da
// sind). Stehen zwei Sprachen auf der Seite, ein Durchgang mit beiden zugleich; ist er deutlich sicherer, gilt er und
// die Seite bekommt beide Sprachen. Ergebnis: die Lesung und die Sprachen der Seite („deu“, „deu+fra“ oder leer).
struct Seite { Lesung l; std::string sprachen; };
Seite liesAutomatisch(Pix *bild, int dpi, Stand &s, const std::string &schrift) {
  std::string erst = s.sprachen.empty() ? "deu" : teile(s.sprachen)[0];
  if (!sprache(erst)) erst = "deu";
  const std::string passend = spracheFuerSchrift(schrift, erst, [](const std::string &k) { return sprache(k) != nullptr; });
  if (!passend.empty()) erst = passend;
  Lesung l = liesMit(erst, bild, dpi);
  std::string gelesen = erst;
  std::vector<std::string> erkannt = sprachenEinerSeite(l.text);
  if (!erkannt.empty() && erkannt[0] != gelesen && sprache(erkannt[0])) {
    Lesung zwei = liesMit(erkannt[0], bild, dpi);
    s.zweite++;
    log(DEBUG, "zweiter Durchgang mit " + erkannt[0] + ": Sicherheit " + std::to_string(zwei.sicherheit) + " statt " + std::to_string(l.sicherheit) + " %");
    if (zwei.sicherheit > l.sicherheit) {
      l = zwei;
      gelesen = erkannt[0];
      // In der richtigen Sprache gelesen (mit Akzenten) erkennt der Text sich sicherer.
      std::vector<std::string> neu = sprachenEinerSeite(l.text);
      if (!neu.empty()) erkannt = neu;
    }
  }
  std::string seite = erkannt.empty() ? "" : erkannt[0];
  if (erkannt.size() == 2 && sprache(erkannt[0]) && sprache(erkannt[1])) {
    const std::string beide = erkannt[0] + "+" + erkannt[1];
    tesseract::TessBaseAPI *a = sprache(beide);
    if (a) {
      Lesung m = lies(a, bild, dpi);
      log(DEBUG, "Mischseite " + beide + ": Sicherheit " + std::to_string(m.sicherheit) + " statt " + std::to_string(l.sicherheit) + " %");
      if (m.sicherheit >= l.sicherheit + MISCH_DEUTLICH) { l = m; seite = beide; s.misch++; }
    }
  } else if (erkannt.size() == 2) {
    sprache(erkannt[1]); // fehlende Sprachdaten melden
  }
  s.sprachen = gelesen;
  return {l, seite};
}

// Sprachen je Seite als JSON für das DMS: [["deu"],["fra"],null] – null: das DMS erkennt die Sprache selbst.
std::string seitenJson(const std::vector<std::string> &seiten) {
  std::string r = "[";
  for (size_t i = 0; i < seiten.size(); i++) {
    if (i) r += ",";
    if (seiten[i].empty()) { r += "null"; continue; }
    std::vector<std::string> k = teile(seiten[i]);
    r += "[";
    for (size_t j = 0; j < k.size(); j++) r += (j ? "," : "") + jsonText(k[j]);
    r += "]";
  }
  return r + "]";
}

// Kurz für die Meldung: „deu, enthält auch fra“ (nach Seiten gezählt, Mischseiten für beide).
std::string sprachenMeldung(const std::vector<std::string> &seiten) {
  std::map<std::string, int> n;
  for (const std::string &x : seiten) for (const std::string &k : teile(x)) n[k]++;
  std::vector<std::pair<std::string, int>> l(n.begin(), n.end());
  std::sort(l.begin(), l.end(), [](const auto &a, const auto &b) { return a.second > b.second; });
  if (l.empty()) return "";
  std::string r = l[0].first;
  for (size_t i = 1; i < l.size(); i++) r += (i == 1 ? ", enthält auch " : ", ") + l[i].first;
  return r;
}

// Die Wortpositionen aus dem Stand (je Seite „[…]“ oder „null“, durch Komma getrennt) wieder je Seite.
std::vector<std::string> seitenWoerter(const std::string &s) {
  std::vector<std::string> r;
  int tiefe = 0;
  bool text = false, flucht = false;
  size_t a = 0;
  for (size_t i = 0; i < s.size(); i++) {
    char c = s[i];
    if (text) { if (flucht) flucht = false; else if (c == '\\') flucht = true; else if (c == '"') text = false; continue; }
    if (c == '"') text = true;
    else if (c == '[') tiefe++;
    else if (c == ']') tiefe--;
    else if (c == ',' && tiefe == 0) { r.push_back(s.substr(a, i - a)); a = i + 1; }
  }
  if (!s.empty()) r.push_back(s.substr(a));
  return r;
}

// Id aus einem Eintrag: seit 2.3.0 (dms-registry #105, DMS #658) eine Id als Text, vorher ein Listeneintrag { typ }.
std::string eintragId(const Json &e) { return e.art == Json::TEXT ? e.text() : e["typ"].text(); }

bool typErlaubt(const Json &einstellungen, const std::string &mappe) {
  const Json &nur = einstellungen["typen"];
  const Json &ohne = einstellungen["ohne_typen"];
  const bool mitNur = nur.art == Json::LISTE && !nur.l.empty();
  const bool mitOhne = ohne.art == Json::LISTE && !ohne.l.empty();
  if (!mitNur && !mitOhne) return true;
  if (!sichereId(mappe)) return false;
  Antwort a = api("GET", "/mappen/" + mappe);
  if (a.status != 200) { log(WARNUNG, "Mappe nicht lesbar (HTTP " + std::to_string(a.status) + ")"); return false; }
  std::string typ = JsonLeser::lies(a.body.data(), a.body.size())["typId"].text();
  // Ausgeschlossene gelten immer; ist „Nur diese“ leer, sind alle übrigen erlaubt.
  if (mitOhne) for (const Json &e : ohne.l) if (eintragId(e) == typ) return false;
  if (!mitNur) return true;
  for (const Json &e : nur.l) if (eintragId(e) == typ) return true;
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
    if (!typErlaubt(einst, d["mappe"].text())) { ergebnis("Mappentyp nicht gewählt oder ausgeschlossen"); return 0; }
  }

  // Sprache wie in manifest.yaml: Automatisch, Deutsch, Englisch oder beide (je Seite die sicherere Lesung).
  const std::string wahl = einst["sprache"].text("Automatisch");
  const bool automatisch = wahl == "Automatisch";
  Stand s;
  // Fortsetzung eines Abschnitts. Ein Stand aus Version 2.0 oder 2.1 (ohne Sprachen bzw. Wortpositionen je Seite) fängt
  // neu an.
  if (fortsetzung && weiter["seiten"].art == Json::TEXT && weiter["woerter"].art == Json::TEXT) {
    s.seite = std::max(1, (int)weiter["seite"].zahl(1));
    s.text = weiter["text"].text();
    s.seiten = weiter["seiten"].text();
    s.sprachen = weiter["sprachen"].text();
    s.gedreht = (int)weiter["gedreht"].zahl(0);
    s.zweite = (int)weiter["zweite"].zahl(0);
    s.misch = (int)weiter["misch"].zahl(0);
    s.anzahl = (int)weiter["anzahl"].zahl(0);
    s.woerter = weiter["woerter"].text();
    s.ohneWoerter = weiter["ohneWoerter"].wahr();
    for (const Json &k : weiter["fehlen"].l) fehlen.insert(k.text());
  }
  if (!automatisch) s.sprachen = wahl == "Englisch" ? "eng" : wahl == "Deutsch und Englisch" ? "deu+eng" : "deu";
  for (const std::string &k : teile(automatisch ? "deu" : s.sprachen)) if (!sprache(k)) { log(FEHLER, "Sprachdaten fehlen im Paket: " + k); return 2; }
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
    int vierteln = 0;
    PixPtr aufrecht = drehen ? richteAuf(PixPtr(pixClone(bild.get())), dpi, gedreht, schrift, vierteln) : PixPtr(pixClone(bild.get()));
    Seite seite;
    if (automatisch) {
      seite = liesAutomatisch(aufrecht.get(), dpi, s, schrift);
      if (gedreht && seite.l.sicherheit < 60) {
        // Unsicher nach dem Drehen? Dann auch ungedreht (in der Sprache der Seite) – die bessere Lesung gilt.
        Lesung u = liesMit(seite.sprachen.empty() ? s.sprachen : seite.sprachen, bild.get(), dpi);
        if (u.sicherheit > seite.l.sicherheit) { seite.l = u; gedreht = false; }
      }
    } else {
      seite.l = liesMit(s.sprachen, aufrecht.get(), dpi);
      if (gedreht && seite.l.sicherheit < 60) {
        Lesung u = liesMit(s.sprachen, bild.get(), dpi);
        if (u.sicherheit > seite.l.sicherheit) { seite.l = u; gedreht = false; }
      }
      // Feste Sprache: Die Seite bekommt die Sprache ihres Texts (für die Wortstämme der Suche), ohne zweiten Durchgang.
      std::vector<std::string> erkannt = sprachenEinerSeite(seite.l.text);
      seite.sprachen = erkannt.empty() ? "" : erkannt[0];
    }
    if (gedreht) s.gedreht++;
    // Seiten durch Seitenvorschub getrennt; im Text selbst darf keiner stehen.
    std::string t = seite.l.text;
    t.erase(std::remove(t.begin(), t.end(), '\f'), t.end());
    if (s.anzahl > 0) { s.text += '\f'; s.seiten += '|'; }
    s.text += t;
    s.seiten += seite.sprachen;
    // Wortpositionen (#631) relativ zur Seite, wie das DMS sie liefert: aus dem gedrehten Bild zurückgerechnet.
    if (s.anzahl > 0) s.woerter += ',';
    if (s.ohneWoerter) s.woerter += "null";
    else {
      const int W = pixGetWidth(bild.get()), H = pixGetHeight(bild.get());
      std::string liste = "[";
      for (const Wort &w : seite.l.woerter) {
        const std::string j = gedreht ? woerter::json(w.text, woerter::zurueck(vierteln, W, H, w.k), W, H) : woerter::json(w.text, w.k, W, H);
        if (j.empty()) continue;
        if (liste.size() > 1) liste += ',';
        liste += j;
      }
      liste += ']';
      if (s.woerter.size() + liste.size() > WOERTER_MAX_BYTES) {
        s.ohneWoerter = true;
        s.woerter += "null";
        log(WARNUNG, "Wortpositionen: ab Seite " + std::to_string(nr) + " zu viele für die Fortsetzung – für die übrigen Seiten keine");
      } else s.woerter += liste;
    }
    s.anzahl++;
    log(DEBUG, "Seite " + std::to_string(nr) + ": " + std::to_string(t.size()) + " Zeichen, Sicherheit " + std::to_string(seite.l.sicherheit) + " % (" + (seite.sprachen.empty() ? "Sprache unbekannt" : seite.sprachen) + (gedreht ? ", gedreht" : "") + ")");
  }
  if (liste && pos > letzte) ende = true;
  const int seiten = pos - 1;
  if (!ende && pos <= letzte) {
    std::string f = "[";
    for (const std::string &k : fehlen) f += (f.size() > 1 ? "," : "") + jsonText(k);
    f += "]";
    std::string fort = "Seite " + std::to_string(seiten) + (gesamt ? " von " + std::to_string(gesamt) : "");
    ergebnis("{\"weiter\":{\"seite\":" + std::to_string(pos) + ",\"text\":" + jsonText(s.text) + ",\"seiten\":" + jsonText(s.seiten) +
             ",\"sprachen\":" + jsonText(s.sprachen) + ",\"gedreht\":" + std::to_string(s.gedreht) + ",\"zweite\":" + std::to_string(s.zweite) +
             ",\"misch\":" + std::to_string(s.misch) + ",\"anzahl\":" + std::to_string(s.anzahl) + ",\"woerter\":" + jsonText(s.woerter) +
             ",\"ohneWoerter\":" + (s.ohneWoerter ? "true" : "false") + ",\"fehlen\":" + f + ",\"fortschritt\":" + jsonText(fort) + "}}");
    return 0;
  }
  if (seiten == 0 || s.anzahl == 0) { ergebnis("keine Seiten"); return 0; }

  // Text und Sprachen je Seite (#579). Gemischtes PDF: Die Seiten mit Text liefert das DMS (ab 0.139.0 mit Text je
  // Seite); die erkannten kommen an ihre Stelle. Ohne Seiten vom DMS: Text aus dem PDF vorn, erkannte dahinter.
  std::vector<std::string> texte = teileAn(s.text, '\f', true);
  std::vector<std::string> sprachenJe = teileAn(s.seiten, '|', true);
  sprachenJe.resize(texte.size());
  std::vector<std::string> woerterJe = seitenWoerter(s.woerter);
  woerterJe.resize(texte.size(), "null");
  int alleSeiten = seiten;
  std::string body;
  if (liste) {
    Antwort v = api("GET", "/dokumente/" + dok + "/volltext");
    if (v.status != 200) { log(FEHLER, "Volltext lesen: HTTP " + std::to_string(v.status)); return 4; }
    const Json j = JsonLeser::lies(v.body.data(), v.body.size());
    alleSeiten = std::max(seiten, (int)d["seiten"].zahl(seiten));
    const Json &vom = j["seiten"];
    if (vom.art == Json::LISTE && (int)vom.l.size() >= alleSeiten) {
      std::vector<std::string> t2((size_t)alleSeiten), s2((size_t)alleSeiten), w2((size_t)alleSeiten, "null");
      for (int i = 0; i < alleSeiten; i++) {
        t2[(size_t)i] = vom.l[(size_t)i]["text"].text();
        std::vector<std::string> k;
        for (const Json &x : vom.l[(size_t)i]["sprachen"].l) if (x.art == Json::TEXT) k.push_back(x.text());
        s2[(size_t)i] = verbinde(k, "+");
      }
      for (size_t i = 0; i < nurSeiten.size() && i < texte.size(); i++) {
        if (nurSeiten[i] < 1 || nurSeiten[i] > alleSeiten) continue;
        t2[(size_t)nurSeiten[i] - 1] = texte[i];
        s2[(size_t)nurSeiten[i] - 1] = sprachenJe[i];
        w2[(size_t)nurSeiten[i] - 1] = woerterJe[i];  // Seiten mit Textebene: null – deren Wörter liest das DMS selbst
      }
      for (std::string &x : t2) x.erase(std::remove(x.begin(), x.end(), '\f'), x.end());
      texte = t2;
      sprachenJe = s2;
      woerterJe = w2;
    } else {
      std::string alt = j["text"].text();
      alt.erase(std::remove(alt.begin(), alt.end(), '\f'), alt.end());
      texte.insert(texte.begin(), alt);
      sprachenJe.insert(sprachenJe.begin(), "");
      woerterJe.insert(woerterJe.begin(), "null");
    }
  }
  body = "{\"text\":" + jsonText(verbinde(texte, "\f")) + ",\"seiten\":" + std::to_string(alleSeiten) + ",\"seitensprachen\":" + seitenJson(sprachenJe);
  // Wortpositionen (#631) für die Archivfassung: je Seite eine Liste oder null. Ältere DMS übergehen das Feld; nimmt
  // ein DMS sie nicht (zu groß für 0.139–0.144 mit 2 MB je Anfrage, oder abgelehnt), geht der Text ohne sie.
  const std::string mitWoertern = body + ",\"woerter\":[" + verbinde(woerterJe, ",") + "]}";
  body += "}";
  Antwort r = api("PUT", "/dokumente/" + dok + "/volltext", mitWoertern);
  bool ohneWp = false;
  if (r.status == 413 || r.status == 422) {
    log(WARNUNG, "Volltext mit Wortpositionen nicht angenommen (HTTP " + std::to_string(r.status) + " " + r.body.substr(0, 200) + ") – ohne Wortpositionen");
    r = api("PUT", "/dokumente/" + dok + "/volltext", body);
    ohneWp = true;
  }
  if (r.status != 200) { log(FEHLER, "Volltext schreiben: HTTP " + std::to_string(r.status) + " " + r.body.substr(0, 200)); return 4; }
  const size_t zeichen = s.text.size() - (size_t)(s.anzahl - 1); // ohne die Seitenvorschübe
  std::string meldung = seitenText(s.anzahl) + (liste ? " ohne Text erkannt" : "") + ", " + std::to_string(zeichen) + " Zeichen";
  const std::string spr = sprachenMeldung(sprachenJe);
  if (!spr.empty()) meldung += ", " + spr;
  if (s.misch) meldung += ", " + std::to_string(s.misch) + (s.misch == 1 ? " Mischseite" : " Mischseiten");
  if (s.gedreht) meldung += ", " + seitenText(s.gedreht) + " gedreht";
  if (s.zweite) meldung += ", " + std::to_string(s.zweite) + "× zweiter Durchgang";
  if (!liste && seiten == maxSeiten && !ende) meldung += " (Grenze erreicht)";
  if (ohneWp || s.ohneWoerter) meldung += ohneWp ? ", ohne Wortpositionen" : ", Wortpositionen nur für einen Teil der Seiten";
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
