// Reine Logik des Pakets Compliance – ohne Ablago testbar (tests/stand_test.cpp): Monate, Auswahl „was zählt“,
// Änderungen filtern und in Worte fassen, Zusammenfassung der Nachweise.
#pragma once
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <set>
#include <string>
#include <vector>

#include "bereiche.h"
#include "json.h"

namespace compliance {

// ---- Monate „JJJJ-MM“ -----------------------------------------------------------------------------------------------

inline bool ist_monat(const std::string &m) {
  if (m.size() != 7 || m[4] != '-') return false;
  for (int i : {0, 1, 2, 3, 5, 6})
    if (m[i] < '0' || m[i] > '9') return false;
  int mo = atoi(m.c_str() + 5);
  return mo >= 1 && mo <= 12;
}

// „2026-11-10“ oder „2026-11-10T04:30:00Z“ → „2026-11“ (sonst leer)
inline std::string monat_von(const std::string &datum) {
  std::string m = datum.substr(0, 7);
  return ist_monat(m) ? m : "";
}

inline std::string monat_plus(const std::string &m, int n) {
  int j = atoi(m.c_str()), mo = atoi(m.c_str() + 5) - 1 + n;
  j += mo >= 0 ? mo / 12 : -((11 - mo) / 12);
  mo = ((mo % 12) + 12) % 12;
  char b[16];
  snprintf(b, sizeof b, "%04d-%02d", j, mo + 1);
  return b;
}

inline std::string monatsende(const std::string &m) {
  int j = atoi(m.c_str()), mo = atoi(m.c_str() + 5);
  static const int tage[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  int t = tage[mo - 1] + (mo == 2 && ((j % 4 == 0 && j % 100 != 0) || j % 400 == 0));
  char b[16];
  snprintf(b, sizeof b, "%s-%02d", m.c_str(), t);
  return b;
}

// Monate, für die Nachweise fehlen: nach „zuletzt“ bis vor „jetzt“, höchstens die letzten `hoechstens`.
inline std::vector<std::string> fehlende_monate(const std::string &zuletzt, const std::string &jetzt, int hoechstens = 12) {
  std::vector<std::string> r;
  if (!ist_monat(zuletzt) || !ist_monat(jetzt)) return r;
  for (std::string m = monat_plus(zuletzt, 1); m < jetzt; m = monat_plus(m, 1)) r.push_back(m);
  if ((int)r.size() > hoechstens) r.erase(r.begin(), r.end() - hoechstens);
  return r;
}

// ---- Auswahl „was zählt“ --------------------------------------------------------------------------------------------

// Kennungen der angehakten Zeilen eines Bereichs. Fehlt die Einstellung (noch nie gespeichert), gilt die Vorauswahl;
// Texte, die es nicht (mehr) gibt, zählen nicht.
inline std::vector<std::string> auswahl(const Bereich &b, const Json &einstellungen) {
  std::vector<std::string> r;
  const Json &w = einstellungen[(std::string("zaehlt_") + b.schluessel).c_str()];
  for (const Zaehlt &z : b.zaehlt) {
    bool an = z.vorgabe;
    if (w.art == Json::LISTE) {
      an = false;
      for (const Json &x : w.l)
        if (x.text() == z.text) an = true;
    }
    if (an) r.push_back(z.kennung);
  }
  return r;
}

// Die ganze Auswahl als ein Text zum Speichern („bereich:kennung“ je Zeile, sortiert).
inline std::string auswahl_text(const Json &einstellungen) {
  std::vector<std::string> z;
  for (const Bereich &b : bereiche())
    for (const std::string &k : auswahl(b, einstellungen)) z.push_back(k);
  std::sort(z.begin(), z.end());
  std::string r;
  for (const std::string &k : z) r += k + "\n";
  return r;
}

inline const Zaehlt *zeile(const std::string &kennung) {
  for (const Bereich &b : bereiche())
    for (const Zaehlt &z : b.zaehlt)
      if (kennung == z.kennung) return &z;
  return nullptr;
}

// Satz zur geänderten Auswahl, z. B. „Was zählt: neu „Sitzungsdauer“ (Zugang und Berechtigungen); nicht mehr „PDF/A an
// oder aus“ (Belegeingang und Scannen)“ – leer, wenn gleich oder vorher unbekannt.
inline std::string auswahl_aenderung(const std::string &vorher, const std::string &nachher) {
  if (vorher.empty() || vorher == nachher) return "";
  auto zeilen = [](const std::string &t) {
    std::set<std::string> s;
    size_t a = 0;
    for (size_t e; (e = t.find('\n', a)) != std::string::npos; a = e + 1) s.insert(t.substr(a, e - a));
    return s;
  };
  std::set<std::string> v = zeilen(vorher), n = zeilen(nachher);
  auto name = [](const std::string &k) {
    const Zaehlt *z = zeile(k);
    const Bereich *b = bereich(k.substr(0, k.find('.')));
    return std::string("„") + (z ? z->text : k.c_str()) + "“" + (b ? std::string(" (") + b->name + ")" : "");
  };
  std::string neu, weg;
  for (const std::string &k : n)
    if (!v.count(k)) neu += (neu.empty() ? "" : ", ") + name(k);
  for (const std::string &k : v)
    if (!n.count(k)) weg += (weg.empty() ? "" : ", ") + name(k);
  if (neu.empty() && weg.empty()) return "";
  return "Was zählt: " + (neu.empty() ? "" : "neu " + neu) + (neu.empty() || weg.empty() ? "" : "; ") + (weg.empty() ? "" : "nicht mehr " + weg);
}

// ---- Änderungen -----------------------------------------------------------------------------------------------------

struct Aenderung {
  std::string kennung;
  std::string satz;
};

// Änderungen aus dem Vergleich des Kerns ({ aenderungen: [{ kennung, vorher, nachher, satz }] }), nur was zählt.
inline std::vector<Aenderung> zaehlende(const Json &vergleich, const std::vector<std::string> &auswahl) {
  std::vector<Aenderung> r;
  for (const Json &a : vergleich["aenderungen"].l) {
    std::string k = a["kennung"].text();
    if (k.empty() || !zaehlt(k, auswahl)) continue;
    std::string s = a["satz"].text();
    r.push_back({k, s.empty() ? k : s});
  }
  return r;
}

// In Worten für das Feld „Änderung“: je Änderung eine Zeile, höchstens `hoechstens` Zeichen.
inline std::string als_text(const std::vector<Aenderung> &a, size_t hoechstens = 4000) {
  std::string r;
  for (size_t i = 0; i < a.size(); i++) {
    std::string z = "• " + a[i].satz + "\n";
    if (r.size() + z.size() > hoechstens - 40) {
      r += "… und " + std::to_string(a.size() - i) + " weitere (siehe JSON-Datei)\n";
      break;
    }
    r += z;
  }
  if (!r.empty()) r.pop_back();
  return r;
}

// ---- Nachweise ------------------------------------------------------------------------------------------------------

inline std::string zahl_text(const Json &w) {
  if (w.art == Json::ZAHL) {
    char b[32];
    if (w.z == (double)(long long)w.z) snprintf(b, sizeof b, "%lld", (long long)w.z); else snprintf(b, sizeof b, "%.2f", w.z);
    return b;
  }
  return w.art == Json::TEXT ? w.t : w.art == Json::BOOL ? (w.b ? "ja" : "nein") : "–";
}

// „Zahlen je Bereich“ aus den Nachweisen des Kerns ({ zahlen: [{ bereich, name, wert }] }), je Bereich eine Zeile in der
// Reihenfolge der Bereiche: „Sicherung: Sicherungsläufe 31, fehlgeschlagen 0“.
inline std::string zusammenfassung(const Json &nachweise) {
  std::map<std::string, std::string> je;
  for (const Json &z : nachweise["zahlen"].l) {
    std::string b = z["bereich"].text(), n = z["name"].text();
    if (b.empty() || n.empty()) continue;
    std::string &t = je[b];
    t += (t.empty() ? "" : ", ") + n + " " + zahl_text(z["wert"]);
  }
  std::string r;
  for (const Bereich &b : bereiche()) {
    auto i = je.find(b.schluessel);
    if (i != je.end()) r += std::string(b.name) + ": " + i->second + "\n";
  }
  if (!r.empty()) r.pop_back();
  return r.size() > 4000 ? r.substr(0, 3990) + " …" : r;
}

// Namen der enthaltenen Bereiche: „Zugang und Berechtigungen, Sicherung“.
inline std::string bereichsnamen(const Json &liste) {
  std::string r;
  for (const Bereich &b : bereiche())
    for (const Json &x : liste.l)
      if (x.text() == b.schluessel) r += (r.empty() ? "" : ", ") + std::string(b.name);
  return r;
}

}  // namespace compliance
