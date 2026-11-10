// Bereiche und die Liste „was zählt“ des Pakets Compliance (dms-registry #166).
//
// Jede Zeile verbindet den Text in den Paket-Einstellungen (manifest.yaml, zaehlt_<bereich>) mit der Kennung der
// Änderungsart, die der Kern im Vergleich liefert (DMS #1053, z. B. „ablage.feldtyp“). Eine Änderung zählt, wenn ihre
// Kennung gleich ist oder mit „<kennung>.“ beginnt. Die Kennungen sind ein Vorschlag, bis #1053 sie festlegt.
// tests/einstellungen_test.py prüft, dass Texte und Vorauswahl hier und im Manifest gleich sind.
#pragma once
#include <string>
#include <vector>

namespace compliance {

struct Zaehlt {
  const char *text;     // so steht es in den Einstellungen
  const char *kennung;  // Änderungsart im Vergleich des Kerns
  bool vorgabe;         // vorausgewählt (bestätigter Vorschlag)
};

struct Bereich {
  const char *schluessel;  // wie in code.rechte.einrichtung und GET /einrichtung/{bereich}
  const char *name;        // Wert der Auswahl „Bereich“ in den Mappentypen
  std::vector<Zaehlt> zaehlt;
};

// Eigene Änderungsart des Pakets: die Auswahl in diesen Einstellungen selbst (zählt im Bereich Allgemeines).
inline const char *AUSWAHL = "allgemeines.auswahl";

inline const std::vector<Bereich> &bereiche() {
  static const std::vector<Bereich> b = {
      {"allgemeines", "Allgemeines", {
           {"Ablago-Version (Haupt- und Nebenversion)", "allgemeines.version", true},
           {"Patch-Versionen", "allgemeines.patch", false},
           {"„beruflich genutzt“", "allgemeines.beruflich", true},
           {"Angaben der eigenen Organisation", "allgemeines.organisation", true},
           {"Auswahl in diesen Einstellungen", AUSWAHL, true}}},
      {"belegeingang", "Belegeingang und Scannen", {
           {"Eingangsweg hinzugefügt oder entfernt", "belegeingang.eingangsweg", true},
           {"Zielordner bzw. Postfach", "belegeingang.ziel", true},
           {"Trennblatt- und Barcode-Regeln", "belegeingang.trennblatt", true},
           {"Texterkennung an oder aus", "belegeingang.texterkennung", true},
           {"Sprachen der Texterkennung", "belegeingang.texterkennung_sprachen", false},
           {"PDF/A an oder aus", "belegeingang.pdfa", true}}},
      {"ablage", "Ablage", {
           {"Mappentyp neu oder gelöscht", "ablage.mappentyp", true},
           {"Archivmodus, Frist, Stichtag", "ablage.archiv", true},
           {"Feld neu oder entfernt", "ablage.feld", true},
           {"Feldtyp", "ablage.feldtyp", true},
           {"Pflichtfeld", "ablage.pflicht", true},
           {"Versionierung", "ablage.versionierung", true},
           {"An KI übergeben", "ablage.ki", true},
           {"Beschriftung", "ablage.beschriftung", false},
           {"Hilfetext", "ablage.hilfe", false},
           {"Titel-Vorlage", "ablage.titelvorlage", false},
           {"Ansichten und Spalten", "ablage.ansichten", false},
           {"Erkennung und Wiederfinden", "ablage.erkennung", false}}},
      {"zugang", "Zugang und Berechtigungen", {
           {"Zwei-Faktor möglich oder Pflicht", "zugang.zweifaktor", true},
           {"Passkey", "zugang.passkey", true},
           {"Anmeldeschutz", "zugang.anmeldeschutz", true},
           {"WebDAV an oder aus", "zugang.webdav", true},
           {"Schnittstelle an oder aus", "zugang.schnittstelle", true},
           {"Rolle neu oder gelöscht", "zugang.rolle", true},
           {"Rechte-Regeln", "zugang.rechte", true},
           {"Verwaltungsrechte", "zugang.verwaltung", true},
           {"Sitzungsdauer", "zugang.sitzung", false}}},
      {"betrieb", "Betrieb", {
           {"Paket installiert oder entfernt", "betrieb.paket", true},
           {"Paket-Update", "betrieb.paket_update", true},
           {"Rechte eines Pakets", "betrieb.paket_rechte", true},
           {"Automatisierung neu oder gelöscht", "betrieb.automatisierung", true},
           {"Automatisierung geändert", "betrieb.automatisierung_geaendert", false},
           {"KI-Assistent an oder aus", "betrieb.ki", true}}},
      {"sicherung", "Sicherung", {
           {"Zeitplan", "sicherung.zeitplan", true},
           {"Ziel neu oder entfernt", "sicherung.ziel", true},
           {"Verschlüsselung", "sicherung.verschluesselung", true},
           {"Aufbewahrung der Sicherungen", "sicherung.aufbewahrung", true}}},
      {"unveraenderbarkeit", "Unveränderbarkeit", {
           {"Zeitplan „Alle Dateien prüfen“", "unveraenderbarkeit.pruefung", true},
           {"Versionierung je Mappentyp", "unveraenderbarkeit.versionierung", true}}},
      {"datenschutz", "Datenschutz", {
           {"Löschkonzept", "datenschutz.loeschkonzept", true},
           {"Frist des Papierkorbs", "datenschutz.papierkorb", true}}},
      {"betriebspruefung", "Betriebsprüfung", {
           {"Prüferzugang eingerichtet oder entfernt", "betriebspruefung.prueferzugang", true},
           {"Exportformate", "betriebspruefung.export", true}}},
  };
  return b;
}

inline const Bereich *bereich(const std::string &schluessel) {
  for (const Bereich &b : bereiche())
    if (schluessel == b.schluessel) return &b;
  return nullptr;
}

// Zählt eine Änderung mit dieser Kennung bei dieser Auswahl (Kennungen der angehakten Zeilen)?
inline bool zaehlt(const std::string &kennung, const std::vector<std::string> &auswahl) {
  for (const std::string &k : auswahl)
    if (kennung == k || (kennung.size() > k.size() && kennung.compare(0, k.size(), k) == 0 && kennung[k.size()] == '.')) return true;
  return false;
}

}  // namespace compliance
