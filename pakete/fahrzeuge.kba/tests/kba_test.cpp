// Native Tests der Logik (code/kba.h): bauen.sh baut und startet sie, wenn ein C++-Compiler da ist.
// Alle Daten erfunden.
#include <fstream>
#include <iostream>
#include <sstream>

#include "kba.h"

static int fehler = 0;
#define PRUEFE(bed, was) do { if (bed) std::cout << "ok   " << was << "\n"; else { std::cout << "FEHL " << was << "\n"; fehler++; } } while (0)
static std::string datei(const std::string &n) { std::ifstream f(n); std::stringstream s; s << f.rdbuf(); return s.str(); }
static std::string feld(const kba::Ergebnis &e, const std::string &k) { for (auto &f : e.felder) if (f.first == k) return f.second; return ""; }

int main(int argc, char **argv) {
  std::string ordner = argc > 1 ? argv[1] : ".";
  PRUEFE(kba::sha256("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "SHA-256 abc");
  PRUEFE(kba::base64("Ma") == "TWE=" && kba::base64("Man") == "TWFu" && kba::base64("M") == "TQ==", "Base64");
  PRUEFE(kba::altcha_zahl("0123456789abcdef0123456789?expires=1700000000&", "7aac303324e52efe8128a2be2b85285aa4c610c666a2bbb10bbeb86e430ca6d5", 10000) == 4242, "Altcha gelöst");
  PRUEFE(kba::altcha_zahl("x", "00", 50) == -1, "Altcha ohne Lösung");

  auto d = kba::link_zerlegen("https://www.kba-online.de/dub/#/zugriffsdaten/ABCD12EFG3H4/X000000000001/9999");
  PRUEFE(d.suchid == "ABCD12EFG3H4" && d.bericht == "X000000000001" && d.kennnummer == "9999", "QR-Link mit Pfad");
  d = kba::link_zerlegen("https://example.org/dub?dubsuchid=ABCD12EFG3H4&pruefberichtsnummer=X1&kennnummer=9999");
  PRUEFE(d.suchid == "ABCD12EFG3H4" && d.bericht == "X1" && d.kennnummer == "9999", "Link mit Parametern");
  d = kba::link_zerlegen("Such-ID ABCD12EFG3H4");
  PRUEFE(d.suchid == "ABCD12EFG3H4" && d.bericht.empty(), "Such-ID im Text");

  std::string dub = datei(ordner + "/dub_antwort.json");
  Json j = JsonLeser::lies(dub.data(), dub.size());
  Json leer = JsonLeser::lies("{}", 2);
  kba::Ergebnis e = kba::dub_abbilden(j["rueckgabe"], leer);
  PRUEFE(feld(e, "art_untersuchung") == "\"Hauptuntersuchung\"" && feld(e, "typ_untersuchung") == "\"Erstuntersuchung\"", "DUB: Art und Typ");
  PRUEFE(feld(e, "geprueft_am") == "\"2026-11-20\"" && feld(e, "naechste_hu") == "\"2028-11-01\"", "DUB: Datum und nächste HU");
  PRUEFE(feld(e, "ergebnis") == "\"geringe Mängel\"" && feld(e, "kilometerstand") == "81234", "DUB: Ergebnis und Kilometer");
  PRUEFE(feld(e, "pruefplakette") == "true" && feld(e, "wiedervorfuehrung") == "false", "DUB: Plakette und Wiedervorführung");
  PRUEFE(feld(e, "maengel").find("geringer Mangel: Wischerblätter vorn verschlissen (1.2.3)") != std::string::npos &&
             feld(e, "maengel").find("Hinweise:\\nBremsbeläge hinten bald erneuern") != std::string::npos, "DUB: Mängel und Hinweise als Text");
  PRUEFE(feld(e, "kosten") == "{\"betrag\":122.50,\"waehrung\":\"EUR\"}", "DUB: Kosten summiert");
  PRUEFE(feld(e, "hsn") == "\"0603\"" && feld(e, "tsn") == "\"ABC\"" && feld(e, "zul_gesamtmasse") == "1830", "DUB: HSN, TSN, Masse");
  PRUEFE(feld(e, "naechste_sp").empty() && e.notizen.size() == 1, "DUB: keine SP, Hinweis zur Prüfstelle");

  std::string ws = "{\"kilometerstand\":81000,\"ergebnis\":\"geringe Mängel\",\"pruefstelle\":\"id-1\"}";
  Json werte = JsonLeser::lies(ws.data(), ws.size());
  e = kba::dub_abbilden(j["rueckgabe"], werte);
  PRUEFE(feld(e, "kilometerstand").empty() && feld(e, "ergebnis").empty() && e.gleich == 1 && e.abweichend.size() == 1, "DUB: nichts überschreiben");
  PRUEFE(e.meldung("Abgerufen.").find("Kilometerstand: laut KBA 81234, eingetragen 81000") != std::string::npos && e.notizen.empty(), "DUB: Abweichung in der Meldung");
  PRUEFE(kba::ergebnis_auswahl("ohne festgestellte Mängel") == "ohne Mängel" && kba::ergebnis_auswahl("mit festgestellten Mängeln").empty() &&
             kba::ergebnis_auswahl("unmittelbare Verkehrsgefährdung") == "unmittelbare Verkehrsgefährdung", "DUB: Ergebnis-Texte");

  kba::Knoten w1 = kba::XmlLeser::lies(datei(ordner + "/ivi1.xml"));
  PRUEFE(kba::ivi_version(w1) == "1.8.2", "IVI 1.x: Version");
  e = kba::ivi_abbilden(w1, leer, "WMEZZZ00000000001");
  PRUEFE(feld(e, "hsn") == "\"0005\"" && feld(e, "tsn") == "\"ABC\"", "IVI 1.x: HSN/TSN");
  PRUEFE(feld(e, "typgenehmigung") == "\"e1*168/2013*00001*01\"" && feld(e, "hubraum") == "1802", "IVI 1.x: Typgenehmigung, Hubraum");
  PRUEFE(feld(e, "kraftstoff") == "\"Benzin\"" && feld(e, "emissionsklasse") == "\"Euro 5\"" && feld(e, "co2") == "129", "IVI 1.x: Kraftstoff, Euro, CO2");
  PRUEFE(feld(e, "zul_gesamtmasse") == "560", "IVI 1.x: Gesamtmasse");
  PRUEFE(feld(e, "reifengroessen").find("Achse 1: 120/70R19 60V") != std::string::npos && feld(e, "reifengroessen").find("\\nAchse1: 120/70 B21 M/C 68H reinf Achse2") != std::string::npos &&
             feld(e, "reifengroessen").find("Zu 6.18") == std::string::npos, "IVI 1.x: Reifen mit Bemerkungen, ohne „Zu 6.18.1.1.“");
  e = kba::ivi_abbilden(w1, leer, "WVWZZZ00000000009");
  PRUEFE(e.felder.empty() && e.notizen.size() == 1, "IVI: andere FIN → nichts");

  kba::Knoten w2 = kba::XmlLeser::lies(datei(ordner + "/ivi2.xml"));
  PRUEFE(kba::ivi_version(w2) == "2.0", "IVI 2.0: Version");
  e = kba::ivi_abbilden(w2, leer, "WVWZZZ00000000002");
  PRUEFE(feld(e, "hsn").empty() && feld(e, "tsn").empty(), "IVI 2.0: keine HSN/TSN");
  PRUEFE(feld(e, "kraftstoff") == "\"Hybrid Benzin/Elektro\"" && feld(e, "hubraum") == "1498" && feld(e, "co2") == "132", "IVI 2.0: Hybrid, Hubraum, CO2");
  PRUEFE(feld(e, "anhaengelast_gebremst") == "1800" && feld(e, "anhaengelast_ungebremst") == "750" && feld(e, "stuetzlast") == "80", "IVI 2.0: Anhänge- und Stützlast");
  PRUEFE(feld(e, "emissionsklasse") == "\"Euro 6 AP\"" && feld(e, "zul_gesamtmasse") == "2150", "IVI 2.0: Euro, Masse");
  PRUEFE(feld(e, "reifengroessen").find("Achse 1: 215/55 R17 94W") != std::string::npos && feld(e, "reifengroessen").find("225/45 R18 95W XL & Felge") != std::string::npos, "IVI 2.0: Reifen und Bemerkung");

  kba::Knoten w3 = kba::XmlLeser::lies("<InitialVehicleInformation><Header><IviVersionNumberXsd>3.0</IviVersionNumberXsd></Header></InitialVehicleInformation>");
  e = kba::ivi_abbilden(w3, leer, "");
  PRUEFE(!e.notizen.empty() && e.notizen[0].find("neueres Datenformat (3.0)") != std::string::npos, "IVI: unbekannte Version gemeldet");
  PRUEFE(kba::XmlLeser::lies("<a><b>").name.empty() || true, "XML: kaputt ohne Absturz");

  std::cout << (fehler ? "FEHLER: " : "alle ok: ") << fehler << "\n";
  return fehler ? 1 : 0;
}
