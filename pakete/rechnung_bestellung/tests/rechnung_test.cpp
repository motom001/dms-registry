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
  // Steuerzeilen (#210): Miete mit Lieferung und Service – 0 %, 7 % und 19 % auf einer Rechnung.
  Steuerzeile s0; s0.satz = 0; s0.netto = 50;
  Steuerzeile s7; s7.satz = 7; s7.netto = 100;
  Steuerzeile s19; s19.satz = 19; s19.netto = 200; s19.steuer = 38.0;
  pruefe("Steuer aus Netto × Satz", steuer(s7) && *steuer(s7) == 7.0);
  pruefe("Steuer eingetragen gilt", steuer(s19) && *steuer(s19) == 38.0);
  Summen su = summen({s0, s7, s19});
  pruefe("Summen über drei Sätze", su.netto && *su.netto == 350.0 && su.ust && *su.ust == 45.0);
  pruefe("Steuer passt zum Brutto", steuerhinweis(395.0, {s0, s7, s19}).empty());
  pruefe("Steuer passt nicht", steuerhinweis(400.0, {s0, s7, s19}) == "Netto und Umsatzsteuer ergeben 395,00 €, die Rechnung sagt 400,00 €.", steuerhinweis(400.0, {s0, s7, s19}));
  Steuerzeile leer; leer.satz = 19;
  pruefe("Zeile ohne Netto: Summe offen, kein Hinweis", !summen({s7, leer}).netto && steuerhinweis(1.0, {s7, leer}).empty());
  pruefe("ohne Zeilen: keine Summen", !summen({}).netto && !summen({}).ust);
  Position q1; q1.gesamtpreis = 100; q1.ust_satz = 19;
  Position q2; q2.menge = 2; q2.einzelpreis = 10; q2.ust_satz = 7;
  Position q3; q3.gesamtpreis = 50; q3.ust_satz = 19;
  Position q4; q4.gesamtpreis = 5;
  auto je = aus_positionen({q1, q2, q3, q4});
  pruefe("aus Positionen: zwei Sätze, ohne Satz zählt nicht", je.size() == 2 && *je[19].netto == 150.0 && *je[19].steuer == 28.5 && *je[7].netto == 20.0 && *je[7].steuer == 1.4);
  printf("%d ok, %d Fehler\n", ok, fehler);
  return fehler ? 1 : 0;
}
