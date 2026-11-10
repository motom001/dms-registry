// Paket Compliance (dms-registry #166): hält jeden Tag fest, wie Ablago eingerichtet ist (Konfiguration je Bereich und
// Monat), und legt am Monatsanfang die Nachweise des Vormonats an.
//
// Ereignisse: zeitplan.ausgefuehrt (Automatisierung „Konfiguration und Nachweise festhalten“, DMS #1082) und
// paket.einstellungen_geaendert (Erstlauf, sobald der Admin Bereiche anhakt; geänderte Auswahl „was zählt“).
//
// Kern-Schnittstellen aus DMS #1053 (Entwurf – so angenommen, bis Entwicklung sie festlegt):
//   GET  /einrichtung/{bereich}            → { bereich, ablago, daten: {…} }; 403, wenn der Bereich nicht freigegeben ist
//   POST /einrichtung/{bereich}/vergleich  { vorher, nachher } → { aenderungen: [{ kennung, vorher, nachher, satz }] }
//   GET  /nachweise?monat=JJJJ-MM          → { monat, stichtag, bereiche: […], zahlen: [{ bereich, name, wert }], benutzer: […], … }
// Gespeichert wird über die API v1 wie bei jedem Paket: POST /mappen, POST /mappen/{id}/dokumente, POST /dokumente/{id}/ersetzen,
// PUT /mappen/{id}. Im Speicher des Pakets steht je Bereich nur, welche Mappe und welches Dokument der letzte Stand ist.
#include <cstdint>
#include <cstdlib>
#include <string>
#include <vector>

#include "bereiche.h"
#include "json.h"
#include "sha256.h"
#include "stand.h"

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
extern "C" {
DMS(api) int32_t dms_api(const char *json, int32_t len);
DMS(api_binaer) int32_t dms_api_binaer(const char *json, int32_t len, const uint8_t *body, int32_t blen);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(char *ziel, int32_t max);
DMS(speicher_lesen) int32_t dms_speicher_lesen(const char *schluessel, int32_t len);
DMS(speicher_schreiben) int32_t dms_speicher_schreiben(const char *schluessel, int32_t len, const char *wert, int32_t wlen);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);
}

namespace {

using namespace compliance;

enum Stufe { DEBUG = 0, INFO = 1, WARNUNG = 2, FEHLER = 3 };
const char *SPEICHER = "stand";

char *eingang = nullptr;

void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }

struct Antwort {
  int status;
  std::string roh;
  Json json;
};

std::string letzte_antwort() {
  std::string a((size_t)dms_antwort_laenge(), '\0');
  if (!a.empty()) dms_antwort_lesen(a.data(), (int32_t)a.size());
  return a;
}

Antwort api(const std::string &methode, const std::string &pfad, const std::string &body = "") {
  std::string q = "{\"methode\":" + jsonText(methode) + ",\"pfad\":" + jsonText(pfad) + (body.empty() ? "" : ",\"body\":" + body) + "}";
  int s = dms_api(q.data(), (int32_t)q.size());
  std::string a = letzte_antwort();
  return {s, a, JsonLeser::lies(a.data(), a.size())};
}

Antwort hochladen(const std::string &pfad, const std::string &inhalt) {
  std::string q = "{\"methode\":\"POST\",\"pfad\":" + jsonText(pfad) + ",\"typ\":\"application/json\"}";
  int s = dms_api_binaer(q.data(), (int32_t)q.size(), reinterpret_cast<const uint8_t *>(inhalt.data()), (int32_t)inhalt.size());
  std::string a = letzte_antwort();
  return {s, a, JsonLeser::lies(a.data(), a.size())};
}

Json txt(const std::string &s) {
  Json j;
  if (s.empty()) return j;
  j.art = Json::TEXT;
  j.t = s;
  return j;
}
Json zahl(double z) {
  Json j;
  j.art = Json::ZAHL;
  j.z = z;
  return j;
}
Json objekt() {
  Json j;
  j.art = Json::OBJEKT;
  return j;
}

// ---- Speicher des Pakets: { b: { <bereich>: { m, d, z, p, n, q } }, a: <auswahl>, nl: <letzter Nachweis-Monat> } ----

Json lies_stand() {
  if (dms_speicher_lesen(SPEICHER, (int32_t)strlen(SPEICHER)) < 0) return objekt();
  std::string t = letzte_antwort();
  Json j = JsonLeser::lies(t.data(), t.size());
  return j.art == Json::OBJEKT ? j : objekt();
}

void schreib_stand(const Json &s) {
  std::string t = jsonSchreib(s);
  if (dms_speicher_schreiben(SPEICHER, (int32_t)strlen(SPEICHER), t.data(), (int32_t)t.size()) < 0) log(FEHLER, "Speicher des Pakets voll – Stand nicht gemerkt");
}

// ---- Typen ----------------------------------------------------------------------------------------------------------

std::string typ_id(const std::string &schluessel) {
  static Json typen;
  if (typen.art == Json::NUL) {
    Antwort a = api("GET", "/typen");
    typen = a.json.art == Json::LISTE ? a.json : a.json["typen"];
  }
  for (const Json &x : typen.l)
    if (x["schluessel"].text() == schluessel) return x["id"].text();
  return "";
}

std::string neue_id(const Json &j) {
  std::string id = j["id"].text();
  return id.empty() ? j["dokument"]["id"].text() : id;
}

// ---- Konfiguration --------------------------------------------------------------------------------------------------

struct Lauf {
  std::string heute;  // JJJJ-MM-TT
  std::string monat;  // JJJJ-MM
  int neu = 0, versionen = 0, gleich = 0, gesperrt = 0, fehler = 0;
};

// Neue Monatsmappe mit dem ersten Dokument. Liefert { m, d } im Eintrag oder false.
bool lege_an(const Bereich &b, const std::string &roh, const std::string &ablago, const std::string &aenderung, const std::string &vorgaenger, Lauf &l, Json &eintrag) {
  std::string typ = typ_id("compliance_konfiguration");
  if (typ.empty()) { log(FEHLER, "Mappentyp Konfiguration nicht gefunden"); return false; }
  std::string pw = sha256(roh);
  Json w = objekt();
  w.o["bereich"] = txt(b.name);
  w.o["zeitraum"] = txt(l.monat);
  w.o["status"] = txt("aktuell");
  w.o["aenderung"] = txt(aenderung);
  w.o["stand_vom"] = txt(l.heute);
  w.o["versionen"] = zahl(1);
  w.o["ablago_version"] = txt(ablago);
  w.o["pruefwert"] = txt(pw);
  if (!vorgaenger.empty()) w.o["vorgaenger"] = txt(vorgaenger);
  Antwort m = api("POST", "/mappen", "{\"typId\":" + jsonText(typ) + ",\"werte\":" + jsonSchreib(w) + "}");
  std::string mid = neue_id(m.json);
  if ((m.status != 200 && m.status != 201) || mid.empty()) {
    log(FEHLER, std::string("Konfiguration ") + b.name + " " + l.monat + " anlegen: HTTP " + std::to_string(m.status) + " " + m.json["fehler"].text());
    return false;
  }
  Antwort d = hochladen("/mappen/" + mid + "/dokumente?register=dateien&name=konfiguration-" + b.schluessel + "-" + l.monat + ".json&typ=application%2Fjson", roh);
  std::string did = neue_id(d.json);
  if ((d.status != 200 && d.status != 201) || did.empty()) {
    log(FEHLER, std::string("Konfiguration ") + b.name + ": Datei hochladen HTTP " + std::to_string(d.status));
    return false;
  }
  if (!vorgaenger.empty()) {
    Json alt = objekt();
    alt.o["status"] = txt("abgelöst");
    alt.o["abgeloest_am"] = txt(l.heute);
    alt.o["nachfolger"] = txt(mid);
    Antwort a = api("PUT", "/mappen/" + vorgaenger, "{\"werte\":" + jsonSchreib(alt) + "}");
    if (a.status != 200 && a.status != 404) log(WARNUNG, std::string("Konfiguration ") + b.name + ": Vormonat als abgelöst markieren HTTP " + std::to_string(a.status));
  }
  eintrag = objekt();
  eintrag.o["m"] = txt(mid);
  eintrag.o["d"] = txt(did);
  eintrag.o["z"] = txt(l.monat);
  eintrag.o["p"] = txt(pw);
  eintrag.o["q"] = txt(pw);
  eintrag.o["n"] = zahl(1);
  l.neu++;
  return true;
}

// Neue Version im selben Monat: Datei ersetzen (die alte bleibt als Version), Felder nachziehen.
bool neue_version(const Bereich &b, const std::string &roh, const std::string &ablago, const std::string &aenderung, Lauf &l, Json &eintrag) {
  std::string mid = eintrag["m"].text(), did = eintrag["d"].text();
  int n = (int)eintrag["n"].zahl(1) + 1;
  Antwort d = hochladen("/dokumente/" + did + "/ersetzen?typ=application%2Fjson", roh);
  if (d.status == 404) {
    // Dokument weg, Mappe noch da: die Datei neu in die Mappe des Monats (die Kennung Bereich · Monat ist eindeutig).
    d = hochladen("/mappen/" + mid + "/dokumente?register=dateien&name=konfiguration-" + b.schluessel + "-" + l.monat + ".json&typ=application%2Fjson", roh);
    if (d.status == 404) return false;  // auch die Mappe ist weg – dann eine neue
    if (!neue_id(d.json).empty()) eintrag.o["d"] = txt(neue_id(d.json));
  }
  if (d.status != 200 && d.status != 201) { log(FEHLER, std::string("Konfiguration ") + b.name + ": neue Version HTTP " + std::to_string(d.status)); l.fehler++; return true; }
  std::string pw = sha256(roh);
  Json w = objekt();
  w.o["aenderung"] = txt(aenderung);
  w.o["stand_vom"] = txt(l.heute);
  w.o["versionen"] = zahl(n);
  w.o["ablago_version"] = txt(ablago);
  w.o["pruefwert"] = txt(pw);
  Antwort a = api("PUT", "/mappen/" + mid, "{\"werte\":" + jsonSchreib(w) + "}");
  if (a.status != 200) log(WARNUNG, std::string("Konfiguration ") + b.name + ": Felder nachziehen HTTP " + std::to_string(a.status));
  eintrag.o["p"] = txt(pw);
  eintrag.o["q"] = txt(pw);
  eintrag.o["n"] = zahl(n);
  l.versionen++;
  return true;
}

// Speicher leer (neu installiert, zurückgesetzt), aber es gibt schon Stände? Den aktuellen dieses Bereichs wiederfinden,
// damit keine zweite Mappe mit derselben Kennung entsteht. Leeres Objekt, wenn es keinen gibt.
Json wiederfinden(const Bereich &b) {
  std::string typ = typ_id("compliance_konfiguration");
  if (typ.empty()) return Json();
  const int SEITE = 100;
  for (int von = 0; von < 2000; von += SEITE) {
    Antwort s = api("GET", "/mappen?sicht=typ:" + typ + "&von=" + std::to_string(von) + "&anzahl=" + std::to_string(SEITE));
    if (s.status != 200) return Json();
    for (const Json &m : s.json["mappen"].l) {
      const Json &w = m["werte"];
      if (w["bereich"].text() != b.name || w["status"].text() != "aktuell") continue;
      Json e = objekt();
      e.o["m"] = txt(m["id"].text());
      e.o["z"] = txt(w["zeitraum"].text());
      e.o["p"] = txt(w["pruefwert"].text());
      e.o["n"] = zahl(w["versionen"].zahl(1));
      Antwort d = api("GET", "/mappen/" + m["id"].text());
      for (const Json &x : d.json["dokumente"].l)
        if (x["register"].text("dateien") == "dateien") e.o["d"] = txt(x["id"].text());  // die neueste Datei steht zuletzt
      log(INFO, std::string("Konfiguration ") + b.name + ": Stand " + w["zeitraum"].text() + " wiedergefunden");
      return e;
    }
    if ((int)s.json["mappen"].l.size() < SEITE) break;
  }
  return Json();
}

void bereich_festhalten(const Bereich &b, const Json &einstellungen, const std::string &auswahl_satz, Lauf &l, Json &stand) {
  Antwort e = api("GET", std::string("/einrichtung/") + b.schluessel);
  if (e.status == 403 || e.status == 404) { l.gesperrt++; return; }  // nicht freigegeben (bzw. dieser Kern kennt den Bereich nicht)
  if (e.status != 200 || e.json.art != Json::OBJEKT) { log(FEHLER, std::string("Einrichtung ") + b.name + ": HTTP " + std::to_string(e.status)); l.fehler++; return; }
  const std::string ablago = e.json["ablago"].text();
  Json &alle = stand.o["b"];
  if (alle.art != Json::OBJEKT) alle = objekt();
  Json eintrag = alle[b.schluessel];
  if (eintrag.art != Json::OBJEKT || eintrag["m"].text().empty()) eintrag = wiederfinden(b);
  const std::string pw = sha256(e.roh);

  if (eintrag.art != Json::OBJEKT || eintrag["m"].text().empty()) {
    Json neu;
    if (lege_an(b, e.roh, ablago, "Erster Stand – ab hier hält Ablago jede Änderung fest, die zählt.", "", l, neu)) alle.o[b.schluessel] = neu;
    else l.fehler++;
    return;
  }
  // Seit dem letzten Lauf nichts geändert (gleiche Bytes) – kein Vergleich nötig. Zusatz aus der eigenen Auswahl zählt trotzdem.
  std::vector<Aenderung> zaehlen;
  if (pw != eintrag["q"].text()) {
    Antwort vorher = api("GET", "/dokumente/" + eintrag["d"].text() + "/inhalt");
    if (vorher.status == 200 && vorher.json.art == Json::OBJEKT) {
      Antwort v = api("POST", std::string("/einrichtung/") + b.schluessel + "/vergleich", "{\"vorher\":" + vorher.roh + ",\"nachher\":" + e.roh + "}");
      if (v.status != 200) { log(FEHLER, std::string("Vergleich ") + b.name + ": HTTP " + std::to_string(v.status)); l.fehler++; return; }
      zaehlen = zaehlende(v.json, auswahl(b, einstellungen));
    } else {
      zaehlen.push_back({"", "Neuer Ausgangsstand – der vorige Stand war nicht mehr lesbar."});
    }
    eintrag.o["q"] = txt(pw);
  }
  if (!auswahl_satz.empty()) zaehlen.push_back({AUSWAHL, auswahl_satz});
  if (zaehlen.empty()) { alle.o[b.schluessel] = eintrag; l.gleich++; return; }

  const std::string text = als_text(zaehlen);
  if (eintrag["z"].text() == l.monat && neue_version(b, e.roh, ablago, text, l, eintrag)) { alle.o[b.schluessel] = eintrag; return; }
  Json neu;
  if (lege_an(b, e.roh, ablago, text, eintrag["z"].text() == l.monat ? "" : eintrag["m"].text(), l, neu)) alle.o[b.schluessel] = neu;
  else l.fehler++;
}

// ---- Nachweise ------------------------------------------------------------------------------------------------------

struct NachweisLauf {
  std::vector<std::string> angelegt;
  bool gesperrt = false;
  int fehler = 0;
};

// Nachweise eines Monats anlegen. true = erledigt (angelegt oder gab es schon), false = später noch einmal.
bool nachweise(const std::string &monat, NachweisLauf &n) {
  Antwort a = api("GET", "/nachweise?monat=" + monat);
  if (a.status == 403 || a.status == 404) { n.gesperrt = true; return false; }
  if (a.status != 200 || a.json.art != Json::OBJEKT) { log(FEHLER, "Nachweise " + monat + ": HTTP " + std::to_string(a.status)); n.fehler++; return false; }
  std::string typ = typ_id("compliance_nachweise");
  if (typ.empty()) { log(FEHLER, "Mappentyp Nachweise nicht gefunden"); n.fehler++; return false; }
  Json w = objekt();
  w.o["monat"] = txt(monat);
  w.o["stichtag"] = txt(a.json["stichtag"].text(monatsende(monat).c_str()));
  w.o["zusammenfassung"] = txt(zusammenfassung(a.json));
  if (a.json["benutzer"].art == Json::LISTE) w.o["benutzer"] = zahl((double)a.json["benutzer"].l.size());
  w.o["bereiche"] = txt(bereichsnamen(a.json["bereiche"]));
  w.o["pruefwert"] = txt(sha256(a.roh));
  Antwort m = api("POST", "/mappen", "{\"typId\":" + jsonText(typ) + ",\"werte\":" + jsonSchreib(w) + "}");
  if (m.status == 409 || m.status == 422) { log(INFO, "Nachweise " + monat + " gibt es schon"); return true; }  // eindeutiger Monat
  std::string mid = neue_id(m.json);
  if ((m.status != 200 && m.status != 201) || mid.empty()) { log(FEHLER, "Nachweise " + monat + " anlegen: HTTP " + std::to_string(m.status)); n.fehler++; return false; }
  Antwort d = hochladen("/mappen/" + mid + "/dokumente?register=dateien&name=nachweise-" + monat + ".json&typ=application%2Fjson", a.roh);
  if (d.status != 200 && d.status != 201) log(FEHLER, "Nachweise " + monat + ": Datei hochladen HTTP " + std::to_string(d.status));
  n.angelegt.push_back(monat);
  return true;
}

// ---- Ablauf ---------------------------------------------------------------------------------------------------------

int verarbeite(const Json &e) {
  const std::string art = e["art"].text();
  if (art != "zeitplan.ausgefuehrt" && art != "paket.einstellungen_geaendert") return 0;
  Lauf l;
  l.heute = e["daten"]["datum"].text();
  if (l.heute.size() < 10) l.heute = e["erstellt"].text();
  l.heute = l.heute.substr(0, 10);
  l.monat = monat_von(l.heute);
  if (l.monat.empty()) { log(FEHLER, "Ereignis ohne gültiges Datum"); return 2; }

  const Json &einstellungen = e["einstellungen"];
  Json stand = lies_stand();
  const std::string auswahl_jetzt = auswahl_text(einstellungen);
  std::string satz = auswahl_aenderung(stand["a"].text(), auswahl_jetzt);
  // Die geänderte Auswahl zählt nur, wenn „Auswahl in diesen Einstellungen“ selbst angehakt ist.
  if (!zaehlt(AUSWAHL, auswahl(*bereich("allgemeines"), einstellungen))) satz.clear();

  for (const Bereich &b : bereiche()) bereich_festhalten(b, einstellungen, b.schluessel == std::string("allgemeines") ? satz : "", l, stand);
  stand.o["a"] = txt(auswahl_jetzt);

  // Nachweise: vom ersten Lauf an Monat für Monat; verpasste holt der nächste Lauf nach (höchstens zwölf).
  NachweisLauf n;
  if (!ist_monat(stand["nl"].text())) stand.o["nl"] = txt(monat_plus(l.monat, -1));
  for (const std::string &m : fehlende_monate(stand["nl"].text(), l.monat)) {
    if (!nachweise(m, n)) break;
    stand.o["nl"] = txt(m);
  }
  schreib_stand(stand);

  std::string r;
  if (l.neu) r += std::to_string(l.neu) + (l.neu == 1 ? " neuer Stand" : " neue Stände");
  if (l.versionen) r += (r.empty() ? "" : ", ") + std::to_string(l.versionen) + (l.versionen == 1 ? " neue Version" : " neue Versionen");
  if (l.gleich) r += (r.empty() ? "" : ", ") + std::to_string(l.gleich) + (l.gleich == 1 ? " Bereich unverändert" : " Bereiche unverändert");
  if (!n.angelegt.empty()) r += (r.empty() ? "" : ", ") + std::string("Nachweise ") + n.angelegt.back() + (n.angelegt.size() > 1 ? " (und " + std::to_string(n.angelegt.size() - 1) + " nachgeholt)" : "");
  if (r.empty() && l.gesperrt == (int)bereiche().size()) r = "Noch kein Bereich freigegeben – in den Einstellungen des Pakets anhaken";
  if (l.fehler + n.fehler) r += (r.empty() ? "" : ", ") + std::to_string(l.fehler + n.fehler) + " Fehler (siehe Protokoll)";
  ergebnis(r.empty() ? "Nichts zu tun" : r);
  return (l.fehler + n.fehler) && !l.neu && !l.versionen && n.angelegt.empty() && !l.gleich ? 2 : 0;
}

}  // namespace

extern "C" {

__attribute__((export_name("dms_puffer"))) char *dms_puffer(int32_t n) {
  free(eingang);
  eingang = static_cast<char *>(malloc((size_t)n + 1));
  if (eingang) eingang[n] = 0;
  return eingang;
}

__attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *json, int32_t len) {
  return verarbeite(JsonLeser::lies(json, (size_t)len));
}

}
