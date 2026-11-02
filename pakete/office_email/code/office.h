// Text aus Office-Dateien: Word, Excel und PowerPoint (Office Open XML: .docx, .xlsx, .pptx, auch mit Makros
// .docm/.xlsm/.pptm und Vorlagen) sowie OpenDocument (.odt, .ods, .odp). Gelesen wird nur das XML mit dem Text –
// Makros (vbaProject.bin, Basic/) und eingebettete Objekte (embeddings/, Object …) liest und startet das Paket nie.
#pragma once
#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>
#include <vector>

#include "xml.h"
#include "zeichen.h"
#include "zip.h"

namespace office {

struct Ergebnis {
  std::string art;     // „Word“, „Excel“ … (leer: kein Office-Dokument)
  std::string fehler;  // gesetzt: nicht lesbar (beschädigt, verschlüsselt …)
  int teile = 0;       // Folien bzw. Tabellenblätter
  bool makros = false;
};

// Inhalt von mc:Fallback überspringen (Textfelder stehen sonst doppelt im Text).
struct Fallback {
  int tiefe = 0;
  bool aktiv(const xml::Teil &t) {
    if (xml::lokal(t.name) != "Fallback") return tiefe > 0;
    if (t.art == xml::Teil::AUF && !t.leer) tiefe++;
    else if (t.art == xml::Teil::ZU && tiefe > 0) tiefe--;
    return true;
  }
};

// Beziehungen eines Teils (…/_rels/x.xml.rels): Id → Ziel als Pfad im Archiv.
inline std::map<std::string, std::pair<std::string, std::string>> beziehungen(zip::Archiv &z, const std::string &teil) {
  std::map<std::string, std::pair<std::string, std::string>> r;
  const size_t s = teil.rfind('/');
  const std::string ordner = s == std::string::npos ? "" : teil.substr(0, s + 1);
  std::string x;
  if (!z.lies(ordner + "_rels/" + teil.substr(s == std::string::npos ? 0 : s + 1) + ".rels", x)) return r;
  xml::Leser l(x);
  for (xml::Teil t = l.naechster(); t.art != xml::Teil::ENDE; t = l.naechster()) {
    if (t.art != xml::Teil::AUF || xml::lokal(t.name) != "Relationship") continue;
    std::string ziel = t.attribut("Target");
    if (t.attribut("TargetMode") == "External") continue;
    if (!ziel.empty() && ziel[0] == '/') ziel = ziel.substr(1);
    else {
      std::string pfad = ordner;
      while (ziel.compare(0, 3, "../") == 0) {
        ziel = ziel.substr(3);
        if (!pfad.empty()) pfad.pop_back();
        const size_t k = pfad.rfind('/');
        pfad = k == std::string::npos ? "" : pfad.substr(0, k + 1);
      }
      ziel = pfad + ziel;
    }
    r[t.attribut("Id")] = {ziel, t.attribut("Type")};
  }
  return r;
}

inline bool endetMit(const std::string &s, const char *e) {
  const size_t l = strlen(e);
  return s.size() >= l && !s.compare(s.size() - l, l, e);
}

/* ---------- Word ---------- */

inline void wordTeil(const std::string &x, zeichen::Sammler &s) {
  xml::Leser l(x);
  Fallback fb;
  bool imText = false;
  int zelle = 0;  // in einer Tabellenzelle: Absätze mit Abstand statt Zeile, die Zeile endet mit der Tabellenzeile
  for (xml::Teil t = l.naechster(); t.art != xml::Teil::ENDE && !s.voll; t = l.naechster()) {
    if (fb.aktiv(t)) continue;
    if (t.art == xml::Teil::TEXT) { if (imText) s.text(t.text); continue; }
    const std::string n = t.name;
    if (n == "w:t" || n == "m:t") imText = t.art == xml::Teil::AUF && !t.leer;  // m:t: Text in Formeln
    else if (t.art == xml::Teil::AUF && (n == "w:tab" || n == "w:ptab")) s.tab();
    else if (t.art == xml::Teil::AUF && (n == "w:br" || n == "w:cr")) s.zeile();
    else if (n == "w:tc" && !t.leer) { zelle += t.art == xml::Teil::AUF ? 1 : (zelle > 0 ? -1 : 0); if (t.art == xml::Teil::ZU) s.tab(); }
    else if (t.art == xml::Teil::ZU && n == "w:p") { if (zelle) s.tab(); else s.zeile(); }
    else if (t.art == xml::Teil::ZU && n == "w:tr") s.zeile();
  }
}

inline void word(zip::Archiv &z, zeichen::Sammler &s, Ergebnis &e) {
  std::string x;
  if (!z.lies("word/document.xml", x)) { e.fehler = z.fehler; return; }
  wordTeil(x, s);
  // Danach Fußnoten, Endnoten, Kommentare, Kopf- und Fußzeilen (in der Reihenfolge der Dateinamen).
  std::vector<std::string> weitere;
  for (auto &t : z.eintraege) {
    const std::string &n = t.name;
    if (n.compare(0, 5, "word/") || n.find('/', 5) != std::string::npos || !endetMit(n, ".xml")) continue;
    if (!n.compare(5, 9, "footnotes") || !n.compare(5, 8, "endnotes") || !n.compare(5, 8, "comments") || !n.compare(5, 6, "header") || !n.compare(5, 6, "footer"))
      weitere.push_back(n);
  }
  std::sort(weitere.begin(), weitere.end());
  for (auto &n : weitere) {
    if (s.voll) break;
    if (!z.lies(n, x)) continue;
    s.absatz();
    wordTeil(x, s);
  }
}

/* ---------- Excel ---------- */

inline void excel(zip::Archiv &z, zeichen::Sammler &s, Ergebnis &e) {
  std::string x;
  // Gemeinsame Texte (die meisten Zellen mit Text verweisen darauf).
  std::vector<std::string> texte;
  if (z.lies("xl/sharedStrings.xml", x)) {
    xml::Leser l(x);
    bool imT = false; int phonetik = 0;
    for (xml::Teil t = l.naechster(); t.art != xml::Teil::ENDE; t = l.naechster()) {
      const std::string n = xml::lokal(t.name);
      if (t.art == xml::Teil::TEXT) { if (imT && !phonetik && !texte.empty()) texte.back() += t.text; continue; }
      if (n == "si" && t.art == xml::Teil::AUF) texte.emplace_back();
      else if (n == "t") imT = t.art == xml::Teil::AUF && !t.leer;
      else if (n == "rPh" && !t.leer) phonetik += t.art == xml::Teil::AUF ? 1 : -1;
    }
  }
  if (!z.lies("xl/workbook.xml", x)) { e.fehler = z.fehler; return; }
  auto rel = beziehungen(z, "xl/workbook.xml");
  std::vector<std::pair<std::string, std::string>> blaetter;  // Name, Pfad
  {
    xml::Leser l(x);
    for (xml::Teil t = l.naechster(); t.art != xml::Teil::ENDE; t = l.naechster())
      if (t.art == xml::Teil::AUF && xml::lokal(t.name) == "sheet") {
        auto i = rel.find(t.attribut("r:id"));
        if (i != rel.end()) blaetter.push_back({t.attribut("name"), i->second.first});
      }
  }
  for (auto &b : blaetter) {
    if (s.voll) break;
    if (!z.lies(b.second, x)) continue;  // z. B. Diagrammblatt
    e.teile++;
    if (blaetter.size() > 1) { s.absatz(); s.text(b.first); s.zeile(); }
    xml::Leser l(x);
    std::string typ, wert;
    bool imV = false, imT = false, inZelle = false;
    for (xml::Teil t = l.naechster(); t.art != xml::Teil::ENDE && !s.voll; t = l.naechster()) {
      if (t.art == xml::Teil::TEXT) { if (imV || imT) wert += t.text; continue; }
      const std::string n = xml::lokal(t.name);
      if (n == "c" && t.art == xml::Teil::AUF) { typ = t.attribut("t"); wert.clear(); inZelle = !t.leer; }
      else if (n == "v") imV = t.art == xml::Teil::AUF && !t.leer;
      else if (n == "t") imT = t.art == xml::Teil::AUF && !t.leer;
      else if (n == "c" && t.art == xml::Teil::ZU && inZelle) {
        inZelle = false;
        std::string z2;
        if (typ == "s") {
          char *ende = nullptr;
          const long i = strtol(wert.c_str(), &ende, 10);
          if (ende != wert.c_str() && i >= 0 && (size_t)i < texte.size()) z2 = texte[(size_t)i];
        } else if (typ != "b" && typ != "e") z2 = wert;  // Zahl, Formeltext, Datum (als Zahl), Text in der Zelle
        if (!z2.empty()) { s.text(z2); s.tab(); }
      } else if (n == "row" && t.art == xml::Teil::ZU) s.zeile();
    }
  }
}

/* ---------- PowerPoint ---------- */

inline void folieText(const std::string &x, zeichen::Sammler &s) {
  xml::Leser l(x);
  Fallback fb;
  bool imT = false;
  for (xml::Teil t = l.naechster(); t.art != xml::Teil::ENDE && !s.voll; t = l.naechster()) {
    if (fb.aktiv(t)) continue;
    if (t.art == xml::Teil::TEXT) { if (imT) s.text(t.text); continue; }
    const std::string n = t.name;
    if (n == "a:t") imT = t.art == xml::Teil::AUF && !t.leer;
    else if (n == "a:br" && t.art == xml::Teil::AUF) s.zeile();
    else if (n == "a:p" && t.art == xml::Teil::ZU) s.zeile();
    else if (n == "a:tc" && t.art == xml::Teil::ZU) s.tab();
    else if (n == "a:fld" && t.art == xml::Teil::AUF && t.attribut("type") == "slidenum") imT = false;
  }
}

inline void powerpoint(zip::Archiv &z, zeichen::Sammler &s, Ergebnis &e) {
  std::string x;
  if (!z.lies("ppt/presentation.xml", x)) { e.fehler = z.fehler; return; }
  auto rel = beziehungen(z, "ppt/presentation.xml");
  std::vector<std::string> folien;
  xml::Leser l(x);
  for (xml::Teil t = l.naechster(); t.art != xml::Teil::ENDE; t = l.naechster())
    if (t.art == xml::Teil::AUF && xml::lokal(t.name) == "sldId") {
      auto i = rel.find(t.attribut("r:id"));
      if (i != rel.end()) folien.push_back(i->second.first);
    }
  for (auto &f : folien) {
    if (s.voll) break;
    if (!z.lies(f, x)) continue;
    e.teile++;
    s.absatz();
    folieText(x, s);
    // Notizen zur Folie
    for (auto &r : beziehungen(z, f)) {
      if (!endetMit(r.second.second, "/notesSlide")) continue;
      std::string notiz;
      if (z.lies(r.second.first, notiz)) { s.zeile(); folieText(notiz, s); }
    }
  }
}

/* ---------- OpenDocument ---------- */

inline void openDocument(zip::Archiv &z, zeichen::Sammler &s, Ergebnis &e) {
  std::string x;
  if (z.lies("META-INF/manifest.xml", x) && x.find("encryption-data") != std::string::npos) { e.fehler = "mit einem Passwort verschlüsselt"; return; }
  if (!z.lies("content.xml", x)) { e.fehler = z.fehler; return; }
  xml::Leser l(x);
  int ueberspringen = 0;  // eingebettete Binärdaten, Änderungsverfolgung (gelöschter Text)
  int zelle = 0, absatz = 0;
  for (xml::Teil t = l.naechster(); t.art != xml::Teil::ENDE && !s.voll; t = l.naechster()) {
    const std::string &n = t.name;
    if (n == "office:binary-data" || n == "text:tracked-changes") {
      if (!t.leer) ueberspringen += t.art == xml::Teil::AUF ? 1 : -1;
      continue;
    }
    if (ueberspringen) continue;
    if (t.art == xml::Teil::TEXT) {
      // Nur Text in Absätzen zählt; Zeilenumbrüche im XML sind dort Leerraum (ODF 1.2, 6.1.2).
      if (absatz) for (char c : t.text) s.zeichen(c == '\n' || c == '\r' ? ' ' : c);
      continue;
    }
    if ((n == "text:p" || n == "text:h") && !t.leer) absatz += t.art == xml::Teil::AUF ? 1 : (absatz > 0 ? -1 : 0);
    if (t.art == xml::Teil::AUF) {
      if (n == "text:s") { int c = atoi(t.attribut("text:c").c_str()); for (int i = 0; i < std::max(1, std::min(c, 8)); i++) s.zeichen(' '); }
      else if (n == "text:tab") s.tab();
      else if (n == "text:line-break") s.zeile();
      else if (n == "table:table") { e.teile++; s.absatz(); if (e.art == "OpenDocument-Tabelle") { s.text(t.attribut("table:name")); s.zeile(); } }
      else if (n == "draw:page") { e.teile++; s.absatz(); }
      else if (n == "table:table-cell" && !t.leer) zelle++;
      else if ((n == "text:p" || n == "text:h") && t.leer) s.zeile();
    } else if (t.art == xml::Teil::ZU) {
      if (n == "text:p" || n == "text:h") { if (zelle) s.tab(); else s.zeile(); }
      else if (n == "table:table-cell") { s.tab(); if (zelle > 0) zelle--; }
      else if (n == "table:table-row") s.zeile();
    }
  }
}

/* ---------- Erkennen und lesen ---------- */

// Ein ZIP-Archiv: welches Office-Format? Leer, wenn keins.
inline std::string formatImZip(zip::Archiv &z) {
  if (const zip::Eintrag *m = z.finde("mimetype")) {
    std::string t;
    if (z.lies(*m, t)) {
      if (t.compare(0, 39, "application/vnd.oasis.opendocument.text") == 0) return "OpenDocument-Text";
      if (t.compare(0, 46, "application/vnd.oasis.opendocument.spreadsheet") == 0) return "OpenDocument-Tabelle";
      if (t.compare(0, 47, "application/vnd.oasis.opendocument.presentation") == 0) return "OpenDocument-Präsentation";
    }
  }
  if (z.finde("[Content_Types].xml")) {
    if (z.finde("word/document.xml")) return "Word";
    if (z.finde("xl/workbook.xml")) return "Excel";
    if (z.finde("ppt/presentation.xml")) return "PowerPoint";
  }
  return "";
}

inline Ergebnis lies(const uint8_t *d, size_t n, zeichen::Sammler &s) {
  Ergebnis e;
  zip::Archiv z;
  if (!z.oeffne(d, n)) { e.art = "ZIP"; e.fehler = z.fehler; return e; }
  e.art = formatImZip(z);
  if (e.art.empty()) return e;
  for (auto &t : z.eintraege)
    if (endetMit(t.name, "vbaProject.bin") || t.name.compare(0, 6, "Basic/") == 0 || t.name.compare(0, 8, "Scripts/") == 0) e.makros = true;
  if (e.art == "Word") word(z, s, e);
  else if (e.art == "Excel") excel(z, s, e);
  else if (e.art == "PowerPoint") powerpoint(z, s, e);
  else openDocument(z, s, e);
  return e;
}

}  // namespace office
