// Ergänzung „Fahrzeuge: Abruf beim KBA“ (dms-registry #278): zwei Aktionen im Menü „Mappe“ (DMS #1039).
//  - dub_abrufen an der Hauptuntersuchung: holt den Digitalen Untersuchungsbericht mit den Angaben aus dem QR-Link.
//  - coc_abrufen am Fahrzeug: holt den elektronischen CoC (IVI) zur FIN.
// Schritt 1 zeigt, was an das KBA geht; erst der Klick auf „Abrufen“ (Schritt 2) fragt das KBA. Das Captcha der
// öffentlichen Seiten ist eine Rechenaufgabe (Altcha), die das Paket selbst löst. Ergebnis: nur leere Felder werden
// gefüllt, Abweichungen stehen in der Meldung. Die Logik steht in kba.h.
//
// Die Schnittstellen sind nicht als offizielle Programmierschnittstelle veröffentlicht – das Paket nutzt die Aufrufe,
// die die öffentlichen Seiten des KBA selbst machen (siehe README).
#include <cstdint>
#include <cstdlib>
#include <ctime>
#include <string>

#include "json.h"
#include "kba.h"

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
extern "C" {
DMS(netz) int32_t dms_netz(const char *json, int32_t len, const char *body, int32_t blen);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(char *ziel, int32_t max);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);
}

namespace {

enum Stufe { DEBUG = 0, INFO = 1, WARNUNG = 2, FEHLER = 3 };
const char *DUB = "https://www.kba-online.de/dub/api";
const char *IVI = "https://www.kba-online.de/ivicoc_prod/public-access/webapp/api";
const long ALTCHA_MAX = 2000000;  // Schutz gegen eine Aufgabe, die nicht in die 30 s einer Aktion passt

char *eingang = nullptr;
void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }
double jetzt_ms() { timespec t{}; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1000.0 + t.tv_nsec / 1e6; }

struct Antwort { int status; std::string text; };
Antwort netz(const char *methode, const std::string &url, const std::string &body = "") {
  std::string q = "{\"methode\":" + jsonText(methode) + ",\"url\":" + jsonText(url) +
                  ",\"kopf\":{\"accept\":\"application/json, text/plain, */*\"" + (body.empty() ? "" : ",\"content-type\":\"application/json\"") + "}}";
  int s = dms_netz(q.data(), (int32_t)q.size(), body.empty() ? nullptr : body.data(), (int32_t)body.size());
  std::string a((size_t)dms_antwort_laenge(), '\0');
  if (!a.empty()) dms_antwort_lesen(a.data(), (int32_t)a.size());
  return {s, a};
}

std::string meldung_json(const std::string &m) { return "{\"ergebnis\":{\"meldung\":" + jsonText(m) + "}}"; }
int fertig(const std::string &m) { ergebnis(meldung_json(m)); return 0; }
std::string problem(const Antwort &a) {
  if (a.status == -2) return "Die Adresse des KBA ist für das Paket nicht freigegeben (Werkbank → Pakete).";
  if (a.status < 0) return "Das KBA ist gerade nicht erreichbar. Bitte später noch einmal.";
  if (a.status == 429) return "Das KBA bittet um eine Pause (HTTP 429). Bitte später noch einmal.";
  if (a.status >= 500) return "Das KBA hat einen Fehler gemeldet (HTTP " + std::to_string(a.status) + "). Bitte später noch einmal.";
  return "";
}

// Captcha holen und lösen; liefert die Antwort für das Formular oder leer (dann steht die Meldung in fehler).
std::string captcha(const char *basis, std::string &fehler) {
  Antwort a = netz("GET", std::string(basis) + "/altcha");
  if (a.status != 200) { fehler = problem(a); if (fehler.empty()) fehler = "Das KBA hat die Abfrage abgelehnt (HTTP " + std::to_string(a.status) + ")."; return ""; }
  Json j = JsonLeser::lies(a.text.data(), a.text.size());
  long max = (long)j["maxnumber"].zahl(1000000);
  if (j["algorithm"].text("SHA-256") != "SHA-256" || j["challenge"].text().empty() || max > ALTCHA_MAX) {
    fehler = "Das KBA stellt eine Aufgabe, die das Paket nicht kennt. Bitte das Paket aktualisieren.";
    log(WARNUNG, "Unbekanntes Captcha: " + j["algorithm"].text() + ", maxnumber " + std::to_string(max));
    return "";
  }
  double t0 = jetzt_ms();
  long n = kba::altcha_zahl(j["salt"].text(), j["challenge"].text(), max);
  if (n < 0) { fehler = "Die Aufgabe des KBA ließ sich nicht lösen. Bitte noch einmal."; return ""; }
  return kba::altcha_antwort(j, n, (long)(jetzt_ms() - t0));
}

std::string dialog(const std::string &titel, const std::string &satz, const std::string &felder) {
  return "{\"dialog\":{\"titel\":" + jsonText(titel) + ",\"knopf\":\"Abrufen\",\"felder\":[{\"art\":\"text\",\"text\":" + jsonText(satz) + "}" +
         felder + "]}}";
}
std::string textfeld(const char *s, const char *name, const std::string &wert, const char *hilfe) {
  return std::string(",{\"art\":\"textfeld\",\"schluessel\":\"") + s + "\",\"name\":" + jsonText(name) + ",\"pflicht\":true,\"standard\":" +
         jsonText(wert) + ",\"hilfe\":" + jsonText(hilfe) + "}";
}

// „Daten beim KBA abrufen“ an der Hauptuntersuchung.
int dub_abrufen(const Json &e) {
  const Json &werte = e["mappe"]["werte"];
  if ((int)e["schritt"].zahl(1) <= 1) {
    kba::DubSchluessel d = kba::link_zerlegen(werte["digitaler_bericht"].text());
    ergebnis(dialog("Digitalen Untersuchungsbericht abrufen",
                    "Ablago schickt diese drei Angaben an das Kraftfahrt-Bundesamt (www.kba-online.de) und trägt die Antwort in leere Felder ein. "
                    "Schon eingetragene Werte bleiben; Abweichungen siehst du in der Meldung.",
                    textfeld("suchid", "Such-ID", d.suchid, "12 Zeichen, aus dem QR-Code") +
                        textfeld("bericht", "Prüfberichtsnummer", d.bericht, "steht auf dem Prüfbericht") +
                        textfeld("kennnummer", "Kennnummer der Prüfstelle", d.kennnummer, "aus dem QR-Code")));
    return 0;
  }
  const Json &an = e["antworten"];
  std::string suchid = kba::trimmen(an["suchid"].text()), bericht = kba::trimmen(an["bericht"].text()), kenn = kba::trimmen(an["kennnummer"].text());
  for (char &c : suchid) if (c >= 'a' && c <= 'z') c = (char)(c - 'a' + 'A');
  if (!kba::ist_suchid(suchid)) return fertig("Die Such-ID hat 12 Zeichen aus Großbuchstaben und Ziffern – bitte prüfen. Nichts abgerufen.");
  if (bericht.empty() || kenn.empty()) return fertig("Prüfberichtsnummer und Kennnummer werden gebraucht. Nichts abgerufen.");
  std::string fehler, c = captcha(DUB, fehler);
  if (c.empty()) return fertig(fehler);
  std::string body = "{\"dubsuchid\":" + jsonText(suchid) + ",\"pruefberichtsnummer\":" + jsonText(bericht) +
                     ",\"kennnummerDerInstitution\":" + jsonText(kenn) + ",\"captcha\":" + jsonText(c) + "}";
  Antwort a = netz("POST", std::string(DUB) + "/dubAnfrage", body);
  std::string p = problem(a);
  if (!p.empty()) return fertig(p);
  Json j = JsonLeser::lies(a.text.data(), a.text.size());
  const Json &r = j["rueckgabe"];
  if (a.status != 200 || r.art != Json::OBJEKT)
    return fertig("Das KBA hat zu diesen Angaben keinen Bericht gefunden. Bitte Such-ID, Prüfberichtsnummer und Kennnummer prüfen.");
  kba::Ergebnis erg = kba::dub_abbilden(r, werte);
  std::string kopf = "Bericht vom KBA abgerufen.";
  std::string m = erg.meldung(kopf);
  ergebnis("{\"ergebnis\":{\"meldung\":" + jsonText(m) + (erg.felder.empty() ? "" : ",\"felder\":" + erg.felder_json()) + "}}");
  return 0;
}

// „Technische Daten beim KBA abrufen“ am Fahrzeug.
int coc_abrufen(const Json &e) {
  const Json &werte = e["mappe"]["werte"];
  std::string fin = kba::trimmen(werte["fin"].text());
  for (char &c : fin) if (c >= 'a' && c <= 'z') c = (char)(c - 'a' + 'A');
  if (fin.size() != 17) return fertig("Am Fahrzeug steht keine vollständige Fahrzeug-Identnummer (17 Zeichen). Nichts abgerufen.");
  if ((int)e["schritt"].zahl(1) <= 1) {
    ergebnis(dialog("Technische Daten abrufen",
                    "Ablago schickt die Fahrzeug-Identnummer " + fin + " an das Kraftfahrt-Bundesamt (www.kba-online.de) und holt den "
                    "elektronischen CoC. Die Daten kommen in leere Felder unter „Technische Daten“; schon eingetragene Werte bleiben. "
                    "Elektronische CoC gibt es vor allem für neuere Fahrzeuge.",
                    ""));
    return 0;
  }
  std::string fehler, c = captcha(IVI, fehler);
  if (c.empty()) return fertig(fehler);
  std::string body = "{\"publicAccessAbfrageArbeitsdaten\":{\"vin\":" + jsonText(fin) + ",\"altchaPayload\":" + jsonText(c) + "}}";
  Antwort a = netz("POST", std::string(IVI) + "/vin/data", body);
  std::string p = problem(a);
  if (!p.empty()) return fertig(p);
  Json j = JsonLeser::lies(a.text.data(), a.text.size());
  const Json &zwei = j["ivi2xDataEntries"], &eins = j["ivi1xDataEntries"];
  const Json *xml = zwei.art == Json::LISTE && !zwei.l.empty() ? &zwei.l.back() : eins.art == Json::LISTE && !eins.l.empty() ? &eins.l.back() : nullptr;
  if (a.status != 200 || !xml || xml->text().empty())
    return fertig("Zu dieser Fahrzeug-Identnummer hat das KBA keinen elektronischen CoC. Bei älteren Fahrzeugen ist das normal – die Daten stehen dann in der Zulassungsbescheinigung.");
  kba::Knoten w = kba::XmlLeser::lies(xml->text());
  if (w.name.empty()) return fertig("Der elektronische CoC vom KBA ließ sich nicht lesen. Bitte das Paket aktualisieren.");
  kba::Ergebnis erg = kba::ivi_abbilden(w, werte, fin);
  std::string m = erg.meldung("Elektronischen CoC (Version " + kba::ivi_version(w) + ") vom KBA abgerufen.");
  ergebnis("{\"ergebnis\":{\"meldung\":" + jsonText(m) + (erg.felder.empty() ? "" : ",\"felder\":" + erg.felder_json()) + "}}");
  return 0;
}

int aktion(const Json &e) {
  if (e["aktion"].text() != "dms:mappenaktion") return 0;
  const std::string a = e["mappenaktion"].text();
  if (a == "dub_abrufen") return dub_abrufen(e);
  if (a == "coc_abrufen") return coc_abrufen(e);
  log(WARNUNG, "Unbekannte Aktion „" + a + "“");
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
__attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *, int32_t) { return 0; }
__attribute__((export_name("dms_aktion"))) int32_t dms_aktion(char *json, int32_t len) { return aktion(JsonLeser::lies(json, (size_t)len)); }
}
