// Leerseiten als Paket für Ablago (dms #997): leere Seiten in neuer Post erkennen und markieren.
//
// Ablauf: Ereignis „Dokument hochgeladen“ in einer neuen Post aus einem gewählten Kanal → Seiten als Graustufenbild
// über die API holen → je Seite prüfen (gemeinsam/leerseite/leerseite.h) → erkannte Seiten mit
// PUT /dokumente/{id}/leerseiten markieren (Schnittstelle dms:leerseiten). Das Paket markiert nur: Es löscht nichts und
// ändert weder Datei noch Post – weggelassen werden die Seiten erst, wenn eine Person die Post in eine Mappe übernimmt.
// Kein Netz, kein Dateisystem.
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "json.h"
#include "leerseite.h"

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
// Seiten holt das Paket mit 100 dpi: genug für Bleistift und Lochung, schnell auch bei langen Scans.
const int DPI = 100;
// Vorgabe „Nur Post aus diesen Kanälen“, wenn die Einstellung fehlt (dms #997).
const char *const KANAELE_VORGABE[] = { "Scan", "Eingangsordner", "Hochgeladen" };

void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }
std::string zahl(long n) { return std::to_string(n); }

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

Json lies(const Antwort &a) { return JsonLeser::lies(a.body.data(), a.body.size()); }

// Ids kommen von Ablago; trotzdem nur harmlose Zeichen in Pfade lassen.
bool sichereId(const std::string &id) {
  if (id.empty() || id.size() > 64) return false;
  for (char c : id) if (!(isalnum((unsigned char)c) || c == '-')) return false;
  return true;
}

// Auswahlwert als Text (einfach oder erster einer Liste), wie auswahlText in Ablago.
std::string auswahl(const Json &j) {
  if (j.art == Json::LISTE) return j.l.empty() ? "" : j.l[0].text();
  return j.text();
}

// Einstellung „Nur Post aus diesen Kanälen“ → Kanal der Post (Feld kanal, siehe POST_KANAL in Ablago).
std::string kanalVon(const std::string &wahl) {
  if (wahl == "Eingangsordner") return "Ordner";
  if (wahl == "E-Mail-Postfach") return "E-Mail";
  return wahl; // Hochgeladen, Scan, Import, API, WebDAV
}

// Fehlt die Einstellung, gelten Scan, Eingangsordner und Hochgeladen; eine leere Liste heißt: alle Kanäle.
bool kanalErlaubt(const Json &einst, const std::string &kanal) {
  const Json &l = einst["kanaele"];
  if (l.art != Json::LISTE) {
    for (const char *k : KANAELE_VORGABE) if (kanalVon(k) == kanal) return true;
    return false;
  }
  if (l.l.empty()) return true;
  for (const Json &e : l.l) if (kanalVon(e.text()) == kanal) return true;
  return false;
}

// PGM (P5, 8 Bit) aus der Antwort von Ablago: Kopf „P5 Breite Höhe 255“, ein Leerzeichen, dann die Bildpunkte.
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

std::string liste(const std::vector<int> &l) {
  std::string s;
  for (int n : l) s += (s.empty() ? "" : ",") + zahl(n);
  return s;
}

std::string seitenText(const std::vector<int> &l) {
  std::string s;
  for (int n : l) s += (s.empty() ? "" : ", ") + zahl(n);
  return s;
}

int verarbeite(const Json &e) {
  if (e["art"].text() != "dokument.hochgeladen") return 0;
  const Json &d = e["daten"];
  const Json &einst = e["einstellungen"];
  const std::string dok = d["dokument"].text(), mappe = d["mappe"].text(), mime = d["mime"].text();
  if (!sichereId(dok) || !sichereId(mappe)) return 0;
  const bool istPdf = mime == "application/pdf";
  if (!istPdf && mime != "image/jpeg" && mime != "image/png") { ergebnis("kein PDF und kein Bild"); return 0; }

  // Nur neue, eingehende Post aus einem gewählten Kanal.
  Antwort m = api("GET", "/mappen/" + mappe);
  if (m.status == 404) { ergebnis("Mappe nicht lesbar"); return 0; }
  if (m.status != 200) { log(FEHLER, "Mappe lesen: HTTP " + zahl(m.status)); return 1; }
  Json md = lies(m);
  const Json &mp = md["mappe"];
  Antwort t = api("GET", "/typen");
  if (t.status != 200) { log(FEHLER, "Mappentypen lesen: HTTP " + zahl(t.status)); return 1; }
  bool istPost = false;
  for (const Json &typ : lies(t).l) if (typ["id"].text() == mp["typId"].text() && typ["system"].text() == "post") istPost = true;
  if (!istPost) { ergebnis("keine Post"); return 0; }
  const Json &w = mp["werte"];
  if (auswahl(w["stand"]) != "Neu") { ergebnis("Post ist nicht mehr neu"); return 0; }
  if (auswahl(w["richtung"]) == "Ausgehend") { ergebnis("ausgehende Post"); return 0; }
  const std::string kanal = auswahl(w["kanal"]);
  if (!kanalErlaubt(einst, kanal)) { ergebnis("Kanal „" + kanal + "“ nicht gewählt"); return 0; }
  std::string sha;
  for (const Json &x : md["dokumente"].l) if (x["id"].text() == dok) sha = x["sha256"].text();
  if (sha.empty()) { ergebnis("Dokument nicht mehr in der Post"); return 0; }

  int anzahl = 1;
  if (istPdf) {
    Antwort si = api("GET", "/dokumente/" + dok + "/seiten");
    if (si.status != 200) { log(FEHLER, "Seiten lesen: HTTP " + zahl(si.status) + " " + si.body.substr(0, 200)); return si.status == 422 ? 0 : 1; }
    anzahl = (int)lies(si)["anzahl"].zahl(0);
  }
  const int maxSeiten = (int)std::max(1.0, std::min(400.0, einst["max_seiten"].zahl(100)));
  if (anzahl < 1) { ergebnis("keine Seiten"); return 0; }
  if (anzahl > maxSeiten) {
    log(WARNUNG, "Dokument " + dok + " hat " + zahl(anzahl) + " Seiten – mehr als eingestellt (" + zahl(maxSeiten) + "), nicht geprüft");
    ergebnis(zahl(anzahl) + " Seiten – mehr als eingestellt, nicht geprüft");
    return 0;
  }

  const std::string stufeText = auswahl(einst["empfindlichkeit"]);
  const ls_stufe stufe = ls_stufe_von(stufeText.empty() ? "vorsichtig" : stufeText.c_str());
  std::vector<int> leer;
  for (int nr = 1; nr <= anzahl; nr++) {
    Antwort bild = api("GET", "/dokumente/" + dok + "/seiten/" + zahl(nr) + "/scan?dpi=" + zahl(DPI));
    if (bild.status != 200) { log(FEHLER, "Seite " + zahl(nr) + ": HTTP " + zahl(bild.status) + " " + bild.body.substr(0, 200)); return 3; }
    int bw, bh; size_t start;
    if (!pgm(bild.body, bw, bh, start)) { log(FEHLER, "Seite " + zahl(nr) + ": kein Graustufenbild"); return 3; }
    const uint8_t *px = reinterpret_cast<const uint8_t *>(bild.body.data()) + start;
    ls_befund b;
    // Bilder (JPEG, PNG) kommen in Originalgröße – die Auflösung schätzt die Erkennung dann selbst.
    const int r = ls_pruefe(px, bw, bh, bw, istPdf ? DPI : 0, stufe, &b);
    if (r < 0) { log(FEHLER, "Seite " + zahl(nr) + ": nicht genug Speicher"); return 3; }
    char zeile[160];
    snprintf(zeile, sizeof zeile, "Seite %d: %s (Tinte %.1f mm², größter Fleck %.1f mm, %d Flecken, %d Löcher, %d Rand, %d Staub, Papier %d)",
             nr, r ? "leer" : "Inhalt", b.tinte_mm2, b.groesste_mm, b.flecken, b.loecher, b.rand, b.staub, b.papier);
    log(DEBUG, zeile);
    if (r == 1) leer.push_back(nr);
  }

  // Nur markieren, wenn es etwas zu markieren gibt – sonst bleibt die Post, wie sie ist.
  if (leer.empty()) { ergebnis("keine leere Seite (" + zahl(anzahl) + (anzahl == 1 ? " Seite)" : " Seiten)")); return 0; }
  Antwort r = api("PUT", "/dokumente/" + dok + "/leerseiten", "{\"sha256\":" + jsonText(sha) + ",\"seiten\":[" + liste(leer) + "]}");
  if (r.status == 409) { ergebnis("Datei hat sich inzwischen geändert – nicht markiert"); return 0; }
  if (r.status != 200) { log(FEHLER, "Markieren: HTTP " + zahl(r.status) + " " + r.body.substr(0, 300)); return 4; }
  const std::string meldung = zahl((long)leer.size()) + " von " + zahl(anzahl) + " Seiten leer (" + seitenText(leer) + ")";
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
  return verarbeite(JsonLeser::lies(json, (size_t)n));
}

}
