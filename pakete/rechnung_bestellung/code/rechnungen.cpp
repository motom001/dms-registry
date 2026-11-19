// Paket Rechnungen und Bestellungen (dms-registry #161, #210; bis 1.x das Paket Rechnungen): Status der Rechnung,
// Umsatzsteuer und Gesamtpreis der Positionen, Steuerzeilen je Satz mit Summen an der Rechnung, Summenprüfungen als
// Hinweis an der Rechnung (dms:hinweise). Die Regeln stehen in rechnung.h.
//
// Ereignisse: mappe.angelegt / mappe.geaendert zu Rechnungen, Positionen und Steuerzeilen, zeitplan.ausgefuehrt
// (überfällig, Summen). Geschrieben wird nur, was sich ändert, mit „stand“; bei 409 liest das Paket die Mappe einmal
// neu und rechnet noch einmal. Eigene Änderungen meldet Ablago dem Paket nicht – deshalb rechnet es Folgen gleich mit.
// Hinweise setzen/entfernen: PUT bzw. DELETE /mappen/{id}/hinweise/summe bzw. …/steuer (DMS #1034, höchstens 300 Zeichen).
// Steuerzeilen „aus Positionen“ (#210): je Satz der Positionen eine Zeile, angelegt mit POST /mappen und aktuell gehalten;
// gibt es an der Rechnung eine Zeile von Hand, fasst das Paket die Steuerzeilen nicht an.
// Aktion im Menü „Mappe“ (dms-registry #162, DMS #1039, ab 0.245.0): „Als bezahlt markieren“ – dms_aktion mit
// { aktion: dms:mappenaktion }; Schritt 1 fragt das Datum (heute vorgeschlagen), Schritt 2 setzt „Bezahlt am“.
#include <cstdint>
#include <cstdlib>
#include <ctime>
#include <string>
#include <vector>

#include "json.h"
#include "rechnung.h"

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
// Kennungen in Ablago ab 0.229.0: <paket>:<schluessel> (DMS #1084)
const char *TYP_RECHNUNG = "rechnung_bestellung:rechnung", *TYP_POSITION = "rechnung_bestellung:rechnungsposition",
           *TYP_STEUER = "rechnung_bestellung:steuerzeile";
const char *AUS_POSITIONEN = "aus Positionen";
const int SEITE = 100, HOECHSTENS = 5000;
const char *HINWEIS = "summe", *HINWEIS_STEUER = "steuer";

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
// GET /mappen/{id} liefert die Mappe unter „mappe“, daneben Dokumente, Notizen, Rechte … (dms-registry #209: das Paket
// las bis 1.2.0 die oberste Ebene, fand keine Werte und schrieb deshalb nie einen Status). Die Form ohne Hülle gilt weiter.
const Json &mappe_aus(const Json &a) { return a["mappe"].art == Json::OBJEKT ? a["mappe"] : a; }

std::optional<rechnung::Datum> datum(const Json &w) { return w.art == Json::TEXT ? rechnung::lies_iso(w.t) : std::nullopt; }
std::optional<double> zahl(const Json &w) {
  if (w.art == Json::ZAHL) return w.z;
  if (w.art == Json::OBJEKT && w["betrag"].art == Json::ZAHL) return w["betrag"].z;
  return std::nullopt;
}
// Id einer verwiesenen Mappe: Text, { id } oder die erste aus einer Liste.
std::string verweis(const Json &w) {
  if (w.art == Json::TEXT) return w.t;
  if (w.art == Json::OBJEKT) return w["id"].text();
  if (w.art == Json::LISTE && !w.l.empty()) return verweis(w.l[0]);
  return "";
}
Json text_json(const std::string &s) { Json j; if (!s.empty()) { j.art = Json::TEXT; j.t = s; } return j; }
Json betrag_json(const std::optional<double> &w, const std::string &waehrung) {
  Json j;
  if (!w) return j;
  j.art = Json::OBJEKT;
  Json z; z.art = Json::ZAHL; z.z = *w;
  j.o["betrag"] = z; j.o["waehrung"] = text_json(waehrung.empty() ? "EUR" : waehrung);
  return j;
}
bool gleich(const Json &a, const Json &b) { return jsonSchreib(a) == jsonSchreib(b); }

rechnung::Datum heute_aus(const Json &e) {
  std::string s = e["daten"]["datum"].text();
  if (s.empty()) s = e["erstellt"].text();
  if (auto d = rechnung::lies_iso(s.substr(0, 10))) return *d;
  return {2026, 1, 1};
}

// Nur geänderte Felder schreiben. 0 = geschrieben, 1 = nichts zu tun, 2 = Fehler, 3 = Konflikt (409: seit dem Lesen hat
// sich ein Feld geändert, das das Paket schreiben will – neu lesen und neu rechnen, was ein Mensch einträgt, gilt).
int schreibe(const std::string &id, const Json &m, const std::vector<std::pair<std::string, Json>> &neu) {
  const Json &w = m["werte"];
  Json aend; aend.art = Json::OBJEKT;
  for (const auto &kv : neu)
    if (!(w[kv.first.c_str()].art == Json::NUL && kv.second.art == Json::NUL) && !gleich(w[kv.first.c_str()], kv.second)) aend.o[kv.first] = kv.second;
  if (aend.o.empty()) return 1;
  std::string body = "{\"werte\":" + jsonSchreib(aend) + (m["geaendert"].art == Json::TEXT ? ",\"stand\":" + jsonText(m["geaendert"].t) : "") + "}";
  Antwort a = api("PUT", "/mappen/" + id, body);
  if (a.status == 409) { log(INFO, "Mappe " + id + ": Speichern 409 – inzwischen geändert"); return 3; }
  if (a.status == 404) { log(INFO, "Mappe " + id + ": Speichern 404 – nicht mehr da oder nicht lesbar"); return 1; }
  if (a.status != 200) { log(FEHLER, "Mappe " + id + ": Speichern HTTP " + std::to_string(a.status)); return 2; }
  return 0;
}

int rechnung_status(const std::string &id, const Json &m, const rechnung::Datum &heute) {
  const Json &w = m["werte"];
  rechnung::Eingabe e;
  e.betrag = zahl(w["betrag"]);
  e.faellig_am = datum(w["faellig_am"]);
  e.bezahlt_am = datum(w["bezahlt_am"]);
  e.zahlungseingang_am = datum(w["zahlungseingang_am"]);
  return schreibe(id, m, {{"status", text_json(rechnung::status(e, heute))}});
}

rechnung::Position position(const Json &w) {
  rechnung::Position p;
  p.menge = zahl(w["menge"]);
  p.einzelpreis = zahl(w["einzelpreis"]);
  p.gesamtpreis = zahl(w["gesamtpreis"]);
  p.ust_satz = zahl(w["ust_satz"]);
  return p;
}

int position_rechnen(const std::string &id, const Json &m) {
  const Json &w = m["werte"];
  rechnung::Position p = position(w);
  std::string waehrung = w["einzelpreis"]["waehrung"].text(w["gesamtpreis"]["waehrung"].text("EUR").c_str());
  std::vector<std::pair<std::string, Json>> neu = {{"ust_betrag", betrag_json(rechnung::ust_betrag(p), waehrung)}};
  // Gesamtpreis nur füllen, wenn er leer ist – was ein Mensch einträgt, gilt.
  if (!p.gesamtpreis && rechnung::gesamt(p)) neu.push_back({"gesamtpreis", betrag_json(rechnung::gesamt(p), waehrung)});
  return schreibe(id, m, neu);
}

// Id eines Mappentyps; GET /typen nur einmal je Aufruf.
std::string typ_id(const char *schluessel) {
  static bool gelesen = false;
  static Json typen;
  if (!gelesen) {
    Antwort a = api("GET", "/typen");
    typen = a.json.art == Json::LISTE ? a.json : a.json["typen"];
    gelesen = a.status == 200;
  }
  for (const Json &x : typen.l)
    if (x["schluessel"].text() == schluessel) return x["id"].text();
  return "";
}

// Alle Mappen eines Typs (seitenweise); f(id, mappe) für jede.
template <class F> int jede(const std::string &typ, F f) {
  for (int von = 0; von < HOECHSTENS; von += SEITE) {
    Antwort s = api("GET", "/mappen?sicht=typ:" + typ + "&von=" + std::to_string(von) + "&anzahl=" + std::to_string(SEITE));
    if (s.status != 200) { log(FEHLER, "Mappen lesen: HTTP " + std::to_string(s.status)); return 2; }
    for (const Json &m : s.json["mappen"].l) f(m["id"].text(), m);
    if ((int)s.json["mappen"].l.size() < SEITE) break;
  }
  return 0;
}

int hinweis_setzen(const std::string &rechnung_id, const char *schluessel, const std::string &h);
int hinweis(const std::string &rechnung_id, const Json &w, const std::vector<rechnung::Position> &pos) {
  return hinweis_setzen(rechnung_id, HINWEIS, rechnung::summenhinweis(zahl(w["betrag"]), pos, w["betrag"]["waehrung"].text("EUR")));
}

rechnung::Steuerzeile steuerzeile(const Json &w) {
  rechnung::Steuerzeile z;
  z.satz = zahl(w["satz"]);
  z.netto = zahl(w["netto"]);
  z.steuer = zahl(w["steuer"]);
  return z;
}
bool von_hand(const Json &w) { return w["herkunft"].text() != AUS_POSITIONEN && w["herkunft"].text() != "aus E-Rechnung"; }

struct Zeile { std::string id; Json mappe; };
// Steuerzeilen einer Rechnung (vollständige Mappen aus der Liste).
int steuerzeilen_von(const std::string &rechnung_id, const std::string &steuer_typ, std::vector<Zeile> &aus) {
  if (steuer_typ.empty()) return 0;
  return jede(steuer_typ, [&](const std::string &id, const Json &m) {
    if (verweis(m["werte"]["rechnung"]) == rechnung_id) aus.push_back({id, m});
  });
}

int hinweis_setzen(const std::string &rechnung_id, const char *schluessel, const std::string &h) {
  Antwort a = h.empty() ? api("DELETE", "/mappen/" + rechnung_id + "/hinweise/" + schluessel)
                        : api("PUT", "/mappen/" + rechnung_id + "/hinweise/" + schluessel, "{\"text\":" + jsonText(h) + "}");
  if (a.status >= 500) { log(FEHLER, "Hinweis: HTTP " + std::to_string(a.status)); return 2; }
  return 0;
}

// Summen der Steuerzeilen an die Rechnung und Hinweis, wenn Netto + Umsatzsteuer nicht zum Betrag passen.
// rechnung: die Mappe der Rechnung (frisch gelesen). Ohne Zeilen werden vorhandene Summen geleert.
int steuern_rechnen(const std::string &rechnung_id, const Json &rechnung, const std::vector<Zeile> &zeilen) {
  std::vector<rechnung::Steuerzeile> z;
  for (const Zeile &x : zeilen) z.push_back(steuerzeile(x.mappe["werte"]));
  const Json &w = rechnung["werte"];
  // Nichts da und nichts gesetzt: nichts zu tun (auch kein Hinweis zu entfernen).
  if (z.empty() && w["netto_gesamt"].art == Json::NUL && w["ust_gesamt"].art == Json::NUL) return 1;
  const std::string waehrung = w["betrag"]["waehrung"].text("EUR");
  rechnung::Summen s = rechnung::summen(z);
  int r = schreibe(rechnung_id, rechnung, {{"netto_gesamt", betrag_json(s.netto, waehrung)}, {"ust_gesamt", betrag_json(s.ust, waehrung)}});
  if (r == 2) return 2;
  if (hinweis_setzen(rechnung_id, HINWEIS_STEUER, rechnung::steuerhinweis(zahl(w["betrag"]), z, waehrung)) == 2) return 2;
  return r == 3 ? 1 : r;
}

// Steuerzeilen „aus Positionen“ (#210): je Satz der Positionen eine Zeile anlegen bzw. aktualisieren; Zeilen eines
// Satzes, den keine Position mehr hat, bekommen 0. Gibt es eine Zeile von Hand, bleibt alles, wie es ist.
int aus_positionen(const std::string &rechnung_id, const std::vector<rechnung::Position> &pos, std::vector<Zeile> &zeilen,
                   const std::string &steuer_typ, const std::string &waehrung) {
  for (const Zeile &x : zeilen) if (von_hand(x.mappe["werte"])) return 0;
  std::map<double, rechnung::Steuerzeile> je = rechnung::aus_positionen(pos);
  if (je.empty() && zeilen.empty()) return 0;
  int fehler = 0;
  for (Zeile &x : zeilen) {
    auto sz = zahl(x.mappe["werte"]["satz"]);
    auto i = sz ? je.find(*sz) : je.end();
    std::optional<double> n = i == je.end() ? std::optional<double>(0.0) : i->second.netto;
    std::optional<double> st = i == je.end() ? std::optional<double>(0.0) : i->second.steuer;
    if (i != je.end()) je.erase(i);
    fehler += schreibe(x.id, x.mappe, {{"netto", betrag_json(n, waehrung)}, {"steuer", betrag_json(st, waehrung)}}) == 2;
    // Für die Summen gleich mit den neuen Werten weiterrechnen.
    x.mappe.o["werte"].o["netto"] = betrag_json(n, waehrung);
    x.mappe.o["werte"].o["steuer"] = betrag_json(st, waehrung);
  }
  for (const auto &kv : je) {
    Json satz; satz.art = Json::ZAHL; satz.z = kv.first;
    Json werte; werte.art = Json::OBJEKT;
    werte.o["rechnung"] = text_json(rechnung_id);
    werte.o["satz"] = satz;
    werte.o["netto"] = betrag_json(kv.second.netto, waehrung);
    werte.o["steuer"] = betrag_json(kv.second.steuer, waehrung);
    werte.o["herkunft"] = text_json(AUS_POSITIONEN);
    Antwort a = api("POST", "/mappen", "{\"typId\":" + jsonText(steuer_typ) + ",\"werte\":" + jsonSchreib(werte) + "}");
    if (a.status != 200 && a.status != 201) { log(FEHLER, "Steuerzeile anlegen: HTTP " + std::to_string(a.status)); fehler++; continue; }
    Json m; m.art = Json::OBJEKT; m.o["werte"] = werte;
    zeilen.push_back({mappe_aus(a.json)["id"].text(), m});
  }
  return fehler ? 2 : 0;
}

// Nach einer Änderung an Positionen oder Steuerzeilen: Steuerzeilen aus Positionen (falls eingeschaltet), Summen, Hinweis.
int steuern_nachziehen(const std::string &rechnung_id, const std::string &pos_typ, const std::string &steuer_typ, const Json &einstellungen) {
  if (rechnung_id.empty() || steuer_typ.empty()) return 0;
  Antwort r = api("GET", "/mappen/" + rechnung_id);
  if (r.status != 200) return r.status == 404 ? 0 : 2;
  const Json &rm = mappe_aus(r.json);
  std::vector<Zeile> zeilen;
  if (steuerzeilen_von(rechnung_id, steuer_typ, zeilen) == 2) return 2;
  int fehler = 0;
  if (einstellungen["steuerzeilen_aus_positionen"].wahr(true) && !pos_typ.empty()) {
    std::vector<rechnung::Position> pos;
    if (jede(pos_typ, [&](const std::string &, const Json &m) {
          if (verweis(m["werte"]["rechnung"]) == rechnung_id) pos.push_back(position(m["werte"]));
        }) == 2) return 2;
    fehler += aus_positionen(rechnung_id, pos, zeilen, steuer_typ, rm["werte"]["betrag"]["waehrung"].text("EUR")) == 2;
  }
  fehler += steuern_rechnen(rechnung_id, rm, zeilen) == 2;
  return fehler ? 2 : 0;
}

// Ändert jemand an einer Zeile „aus Positionen“ Satz, Netto oder Steuer, gehört sie ihm: Herkunft „von Hand“
// (eigene Änderungen meldet Ablago dem Paket nicht, das Ereignis kommt also von einem Menschen oder einem anderen Weg).
int steuerzeile_aendern(const std::string &id, const Json &m, const Json &d) {
  const Json &w = m["werte"];
  bool angefasst = false;
  for (const Json &f : d["felder"].l) angefasst = angefasst || f.text() == "satz" || f.text() == "netto" || f.text() == "steuer";
  std::vector<std::pair<std::string, Json>> neu;
  if (angefasst && w["herkunft"].text() == AUS_POSITIONEN) neu.push_back({"herkunft", text_json("von Hand")});
  if (w["steuer"].art == Json::NUL)
    if (auto st = rechnung::steuer(steuerzeile(w))) neu.push_back({"steuer", betrag_json(st, w["netto"]["waehrung"].text("EUR"))});
  return neu.empty() ? 1 : schreibe(id, m, neu);
}

// Summenprüfung einer Rechnung: Positionen holen, vergleichen, Hinweis setzen oder entfernen.
int summe_pruefen(const std::string &rechnung_id, const std::string &pos_typ, const Json &einstellungen) {
  if (!einstellungen["summenpruefung"].wahr(true) || rechnung_id.empty()) return 0;
  Antwort r = api("GET", "/mappen/" + rechnung_id);
  if (r.status != 200) return r.status == 404 ? 0 : 2;
  std::vector<rechnung::Position> pos;
  if (!pos_typ.empty() && jede(pos_typ, [&](const std::string &, const Json &m) {
        if (verweis(m["werte"]["rechnung"]) == rechnung_id) pos.push_back(position(m["werte"]));
      }) == 2) return 2;
  return hinweis(rechnung_id, mappe_aus(r.json)["werte"], pos);
}

int rechnung_fertig(const std::string &id, int r, const Json &d, const std::string &pos_typ, const Json &e);

int verarbeite(const Json &e) {
  const std::string art = e["art"].text();
  const Json &d = e["daten"];
  if (art == "zeitplan.ausgefuehrt") {
    const std::string typ = typ_id(TYP_RECHNUNG);
    if (typ.empty()) { ergebnis("Mappentyp Rechnung nicht gefunden – nichts zu tun"); return 0; }
    const rechnung::Datum heute = heute_aus(e);
    // Positionen einmal lesen und nach Rechnung ordnen – für die Summenprüfung der Rechnungen, die Positionen haben.
    std::vector<std::pair<std::string, rechnung::Position>> alle_pos;
    const std::string pos_typ = typ_id(TYP_POSITION);
    // Dabei Umsatzsteuer und leere Gesamtpreise nachrechnen – z. B. nach dem Umzug aus dem Paket Rechnungen, der die
    // berechnete Umsatzsteuer nicht mitnimmt (Konflikt zählt nicht: die Änderung bringt ihr eigenes Ereignis).
    int pos_neu = 0;
    if (!pos_typ.empty() && jede(pos_typ, [&](const std::string &pid, const Json &m) {
          pos_neu += position_rechnen(pid, m) == 0;
          alle_pos.push_back({verweis(m["werte"]["rechnung"]), position(m["werte"])});
        }) == 2) return 2;
    // Steuerzeilen ebenso einmal lesen (#210): Summen und Hinweis der Rechnungen, die Zeilen haben.
    std::vector<std::pair<std::string, Zeile>> alle_zeilen;
    const std::string steuer_typ = typ_id(TYP_STEUER);
    if (!steuer_typ.empty() && jede(steuer_typ, [&](const std::string &zid, const Json &m) { alle_zeilen.push_back({verweis(m["werte"]["rechnung"]), {zid, m}}); }) == 2) return 2;
    const bool summen = e["einstellungen"]["summenpruefung"].wahr(true);
    int n = 0, neu = 0, fehler = 0;
    if (jede(typ, [&](const std::string &id, const Json &m) {
          // Konflikt (3): Die Rechnung wurde gerade geändert; das Ereignis dazu rechnet den Status ohnehin neu.
          int r = rechnung_status(id, m, heute); n++; neu += r == 0; fehler += r == 2;
          std::vector<Zeile> zeilen;
          for (const auto &z : alle_zeilen) if (z.first == id) zeilen.push_back(z.second);
          if (!zeilen.empty()) {
            // Nach einem neuen Status ist „stand“ der Liste alt – für die Summen frisch lesen.
            Antwort f = r == 0 ? api("GET", "/mappen/" + id) : Antwort{200, m};
            if (f.status == 200) fehler += steuern_rechnen(id, r == 0 ? mappe_aus(f.json) : m, zeilen) == 2;
          }
          if (!summen) return;
          std::vector<rechnung::Position> pos;
          for (const auto &p : alle_pos) if (p.first == id) pos.push_back(p.second);
          if (!pos.empty()) fehler += hinweis(id, m["werte"], pos) == 2;
        }) == 2) return 2;
    ergebnis(std::to_string(n) + (n == 1 ? " Rechnung" : " Rechnungen") + " geprüft, " + std::to_string(neu) + " Status neu" +
             (pos_neu ? ", " + std::to_string(pos_neu) + (pos_neu == 1 ? " Position" : " Positionen") + " neu berechnet" : ""));
    return fehler && !neu ? 2 : 0;
  }
  if (art != "mappe.angelegt" && art != "mappe.geaendert") return 0;
  const std::string id = d["mappe"].text();
  if (id.empty() || id.size() > 64) return 0;
  const std::string pos_typ = typ_id(TYP_POSITION), steuer_typ = typ_id(TYP_STEUER);
  // Bei einem Konflikt (3) einmal neu lesen und neu rechnen.
  for (int versuch = 1;; versuch++) {
    Antwort m = api("GET", "/mappen/" + id);
    if (m.status == 404) { ergebnis("Die Mappe gibt es nicht mehr – nichts zu tun"); return 0; }
    if (m.status != 200) { log(FEHLER, "Mappe lesen: HTTP " + std::to_string(m.status)); return 2; }
    const Json &mappe = mappe_aus(m.json);
    const Json &w = mappe["werte"];
    const std::string typ = d["typ"].text(mappe["typId"].text().c_str());
    const bool ist_position = !pos_typ.empty() && typ == pos_typ;
    const bool ist_steuer = !steuer_typ.empty() && typ == steuer_typ;
    int r = ist_position ? position_rechnen(id, mappe) : ist_steuer ? steuerzeile_aendern(id, mappe, d) : rechnung_status(id, mappe, heute_aus(e));
    if (r == 3 && versuch < 2) continue;
    if (r == 3) { log(WARNUNG, "Mappe " + id + ": auch beim zweiten Versuch 409 – nichts gespeichert"); return 2; }
    if (r == 2) return 2;
    if (ist_position) {
      if (summe_pruefen(verweis(w["rechnung"]), pos_typ, e["einstellungen"]) == 2) return 2;
      if (steuern_nachziehen(verweis(w["rechnung"]), pos_typ, steuer_typ, e["einstellungen"]) == 2) return 2;
      ergebnis(r == 0 ? "Position neu berechnet" : "Position unverändert");
      return 0;
    }
    if (ist_steuer) {
      if (steuern_nachziehen(verweis(w["rechnung"]), pos_typ, steuer_typ, e["einstellungen"]) == 2) return 2;
      ergebnis(r == 0 ? "Steuerzeile neu berechnet" : "Steuerzeile unverändert");
      return 0;
    }
    return rechnung_fertig(id, r, d, pos_typ, e);
  }
}

// Nach dem Status einer Rechnung: Summenprüfung, wenn nötig, und das Ergebnis für den Verlauf.
int rechnung_fertig(const std::string &id, int r, const Json &d, const std::string &pos_typ, const Json &e) {
  // Summenprüfung nur, wenn sich der Betrag geändert hat (oder unbekannt ist, was sich geändert hat).
  const Json &felder = d["felder"];
  bool betrag = felder.art != Json::LISTE || felder.l.empty();
  for (const Json &f : felder.l) betrag = betrag || f.text() == "betrag";
  if (betrag && summe_pruefen(id, pos_typ, e["einstellungen"]) == 2) return 2;
  if (betrag && steuern_nachziehen(id, pos_typ, typ_id(TYP_STEUER), e["einstellungen"]) == 2) return 2;
  ergebnis(r == 0 ? "Rechnung: Status neu" : "Rechnung unverändert");
  return 0;
}

// Heute (UTC) als JJJJ-MM-TT – leer, wenn der Läufer keine Uhr hat.
std::string heute_iso() {
  struct timespec ts {};
  if (clock_gettime(CLOCK_REALTIME, &ts) != 0 || ts.tv_sec <= 0) return "";
  time_t s = ts.tv_sec;
  struct tm u {};
  if (!gmtime_r(&s, &u)) return "";
  char b[16];
  strftime(b, sizeof b, "%Y-%m-%d", &u);
  return b;
}

// „Als bezahlt markieren“: Dialog mit dem Datum, dann das Ergebnis { felder: { bezahlt_am } }. Ablago schreibt mit dem
// Zugriff der Person; den Status rechnet danach das Ereignis mappe.geaendert.
int bezahlt(const Json &e) {
  const int schritt = (int)e["schritt"].zahl(1);
  if (schritt <= 1) {
    const std::string heute = heute_iso();
    std::string datum = "{\"art\":\"datum\",\"schluessel\":\"am\",\"name\":\"Bezahlt am\",\"pflicht\":true" +
                        (heute.empty() ? std::string() : ",\"standard\":" + jsonText(heute)) + "}";
    const Json &w = e["mappe"]["werte"];
    std::string satz = "Wann wurde die Rechnung bezahlt?";
    if (auto b = zahl(w["betrag"])) satz += " Betrag: " + rechnung::euro(*b, w["betrag"]["waehrung"].text("EUR")) + ".";
    ergebnis("{\"dialog\":{\"titel\":\"Als bezahlt markieren\",\"knopf\":\"Markieren\",\"felder\":[{\"art\":\"text\",\"text\":" +
             jsonText(satz) + "}," + datum + "]}}");
    return 0;
  }
  const std::string am = e["antworten"]["am"].text();
  auto d = rechnung::lies_iso(am);
  if (!d || am.size() != 10) {
    ergebnis("{\"ergebnis\":{\"meldung\":\"Kein gültiges Datum – nichts geändert.\"}}");
    return 0;
  }
  ergebnis("{\"ergebnis\":{\"meldung\":" + jsonText("Als bezahlt markiert (" + rechnung::text(*d) + ").") +
           ",\"felder\":{\"bezahlt_am\":" + jsonText(am) + "}}}");
  return 0;
}

int aktion(const Json &e) {
  if (e["aktion"].text() != "dms:mappenaktion") return 0;
  if (e["mappenaktion"].text() == "bezahlt") return bezahlt(e);
  log(WARNUNG, "Unbekannte Aktion „" + e["mappenaktion"].text() + "“");
  return 2;
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

__attribute__((export_name("dms_aktion"))) int32_t dms_aktion(char *json, int32_t len) {
  return aktion(JsonLeser::lies(json, (size_t)len));
}

}
