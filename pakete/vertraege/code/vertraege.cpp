// Paket Verträge (dms-registry #159): rechnet die berechneten Felder eines Vertrags aus (Status, Kündigen bis,
// frühestes Ende, nächste Verlängerung, Ende, Laufzeit in Monaten, pro Monat) und schreibt nur, was sich ändert.
//
// Ereignisse: mappe.angelegt / mappe.geaendert (ein Vertrag), zeitplan.ausgefuehrt (Automatisierung „Verträge täglich
// prüfen“, DMS #1082) und paket.einstellungen_geaendert (alle Verträge – der Status hängt am Datum). Was das Paket selbst ändert, meldet Ablago ihm nicht zurück.
// Geschrieben wird mit „stand“: Hat ein Mensch dasselbe Feld inzwischen geändert, gewinnt der Mensch (409, nichts
// überschrieben). Die Berechnung steht in berechnung.h.
#include <cstdint>
#include <cstdlib>
#include <string>
#include <vector>

#include "berechnung.h"
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
const char *TYP_SCHLUESSEL = "vertraege:vertrag";  // Kennung in Ablago ab 0.229.0: <paket>:<schluessel> (DMS #1084)
const int SEITE = 100;                             // Mappen je Abruf
const int HOECHSTENS = 5000;                       // Verträge je Durchgang (danach morgen weiter)
const char *BERECHNET[] = {"status", "kuendigen_bis", "fruehestes_ende", "naechste_verlaengerung", "ende", "laufzeit_monate", "pro_monat"};

char *eingang = nullptr;

void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }

struct Antwort { int status; Json json; };

Antwort api(const std::string &methode, const std::string &pfad, const std::string &body = "") {
  std::string q = "{\"methode\":" + jsonText(methode) + ",\"pfad\":" + jsonText(pfad) + (body.empty() ? "" : ",\"body\":" + body) + "}";
  int s = dms_api(q.data(), (int32_t)q.size());
  std::string a((size_t)dms_antwort_laenge(), '\0');
  if (!a.empty()) dms_antwort_lesen(a.data(), (int32_t)a.size());
  return {s, JsonLeser::lies(a.data(), a.size())};
}

std::optional<vertrag::Datum> datum(const Json &w) { return w.art == Json::TEXT ? vertrag::lies_iso(w.t) : std::nullopt; }

std::optional<vertrag::Zeitraum> zeitraum(const Json &w) {
  if (w.art != Json::OBJEKT || w["anzahl"].art != Json::ZAHL) return std::nullopt;
  double n = w["anzahl"].z;
  if (n < 0 || n > 1200 || n != (double)(int)n) return std::nullopt;
  std::string e = w["einheit"].text();
  vertrag::Einheit ein = e == "tage" ? vertrag::Einheit::TAGE : e == "wochen" ? vertrag::Einheit::WOCHEN
                       : e == "monate" ? vertrag::Einheit::MONATE : e == "jahre" ? vertrag::Einheit::JAHRE : vertrag::Einheit(-1);
  if ((int)ein < 0) return std::nullopt;
  return vertrag::Zeitraum{(int)n, ein};
}

vertrag::Eingabe eingabe(const Json &w) {
  vertrag::Eingabe e;
  e.beginn = datum(w["beginn"]);
  e.vertragsende = datum(w["vertragsende"]);
  e.gekuendigt_am = datum(w["gekuendigt_am"]);
  e.bestaetigt_am = datum(w["kuendigung_bestaetigt_am"]);
  e.mindestlaufzeit = zeitraum(w["mindestlaufzeit"]);
  e.verlaengerung_um = zeitraum(w["verlaengerung_um"]);
  e.kuendigungsfrist = zeitraum(w["kuendigungsfrist"]);
  std::string d = w["verlaengerung"].text();
  e.danach = d == "verlängert sich um" ? vertrag::Danach::UM : d == "läuft unbefristet weiter" ? vertrag::Danach::UNBEFRISTET
           : d == "endet" ? vertrag::Danach::ENDET : vertrag::Danach::LEER;
  std::string z = w["kuendigung_zum"].text();
  e.zum = z == "Laufzeitende" ? vertrag::Zum::LAUFZEITENDE : z == "Monatsende" ? vertrag::Zum::MONATSENDE : z == "Quartalsende" ? vertrag::Zum::QUARTALSENDE
        : z == "Jahresende" ? vertrag::Zum::JAHRESENDE : z == "jederzeit" ? vertrag::Zum::JEDERZEIT : vertrag::Zum::LEER;
  const Json &b = w["betrag"];
  if (b.art == Json::OBJEKT && b["betrag"].art == Json::ZAHL) e.betrag = b["betrag"].z;
  else if (b.art == Json::ZAHL) e.betrag = b.z;
  e.zahlweise = w["zahlweise"].text();
  return e;
}

// Neue Werte der berechneten Felder als Json (null = leeren).
Json werte(const vertrag::Ergebnis &r, const Json &alt) {
  Json o; o.art = Json::OBJEKT;
  auto txt = [](const std::string &s) { Json j; if (s.empty()) return j; j.art = Json::TEXT; j.t = s; return j; };
  auto dat = [&](const std::optional<vertrag::Datum> &d) { return d ? txt(vertrag::iso(*d)) : Json(); };
  o.o["status"] = txt(r.status);
  o.o["kuendigen_bis"] = dat(r.kuendigen_bis);
  o.o["fruehestes_ende"] = dat(r.fruehestes_ende);
  o.o["naechste_verlaengerung"] = dat(r.naechste_verlaengerung);
  o.o["ende"] = dat(r.ende);
  Json l; if (r.laufzeit_monate) { l.art = Json::ZAHL; l.z = *r.laufzeit_monate; }
  o.o["laufzeit_monate"] = l;
  Json p;
  if (r.pro_monat) {
    p.art = Json::OBJEKT;
    Json z; z.art = Json::ZAHL; z.z = *r.pro_monat;
    Json wae = txt(alt["betrag"]["waehrung"].text("EUR"));
    p.o["betrag"] = z; p.o["waehrung"] = wae;
  }
  o.o["pro_monat"] = p;
  return o;
}

bool gleich(const Json &a, const Json &b) { return jsonSchreib(a) == jsonSchreib(b); }

// Eine Mappe (werte + geaendert) neu rechnen und nur Abweichungen schreiben. 0 = gut, 1 = übersprungen, 2 = Fehler.
int rechne_mappe(const std::string &id, const Json &m, const vertrag::Datum &heute) {
  const Json &w = m["werte"];
  vertrag::Ergebnis r = vertrag::rechne(eingabe(w), heute);
  Json neu = werte(r, w), aenderung; aenderung.art = Json::OBJEKT;
  for (const char *k : BERECHNET) {
    const Json &a = w[k], &n = neu[k];
    bool alt_leer = a.art == Json::NUL, neu_leer = n.art == Json::NUL;
    if (alt_leer && neu_leer) continue;
    if (!gleich(a, n)) aenderung.o[k] = n;
  }
  if (aenderung.o.empty()) return 1;
  std::string body = "{\"werte\":" + jsonSchreib(aenderung) + (m["geaendert"].art == Json::TEXT ? ",\"stand\":" + jsonText(m["geaendert"].t) : "") + "}";
  Antwort a = api("PUT", "/mappen/" + id, body);
  if (a.status == 409) { log(INFO, "Vertrag " + id + ": inzwischen von jemandem geändert – berechne beim nächsten Mal neu"); return 1; }
  if (a.status == 404) return 1;
  if (a.status != 200) { log(FEHLER, "Vertrag " + id + ": Speichern HTTP " + std::to_string(a.status)); return 2; }
  return 0;
}

vertrag::Datum heute_aus(const Json &e) {
  std::string s = e["daten"]["datum"].text();
  if (s.empty()) s = e["erstellt"].text();
  if (auto d = vertrag::lies_iso(s.substr(0, 10))) return *d;
  return {2026, 1, 1};
}

std::string typ_id(const Json &e) {
  std::string t = e["daten"]["typ"].text();
  if (!t.empty()) return t;
  Antwort a = api("GET", "/typen");
  const Json &liste = a.json.art == Json::LISTE ? a.json : a.json["typen"];
  for (const Json &x : liste.l)
    if (x["schluessel"].text() == TYP_SCHLUESSEL) return x["id"].text();
  return "";
}

int eine(const Json &e) {
  const std::string id = e["daten"]["mappe"].text();
  if (id.empty() || id.size() > 64) return 0;
  // Nur die berechneten Felder geändert? Dann nichts zu tun (Ablago meldet eigene Änderungen ohnehin nicht).
  const Json &felder = e["daten"]["felder"];
  if (felder.art == Json::LISTE && !felder.l.empty()) {
    bool nur = true;
    for (const Json &f : felder.l) {
      bool b = false;
      for (const char *k : BERECHNET) b = b || f.text() == k;
      nur = nur && b;
    }
    if (nur) { ergebnis("Nur berechnete Felder geändert – nichts zu tun"); return 0; }
  }
  Antwort m = api("GET", "/mappen/" + id);
  if (m.status == 404) { ergebnis("Den Vertrag gibt es nicht mehr – nichts zu tun"); return 0; }
  if (m.status != 200) { log(FEHLER, "Vertrag lesen: HTTP " + std::to_string(m.status)); return 2; }
  int r = rechne_mappe(id, m.json, heute_aus(e));
  if (r == 2) return 2;
  ergebnis(r == 0 ? "Vertrag neu berechnet" : "Vertrag unverändert");
  return 0;
}

int alle(const Json &e) {
  const std::string typ = typ_id(e);
  if (typ.empty()) { ergebnis("Mappentyp Vertrag nicht gefunden – nichts zu tun"); return 0; }
  const vertrag::Datum heute = heute_aus(e);
  int geaendert = 0, gesehen = 0, fehler = 0;
  for (int von = 0; von < HOECHSTENS; von += SEITE) {
    Antwort s = api("GET", "/mappen?sicht=typ:" + typ + "&von=" + std::to_string(von) + "&anzahl=" + std::to_string(SEITE));
    if (s.status != 200) { log(FEHLER, "Verträge lesen: HTTP " + std::to_string(s.status)); return 2; }
    const Json &liste = s.json["mappen"];
    for (const Json &m : liste.l) {
      gesehen++;
      int r = rechne_mappe(m["id"].text(), m, heute);
      geaendert += r == 0;
      fehler += r == 2;
    }
    if ((int)liste.l.size() < SEITE) break;
  }
  ergebnis(std::to_string(gesehen) + (gesehen == 1 ? " Vertrag" : " Verträge") + " geprüft, " + std::to_string(geaendert) + " neu berechnet" +
           (fehler ? ", " + std::to_string(fehler) + " nicht gespeichert" : ""));
  return fehler && !geaendert ? 2 : 0;
}

int verarbeite(const Json &e) {
  const std::string art = e["art"].text();
  if (!e["einstellungen"]["aktiv"].wahr(true)) { ergebnis("Berechnung ausgeschaltet (Einstellungen des Pakets)"); return 0; }
  if (art == "mappe.angelegt" || art == "mappe.geaendert") return eine(e);
  if (art == "zeitplan.ausgefuehrt" || art == "paket.einstellungen_geaendert") return alle(e);
  return 0;
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
