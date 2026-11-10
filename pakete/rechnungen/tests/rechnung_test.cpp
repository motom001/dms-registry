// Tests für code/rechnung.h: Status, Positionen, Summenprüfung. Läuft nativ in code/bauen.sh.
#include <cstdio>
#include <string>

#include "rechnung.h"

using namespace rechnung;
static int fehler = 0, ok = 0;
static void pruefe(const char *name, bool b, const std::string &info = "") {
  if (b) { ok++; printf("ok %s\n", name); } else { fehler++; printf("FEHLER %s %s\n", name, info.c_str()); }
}
static Datum d(const char *s) { return *lies_iso(s); }

int main() {
  const Datum heute = d("2026-11-10");
  Eingabe e;
  e.betrag = 120.8;
  pruefe("offen ohne Fälligkeit", status(e, heute) == "offen");
  e.faellig_am = d("2026-11-15");
  pruefe("offen mit Fälligkeit", status(e, heute) == "offen – fällig am 15.11.2026", status(e, heute));
  e.faellig_am = d("2026-11-01");
  pruefe("überfällig", status(e, heute) == "überfällig seit 01.11.2026", status(e, heute));
  e.bezahlt_am = d("2026-11-09");
  pruefe("bezahlt", status(e, heute) == "bezahlt am 09.11.2026", status(e, heute));
  Eingabe g;
  g.betrag = -12.5;
  pruefe("Gutschrift offen", status(g, heute) == "Gutschrift – noch nicht erhalten");
  g.bezahlt_am = d("2026-11-03");
  pruefe("Gutschrift erhalten", status(g, heute) == "Gutschrift erhalten am 03.11.2026");
  Eingabe a;
  a.betrag = 500;
  a.faellig_am = d("2026-10-01");
  a.zahlungseingang_am = d("2026-10-02");
  pruefe("Ausgangsrechnung bezahlt", status(a, heute) == "bezahlt am 02.10.2026");
  pruefe("ohne Betrag kein Status", status(Eingabe{}, heute).empty());

  pruefe("Euro", euro(118.4) == "118,40 €" && euro(-12.5) == "−12,50 €" && euro(1234567.891) == "1.234.567,89 €", euro(1234567.891));

  Position p1; p1.menge = 3; p1.einzelpreis = 12.99;
  Position p2; p2.gesamtpreis = 80.0;
  pruefe("Gesamt aus Menge × Einzelpreis", gesamt(p1) && *gesamt(p1) == 38.97);
  pruefe("Summe passt", summenhinweis(118.97, {p1, p2}).empty());
  pruefe("Summe passt nicht", summenhinweis(120.8, {p1, p2}) == "Die Positionen ergeben 118,97 €, die Rechnung sagt 120,80 €.", summenhinweis(120.8, {p1, p2}));
  pruefe("Rundung bis 1 Cent je Position", summenhinweis(118.99, {p1, p2}).empty());
  Position n1; n1.gesamtpreis = 100; n1.ust_satz = 19;
  pruefe("Umsatzsteuer netto", ust_betrag(n1) && *ust_betrag(n1) == 19.0);
  pruefe("Summe mit Umsatzsteuer", summenhinweis(119.0, {n1}).empty());
  Position halb; halb.menge = 2;
  pruefe("unvollständige Position: nichts behaupten", summenhinweis(1.0, {p1, halb}).empty());
  pruefe("ohne Positionen: nichts", summenhinweis(1.0, {}).empty());
  printf("%d ok, %d Fehler\n", ok, fehler);
  return fehler ? 1 : 0;
}
