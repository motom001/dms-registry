// Paket Rechnungen (dms-registry #161): Status der Rechnung, Umsatzsteuer und Gesamtpreis der Positionen,
// Summenprüfung als Hinweis an der Rechnung (dms:hinweise). Die Regeln stehen in rechnung.h.
//
// Ereignisse: mappe.angelegt / mappe.geaendert zu Rechnungen und Positionen, zeitplan.ausgefuehrt (überfällig, Summen).
// (überfällig). Geschrieben wird nur, was sich ändert, mit „stand“ – ein Mensch gewinnt (409).
// Hinweis setzen/entfernen: PUT bzw. DELETE /mappen/{id}/hinweise/summe (Schnittstelle aus DMS #1034, ab Ablago 0.231.0; Text höchstens 300 Zeichen).
#include <cstdint>
#include <cstdlib>
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
const char *TYP_RECHNUNG = "rechnungen:rechnung", *TYP_POSITION = "rechnungen:rechnungsposition";
const int SEITE = 100, HOECHSTENS = 5000;
const char *HINWEIS = "summe";

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

// Nur geänderte Felder schreiben. 0 = geschrieben, 1 = nichts zu tun, 2 = Fehler.
int schreibe(const std::string &id, const Json &m, const std::vector<std::pair<std::string, Json>> &neu) {
  const Json &w = m["werte"];
  Json aend; aend.art = Json::OBJEKT;
  for (const auto &kv : neu)
    if (!(w[kv.first.c_str()].art == Json::NUL && kv.second.art == Json::NUL) && !gleich(w[kv.first.c_str()], kv.second)) aend.o[kv.first] = kv.second;
  if (aend.o.empty()) return 1;
  std::string body = "{\"werte\":" + jsonSchreib(aend) + (m["geaendert"].art == Json::TEXT ? ",\"stand\":" + jsonText(m["geaendert"].t) : "") + "}";
  Antwort a = api("PUT", "/mappen/" + id, body);
  if (a.status == 409 || a.status == 404) return 1;
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

std::string typ_id(const char *schluessel) {
  Antwort a = api("GET", "/typen");
  const Json &liste = a.json.art == Json::LISTE ? a.json : a.json["typen"];
  for (const Json &x : liste.l)
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

int hinweis(const std::string &rechnung_id, const Json &w, const std::vector<rechnung::Position> &pos) {
  std::string h = rechnung::summenhinweis(zahl(w["betrag"]), pos, w["betrag"]["waehrung"].text("EUR"));
  Antwort a = h.empty() ? api("DELETE", "/mappen/" + rechnung_id + "/hinweise/" + HINWEIS)
                        : api("PUT", "/mappen/" + rechnung_id + "/hinweise/" + HINWEIS, "{\"text\":" + jsonText(h) + "}");
  if (a.status >= 500) { log(FEHLER, "Hinweis: HTTP " + std::to_string(a.status)); return 2; }
  return 0;
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
  return hinweis(rechnung_id, r.json["werte"], pos);
}

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
    if (!pos_typ.empty() && jede(pos_typ, [&](const std::string &, const Json &m) { alle_pos.push_back({verweis(m["werte"]["rechnung"]), position(m["werte"])}); }) == 2) return 2;
    const bool summen = e["einstellungen"]["summenpruefung"].wahr(true);
    int n = 0, neu = 0, fehler = 0;
    if (jede(typ, [&](const std::string &id, const Json &m) {
          int r = rechnung_status(id, m, heute); n++; neu += r == 0; fehler += r == 2;
          if (!summen) return;
          std::vector<rechnung::Position> pos;
          for (const auto &p : alle_pos) if (p.first == id) pos.push_back(p.second);
          if (!pos.empty()) fehler += hinweis(id, m["werte"], pos) == 2;
        }) == 2) return 2;
    ergebnis(std::to_string(n) + (n == 1 ? " Rechnung" : " Rechnungen") + " geprüft, " + std::to_string(neu) + " Status neu");
    return fehler && !neu ? 2 : 0;
  }
  if (art != "mappe.angelegt" && art != "mappe.geaendert") return 0;
  const std::string id = d["mappe"].text();
  if (id.empty() || id.size() > 64) return 0;
  const std::string pos_typ = typ_id(TYP_POSITION);
  Antwort m = api("GET", "/mappen/" + id);
  if (m.status == 404) { ergebnis("Die Mappe gibt es nicht mehr – nichts zu tun"); return 0; }
  if (m.status != 200) { log(FEHLER, "Mappe lesen: HTTP " + std::to_string(m.status)); return 2; }
  const Json &w = m.json["werte"];
  const std::string typ = d["typ"].text(m.json["typId"].text().c_str());
  if (!pos_typ.empty() && typ == pos_typ) {
    int r = position_rechnen(id, m.json);
    if (r == 2) return 2;
    if (summe_pruefen(verweis(w["rechnung"]), pos_typ, e["einstellungen"]) == 2) return 2;
    ergebnis(r == 0 ? "Position neu berechnet" : "Position unverändert");
    return 0;
  }
  int r = rechnung_status(id, m.json, heute_aus(e));
  if (r == 2) return 2;
  // Summenprüfung nur, wenn sich der Betrag geändert hat (oder unbekannt ist, was sich geändert hat).
  const Json &felder = d["felder"];
  bool betrag = felder.art != Json::LISTE || felder.l.empty();
  for (const Json &f : felder.l) betrag = betrag || f.text() == "betrag";
  if (betrag && summe_pruefen(id, pos_typ, e["einstellungen"]) == 2) return 2;
  ergebnis(r == 0 ? "Rechnung: Status neu" : "Rechnung unverändert");
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
