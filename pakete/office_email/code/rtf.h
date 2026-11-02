// Text aus RTF: Gruppen, Steuerwörter, \'hh (Windows-1252), \uN mit Ersatzzeichen (\ucN). Ziele ohne
// Fließtext (Schriften, Farben, Stile, Bilder, eingebettete Objekte, Feldbefehle …) werden übersprungen.
#pragma once
#include <cstdlib>
#include <string>
#include <vector>

#include "zeichen.h"

namespace rtf {

inline bool erkannt(const uint8_t *d, size_t n) { return n >= 5 && !memcmp(d, "{\\rtf", 5); }

inline bool ohneText(const std::string &w) {
  static const char *ziele[] = {"fonttbl", "colortbl", "stylesheet", "info", "pict", "object", "objdata", "themedata", "datastore",
                                "xmlnstbl", "listtable", "listoverridetable", "rsidtbl", "generator", "latentstyles", "mmathPr",
                                "fldinst", "filetbl", "revtbl", "pgdsctbl", "colorschememapping", "nonshppict", "bkmkstart", "bkmkend",
                                "wgrffmtfilter", "userprops", "xmlopen", "pnseclvl", "pntext", "pntxta", "pntxtb", "falt", "template"};
  for (auto z : ziele) if (w == z) return true;
  return false;
}

// Liefert false, wenn die Datei kein RTF ist.
inline bool lies(const std::string &t, zeichen::Sammler &s) {
  struct Stand { bool aus; int uc; };
  std::vector<Stand> stapel{{false, 1}};
  int ueberspringen = 0;  // Ersatzzeichen nach \uN
  std::string bytes;       // \'hh sammeln, dann als Windows-1252
  auto byteAus = [&]() { for (unsigned char b : bytes) { std::string z; zeichen::utf8(z, zeichen::cp1252(b)); s.text(z); } bytes.clear(); };
  bool gruppenAnfang = false;
  for (size_t i = 0; i < t.size() && !s.voll; i++) {
    char c = t[i];
    if (c == '{') { byteAus(); stapel.push_back(stapel.back()); gruppenAnfang = true; if (stapel.size() > 200) return true; continue; }
    if (c == '}') { byteAus(); if (stapel.size() > 1) stapel.pop_back(); gruppenAnfang = false; continue; }
    const bool anfang = gruppenAnfang;
    gruppenAnfang = false;
    Stand &st = stapel.back();
    if (c == '\\' && i + 1 < t.size()) {
      char d = t[i + 1];
      if (d == '\'' && i + 3 < t.size()) {
        const int h = zeichen::hexwert(t[i + 2]), l = zeichen::hexwert(t[i + 3]);
        i += 3;
        if (ueberspringen > 0) { ueberspringen--; continue; }
        if (!st.aus && h >= 0 && l >= 0) bytes += (char)(h << 4 | l);
        continue;
      }
      if (d == '*') { st.aus = true; i++; continue; }
      if (!((d >= 'a' && d <= 'z') || (d >= 'A' && d <= 'Z'))) {  // Steuerzeichen: \\ \{ \} \~ \- \_ …
        i++;
        byteAus();
        if (ueberspringen > 0) { ueberspringen--; continue; }
        if (st.aus) continue;
        if (d == '\\' || d == '{' || d == '}') s.zeichen(d);
        else if (d == '~') s.zeichen(' ');
        else if (d == '_') s.zeichen('-');
        else if (d == '\n' || d == '\r') s.zeile();
        continue;
      }
      size_t j = i + 1;
      std::string wort;
      while (j < t.size() && wort.size() < 32 && ((t[j] >= 'a' && t[j] <= 'z') || (t[j] >= 'A' && t[j] <= 'Z'))) wort += t[j++];
      long param = 0; bool hatParam = false, neg = false;
      if (j < t.size() && t[j] == '-') { neg = true; j++; }
      while (j < t.size() && t[j] >= '0' && t[j] <= '9' && param < 100000000) { param = param * 10 + (t[j++] - '0'); hatParam = true; }
      if (neg) param = -param;
      if (j < t.size() && t[j] == ' ') j++;
      i = j - 1;
      byteAus();
      if (wort == "bin" && hatParam && param > 0) { i += (size_t)param; continue; }  // Binärdaten
      if (anfang && ohneText(wort)) { st.aus = true; continue; }
      if (wort == "uc" && hatParam) { st.uc = (int)param; continue; }
      if (wort == "u" && hatParam) {
        if (!st.aus) { std::string z; zeichen::utf8(z, (uint32_t)(param < 0 ? param + 65536 : param)); s.text(z); }
        ueberspringen = st.uc;
        continue;
      }
      if (ueberspringen > 0) { ueberspringen--; continue; }
      if (st.aus) continue;
      if (wort == "par" || wort == "line" || wort == "row" || wort == "sect" || wort == "page") s.zeile();
      else if (wort == "tab" || wort == "cell") s.tab();
      else if (wort == "emdash") s.text("\xe2\x80\x94");
      else if (wort == "endash") s.text("\xe2\x80\x93");
      else if (wort == "bullet") s.text("\xe2\x80\xa2");
      else if (wort == "lquote") s.text("\xe2\x80\x98");
      else if (wort == "rquote") s.text("\xe2\x80\x99");
      else if (wort == "ldblquote") s.text("\xe2\x80\x9c");
      else if (wort == "rdblquote") s.text("\xe2\x80\x9d");
      continue;
    }
    if (c == '\r' || c == '\n') continue;
    if (ueberspringen > 0) { ueberspringen--; continue; }
    if (st.aus) continue;
    if ((unsigned char)c >= 0x80) bytes += c;
    else { byteAus(); s.zeichen(c); }
  }
  byteAus();
  return true;
}

}  // namespace rtf
