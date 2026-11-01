// Texterkennung als Paket für das DMS (dms-registry #23): Tesseract als WebAssembly.
//
// Ablauf: Ereignis „Dokument hochgeladen“ bzw. „Texterkennung fertig“ → Seiten als Graustufenbild über die API
// holen → Tesseract → Volltext per API zurückschreiben. Kein Netz, kein Dateisystem; die Sprachdaten liegen
// im Paket (code/daten/*.traineddata) und kommen über dms.datei.
#include <leptonica/allheaders.h>
#include <tesseract/baseapi.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

#include "json.h"

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

// Sprachdaten einmal je Aufruf laden.
struct Sprache {
  std::string name;
  std::vector<char> daten;
  std::unique_ptr<tesseract::TessBaseAPI> api;
};

bool lade(Sprache &s) {
  std::string datei = s.name + ".traineddata";
  int32_t n = dms_datei(datei.data(), (int32_t)datei.size());
  if (n <= 0) { log(FEHLER, "Sprachdaten fehlen im Paket: " + datei); return false; }
  s.daten.resize((size_t)n);
  dms_antwort_lesen(s.daten.data(), n);
  s.api = std::make_unique<tesseract::TessBaseAPI>();
  if (s.api->Init(s.daten.data(), n, s.name.c_str(), tesseract::OEM_LSTM_ONLY, nullptr, 0, nullptr, nullptr, false, nullptr)) {
    log(FEHLER, "Tesseract startet nicht mit " + datei);
    return false;
  }
  s.api->SetPageSegMode(tesseract::PSM_AUTO);
  return true;
}

// PGM (P5, 8 Bit) aus der Antwort des DMS lesen.
bool pgm(const std::string &b, int &w, int &h, size_t &start) {
  int mx = 0, n = 0;
  if (sscanf(b.c_str(), "P5 %d %d %d%n", &w, &h, &mx, &n) != 3 || mx != 255 || w <= 0 || h <= 0) return false;
  start = (size_t)n + 1;
  return b.size() >= start + (size_t)w * (size_t)h;
}

std::string erkenne(Sprache &s, const std::string &bild, int w, int h, size_t start, int dpi, int &sicherheit) {
  s.api->SetImage(reinterpret_cast<const unsigned char *>(bild.data()) + start, w, h, 1, w);
  s.api->SetSourceResolution(dpi);
  std::unique_ptr<char[]> t(s.api->GetUTF8Text());
  sicherheit = s.api->MeanTextConf();
  std::string r = t ? t.get() : "";
  s.api->Clear();
  return r;
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

// Hat das Dokument schon Text (aus dem PDF oder von der eingebauten Texterkennung)?
bool hatText(const std::string &dok) {
  Antwort a = api("GET", "/dokumente/" + dok + "/volltext");
  if (a.status != 200) return false;
  std::string t = JsonLeser::lies(a.body.data(), a.body.size())["text"].text();
  size_t zeichen = 0;
  for (unsigned char c : t) if (!isspace(c)) zeichen++;
  return zeichen >= 20;
}

int verarbeite(const Json &e) {
  const std::string art = e["art"].text();
  const Json &d = e["daten"];
  const Json &einst = e["einstellungen"];
  const std::string dok = d["dokument"].text();
  if (!sichereId(dok)) return 0;

  const bool nurOhneText = einst["nur_ohne_text"].wahr(true);
  if (art == "dokument.hochgeladen") {
    // Läuft die Texterkennung des DMS noch, warten wir auf ihr Ergebnis (Ereignis texterkennung.fertig).
    if (d["volltextGeplant"].wahr() && nurOhneText) { ergebnis("wartet auf die Texterkennung des DMS"); return 0; }
    const std::string mime = d["mime"].text();
    if (mime != "application/pdf" && mime.rfind("image/", 0) != 0) { ergebnis("kein PDF und kein Bild"); return 0; }
  } else if (art != "texterkennung.fertig") {
    return 0;
  }
  if (!typErlaubt(einst, d["mappe"].text())) { ergebnis("Mappentyp nicht gewählt"); return 0; }
  if (nurOhneText && hatText(dok)) { ergebnis("hat schon Text"); return 0; }

  // Sprache wie in manifest.yaml (code.einstellungen): Deutsch, Englisch oder beide (je Seite die sicherere Erkennung).
  const std::string wahl = einst["sprache"].text("Deutsch");
  std::vector<Sprache> sprachen;
  if (wahl == "Deutsch und Englisch") { sprachen.push_back({"deu", {}, nullptr}); sprachen.push_back({"eng", {}, nullptr}); }
  else sprachen.push_back({wahl == "Englisch" ? "eng" : "deu", {}, nullptr});
  for (Sprache &s : sprachen) if (!lade(s)) return 2;

  const int dpi = std::clamp((int)einst["dpi"].zahl(300), 150, 400);
  const int maxSeiten = std::clamp((int)einst["max_seiten"].zahl(30), 1, 200);
  std::string text;
  int seiten = 0;
  for (int nr = 1; nr <= maxSeiten; nr++) {
    Antwort bild = api("GET", "/dokumente/" + dok + "/seiten/" + std::to_string(nr) + "/scan?dpi=" + std::to_string(dpi));
    if (bild.status == 404) break; // keine weitere Seite
    if (bild.status != 200) { log(FEHLER, "Seite " + std::to_string(nr) + ": HTTP " + std::to_string(bild.status) + " " + bild.body.substr(0, 200)); return 3; }
    int w, h; size_t start;
    if (!pgm(bild.body, w, h, start)) { log(FEHLER, "Seite " + std::to_string(nr) + ": kein Graustufenbild"); return 3; }
    std::string beste; int besteSicherheit = -1;
    for (Sprache &s : sprachen) {
      int sicherheit = 0;
      std::string t = erkenne(s, bild.body, w, h, start, dpi, sicherheit);
      if (sicherheit > besteSicherheit) { beste = t; besteSicherheit = sicherheit; }
    }
    if (nr > 1) text += "\f";
    text += beste;
    seiten = nr;
    log(DEBUG, "Seite " + std::to_string(nr) + ": " + std::to_string(beste.size()) + " Zeichen, Sicherheit " + std::to_string(besteSicherheit) + " %");
  }
  if (seiten == 0) { ergebnis("keine Seiten"); return 0; }

  Antwort r = api("PUT", "/dokumente/" + dok + "/volltext", "{\"text\":" + jsonText(text) + "}");
  if (r.status != 200) { log(FEHLER, "Volltext schreiben: HTTP " + std::to_string(r.status) + " " + r.body.substr(0, 200)); return 4; }
  std::string meldung = std::to_string(seiten) + (seiten == 1 ? " Seite" : " Seiten") + ", " + std::to_string(text.size()) + " Zeichen";
  if (seiten == maxSeiten) meldung += " (Grenze erreicht)";
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
