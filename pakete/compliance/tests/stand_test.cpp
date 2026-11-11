// Tests der Logik des Pakets Compliance (code/stand.h, code/sha256.h). Läuft nativ in code/bauen.sh.
#include <cstdio>
#include <cstring>
#include <string>

#include "sha256.h"
#include "stand.h"

using namespace compliance;

static int fehler = 0, ok = 0;
static void pruefe(const char *name, bool b, const std::string &info = "") {
  if (b) { ok++; printf("ok %s\n", name); }
  else { fehler++; printf("FEHLER %s %s\n", name, info.c_str()); }
}
static Json j(const char *t) { return JsonLeser::lies(t, strlen(t)); }

int main() {
  // SHA-256 (Prüfwerte aus FIPS 180-4)
  pruefe("SHA-256 leer", sha256("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  pruefe("SHA-256 abc", sha256("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  pruefe("SHA-256 zwei Blöcke", sha256("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq") == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");

  // Monate
  pruefe("Monat aus Datum", monat_von("2026-11-10T04:30:00Z") == "2026-11");
  pruefe("Monat ungültig", monat_von("10.11.2026").empty());
  pruefe("Vormonat über Jahreswechsel", monat_plus("2027-01", -1) == "2026-12");
  pruefe("Folgemonat über Jahreswechsel", monat_plus("2026-12", 1) == "2027-01");
  pruefe("Monatsende Februar Schaltjahr", monatsende("2028-02") == "2028-02-29");
  pruefe("Monatsende Februar", monatsende("2027-02") == "2027-02-28");
  auto f = fehlende_monate("2026-10", "2026-11");
  pruefe("Nichts fehlt im laufenden Monat", f.empty());
  f = fehlende_monate("2026-09", "2026-11");
  pruefe("Ein Monat fehlt", f.size() == 1 && f[0] == "2026-10");
  f = fehlende_monate("2024-01", "2026-11", 12);
  pruefe("Höchstens zwölf nachholen, die neuesten", f.size() == 12 && f.front() == "2025-11" && f.back() == "2026-10");

  // Auswahl „was zählt“
  const Bereich &abl = *bereich("ablage");
  auto a = auswahl(abl, j("{}"));
  pruefe("Ohne Einstellung: Vorauswahl", a.size() == 7 && zaehlt("ablage.feldtyp", a) && !zaehlt("ablage.hilfe", a));
  a = auswahl(abl, j("{\"zaehlt_ablage\":[\"Hilfetext\",\"gibt es nicht\"]}"));
  pruefe("Gespeicherte Auswahl gilt", a.size() == 1 && zaehlt("ablage.hilfe", a) && !zaehlt("ablage.feldtyp", a));
  a = auswahl(abl, j("{\"zaehlt_ablage\":[]}"));
  pruefe("Leere Auswahl: nichts zählt", a.empty());
  pruefe("Unterkennung zählt mit", zaehlt("ablage.feld.neu", {"ablage.feld"}));
  pruefe("Ähnlicher Anfang zählt nicht", !zaehlt("ablage.feldtyp", {"ablage.feld"}));

  std::string vorher = auswahl_text(j("{}"));
  std::string nachher = auswahl_text(j("{\"zaehlt_zugang\":[\"Sitzungsdauer\"]}"));
  std::string s = auswahl_aenderung(vorher, nachher);
  pruefe("Auswahl geändert: neu und nicht mehr", s.find("neu „Sitzungsdauer“ (Zugang und Berechtigungen)") != std::string::npos
                                                  && s.find("nicht mehr „") != std::string::npos && s.find("„Passkey“ (Zugang und Berechtigungen)") != std::string::npos, s);
  pruefe("Auswahl gleich: kein Satz", auswahl_aenderung(vorher, vorher).empty());
  pruefe("Erster Lauf: kein Satz", auswahl_aenderung("", nachher).empty());

  // Änderungen
  Json v = j("{\"aenderungen\":["
             "{\"kennung\":\"sicherung.zeitplan\",\"vorher\":\"02:00\",\"nachher\":\"03:00\",\"satz\":\"Zeitplan: täglich 02:00 → täglich 03:00\"},"
             "{\"kennung\":\"ablage.hilfe\",\"satz\":\"Hilfetext an „Betrag“ geändert\"},"
             "{\"kennung\":\"sicherung.ziel.neu\"},"
             "{\"satz\":\"ohne Kennung\"}]}");
  auto z = zaehlende(v, auswahl(*bereich("sicherung"), j("{}")));
  pruefe("Nur was zählt", z.size() == 2 && z[0].kennung == "sicherung.zeitplan" && z[1].satz == "sicherung.ziel.neu");
  pruefe("In Worten", als_text(z) == "• Zeitplan: täglich 02:00 → täglich 03:00\n• sicherung.ziel.neu");
  std::vector<Aenderung> viele(500, {"ablage.feld", "Feld „Ein recht langer Name für ein Feld“ neu"});
  std::string t = als_text(viele);
  pruefe("Viele Änderungen gekürzt", t.size() <= 4000 && t.find("weitere (siehe JSON-Datei)") != std::string::npos);

  // Nachweise
  Json n = j("{\"zahlen\":[{\"bereich\":\"sicherung\",\"name\":\"Sicherungsläufe\",\"wert\":31},{\"bereich\":\"zugang\",\"name\":\"Fehlanmeldungen\",\"wert\":4},"
             "{\"bereich\":\"sicherung\",\"name\":\"fehlgeschlagen\",\"wert\":0},{\"bereich\":\"unbekannt\",\"name\":\"x\",\"wert\":1}],"
             "\"bereiche\":[\"sicherung\",\"zugang\"]}");
  pruefe("Zusammenfassung in der Reihenfolge der Bereiche", zusammenfassung(n) == "Zugang und Berechtigungen: Fehlanmeldungen 4\nSicherung: Sicherungsläufe 31, fehlgeschlagen 0", zusammenfassung(n));
  pruefe("Namen der Bereiche", bereichsnamen(n["bereiche"]) == "Zugang und Berechtigungen, Sicherung");

  printf("%d ok, %d Fehler\n", ok, fehler);
  return fehler ? 1 : 0;
}
