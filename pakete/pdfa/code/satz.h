// Seiten setzen: Absätze mit Schnitten (normal, fett, kursiv), Zitate, Listen, einfache Tabellen, Bilder, Linien und
// Platzhalter – auf A4, mit Kopf- und Fußzeile. Ergebnis sind Seiten mit Zeichenbefehlen, die der PDF-Schreiber
// (pdfa.h, Schreiber::freieSeite) als Inhalt schreibt. Für die Archivfassung von E-Mails (dms-registry #143).
//
// Der Text wird mit den eingebetteten Schriften als echter Text gesetzt (Darstellungsart 0): sichtbar, durchsuchbar,
// kopierbar. Zeilen brechen an Wortgrenzen; ein Wort, das allein nicht in eine Zeile passt, bricht zwischen Zeichen.
// Zeichen, die die Schrift nicht hat, werden als Rahmen „□“ gezeichnet (nie „?“, nie die Glyphe .notdef).
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "pdfa.h"
#include "schrift.h"

namespace satz {

enum Schnitt { NORMAL = 0, FETT = 1, KURSIV = 2, FETTKURSIV = 3 };

// Ein Stück Text in einem Schnitt.
struct Lauf {
  std::string text;
  int schnitt = NORMAL;
  double groesse = 10;
  double grau = 0;  // 0 schwarz … 1 weiß
};

struct Element;
using Elemente = std::vector<Element>;

struct Element {
  enum Art { ABSATZ, BILD, LINIE, PLATZHALTER, TABELLE, ABSTAND };
  Art art = ABSATZ;
  // ABSATZ
  std::vector<Lauf> laeufe;
  bool leerraumBehalten = false;  // Klartext: Leerzeichen und Einrückung bleiben stehen
  double einzug = 0;              // links, in pt
  double vor = 0, nach = 4;       // Abstand vor und nach
  double zeilenfaktor = 1.35;
  double zusammen = 0;            // so viel Platz muss noch auf der Seite sein, sonst neue Seite (Überschrift mit dem, was folgt)
  int zitat = 0;                  // Tiefe eines Zitats (senkrechte Striche links)
  Lauf marke;                     // Aufzählungszeichen oder Bezeichnung (Von, An …) in der ersten Zeile …
  double markeX = 0;              // … so weit rechts von x (innerhalb des Einzugs)
  // BILD (Index in die Bilderliste des Setzers) und PLATZHALTER
  int bild = -1;
  double breite = 0, hoehe = 0;   // pt
  // TABELLE: Zeilen mit Zellen, jede Zelle eine Folge von Elementen
  std::vector<std::vector<Elemente>> zeilen;
  bool rahmen = false;
};

inline Element absatz(std::vector<Lauf> l, double einzug = 0, double vor = 0, double nach = 4) {
  Element e;
  e.laeufe = std::move(l);
  e.einzug = einzug; e.vor = vor; e.nach = nach;
  return e;
}
inline Element abstand(double pt) { Element e; e.art = Element::ABSTAND; e.hoehe = pt; return e; }
inline Element linie(double vor = 4, double nach = 8) { Element e; e.art = Element::LINIE; e.vor = vor; e.nach = nach; return e; }

/* ---------- Zeichenbefehle einer Seite ---------- */

struct Befehl {
  enum Art { TEXT, BILD, LINIE, RAHMEN };
  Art art = TEXT;
  double x = 0, y = 0, b = 0, h = 0;  // y von oben; bei TEXT die Grundlinie
  int schnitt = 0;
  double groesse = 0, grau = 0;
  std::string hex;                     // TEXT: GIDs als Hex (Identity-H)
  int bild = -1;
};

struct Seite {
  std::vector<Befehl> befehle;
  std::vector<int> bilder;  // benutzte Bilder (Index)
};

/* ---------- Der Setzer ---------- */

struct Rand { double oben = 64, unten = 64, links = 56, rechts = 56; };

class Setzer {
 public:
  static constexpr double BREITE = 595.276, HOEHE = 841.89;  // A4 in pt
  Rand rand;
  std::vector<pdfa::Bild> bilder;      // fertig gepackt, für den Schreiber
  std::vector<Seite> seiten;
  schrift::Schrift *schriften[4] = {nullptr, nullptr, nullptr, nullptr};
  size_t seitenMax = 1000;
  bool zuViel = false;

  double innenBreite() const { return BREITE - rand.links - rand.rechts; }

  void setze(const Elemente &el) {
    if (seiten.empty()) neueSeite();
    for (const Element &e : el) { if (zuViel) return; element(e, rand.links, innenBreite()); }
  }

  // Kopf- und Fußzeile auf alle Seiten (nach dem Setzen, wenn die Seitenzahl feststeht).
  void kopfUndFuss(const std::string &kopf) {
    const size_t n = seiten.size();
    for (size_t i = 0; i < n; i++) {
      Seite &s = seiten[i];
      const double g = 8;
      if (!kopf.empty()) {
        std::string k = kuerze(kopf, NORMAL, g, innenBreite());
        zeichneText(s, k, NORMAL, g, 0.45, rand.links, rand.oben - 30);
        Befehl l; l.art = Befehl::LINIE; l.x = rand.links; l.y = rand.oben - 24; l.b = innenBreite(); l.grau = 0.75; l.groesse = 0.4;
        s.befehle.push_back(l);
      }
      const std::string fuss = "Seite " + std::to_string(i + 1) + " von " + std::to_string(n);
      const double b = textBreite(fuss, NORMAL, g);
      zeichneText(s, fuss, NORMAL, g, 0.45, BREITE - rand.rechts - b, HOEHE - rand.unten + 30);
    }
  }

  double textBreite(const std::string &t, int sch, double g) const {
    double b = 0;
    const schrift::Schrift &f = *schriften[sch];
    for (size_t i = 0; i < t.size();) {
      const uint32_t u = schrift::naechstes(t, i);
      if (u < 0x20) continue;
      const uint16_t gid = f.gid(u);
      b += gid ? f.breite(gid) * g / 1000.0 : 0.6 * g;
    }
    return b;
  }

  // Text auf eine Breite kürzen („…“ am Ende).
  std::string kuerze(const std::string &t, int sch, double g, double max) const {
    if (textBreite(t, sch, g) <= max) return t;
    std::string r;
    for (size_t i = 0; i < t.size();) {
      size_t a = i;
      schrift::naechstes(t, i);
      if (textBreite(r + t.substr(a, i - a) + "…", sch, g) > max) break;
      r += t.substr(a, i - a);
    }
    return r + "…";
  }

 private:
  double y = 0;  // nächste freie Stelle von oben

  Seite &seite() { return seiten.back(); }
  double unten() const { return HOEHE - rand.unten; }
  bool neueSeite() {
    if (seiten.size() >= seitenMax) { zuViel = true; return false; }
    seiten.emplace_back();
    y = rand.oben;
    return true;
  }
  // Platz für h pt? Sonst neue Seite (nur, wenn auf dieser Seite schon etwas steht).
  bool platz(double h) {
    if (y + h <= unten() + 0.01) return true;
    if (y > rand.oben + 0.01) return neueSeite();
    return true;
  }

  void zeichneText(Seite &s, const std::string &t, int sch, double g, double grau, double x, double grund) {
    schrift::Schrift &f = *schriften[sch];
    static const char *H = "0123456789ABCDEF";
    Befehl b;
    b.art = Befehl::TEXT; b.schnitt = sch; b.groesse = g; b.grau = grau; b.x = x; b.y = grund;
    auto abschliessen = [&]() {
      if (!b.hex.empty()) s.befehle.push_back(b);
      b.hex.clear();
    };
    double cx = x;
    for (size_t i = 0; i < t.size();) {
      const uint32_t u = schrift::naechstes(t, i);
      if (u < 0x20 || u == 0x7f) continue;
      const uint16_t gid = f.gid(u);
      if (gid) {
        if (b.hex.empty()) b.x = cx;
        f.merke(gid, u);
        for (int k = 12; k >= 0; k -= 4) b.hex += H[(gid >> k) & 15];
        cx += f.breite(gid) * g / 1000.0;
      } else {
        abschliessen();
        Befehl r;
        r.art = Befehl::RAHMEN; r.x = cx + 0.08 * g; r.y = grund - 0.62 * g; r.b = 0.44 * g; r.h = 0.62 * g; r.grau = grau; r.groesse = std::max(0.4, g / 20);
        s.befehle.push_back(r);
        cx += 0.6 * g;
      }
    }
    abschliessen();
  }

  /* ---------- Zeilen bauen ---------- */

  struct Stueck { Lauf lauf; bool leer; double breite; };
  struct Zeile { std::vector<Stueck> teile; double breite = 0, hoehe = 0; };

  // Ein Lauf in Wörter und Leerräume zerlegen.
  void zerlege(const Lauf &l, bool behalten, std::vector<Stueck> &aus) const {
    std::string cur;
    int art = -1;  // 0 Wort, 1 Leerraum
    auto weg = [&]() {
      if (cur.empty()) return;
      Lauf x = l;
      x.text = cur;
      aus.push_back({x, art == 1, textBreite(cur, l.schnitt, l.groesse)});
      cur.clear();
    };
    for (size_t i = 0; i < l.text.size();) {
      size_t a = i;
      uint32_t u = schrift::naechstes(l.text, i);
      const bool leer = u == ' ' || u == '\t';
      if (u == '\t') { weg(); art = 1; cur = behalten ? "    " : " "; weg(); continue; }
      if ((leer ? 1 : 0) != art) { weg(); art = leer ? 1 : 0; }
      cur += l.text.substr(a, i - a);
    }
    weg();
  }

  std::vector<Zeile> umbreche(const Element &e, double breite) const {
    std::vector<Stueck> st;
    for (const Lauf &l : e.laeufe) zerlege(l, e.leerraumBehalten, st);
    std::vector<Zeile> zeilen(1);
    for (size_t i = 0; i < st.size(); i++) {
      Stueck s = st[i];
      Zeile &z = zeilen.back();
      if (s.leer) {
        if (z.teile.empty() && zeilen.size() > 1) continue;            // Leerraum am Anfang einer umbrochenen Zeile
        if (!e.leerraumBehalten && z.teile.empty()) continue;         // HTML: kein Leerraum am Absatzanfang
        z.teile.push_back(s); z.breite += s.breite;
        continue;
      }
      if (z.breite + s.breite <= breite + 0.01 || z.teile.empty()) {
        if (s.breite > breite && z.teile.empty()) {
          // Ein Wort, breiter als die Zeile: zwischen Zeichen brechen.
          std::string rest = s.lauf.text;
          while (!rest.empty()) {
            std::string teil;
            size_t i2 = 0;
            while (i2 < rest.size()) {
              size_t a = i2;
              schrift::naechstes(rest, i2);
              if (!teil.empty() && textBreite(teil + rest.substr(a, i2 - a), s.lauf.schnitt, s.lauf.groesse) > breite) { i2 = a; break; }
              teil += rest.substr(a, i2 - a);
            }
            Stueck t = s;
            t.lauf.text = teil;
            t.breite = textBreite(teil, s.lauf.schnitt, s.lauf.groesse);
            zeilen.back().teile.push_back(t);
            zeilen.back().breite += t.breite;
            rest = rest.substr(teil.size());
            if (!rest.empty()) zeilen.emplace_back();
          }
          continue;
        }
        z.teile.push_back(s); z.breite += s.breite;
        continue;
      }
      // Umbrechen: Leerraum am Zeilenende fällt weg.
      while (!z.teile.empty() && z.teile.back().leer) { z.breite -= z.teile.back().breite; z.teile.pop_back(); }
      zeilen.emplace_back();
      i--;  // dasselbe Wort in der neuen Zeile
    }
    for (Zeile &z : zeilen) {
      double g = 0;
      for (auto &s : z.teile) g = std::max(g, s.lauf.groesse);
      if (g == 0) g = e.laeufe.empty() ? 10 : e.laeufe[0].groesse;
      z.hoehe = g * e.zeilenfaktor;
    }
    return zeilen;
  }

  /* ---------- Elemente ---------- */

  void element(const Element &e, double x, double breite) {
    switch (e.art) {
      case Element::ABSTAND: y += e.hoehe; if (y > unten()) neueSeite(); return;
      case Element::LINIE: {
        y += e.vor;
        if (!platz(e.nach)) return;
        Befehl l; l.art = Befehl::LINIE; l.x = x; l.y = y; l.b = breite; l.grau = 0.7; l.groesse = 0.5;
        seite().befehle.push_back(l);
        y += e.nach;
        return;
      }
      case Element::BILD: bild(e, x, breite); return;
      case Element::PLATZHALTER: platzhalter(e, x, breite); return;
      case Element::TABELLE: tabelle(e, x, breite); return;
      case Element::ABSATZ: absatzSetzen(e, x, breite); return;
    }
  }

  void absatzSetzen(const Element &e, double x, double breite) {
    const double zitatBreite = 9.0 * e.zitat;
    const double links = x + e.einzug + zitatBreite, b = std::max(40.0, breite - e.einzug - zitatBreite);
    std::vector<Zeile> zeilen = umbreche(e, b);
    y += e.vor;
    if (e.zusammen > 0) platz(e.zusammen);
    bool erste = true;
    for (const Zeile &z : zeilen) {
      if (!platz(z.hoehe)) return;
      const double g = z.hoehe / e.zeilenfaktor;
      const double grund = y + z.hoehe - (z.hoehe - g) / 2 - 0.22 * g;
      for (int k = 0; k < e.zitat; k++) {
        Befehl l; l.art = Befehl::LINIE; l.x = x + e.einzug + 9.0 * k + 2; l.y = y; l.b = 0; l.h = z.hoehe; l.grau = 0.6; l.groesse = 1.2;
        seite().befehle.push_back(l);
      }
      if (erste && !e.marke.text.empty()) zeichneText(seite(), e.marke.text, e.marke.schnitt, e.marke.groesse, e.marke.grau, x + zitatBreite + e.markeX, grund);
      double cx = links;
      for (const Stueck &s : z.teile) {
        if (!s.leer) zeichneText(seite(), s.lauf.text, s.lauf.schnitt, s.lauf.groesse, s.lauf.grau, cx, grund);
        cx += s.breite;
      }
      y += z.hoehe;
      erste = false;
    }
    y += e.nach;
  }

  void bild(const Element &e, double x, double breite) {
    if (e.bild < 0 || e.bild >= (int)bilder.size()) return;
    double b = e.breite, h = e.hoehe;
    if (b > breite) { h *= breite / b; b = breite; }
    const double max = unten() - rand.oben;
    if (h > max) { b *= max / h; h = max; }
    y += e.vor;
    if (!platz(h)) return;
    Befehl c; c.art = Befehl::BILD; c.x = x; c.y = y; c.b = b; c.h = h; c.bild = e.bild;
    seite().befehle.push_back(c);
    if (std::find(seite().bilder.begin(), seite().bilder.end(), e.bild) == seite().bilder.end()) seite().bilder.push_back(e.bild);
    y += h + e.nach;
  }

  void platzhalter(const Element &e, double x, double breite) {
    Element t = e;
    t.art = Element::ABSATZ;
    const double g = e.laeufe.empty() ? 8.5 : e.laeufe[0].groesse;
    const double b = std::min(breite, textBreite(e.laeufe.empty() ? "" : e.laeufe[0].text, e.laeufe.empty() ? KURSIV : e.laeufe[0].schnitt, g) + 12);
    std::vector<Zeile> zeilen = umbreche(t, b - 12);
    const double h = 8 + zeilen.size() * g * t.zeilenfaktor;
    y += e.vor;
    if (!platz(h)) return;
    Befehl r; r.art = Befehl::RAHMEN; r.x = x; r.y = y; r.b = b; r.h = h; r.grau = 0.6; r.groesse = 0.6;
    seite().befehle.push_back(r);
    double zy = y + 4;
    for (const Zeile &z : zeilen) {
      const double grund = zy + z.hoehe - (z.hoehe - g) / 2 - 0.22 * g;
      double cx = x + 6;
      for (const Stueck &s : z.teile) { if (!s.leer) zeichneText(seite(), s.lauf.text, s.lauf.schnitt, s.lauf.groesse, s.lauf.grau, cx, grund); cx += s.breite; }
      zy += z.hoehe;
    }
    y += h + e.nach;
  }

  // Höhe eines Elements in einer bestimmten Breite (nur für Tabellenzellen: Absätze, Platzhalter, Bilder, Linien).
  double hoeheVon(const Element &e, double breite) const {
    switch (e.art) {
      case Element::ABSTAND: return e.hoehe;
      case Element::LINIE: return e.vor + e.nach;
      case Element::BILD: { double b = e.breite, h = e.hoehe; if (b > breite) h *= breite / b; return e.vor + h + e.nach; }
      case Element::PLATZHALTER: {
        const double g = e.laeufe.empty() ? 8.5 : e.laeufe[0].groesse;
        Element t = e; t.art = Element::ABSATZ;
        return e.vor + 8 + umbreche(t, std::max(20.0, breite - 12)).size() * g * t.zeilenfaktor + e.nach;
      }
      case Element::TABELLE: {
        double h = 0;
        for (auto &z : e.zeilen) for (auto &c : z) for (auto &x : c) h += hoeheVon(x, breite);
        return h;
      }
      case Element::ABSATZ: {
        double h = e.vor + e.nach;
        for (auto &z : umbreche(e, std::max(40.0, breite - e.einzug - 9.0 * e.zitat))) h += z.hoehe;
        return h;
      }
    }
    return 0;
  }

  void tabelle(const Element &e, double x, double breite) {
    size_t spalten = 0;
    for (auto &z : e.zeilen) spalten = std::max(spalten, z.size());
    if (!spalten) return;
    const double polster = 4;
    const double sb = breite / (double)spalten;
    y += e.vor;
    for (auto &z : e.zeilen) {
      double h = 0;
      for (auto &c : z) {
        double ch = 0;
        for (auto &el : c) ch += hoeheVon(el, sb - 2 * polster);
        h = std::max(h, ch);
      }
      h += 2 * polster;
      const double max = unten() - rand.oben;
      if (h > max) {
        // Zeile höher als eine Seite: Zellen nacheinander setzen.
        for (auto &c : z) for (auto &el : c) element(el, x, breite);
        continue;
      }
      if (!platz(h)) return;
      const double oben = y;
      const size_t seitenVorher = seiten.size();
      for (size_t i = 0; i < z.size(); i++) {
        if (seiten.size() != seitenVorher) { for (auto &el : z[i]) element(el, x, breite); continue; }  // nur bei falsch geschätzter Höhe
        y = oben + polster;
        for (auto &el : z[i]) element(el, x + sb * (double)i + polster, sb - 2 * polster);
        if (e.rahmen && seiten.size() == seitenVorher) {
          Befehl r; r.art = Befehl::RAHMEN; r.x = x + sb * (double)i; r.y = oben; r.b = sb; r.h = h; r.grau = 0.7; r.groesse = 0.5;
          seite().befehle.push_back(r);
        }
      }
      if (seiten.size() == seitenVorher) y = oben + h;
    }
    y += e.nach;
  }
};

/* ---------- Seiteninhalt als PDF ---------- */

// Zeichenbefehle einer Seite → Inhaltsstrom (Schriften /F0–/F3, Bilder /Im<n>).
inline std::string inhalt(const Seite &s) {
  std::string c;
  const double H = Setzer::HOEHE;
  std::string text;
  int schnitt = -1;
  double groesse = -1, grau = -1;
  auto textEnde = [&]() {
    if (!text.empty()) { c += "BT\n" + text + "ET\n"; text.clear(); schnitt = -1; groesse = -1; grau = -1; }
  };
  for (const Befehl &b : s.befehle) {
    switch (b.art) {
      case Befehl::TEXT:
        if (schnitt != b.schnitt || groesse != b.groesse) { text += "/F" + std::to_string(b.schnitt) + " " + pdfa::zahl(b.groesse, 2) + " Tf\n"; schnitt = b.schnitt; groesse = b.groesse; }
        if (grau != b.grau) { text += pdfa::zahl(b.grau, 3) + " g\n"; grau = b.grau; }
        text += "1 0 0 1 " + pdfa::zahl(b.x, 2) + " " + pdfa::zahl(H - b.y, 2) + " Tm <" + b.hex + "> Tj\n";
        break;
      case Befehl::BILD:
        textEnde();
        c += "q " + pdfa::zahl(b.b, 3) + " 0 0 " + pdfa::zahl(b.h, 3) + " " + pdfa::zahl(b.x, 2) + " " + pdfa::zahl(H - b.y - b.h, 2) + " cm /Im" + std::to_string(b.bild) + " Do Q\n";
        break;
      case Befehl::LINIE:
        textEnde();
        c += "q " + pdfa::zahl(b.grau, 3) + " G " + pdfa::zahl(b.groesse, 2) + " w " + pdfa::zahl(b.x, 2) + " " + pdfa::zahl(H - b.y, 2) + " m " +
             pdfa::zahl(b.x + b.b, 2) + " " + pdfa::zahl(H - b.y - b.h, 2) + " l S Q\n";
        break;
      case Befehl::RAHMEN:
        textEnde();
        c += "q " + pdfa::zahl(b.grau, 3) + " G " + pdfa::zahl(b.groesse, 2) + " w " + pdfa::zahl(b.x, 2) + " " + pdfa::zahl(H - b.y - b.h, 2) + " " +
             pdfa::zahl(b.b, 2) + " " + pdfa::zahl(b.h, 2) + " re S Q\n";
        break;
    }
  }
  textEnde();
  return c;
}

/* ---------- Schriften als PDF ---------- */

// Eine Schrift als Type0/CIDFontType2 mit Teilmenge, Breiten (W) und ToUnicode; nr ist die vorher reservierte Nummer
// der Type0-Schrift. Kennung: sechs Großbuchstaben vor dem Namen, wie PDF es für Teilmengen verlangt.
inline void schreibeSchrift(pdfa::Schreiber &pdf, int nr, const schrift::Schrift &s, const std::string &kennung) {
  const int cid = pdf.neuesObjekt(), beschreibung = pdf.neuesObjekt(), datei = pdf.neuesObjekt(), unicode = pdf.neuesObjekt();
  const std::string name = kennung + "+" + s.name;
  pdf.woerterbuch(nr, "<< /Type /Font /Subtype /Type0 /BaseFont /" + name + " /Encoding /Identity-H /DescendantFonts [" + std::to_string(cid) +
                          " 0 R] /ToUnicode " + std::to_string(unicode) + " 0 R >>");
  std::string w;
  for (uint16_t g : s.benutzt) w += std::to_string(g) + " [" + pdfa::zahl(s.breite(g), 3) + "] ";
  pdf.woerterbuch(cid, "<< /Type /Font /Subtype /CIDFontType2 /BaseFont /" + name + " /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
                       "/FontDescriptor " + std::to_string(beschreibung) + " 0 R /DW 1000 /W [ " + w + "] /CIDToGIDMap /Identity >>");
  const double f = 1000.0 / s.einheiten;
  const int flags = 32 | (s.kursiv ? 64 : 0);
  pdf.woerterbuch(beschreibung, "<< /Type /FontDescriptor /FontName /" + name + " /Flags " + std::to_string(flags) + " /FontBBox [" + pdfa::zahl(s.box[0] * f, 0) + " " +
                                    pdfa::zahl(s.box[1] * f, 0) + " " + pdfa::zahl(s.box[2] * f, 0) + " " + pdfa::zahl(s.box[3] * f, 0) + "] /ItalicAngle " + pdfa::zahl(s.neigung, 2) +
                                    " /Ascent " + pdfa::zahl(s.oben * f, 0) + " /Descent " + pdfa::zahl(s.unten * f, 0) + " /CapHeight " + pdfa::zahl(s.versal * f, 0) +
                                    " /StemV " + (s.fett ? "120" : "80") + " /FontWeight " + (s.fett ? "700" : "400") + " /FontFile2 " + std::to_string(datei) + " 0 R >>");
  const std::vector<uint8_t> teil = s.teilmenge();
  pdf.stromObjekt(datei, "/Length1 " + std::to_string(teil.size()), pdfa::packe(teil.data(), teil.size()), true);
  static const char *H = "0123456789ABCDEF";
  auto hex4 = [&](unsigned v) { std::string r; for (int k = 12; k >= 0; k -= 4) r += H[(v >> k) & 15]; return r; };
  std::string zeilen;
  std::vector<std::string> eintraege;
  for (auto &z : s.zeichen) {
    std::string u;
    if (z.second >= 0x10000) { const unsigned v = z.second - 0x10000; u = hex4(0xD800 | (v >> 10)) + hex4(0xDC00 | (v & 0x3FF)); }
    else u = hex4(z.second);
    eintraege.push_back("<" + hex4(z.first) + "> <" + u + ">\n");
  }
  for (size_t i = 0; i < eintraege.size(); i += 100) {
    const size_t n = std::min<size_t>(100, eintraege.size() - i);
    zeilen += std::to_string(n) + " beginbfchar\n";
    for (size_t k = 0; k < n; k++) zeilen += eintraege[i + k];
    zeilen += "endbfchar\n";
  }
  const std::string cmap =
      "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
      "/CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n" + zeilen +
      "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n";
  pdf.stromObjekt(unicode, "", pdfa::packe(reinterpret_cast<const uint8_t *>(cmap.data()), cmap.size()), true);
}

}  // namespace satz
