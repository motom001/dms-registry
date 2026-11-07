// Dateityp am Inhalt erkennen (nicht am Namen) und den Text herauslösen.
#pragma once
#include <string>

#include "cfb.h"
#include "mailtext.h"
#include "office.h"
#include "rtf.h"
#include "zeichen.h"

namespace erkennen {

struct Gelesen {
  std::string art;     // „Word“, „E-Mail“ … – leer: kein Typ, den das Paket liest
  std::string fehler;  // gesetzt: Typ erkannt, aber nicht lesbar (beschädigt, verschlüsselt, altes Format)
  bool kern = false;   // PDF, JPEG oder PNG: liest das DMS selbst
  bool makros = false;
  bool verschluesselt = false;
  int teile = 0;       // Folien bzw. Tabellenblätter
  int anhaenge = 0;
};

inline bool istText(const uint8_t *d, size_t n) {
  const size_t m = std::min<size_t>(n, 65536);
  size_t steuer = 0;
  for (size_t i = 0; i < m; i++) {
    if (d[i] == 0) return false;
    if (d[i] < 0x20 && d[i] != '\n' && d[i] != '\r' && d[i] != '\t' && d[i] != '\f') steuer++;
  }
  return steuer * 100 <= m;  // höchstens 1 % Steuerzeichen
}

// `emlHinweis`: Dateityp oder Endung sagen „E-Mail“ (nur ein Hinweis – der Inhalt entscheidet).
inline Gelesen lies(const uint8_t *d, size_t n, zeichen::Sammler &s, int tiefe = 0, bool emlHinweis = false) {
  Gelesen g;
  if ((n >= 5 && !memcmp(d, "%PDF-", 5)) || (n >= 3 && d[0] == 0xff && d[1] == 0xd8 && d[2] == 0xff) || (n >= 8 && !memcmp(d, "\x89PNG\r\n\x1a\n", 8))) {
    g.kern = true;
    return g;
  }
  if (n >= 4 && d[0] == 'P' && d[1] == 'K' && ((d[2] == 3 && d[3] == 4) || (d[2] == 5 && d[3] == 6))) {
    office::Ergebnis e = office::lies(d, n, s);
    if (e.art == "ZIP") { g.art = "ZIP-Archiv"; g.fehler = e.fehler; return g; }
    g.art = e.art; g.fehler = e.fehler; g.teile = e.teile; g.makros = e.makros;
    return g;
  }
  if (cfb::erkannt(d, n)) {
    cfb::Datei c;
    if (!c.oeffne(d, n)) { g.art = "Office- oder Outlook-Datei"; g.fehler = c.fehler; return g; }
    if (c.finde(0, "EncryptedPackage") >= 0) { g.art = "Office-Datei"; g.fehler = "mit einem Passwort verschlüsselt"; g.verschluesselt = true; return g; }
    if (mail::istMsg(c)) {
      g.art = "Outlook-Nachricht";
      mailtext::Ergebnis e = mailtext::msg(c, s, tiefe);
      g.anhaenge = e.anhaenge;
      g.verschluesselt = e.verschluesselt;
      return g;
    }
    if (c.finde(0, "WordDocument") >= 0) { g.art = "Word 97–2003 (.doc)"; g.fehler = "das alte Word-Format liest das Paket nicht – in Word als .docx speichern"; return g; }
    if (c.finde(0, "Workbook") >= 0 || c.finde(0, "Book") >= 0) { g.art = "Excel 97–2003 (.xls)"; g.fehler = "das alte Excel-Format liest das Paket nicht – als .xlsx speichern"; return g; }
    if (c.finde(0, "PowerPoint Document") >= 0) { g.art = "PowerPoint 97–2003 (.ppt)"; g.fehler = "das alte PowerPoint-Format liest das Paket nicht – als .pptx speichern"; return g; }
    return g;
  }
  if (rtf::erkannt(d, n)) {
    g.art = "RTF";
    rtf::lies(std::string((const char *)d, n), s);
    return g;
  }
  if (mail::istEml(d, n, emlHinweis)) {
    g.art = "E-Mail";
    mailtext::Ergebnis e = mailtext::eml(std::string((const char *)d, n), s, tiefe);
    g.anhaenge = e.anhaenge;
    g.verschluesselt = e.verschluesselt;
    return g;
  }
  // Text: UTF-16 mit BOM, UTF-8 (mit oder ohne BOM), sonst Windows-1252.
  if (n >= 2 && ((d[0] == 0xff && d[1] == 0xfe) || (d[0] == 0xfe && d[1] == 0xff))) {
    g.art = "Text";
    s.text(d[0] == 0xff ? zeichen::utf16le(d + 2, n - 2) : zeichen::utf16be(d + 2, n - 2));
    return g;
  }
  if (istText(d, n)) {
    g.art = "Text";
    const size_t bom = n >= 3 && d[0] == 0xef && d[1] == 0xbb && d[2] == 0xbf ? 3 : 0;
    s.text(zeichen::heile(std::string((const char *)d + bom, n - bom)));
    return g;
  }
  return g;
}

}  // namespace erkennen

inline bool anhangText(const std::string &name, const std::string &daten, zeichen::Sammler &s, int tiefe) {
  if (daten.empty() || tiefe > mail::TIEFE_MAX) return false;
  // Der Typ zählt am Inhalt; der Name hilft nur, eine E-Mail mit wenigen Kopfzeilen zu erkennen.
  const bool eml = office::endetMit(zeichen::klein(name), ".eml");
  erkennen::Gelesen g = erkennen::lies((const uint8_t *)daten.data(), daten.size(), s, tiefe, eml);
  return !g.art.empty() && g.fehler.empty();
}
