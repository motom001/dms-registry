// Trennblatt als Paket für das DMS (dms-registry #16): Sammelscan per Barcode in mehrere Posts teilen.
//
// Ablauf: Ereignis „Dokument hochgeladen“ in einer neuen Post → Seiten als Graustufenbild über die API holen →
// Code-128-Barcodes suchen (code/barcode.c) → an jedem Trennblatt teilen (POST /dokumente/{id}/seiten mit
// teile: je Teil eine neue Post, die Ausgangspost ist danach erledigt). Trennblätter und ihre leeren Rückseiten
// fallen weg. Ein Aufkleber „DMS-ASN:<nummer>“ auf einer Seite setzt die Archivnummer des jeweiligen Teils.
// Kein Netz, kein Dateisystem.
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "barcode.h"
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
const char *const ASN_PRAEFIX = "DMS-ASN:";
// Leere Seite: weniger dunkle Bildpunkte als das (Anteil im Inneren der Seite).
const double LEER = 0.002;

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

// Ids kommen vom DMS; trotzdem nur harmlose Zeichen in Pfade lassen.
bool sichereId(const std::string &id) {
  if (id.empty() || id.size() > 64) return false;
  for (char c : id) if (!(isalnum((unsigned char)c) || c == '-')) return false;
  return true;
}

// Auswahlwert als Text (einfach oder erster einer Liste), wie auswahlText im DMS.
std::string auswahl(const Json &j) {
  if (j.art == Json::LISTE) return j.l.empty() ? "" : j.l[0].text();
  return j.text();
}

std::string ohneRand(const std::string &s) {
  size_t a = s.find_first_not_of(" \t\r\n"), e = s.find_last_not_of(" \t\r\n");
  return a == std::string::npos ? "" : s.substr(a, e - a + 1);
}

std::string grossOhneRand(const std::string &s) {
  std::string g = ohneRand(s);
  for (char &c : g) c = (char)toupper((unsigned char)c);
  return g;
}

// Einstellung „Nur Post aus diesen Kanälen“ → Kanal der Post (Feld kanal, siehe POST_KANAL im DMS).
std::string kanalVon(const std::string &wahl) {
  if (wahl == "Eingangsordner") return "Ordner";
  if (wahl == "E-Mail-Postfach") return "E-Mail";
  return wahl; // Hochgeladen, Scan, Import, API, WebDAV
}

bool kanalErlaubt(const Json &einst, const std::string &kanal) {
  const Json &l = einst["kanaele"];
  if (l.art != Json::LISTE || l.l.empty()) return true;
  for (const Json &e : l.l) if (kanalVon(e.text()) == kanal) return true;
  return false;
}

// PGM (P5, 8 Bit) aus der Antwort des DMS: Kopf „P5 Breite Höhe 255“, ein Leerzeichen, dann die Bildpunkte.
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

struct Seite {
  int nr = 0;
  bool trenn = false;
  bool leer = false;
  std::string asn;
};

struct Teil {
  std::vector<int> seiten;
  bool inhalt = false; // hat mindestens eine Seite, die kein Trennblatt ist
  std::string asn;
};

// Die Seiten auf die Teile verteilen. Ein Trennblatt beginnt einen neuen Teil; behalten = es bleibt dessen erste Seite.
std::vector<Teil> verteile(const std::vector<Seite> &seiten, bool behalten, bool rueckseite) {
  std::vector<Teil> teile(1);
  bool rueckseitePruefen = false;
  for (const Seite &s : seiten) {
    if (s.trenn) {
      if (teile.back().inhalt) teile.emplace_back();
      if (behalten) teile.back().seiten.push_back(s.nr);
      if (!s.asn.empty() && teile.back().asn.empty()) teile.back().asn = s.asn; // Aufkleber auf dem Trennblatt: gilt für den nächsten Brief
      rueckseitePruefen = rueckseite && !behalten;
      continue;
    }
    if (rueckseitePruefen && s.leer) { rueckseitePruefen = false; continue; }
    rueckseitePruefen = false;
    teile.back().seiten.push_back(s.nr);
    teile.back().inhalt = true;
    if (!s.asn.empty() && teile.back().asn.empty()) teile.back().asn = s.asn;
  }
  // Am Ende nur noch Trennblätter (behalten): an den letzten Brief hängen; ganz ohne Seiten: weglassen.
  if (teile.size() > 1 && !teile.back().inhalt) {
    Teil rest = teile.back();
    teile.pop_back();
    teile.back().seiten.insert(teile.back().seiten.end(), rest.seiten.begin(), rest.seiten.end());
  }
  return teile;
}

std::string mehrzahl(size_t n, const char *eins, const char *viele) { return zahl((long)n) + " " + (n == 1 ? eins : viele); }

// Archivnummer setzen; 409 (Nummer schon vergeben) und andere Fehler nur ins Protokoll – das Teilen ist schon geschehen.
bool setzeAsn(const std::string &dok, const std::string &asn) {
  if (!sichereId(dok)) return false;
  Antwort a = api("PUT", "/dokumente/" + dok + "/archivnummer", "{\"archivnummer\":" + jsonText(asn) + "}");
  if (a.status == 200) { log(INFO, "Archivnummer " + asn + " an Dokument " + dok); return true; }
  log(WARNUNG, "Archivnummer " + asn + " nicht gesetzt (HTTP " + zahl(a.status) + "): " + a.body.substr(0, 200));
  return false;
}

int verarbeite(const Json &e) {
  if (e["art"].text() != "dokument.hochgeladen") return 0;
  const Json &d = e["daten"];
  const Json &einst = e["einstellungen"];
  const std::string dok = d["dokument"].text(), mappe = d["mappe"].text();
  if (!sichereId(dok) || !sichereId(mappe)) return 0;
  if (d["mime"].text() != "application/pdf") { ergebnis("kein PDF"); return 0; }

  // Nur neue, eingehende Post mit genau diesem einen Dokument (ein Sammelscan).
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
  const Json &doks = md["dokumente"];
  bool dabei = false;
  for (const Json &x : doks.l) if (x["id"].text() == dok) dabei = true;
  if (!dabei) { ergebnis("Dokument nicht mehr in der Post"); return 0; }
  if (doks.l.size() != 1) { ergebnis("Post hat " + zahl((long)doks.l.size()) + " Dokumente – geteilt wird nur ein einzelner Sammelscan"); return 0; }

  Antwort si = api("GET", "/dokumente/" + dok + "/seiten");
  if (si.status != 200) { log(FEHLER, "Seiten lesen: HTTP " + zahl(si.status) + " " + si.body.substr(0, 200)); return si.status == 422 ? 0 : 1; }
  const int anzahl = (int)lies(si)["anzahl"].zahl(0);
  const int maxSeiten = (int)std::max(1.0, std::min(200.0, einst["max_seiten"].zahl(60)));
  if (anzahl < 1) { ergebnis("keine Seiten"); return 0; }
  if (anzahl > maxSeiten) {
    log(WARNUNG, "Dokument " + dok + " hat " + zahl(anzahl) + " Seiten – mehr als eingestellt (" + zahl(maxSeiten) + "), nicht geprüft");
    ergebnis(zahl(anzahl) + " Seiten – mehr als eingestellt, nicht geprüft");
    return 0;
  }

  const std::string code = grossOhneRand(einst["barcode"].text("DMS-TRENNEN"));
  const bool behalten = einst["behalten"].wahr(false);
  const bool rueckseite = einst["rueckseite"].wahr(true);
  const bool mitAsn = einst["archivnummer"].wahr(true);
  const int dpi = (int)std::max(150.0, std::min(400.0, einst["dpi"].zahl(300)));
  const int schritt = std::max(2, dpi / 60); // etwa alle 0,4 mm eine Abtastlinie

  std::vector<Seite> seiten;
  int trennblaetter = 0;
  for (int nr = 1; nr <= anzahl; nr++) {
    Antwort bild = api("GET", "/dokumente/" + dok + "/seiten/" + zahl(nr) + "/scan?dpi=" + zahl(dpi));
    if (bild.status != 200) { log(FEHLER, "Seite " + zahl(nr) + ": HTTP " + zahl(bild.status) + " " + bild.body.substr(0, 200)); return 3; }
    int bw, bh; size_t start;
    if (!pgm(bild.body, bw, bh, start)) { log(FEHLER, "Seite " + zahl(nr) + ": kein Graustufenbild"); return 3; }
    const uint8_t *px = reinterpret_cast<const uint8_t *>(bild.body.data()) + start;
    bc_fund funde[BC_FUNDE_MAX];
    int n = bc_suche(px, bw, bh, bw, schritt, funde, BC_FUNDE_MAX);
    Seite s;
    s.nr = nr;
    std::string gesehen;
    for (int i = 0; i < n; i++) {
      std::string text = funde[i].text, gross = grossOhneRand(text);
      gesehen += (gesehen.empty() ? "" : ", ") + text;
      if (gross == code) s.trenn = true;
      else if (mitAsn && s.asn.empty() && gross.rfind(ASN_PRAEFIX, 0) == 0)
        s.asn = ohneRand(ohneRand(text).substr(strlen(ASN_PRAEFIX))); // Aufkleber: „DMS-ASN:<nummer>“
    }
    // Leere Rückseite nur direkt nach einem Trennblatt prüfen (beidseitiger Scan).
    if (!s.trenn && !seiten.empty() && seiten.back().trenn) s.leer = bc_dunkelanteil(px, bw, bh, bw) < LEER;
    if (s.trenn) trennblaetter++;
    if (n) log(DEBUG, "Seite " + zahl(nr) + ": " + gesehen);
    seiten.push_back(s);
  }

  std::vector<Teil> teile = verteile(seiten, behalten, rueckseite);
  std::vector<Teil> mitInhalt;
  for (const Teil &x : teile) if (!x.seiten.empty()) mitInhalt.push_back(x);
  size_t asnGesetzt = 0;

  if (trennblaetter == 0 || mitInhalt.size() < 2) {
    // Nichts zu teilen; eine Archivnummer gilt dann für das ganze Dokument.
    std::string asn;
    for (const Teil &x : teile) if (asn.empty()) asn = x.asn;
    if (!asn.empty() && setzeAsn(dok, asn)) asnGesetzt++;
    std::string meldung = trennblaetter ? "Trennblatt gefunden, aber nur ein Brief – nicht geteilt" : "kein Trennblatt";
    if (asnGesetzt) meldung += ", Archivnummer " + asn;
    ergebnis(meldung);
    return 0;
  }

  // Teilen: seiten = alle verbleibenden Seiten in Reihenfolge, teile = Positionen, an denen ein neuer Teil beginnt.
  std::string sl, tl;
  size_t pos = 0;
  for (size_t i = 0; i < mitInhalt.size(); i++) {
    if (i) tl += (tl.empty() ? "" : ",") + zahl((long)pos);
    for (int nr : mitInhalt[i].seiten) { sl += (sl.empty() ? "" : ",") + std::string("{\"nr\":") + zahl(nr) + "}"; pos++; }
  }
  Antwort r = api("POST", "/dokumente/" + dok + "/seiten", "{\"seiten\":[" + sl + "],\"teile\":[" + tl + "]}");
  if (r.status != 201) { log(FEHLER, "Teilen: HTTP " + zahl(r.status) + " " + r.body.substr(0, 300)); return 4; }
  Json erg = lies(r);
  const Json &neueDoks = erg["dokumente"];
  for (size_t i = 0; i < mitInhalt.size() && i < neueDoks.l.size(); i++)
    if (!mitInhalt[i].asn.empty() && setzeAsn(neueDoks.l[i]["id"].text(), mitInhalt[i].asn)) asnGesetzt++;

  size_t posten = erg["posten"].l.size();
  std::string meldung = "in " + mehrzahl(posten ? posten : mitInhalt.size(), "Post", "Posts") + " geteilt (" + mehrzahl((size_t)trennblaetter, "Trennblatt", "Trennblätter") + ")";
  if (asnGesetzt) meldung += ", " + mehrzahl(asnGesetzt, "Archivnummer", "Archivnummern");
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
