// Rechnungen und Bestellungen (dms-registry #161, #210): Status einer Rechnung, Umsatzsteuer und Gesamtpreis einer
// Position, Steuerzeilen je Satz und die Summenprüfungen – ohne Ablago testbar (tests/rechnung_test.cpp).
#pragma once
#include <cmath>
#include <cstdio>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace rechnung {

struct Datum {
  int j = 0, m = 0, t = 0;
  bool operator<(const Datum &o) const { return j != o.j ? j < o.j : m != o.m ? m < o.m : t < o.t; }
};
inline std::optional<Datum> lies_iso(const std::string &s) {
  Datum d;
  if (s.size() < 10 || sscanf(s.c_str(), "%4d-%2d-%2d", &d.j, &d.m, &d.t) != 3 || d.m < 1 || d.m > 12 || d.t < 1 || d.t > 31) return std::nullopt;
  return d;
}
inline std::string text(const Datum &d) {
  char b[16];
  snprintf(b, sizeof b, "%02d.%02d.%04d", d.t, d.m, d.j);
  return b;
}
inline double runde(double w) { return std::round(w * 100) / 100; }

// 118.4 → „118,40 €“, -12.5 → „−12,50 €“ (Tausender mit Punkt).
inline std::string euro(double w, const std::string &waehrung = "EUR") {
  long long c = std::llround(std::fabs(w) * 100);
  std::string ganz = std::to_string(c / 100), mit;
  for (size_t i = 0; i < ganz.size(); i++) {
    if (i && (ganz.size() - i) % 3 == 0) mit += '.';
    mit += ganz[i];
  }
  char rest[8];
  snprintf(rest, sizeof rest, ",%02lld", c % 100);
  return (w < 0 && c ? "−" : "") + mit + rest + " " + (waehrung == "EUR" || waehrung.empty() ? "€" : waehrung);
}

struct Eingabe {
  std::optional<double> betrag;
  std::optional<Datum> faellig_am, bezahlt_am, zahlungseingang_am;
};

inline std::string status(const Eingabe &e, const Datum &heute) {
  if (e.betrag && *e.betrag < 0) {
    if (e.bezahlt_am) return "Gutschrift erhalten am " + text(*e.bezahlt_am);
    return "Gutschrift – noch nicht erhalten";
  }
  if (e.zahlungseingang_am) return "bezahlt am " + text(*e.zahlungseingang_am);
  if (e.bezahlt_am) return "bezahlt am " + text(*e.bezahlt_am);
  if (e.faellig_am) {
    if (*e.faellig_am < heute) return "überfällig seit " + text(*e.faellig_am);
    return "offen – fällig am " + text(*e.faellig_am);
  }
  return e.betrag ? "offen" : "";
}

struct Position {
  std::optional<double> menge, einzelpreis, gesamtpreis, ust_satz;
};

// Gesamtpreis: eingetragen oder Menge × Einzelpreis.
inline std::optional<double> gesamt(const Position &p) {
  if (p.gesamtpreis) return p.gesamtpreis;
  if (p.menge && p.einzelpreis) return runde(*p.menge * *p.einzelpreis);
  return std::nullopt;
}
// Mit Satz gelten die Preise netto.
inline std::optional<double> ust_betrag(const Position &p) {
  auto g = gesamt(p);
  if (!g || !p.ust_satz) return std::nullopt;
  return runde(*g * *p.ust_satz / 100);
}

// Hinweis, wenn die Positionen nicht zum Betrag passen; leer, wenn sie passen oder nichts zu vergleichen ist.
// Rundung: bis 1 Cent je Position zählt nicht (Hinweis Qualität).
inline std::string summenhinweis(const std::optional<double> &betrag, const std::vector<Position> &pos, const std::string &waehrung = "EUR") {
  if (!betrag || pos.empty()) return "";
  double summe = 0;
  for (const Position &p : pos) {
    auto g = gesamt(p);
    if (!g) return "";  // unvollständig: nichts behaupten
    summe += *g + ust_betrag(p).value_or(0);
  }
  summe = runde(summe);
  if (std::fabs(summe - *betrag) <= 0.01 * (double)pos.size() + 1e-9) return "";
  return "Die Positionen ergeben " + euro(summe, waehrung) + ", die Rechnung sagt " + euro(*betrag, waehrung) + ".";
}

// Steuerzeilen (#210): je Satz Netto und Steuerbetrag. Der Steuerbetrag ist eingetragen oder Netto × Satz.
struct Steuerzeile {
  std::optional<double> satz, netto, steuer;
};
inline std::optional<double> steuer(const Steuerzeile &z) {
  if (z.steuer) return z.steuer;
  if (z.netto && z.satz) return runde(*z.netto * *z.satz / 100);
  return std::nullopt;
}
struct Summen {
  std::optional<double> netto, ust;
};
// Summen über alle Zeilen; leer, wenn es keine Zeile gibt. Fehlt in einer Zeile Netto, ist auch die Summe offen.
inline Summen summen(const std::vector<Steuerzeile> &zeilen) {
  if (zeilen.empty()) return {};
  double n = 0, u = 0;
  bool alle_netto = true, alle_ust = true;
  for (const Steuerzeile &z : zeilen) {
    if (z.netto) n += *z.netto; else alle_netto = false;
    if (auto s = steuer(z)) u += *s; else alle_ust = false;
  }
  Summen r;
  if (alle_netto) r.netto = runde(n);
  if (alle_ust) r.ust = runde(u);
  return r;
}
// Hinweis, wenn Netto + Umsatzsteuer nicht zum Bruttobetrag passen (bis 1 Cent je Zeile zählt nicht).
inline std::string steuerhinweis(const std::optional<double> &betrag, const std::vector<Steuerzeile> &zeilen, const std::string &waehrung = "EUR") {
  Summen s = summen(zeilen);
  if (!betrag || !s.netto || !s.ust) return "";
  double brutto = runde(*s.netto + *s.ust);
  if (std::fabs(brutto - *betrag) <= 0.01 * (double)zeilen.size() + 1e-9) return "";
  return "Netto und Umsatzsteuer ergeben " + euro(brutto, waehrung) + ", die Rechnung sagt " + euro(*betrag, waehrung) + ".";
}
// Aus den Positionen je Satz: Netto (Gesamtpreise) und Steuer. Positionen ohne Satz oder ohne Preis zählen nicht.
inline std::map<double, Steuerzeile> aus_positionen(const std::vector<Position> &pos) {
  std::map<double, Steuerzeile> je;
  for (const Position &p : pos) {
    auto g = gesamt(p);
    if (!g || !p.ust_satz) continue;
    Steuerzeile &z = je[*p.ust_satz];
    z.satz = p.ust_satz;
    z.netto = runde(z.netto.value_or(0) + *g);
    z.steuer = runde(z.steuer.value_or(0) + *ust_betrag(p));
  }
  return je;
}

}  // namespace rechnung
