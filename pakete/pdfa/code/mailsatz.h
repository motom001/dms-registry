// Eine E-Mail als Seiten (dms-registry #143, Stufe 1): Kopfblock wie ein Briefkopf (Betreff, Von, An, Cc, Datum),
// der Text (Klartext mit Zitaten bzw. einfaches HTML), Bilder aus der Mail (cid:), am Ende die Liste der Anhänge und
// darunter weitergeleitete Mails (bis zur dritten Ebene). Externe Bilder werden nie geladen – an ihrer Stelle steht
// ein kleiner Platzhalter; Skripte, Stile aus dem Netz und Formulare gibt es nicht.
#pragma once
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "mail.h"
#include "satz.h"
#include "zeichen.h"

namespace mailsatz {

using satz::Element;
using satz::Elemente;
using satz::Lauf;

constexpr double TEXT = 10;      // Grundschrift in pt
constexpr double KLEIN = 8.5;
constexpr double GRAU = 0.42;    // Bezeichnungen, Hinweise

/* ---------- Datum in der Zeitzone der Ablage ---------- */

// Tag im Monat des n-ten (n > 0) bzw. letzten (n = 0) Sonntags.
inline int sonntag(int64_t jahr, unsigned monat, int n) {
  if (n == 0) {
    const unsigned tage = monat == 2 ? 28 : (monat == 4 || monat == 6 || monat == 9 || monat == 11) ? 30 : 31;
    const int64_t t = mail::tageSeit1970(jahr, monat, tage);
    const int wt = (int)(((t % 7) + 7 + 4) % 7);  // 1970-01-01 war ein Donnerstag; 0 = Sonntag
    return (int)tage - wt;
  }
  const int64_t t = mail::tageSeit1970(jahr, monat, 1);
  const int wt = (int)(((t % 7) + 7 + 4) % 7);
  return 1 + (7 - wt) % 7 + 7 * (n - 1);
}

inline void datumAus(int64_t sek, int64_t &jahr, unsigned &monat, unsigned &tag, int &h, int &m) {
  int64_t tage = sek / 86400, rest = sek % 86400;
  if (rest < 0) { rest += 86400; tage--; }
  tage += 719468;
  const int64_t era = (tage >= 0 ? tage : tage - 146096) / 146097;
  const unsigned doe = (unsigned)(tage - era * 146097);
  const unsigned yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  const unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
  const unsigned mp = (5 * doy + 2) / 153;
  tag = doy - (153 * mp + 2) / 5 + 1;
  monat = mp < 10 ? mp + 3 : mp - 9;
  jahr = (int64_t)yoe + era * 400 + (monat <= 2);
  h = (int)(rest / 3600); m = (int)(rest % 3600 / 60);
}

// Versatz einer Zeitzone (IANA) in Minuten zu einem Zeitpunkt: Europa (EU-Sommerzeit), USA, feste Zonen. Unbekannt:
// false (dann zeigt das Paket UTC mit Zusatz).
inline bool versatz(const std::string &zone, int64_t sek, int &minuten) {
  static const char *WEZ[] = {"Europe/London", "Europe/Dublin", "Europe/Lisbon", "Atlantic/Canary", "Atlantic/Madeira", "Atlantic/Faroe", "Europe/Guernsey", "Europe/Jersey", "Europe/Isle_of_Man"};
  static const char *MEZ[] = {"Europe/Berlin", "Europe/Vienna", "Europe/Zurich", "Europe/Paris", "Europe/Rome", "Europe/Madrid", "Europe/Amsterdam", "Europe/Brussels",
                              "Europe/Luxembourg", "Europe/Copenhagen", "Europe/Oslo", "Europe/Stockholm", "Europe/Warsaw", "Europe/Prague", "Europe/Budapest",
                              "Europe/Bratislava", "Europe/Ljubljana", "Europe/Zagreb", "Europe/Belgrade", "Europe/Sarajevo", "Europe/Skopje", "Europe/Tirane",
                              "Europe/Podgorica", "Europe/Vaduz", "Europe/Monaco", "Europe/San_Marino", "Europe/Vatican", "Europe/Andorra", "Europe/Malta",
                              "Europe/Gibraltar", "Europe/Busingen", "Arctic/Longyearbyen", "CET"};
  static const char *OEZ[] = {"Europe/Helsinki", "Europe/Riga", "Europe/Tallinn", "Europe/Vilnius", "Europe/Sofia", "Europe/Bucharest", "Europe/Athens", "Europe/Kiev",
                              "Europe/Kyiv", "Europe/Chisinau", "Asia/Nicosia", "Europe/Mariehamn", "EET"};
  static const struct { const char *z; int m; } FEST[] = {{"UTC", 0}, {"Etc/UTC", 0}, {"GMT", 0}, {"Etc/GMT", 0}, {"Europe/Moscow", 180}, {"Europe/Istanbul", 180},
                                                         {"Europe/Minsk", 180}, {"Europe/Kaliningrad", 120}, {"Asia/Dubai", 240}, {"Asia/Tokyo", 540}, {"Asia/Shanghai", 480},
                                                         {"Asia/Kolkata", 330}, {"Asia/Singapore", 480}};
  static const struct { const char *z; int m; } USA[] = {{"America/New_York", -300}, {"America/Chicago", -360}, {"America/Denver", -420}, {"America/Los_Angeles", -480}};
  int64_t jahr; unsigned mo, t; int h, m;
  datumAus(sek, jahr, mo, t, h, m);
  for (auto &f : FEST) if (zone == f.z) { minuten = f.m; return true; }
  int basis = 9999;
  for (auto z : WEZ) if (zone == z) basis = 0;
  for (auto z : MEZ) if (zone == z) basis = 60;
  for (auto z : OEZ) if (zone == z) basis = 120;
  if (basis != 9999) {
    // EU: letzter Sonntag im März 01:00 UTC bis letzter Sonntag im Oktober 01:00 UTC.
    const int64_t a = mail::tageSeit1970(jahr, 3, (unsigned)sonntag(jahr, 3, 0)) * 86400 + 3600;
    const int64_t e = mail::tageSeit1970(jahr, 10, (unsigned)sonntag(jahr, 10, 0)) * 86400 + 3600;
    minuten = basis + (sek >= a && sek < e ? 60 : 0);
    return true;
  }
  for (auto &u : USA) {
    if (zone != u.z) continue;
    // USA: zweiter Sonntag im März 02:00 Ortszeit bis erster Sonntag im November 02:00 Ortszeit.
    const int64_t a = mail::tageSeit1970(jahr, 3, (unsigned)sonntag(jahr, 3, 2)) * 86400 + 7200 - u.m * 60;
    const int64_t e = mail::tageSeit1970(jahr, 11, (unsigned)sonntag(jahr, 11, 1)) * 86400 + 7200 - (u.m + 60) * 60;
    minuten = u.m + (sek >= a && sek < e ? 60 : 0);
    return true;
  }
  return false;
}

// „02.11.2026, 09:30 Uhr“ in der Zeitzone der Ablage.
inline std::string datum(int64_t sek, const std::string &zone) {
  int v = 0;
  const bool bekannt = versatz(zone, sek, v);
  int64_t jahr; unsigned mo, t; int h, m;
  datumAus(sek + (int64_t)v * 60, jahr, mo, t, h, m);
  char b[64];
  snprintf(b, sizeof b, "%02u.%02u.%04lld, %02d:%02d Uhr%s", t, mo, (long long)jahr, h, m, bekannt ? "" : " (UTC)");
  return b;
}

/* ---------- Anhänge beschreiben ---------- */

inline bool endet(const std::string &s, const char *e) { const size_t n = strlen(e); return s.size() >= n && s.compare(s.size() - n, n, e) == 0; }

inline std::string art(const std::string &name, const std::string &typ) {
  const std::string n = zeichen::klein(name);
  static const struct { const char *e; const char *a; } E[] = {
      {".pdf", "PDF"}, {".docx", "Word"}, {".doc", "Word"}, {".xlsx", "Excel"}, {".xls", "Excel"}, {".pptx", "PowerPoint"}, {".ppt", "PowerPoint"},
      {".odt", "OpenDocument-Text"}, {".ods", "OpenDocument-Tabelle"}, {".odp", "OpenDocument-Präsentation"}, {".rtf", "RTF"}, {".txt", "Text"},
      {".csv", "CSV"}, {".jpg", "Bild (JPEG)"}, {".jpeg", "Bild (JPEG)"}, {".png", "Bild (PNG)"}, {".gif", "Bild (GIF)"}, {".tif", "Bild (TIFF)"},
      {".tiff", "Bild (TIFF)"}, {".heic", "Bild (HEIC)"}, {".webp", "Bild (WebP)"}, {".eml", "E-Mail"}, {".msg", "Outlook-Nachricht"}, {".zip", "ZIP-Archiv"},
      {".ics", "Kalendereintrag"}, {".vcf", "Kontakt"}, {".xml", "XML"}, {".html", "HTML"}, {".htm", "HTML"}, {".p7s", "digitale Signatur"}, {".asc", "Signatur"}};
  for (auto &x : E) if (endet(n, x.e)) return x.a;
  if (typ == "message/rfc822") return "E-Mail";
  if (typ == "application/vnd.ms-outlook") return "Outlook-Nachricht";
  if (typ == "application/pkcs7-signature" || typ == "application/x-pkcs7-signature") return "digitale Signatur";
  if (typ == "application/pgp-signature") return "Signatur";
  if (typ.compare(0, 6, "image/") == 0) return "Bild";
  return typ.empty() ? "Datei" : typ;
}

/* ---------- Der Leser ---------- */

struct Zaehler { int anhaenge = 0, bilder = 0, extern_ = 0, verschluesselt = 0, weitergeleitet = 0; };

class Leser {
 public:
  using Bildwandler = std::function<bool(const std::string &daten, pdfa::Bild &bild)>;

  Leser(satz::Setzer &s, std::string zone, Bildwandler w) : setzer(s), zeitzone(std::move(zone)), wandler(std::move(w)) {}
  Zaehler zaehler;

  // Eine Nachricht (tiefe 0: die Mail selbst; 1–3: weitergeleitete). c: Compound File bei .msg.
  Elemente nachricht(const mail::Nachricht &n, int tiefe, const cfb::Datei *c) {
    Elemente el;
    if (n.verschluesselt) zaehler.verschluesselt++;
    if (tiefe > 0) {
      el.push_back(satz::linie(10, 6));
      Element w = satz::absatz({lauf("Weitergeleitete E-Mail", satz::NORMAL, KLEIN, GRAU)}, 0, 0, 2);
      w.zusammen = 110;  // nicht allein unten auf der Seite
      el.push_back(w);
    }
    const std::string betreff = n.feld("Betreff");
    el.push_back(satz::absatz({lauf(betreff.empty() ? "(ohne Betreff)" : betreff, satz::FETT, tiefe ? 12.5 : 15)}, 0, 0, 6));
    for (const char *f : {"Von", "An", "Cc", "Datum"}) {
      std::string w = n.feld(f);
      if (std::string(f) == "Datum" && n.zeitOk) w = datum(n.zeit, zeitzone);
      if (w.empty()) continue;
      Element z = satz::absatz({lauf(w, satz::NORMAL, 9.5)}, 52, 0, 1.5);
      z.marke = lauf(f, satz::NORMAL, 9, GRAU);
      el.push_back(z);
    }
    el.push_back(satz::linie(5, 10));

    // Bilder mit Content-ID dieser Nachricht (auch in Alternativen).
    std::map<std::string, const mail::Block *> cids;
    sammleCids(n.bloecke, cids);
    std::vector<const mail::Block *> anhaenge, mails;
    std::map<std::string, bool> benutzt;
    for (const mail::Block &b : n.bloecke) block(b, el, cids, benutzt, anhaenge, mails, tiefe, c);
    // Bilder mit Content-ID, die der Text nicht zeigt, sind doch Anhänge.
    std::vector<const mail::Block *> liste;
    for (const mail::Block *a : anhaenge) if (!(a->eingebettet && benutzt.count(a->cid))) liste.push_back(a);
    if (!liste.empty()) {
      Element u = satz::absatz({lauf(liste.size() == 1 ? "Anhang" : "Anhänge (" + std::to_string(liste.size()) + ")", satz::FETT, TEXT)}, 0, 12, 3);
      u.zusammen = 40;
      el.push_back(u);
      for (const mail::Block *a : liste) {
        zaehler.anhaenge++;
        std::string beschreibung = art(a->name, a->typ);
        if (a->msgOrdner < 0) beschreibung += ", " + pdfa::groesse(a->daten.size());
        std::string name = a->name;
        if (name.empty() && a->typ == "message/rfc822") name = "„" + mail::eml(a->daten).feld("Betreff") + "“";
        if (name.empty() && a->msgOrdner >= 0 && c) name = "„" + mail::Msg(*c).text((uint32_t)a->msgOrdner, "0037") + "“";
        if (name.empty() || name == "„“") name = "(ohne Namen)";
        Element z = satz::absatz({lauf(name, satz::NORMAL, 9.5), lauf("  ·  " + beschreibung, satz::NORMAL, 9, GRAU)}, 14, 0, 1.5);
        z.marke = lauf("•", satz::NORMAL, 9.5);
        z.markeX = 3;
        el.push_back(z);
      }
      el.push_back(satz::absatz({lauf("Inhalte der Anhänge stehen nicht in dieser Archivfassung – sie bleiben im Original.", satz::KURSIV, KLEIN, GRAU)}, 0, 3, 4));
    }
    // Weitergeleitete Mails (als Anhang) darunter, bis zur dritten Ebene.
    for (const mail::Block *m : mails) {
      if (tiefe + 1 > mail::TIEFE_MAX) break;
      zaehler.weitergeleitet++;
      if (m->msgOrdner >= 0 && c) anhaengen(el, nachricht(mail::Msg(*c).lies((uint32_t)m->msgOrdner, false), tiefe + 1, c));
      else if (m->msgOrdner < 0) weitergeleitet(m->daten, el, tiefe + 1);
    }
    return el;
  }

  // Eine angehängte Mail (.eml-Text oder .msg-Datei) zerlegen und setzen.
  void weitergeleitet(const std::string &daten, Elemente &el, int tiefe) {
    if (cfb::erkannt((const uint8_t *)daten.data(), daten.size())) {
      auto c = std::make_unique<cfb::Datei>();
      if (c->oeffne((const uint8_t *)daten.data(), daten.size()) && mail::istMsg(*c)) { anhaengen(el, nachricht(mail::Msg(*c).lies(0, true), tiefe, c.get())); return; }
    }
    anhaengen(el, nachricht(mail::eml(daten), tiefe, nullptr));
  }

  static Lauf lauf(const std::string &t, int schnitt = satz::NORMAL, double groesse = TEXT, double grau = 0) {
    Lauf l;
    l.text = t; l.schnitt = schnitt; l.groesse = groesse; l.grau = grau;
    return l;
  }

 private:
  satz::Setzer &setzer;
  std::string zeitzone;
  Bildwandler wandler;
  std::map<const mail::Block *, int> bildIndex;  // schon gepackte Bilder

  static void anhaengen(Elemente &ziel, Elemente &&quelle) { for (auto &e : quelle) ziel.push_back(std::move(e)); }

  static void sammleCids(const std::vector<mail::Block> &l, std::map<std::string, const mail::Block *> &cids) {
    for (const mail::Block &b : l) {
      if (b.art == mail::Block::ANHANG && !b.cid.empty()) cids[zeichen::klein(b.cid)] = &b;
      if (b.art == mail::Block::ALTERNATIVE) { sammleCids(b.schlicht, cids); sammleCids(b.reich, cids); }
    }
  }

  void block(const mail::Block &b, Elemente &el, const std::map<std::string, const mail::Block *> &cids, std::map<std::string, bool> &benutzt,
             std::vector<const mail::Block *> &anhaenge, std::vector<const mail::Block *> &mails, int tiefe, const cfb::Datei *c) {
    switch (b.art) {
      case mail::Block::TEXT: klartext(b.text, el); break;
      case mail::Block::HTML: html(b.text, el, cids, benutzt); break;
      case mail::Block::ALTERNATIVE:
        for (const mail::Block &x : b.reich.empty() ? b.schlicht : b.reich) block(x, el, cids, benutzt, anhaenge, mails, tiefe, c);
        // Anhänge der anderen Fassung trotzdem nennen (ohne doppelte Texte).
        for (const mail::Block &x : b.reich.empty() ? b.reich : b.schlicht) if (x.art == mail::Block::ANHANG) anhaenge.push_back(&x);
        break;
      case mail::Block::VERSCHLUESSELT:
        el.push_back(satz::absatz({lauf("verschlüsselter Teil – nicht lesbar", satz::KURSIV, TEXT, GRAU)}, 0, 4, 6));
        break;
      case mail::Block::NACHRICHT:
        if (tiefe + 1 <= mail::TIEFE_MAX) { zaehler.weitergeleitet++; weitergeleitet(b.daten, el, tiefe + 1); }
        break;
      case mail::Block::ANHANG:
        anhaenge.push_back(&b);
        if (b.typ == "message/rfc822" || b.msgOrdner >= 0 || endet(zeichen::klein(b.name), ".eml") || endet(zeichen::klein(b.name), ".msg")) mails.push_back(&b);
        break;
    }
  }

  /* ---------- Klartext ---------- */

  void klartext(const std::string &t, Elemente &el) {
    size_t i = 0;
    int leer = 0;
    while (i <= t.size()) {
      size_t e = t.find('\n', i);
      if (e == std::string::npos) e = t.size();
      std::string z = t.substr(i, e - i);
      i = e + 1;
      if (!z.empty() && z.back() == '\r') z.pop_back();
      // Zitate: „>“ am Anfang (auch „> > “), je Ebene eingerückt mit Strich.
      int tiefe = 0;
      size_t k = 0;
      while (k < z.size() && (z[k] == '>' || (z[k] == ' ' && k + 1 < z.size() && z[k + 1] == '>'))) { if (z[k] == '>') tiefe++; k++; }
      if (tiefe) { if (k < z.size() && z[k] == ' ') k++; z = z.substr(k); }
      bool nurLeer = z.find_first_not_of(" \t") == std::string::npos;
      if (nurLeer) {
        if (++leer <= 1) el.push_back(satz::abstand(TEXT * 0.6));
      } else {
        leer = 0;
        Element a = satz::absatz({lauf(z)}, 0, 0, 0);
        a.leerraumBehalten = true;
        a.zitat = std::min(tiefe, 6);
        if (tiefe) a.laeufe[0].grau = 0.25;
        el.push_back(a);
      }
      if (e >= t.size()) break;
    }
  }

  /* ---------- HTML ---------- */

  // Bild aus der Mail (cid: oder data:) → Element; liefert false, wenn es sich nicht lesen ließ.
  bool bildElement(const mail::Block *b, const std::string &datenUri, double w, double h, Elemente &el) {
    int index = -1;
    pdfa::Bild bild;
    if (b && bildIndex.count(b)) index = bildIndex[b];
    else {
      const std::string &d = b ? b->daten : datenUri;
      if (!wandler(d, bild)) return false;
      index = (int)setzer.bilder.size();
      setzer.bilder.push_back(std::move(bild));
      if (b) bildIndex[b] = index;
      zaehler.bilder++;
    }
    const pdfa::Bild &x = setzer.bilder[(size_t)index];
    // Größe: Angabe im HTML (CSS-Pixel → pt), sonst die Bildpunkte bei 96 dpi.
    double bw = x.breite * 0.75, bh = x.hoehe * 0.75;
    if (w > 0 && h > 0) { bw = w * 0.75; bh = h * 0.75; }
    else if (w > 0) { bh *= w * 0.75 / bw; bw = w * 0.75; }
    else if (h > 0) { bw *= h * 0.75 / bh; bh = h * 0.75; }
    Element e;
    e.art = Element::BILD; e.bild = index; e.breite = bw; e.hoehe = bh; e.vor = 2; e.nach = 4;
    el.push_back(e);
    return true;
  }

  static std::string attribut(const std::string &tag, const char *name) {
    // tag: alles zwischen < und >; Name klein vergleichen.
    const std::string k = zeichen::klein(tag), n = name;
    for (size_t p = 0; (p = k.find(n, p)) != std::string::npos; p += n.size()) {
      if (p > 0 && !(k[p - 1] == ' ' || k[p - 1] == '\t' || k[p - 1] == '\n' || k[p - 1] == '\r' || k[p - 1] == '"' || k[p - 1] == '\'')) continue;
      size_t i = p + n.size();
      while (i < k.size() && (k[i] == ' ' || k[i] == '\t' || k[i] == '\n' || k[i] == '\r')) i++;
      if (i >= k.size() || k[i] != '=') continue;
      i++;
      while (i < k.size() && (k[i] == ' ' || k[i] == '\t')) i++;
      std::string w;
      if (i < tag.size() && (tag[i] == '"' || tag[i] == '\'')) {
        const char q = tag[i++];
        const size_t e = tag.find(q, i);
        w = tag.substr(i, e == std::string::npos ? std::string::npos : e - i);
      } else {
        size_t e = i;
        while (e < tag.size() && !(tag[e] == ' ' || tag[e] == '\t' || tag[e] == '>' || tag[e] == '/')) e++;
        w = tag.substr(i, e - i);
      }
      std::string r;
      for (size_t j = 0; j < w.size();) {
        if (w[j] == '&') { std::string z; size_t l = zeichen::entitaetLesen(w.data() + j, w.size() - j, z); if (l) { r += z; j += l; continue; } }
        r += w[j++];
      }
      return r;
    }
    return "";
  }

  struct Html {
    Leser &l;
    const std::map<std::string, const mail::Block *> &cids;
    std::map<std::string, bool> &benutzt;
    std::vector<Elemente *> ziel;
    std::vector<Lauf> laeufe;
    bool leerVorne = true;  // letzte Ausgabe war Leerraum (nichts doppelt)
    int fett = 0, kursiv = 0, zitat = 0, pre = 0;
    bool ueberschrift = false;
    double groesse = TEXT;
    std::string marke;
    struct Liste { bool zahlen; int n; };
    std::vector<Liste> listen;
    struct Offen { std::string name; int fett, kursiv; };
    std::vector<Offen> inline_;
    std::vector<std::pair<std::string, std::string>> links;  // Adresse, Text
    struct Tabelle { Element el; bool zelle = false; bool kopf = false; };
    std::vector<std::unique_ptr<Tabelle>> tabellen;

    Html(Leser &l_, const std::map<std::string, const mail::Block *> &c, std::map<std::string, bool> &b, Elemente &el) : l(l_), cids(c), benutzt(b) { ziel.push_back(&el); }

    int schnitt() const { return (fett > 0 ? satz::FETT : 0) | (kursiv > 0 ? satz::KURSIV : 0); }

    void text(const std::string &t, double grau = 0) {
      for (auto &k : links) k.second += t;
      if (!laeufe.empty() && laeufe.back().schnitt == schnitt() && laeufe.back().groesse == groesse && laeufe.back().grau == grau) laeufe.back().text += t;
      else laeufe.push_back(lauf(t, schnitt(), groesse, grau));
    }
    void zeichen(char c) {
      if (!pre && (c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f')) {
        if (leerVorne) return;
        leerVorne = true;
        text(" ");
        return;
      }
      if (pre && c == '\n') { absatz(0); return; }
      if (pre && c == '\r') return;
      leerVorne = false;
      text(std::string(1, c));
    }
    void absatz(double nach = 4, double vor = 0) {
      bool inhalt = false;
      for (auto &x : laeufe) if (x.text.find_first_not_of(' ') != std::string::npos) inhalt = true;
      if (inhalt) {
        while (!laeufe.empty() && !laeufe.back().text.empty() && laeufe.back().text.back() == ' ') { laeufe.back().text.pop_back(); if (laeufe.back().text.empty()) laeufe.pop_back(); }
        Element e = satz::absatz(laeufe, 16.0 * (double)listen.size(), vor, nach);
        e.zitat = std::min(zitat, 6);
        e.leerraumBehalten = pre > 0;
        if (!marke.empty()) { e.marke = lauf(marke, satz::NORMAL, groesse); e.markeX = 16.0 * (double)listen.size() - (marke.size() > 2 ? 15 : 11); marke.clear(); }
        if (ueberschrift) e.zusammen = 50;
        ziel.back()->push_back(e);
      }
      ueberschrift = false;
      laeufe.clear();
      leerVorne = true;
    }
    void zelleZu() {
      if (tabellen.empty() || !tabellen.back()->zelle) return;
      absatz(1);
      ziel.pop_back();
      if (tabellen.back()->kopf) fett--;
      tabellen.back()->zelle = false;
      tabellen.back()->kopf = false;
    }
    void tabelleZu() {
      zelleZu();
      std::unique_ptr<Tabelle> t = std::move(tabellen.back());
      tabellen.pop_back();
      Element &e = t->el;
      // Leere Zeilen und Zellen weg; Layout-Tabellen (eine Spalte), verschachtelte und sehr breite: Zellen nacheinander.
      std::vector<std::vector<Elemente>> zeilen;
      size_t spalten = 0;
      for (auto &z : e.zeilen) {
        std::vector<Elemente> r;
        for (auto &c : z) if (!c.empty()) r.push_back(std::move(c));
        if (!r.empty()) { spalten = std::max(spalten, r.size()); zeilen.push_back(std::move(r)); }
      }
      bool linear = spalten <= 1 || spalten > 6 || !tabellen.empty();
      for (auto &z : zeilen) for (auto &c : z) for (auto &x : c) if (x.art == Element::TABELLE) linear = true;
      if (linear) {
        for (auto &z : zeilen) for (auto &c : z) for (auto &x : c) ziel.back()->push_back(std::move(x));
        return;
      }
      e.zeilen = std::move(zeilen);
      e.vor = 2; e.nach = 6;
      ziel.back()->push_back(std::move(e));
    }

    void tag(const std::string &roh, std::string name, bool zu) {
      if (name == "br") { absatz(0); return; }
      if (name == "p" || name == "div" || name == "section" || name == "article" || name == "header" || name == "footer" || name == "center" ||
          name == "address" || name == "dl" || name == "dt" || name == "dd" || name == "main" || name == "nav" || name == "figure" || name == "figcaption") {
        absatz(name == "p" && zu ? 6 : 2);
        return;
      }
      if (name.size() == 2 && name[0] == 'h' && name[1] >= '1' && name[1] <= '6') {
        absatz(zu ? 4 : 2, zu ? 0 : 6);
        if (!zu) ueberschrift = true;
        if (!zu) { fett++; groesse = name[1] == '1' ? 15 : name[1] == '2' ? 13 : name[1] == '3' ? 11.5 : 10.5; }
        else { if (fett) fett--; groesse = TEXT; }
        return;
      }
      if (name == "ul" || name == "ol") {
        absatz(2);
        if (!zu) listen.push_back({name == "ol", 0});
        else if (!listen.empty()) listen.pop_back();
        return;
      }
      if (name == "li") {
        absatz(1);
        if (!zu) {
          if (listen.empty()) listen.push_back({false, 0});
          Liste &li = listen.back();
          marke = li.zahlen ? std::to_string(++li.n) + "." : "•";
        }
        return;
      }
      if (name == "blockquote") { absatz(2); zitat += zu ? (zitat > 0 ? -1 : 0) : 1; return; }
      if (name == "pre") { absatz(2); pre += zu ? (pre > 0 ? -1 : 0) : 1; return; }
      if (name == "hr") { absatz(2); ziel.back()->push_back(satz::linie(4, 6)); return; }
      if (name == "table") {
        absatz(2);
        if (!zu) {
          auto t = std::make_unique<Tabelle>();
          t->el.art = Element::TABELLE;
          const std::string r = attribut(roh, "border");
          t->el.rahmen = !r.empty() && atoi(r.c_str()) > 0;
          tabellen.push_back(std::move(t));
        } else if (!tabellen.empty()) tabelleZu();
        return;
      }
      if (name == "tr") {
        if (tabellen.empty()) { absatz(1); return; }
        zelleZu();
        if (!zu) tabellen.back()->el.zeilen.emplace_back();
        return;
      }
      if (name == "td" || name == "th") {
        if (tabellen.empty()) { absatz(1); return; }
        zelleZu();
        if (zu) return;
        Tabelle &t = *tabellen.back();
        if (t.el.zeilen.empty()) t.el.zeilen.emplace_back();
        t.el.zeilen.back().emplace_back();
        absatz();
        ziel.push_back(&t.el.zeilen.back().back());
        t.zelle = true;
        if (name == "th") { t.kopf = true; fett++; }
        return;
      }
      if (name == "b" || name == "strong" || name == "i" || name == "em" || name == "cite" || name == "span" || name == "font" || name == "u") {
        if (!zu) {
          int f = name == "b" || name == "strong" ? 1 : 0, k = name == "i" || name == "em" || name == "cite" ? 1 : 0;
          const std::string stil = zeichen::klein(attribut(roh, "style"));
          if (stil.find("font-weight:bold") != std::string::npos || stil.find("font-weight: bold") != std::string::npos || stil.find("font-weight:700") != std::string::npos ||
              stil.find("font-weight: 700") != std::string::npos) f = 1;
          if (stil.find("font-style:italic") != std::string::npos || stil.find("font-style: italic") != std::string::npos) k = 1;
          fett += f; kursiv += k;
          inline_.push_back({name, f, k});
        } else {
          for (size_t i = inline_.size(); i-- > 0;) {
            if (inline_[i].name != name) continue;
            for (size_t j = inline_.size(); j-- > i;) { fett -= inline_[j].fett; kursiv -= inline_[j].kursiv; }
            inline_.resize(i);
            break;
          }
        }
        return;
      }
      if (name == "a") {
        if (!zu) { links.push_back({attribut(roh, "href"), ""}); return; }
        if (links.empty()) return;
        auto k = links.back();
        links.pop_back();
        std::string adr = k.first;
        const std::string kl = zeichen::klein(adr);
        if (kl.compare(0, 7, "mailto:") == 0) adr = adr.substr(7);
        else if (!(kl.compare(0, 7, "http://") == 0 || kl.compare(0, 8, "https://") == 0 || kl.compare(0, 4, "tel:") == 0)) return;
        std::string txt = k.second;
        while (!txt.empty() && txt.back() == ' ') txt.pop_back();
        while (!txt.empty() && txt.front() == ' ') txt.erase(0, 1);
        if (adr.empty() || txt == adr || txt == k.first) return;
        if (adr.size() > 120) adr = adr.substr(0, 117) + "…";
        text(" (" + adr + ")", GRAU);
        leerVorne = false;
        return;
      }
      if (name == "img" && !zu) {
        const std::string src = attribut(roh, "src"), alt = attribut(roh, "alt");
        const double w = atof(attribut(roh, "width").c_str()), h = atof(attribut(roh, "height").c_str());
        const std::string s = zeichen::klein(src);
        if (s.compare(0, 4, "cid:") == 0) {
          auto it = cids.find(zeichen::klein(src.substr(4)));
          if (it != cids.end()) {
            absatz(2);
            if (l.bildElement(it->second, "", w, h, *ziel.back())) { benutzt[it->second->cid] = true; return; }
          }
        } else if (s.compare(0, 5, "data:") == 0 && s.find(";base64,") != std::string::npos && (s.compare(5, 10, "image/png;") == 0 || s.compare(5, 11, "image/jpeg;") == 0 || s.compare(5, 10, "image/gif;") == 0)) {
          const size_t p = src.find(',');
          const std::string d = zeichen::base64(src.data() + p + 1, src.size() - p - 1);
          absatz(2);
          if (l.bildElement(nullptr, d, w, h, *ziel.back())) return;
        } else if ((w > 0 && w <= 3) || (h > 0 && h <= 3)) {
          return;  // Zählpixel: wird ohnehin nie geladen, auch kein Platzhalter
        } else if (s.compare(0, 4, "http") == 0 || s.compare(0, 2, "//") == 0) {
          l.zaehler.extern_++;
        }
        absatz(2);
        Element p;
        p.art = Element::PLATZHALTER;
        std::string a = alt;
        while (!a.empty() && a.back() == ' ') a.pop_back();
        p.laeufe = {lauf(s.compare(0, 4, "cid:") == 0 ? "Bild nicht lesbar" + std::string(a.empty() ? "" : ": " + a) : "externes Bild nicht geladen" + std::string(a.empty() ? "" : ": " + a), satz::KURSIV, KLEIN, GRAU)};
        p.vor = 2; p.nach = 4;
        ziel.back()->push_back(p);
        return;
      }
    }
  };

  void html(const std::string &h, Elemente &el, const std::map<std::string, const mail::Block *> &cids, std::map<std::string, bool> &benutzt) {
    Html x(*this, cids, benutzt, el);
    const char *p = h.data();
    const size_t n = h.size();
    for (size_t i = 0; i < n;) {
      if (p[i] == '<') {
        if (i + 3 < n && !strncmp(p + i, "<!--", 4)) {
          const size_t e = h.find("-->", i + 4);
          i = e == std::string::npos ? n : e + 3;
          continue;
        }
        size_t j = i + 1;
        const bool zu = j < n && p[j] == '/';
        if (zu) j++;
        std::string name;
        while (j < n && name.size() < 16 && ((p[j] >= 'a' && p[j] <= 'z') || (p[j] >= 'A' && p[j] <= 'Z') || (p[j] >= '0' && p[j] <= '9'))) name += p[j++];
        name = zeichen::klein(name);
        size_t e = j;
        char q = 0;
        while (e < n && (q || p[e] != '>')) { if (q && p[e] == q) q = 0; else if (!q && (p[e] == '"' || p[e] == '\'') && (e > 0 && p[e - 1] == '=')) q = p[e]; e++; }
        const std::string roh(p + i + 1, std::min(e, n) - i - 1);
        i = e < n ? e + 1 : n;
        if (name.empty()) continue;  // <!DOCTYPE …>, <?xml …>
        if (!zu && (name == "script" || name == "style" || name == "head" || name == "title" || name == "template" || name == "noscript" ||
                    name == "select" || name == "textarea" || name == "object" || name == "iframe" || name == "svg" || name == "button")) {
          const std::string ende = "</" + name;
          size_t k = i;
          while (k < n) {
            const size_t f = h.find('<', k);
            if (f == std::string::npos) { k = n; break; }
            k = f;
            if (k + ende.size() <= n && zeichen::klein(h.substr(k, ende.size())) == ende) break;
            k++;
          }
          if (k >= n) continue;
          const size_t f = h.find('>', k);
          i = f == std::string::npos ? n : f + 1;
          continue;
        }
        x.tag(roh, name, zu);
        continue;
      }
      if (p[i] == '&') {
        std::string z;
        const size_t l = zeichen::entitaetLesen(p + i, n - i, z);
        if (l) { for (char c : z) x.zeichen(c == ' ' && !x.pre ? ' ' : c); i += l; continue; }
      }
      x.zeichen(p[i]);
      i++;
    }
    x.absatz();
    while (!x.tabellen.empty()) x.tabelleZu();
  }
};

}  // namespace mailsatz
