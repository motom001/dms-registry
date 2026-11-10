// Tests der Vertragsberechnung (code/berechnung.h) mit typischen Verträgen. Läuft nativ in code/bauen.sh.
#include <cstdio>
#include <string>

#include "berechnung.h"

using namespace vertrag;

static int fehler = 0, ok = 0;
static void pruefe(const char *name, bool b, const std::string &info = "") {
  if (b) { ok++; printf("ok %s\n", name); }
  else { fehler++; printf("FEHLER %s %s\n", name, info.c_str()); }
}
static Datum d(const char *s) { return *lies_iso(s); }
static std::string t(const std::optional<Datum> &x) { return x ? iso(*x) : "-"; }
static Zeitraum monate(int n) { return {n, Einheit::MONATE}; }

int main() {
  // Datumsrechnung
  pruefe("31.01. + 1 Monat = 28.02.", iso(plus_monate(d("2026-01-31"), 1)) == "2026-02-28");
  pruefe("31.01.2028 + 1 Monat = 29.02. (Schaltjahr)", iso(plus_monate(d("2028-01-31"), 1)) == "2028-02-29");
  pruefe("Tagnummer hin und zurück", iso(aus_tagnummer(tagnummer(d("2026-11-10")))) == "2026-11-10");
  pruefe("Quartalsende", iso(aufrunden(d("2026-11-10"), Zum::QUARTALSENDE)) == "2026-12-31");

  // Handyvertrag: 24 Monate ab 15.03.2026, danach unbefristet, 1 Monat jederzeit.
  Eingabe handy;
  handy.beginn = d("2026-03-15");
  handy.mindestlaufzeit = monate(24);
  handy.danach = Danach::UNBEFRISTET;
  handy.kuendigungsfrist = monate(1);
  handy.zum = Zum::JEDERZEIT;
  handy.betrag = 19.99;
  handy.zahlweise = "monatlich";
  Ergebnis r = rechne(handy, d("2026-11-10"));
  pruefe("Handy: frühestens zum Ende der 24 Monate", t(r.fruehestes_ende) == "2028-03-14", t(r.fruehestes_ende));
  pruefe("Handy: kündigen bis einen Monat vorher", t(r.kuendigen_bis) == "2028-02-14", t(r.kuendigen_bis));
  pruefe("Handy: Status", r.status == "läuft – kündigen bis 14.02.2028, Ende dann 14.03.2028", r.status);
  pruefe("Handy: pro Monat", r.pro_monat && *r.pro_monat == 19.99);
  pruefe("Handy: Laufzeit 7 Monate", r.laufzeit_monate && *r.laufzeit_monate == 7, std::to_string(r.laufzeit_monate.value_or(-1)));
  r = rechne(handy, d("2028-05-20"));
  pruefe("Handy nach der Mindestlaufzeit: kein Kündigen bis", !r.kuendigen_bis, t(r.kuendigen_bis));
  pruefe("Handy nach der Mindestlaufzeit: jederzeit", r.status == "läuft – jederzeit kündbar mit 1 Monat, frühestens zum 20.06.2028", r.status);
  handy.gekuendigt_am = d("2028-05-20");
  r = rechne(handy, d("2028-05-21"));
  pruefe("Handy gekündigt", r.status == "gekündigt zum 20.06.2028 – Bestätigung fehlt noch" && t(r.ende) == "2028-06-20", r.status);
  handy.bestaetigt_am = d("2028-05-22");
  r = rechne(handy, d("2028-07-01"));
  pruefe("Handy beendet", r.status == "beendet am 20.06.2028" && !r.kuendigen_bis, r.status);

  // Versicherung: 1 Jahr ab 01.01.2024, verlängert sich um 1 Jahr, 3 Monate zum Laufzeitende, 62,40 € jährlich.
  Eingabe vers;
  vers.beginn = d("2024-01-01");
  vers.mindestlaufzeit = monate(12);
  vers.danach = Danach::UM;
  vers.verlaengerung_um = monate(12);
  vers.kuendigungsfrist = monate(3);
  vers.zum = Zum::LAUFZEITENDE;
  vers.betrag = 62.4;
  vers.zahlweise = "jährlich";
  r = rechne(vers, d("2026-11-10"));
  pruefe("Versicherung: Ende zum 31.12.2027 (2026 ist verpasst)", t(r.fruehestes_ende) == "2027-12-31", t(r.fruehestes_ende));
  pruefe("Versicherung: kündigen bis 30.09.2027", t(r.kuendigen_bis) == "2027-09-30", t(r.kuendigen_bis));
  pruefe("Versicherung: nächste Verlängerung 01.01.2028", t(r.naechste_verlaengerung) == "2028-01-01", t(r.naechste_verlaengerung));
  pruefe("Versicherung: 5,20 € pro Monat", r.pro_monat && *r.pro_monat == 5.2);
  r = rechne(vers, d("2026-09-15"));
  pruefe("Versicherung im September: noch zum 31.12.2026", t(r.fruehestes_ende) == "2026-12-31" && t(r.kuendigen_bis) == "2026-09-30", t(r.kuendigen_bis));

  // Miete: unbefristet, 3 Monate zum Monatsende, ohne Mindestlaufzeit.
  Eingabe miete;
  miete.beginn = d("2020-05-01");
  miete.danach = Danach::UNBEFRISTET;
  miete.kuendigungsfrist = monate(3);
  miete.zum = Zum::MONATSENDE;
  r = rechne(miete, d("2026-11-10"));
  pruefe("Miete: frühestens zum 28.02.2027", t(r.fruehestes_ende) == "2027-02-28", t(r.fruehestes_ende));
  pruefe("Miete: keine Erinnerung jeden Monat", !r.kuendigen_bis);
  pruefe("Miete: Status", r.status == "läuft – jederzeit kündbar mit 3 Monaten zum Monatsende, frühestens zum 28.02.2027", r.status);

  // Befristet: endet von selbst.
  Eingabe befr;
  befr.beginn = d("2026-01-01");
  befr.danach = Danach::ENDET;
  befr.vertragsende = d("2026-12-31");
  r = rechne(befr, d("2026-11-10"));
  pruefe("Befristet: endet von selbst", r.status == "läuft – endet am 31.12.2026 von selbst" && !r.kuendigen_bis && t(r.ende) == "2026-12-31", r.status);

  // Streaming: Monat für Monat, ohne Frist, zum Laufzeitende.
  Eingabe str;
  str.beginn = d("2026-10-05");
  str.mindestlaufzeit = monate(1);
  str.danach = Danach::UM;
  str.verlaengerung_um = monate(1);
  str.kuendigungsfrist = Zeitraum{0, Einheit::TAGE};
  str.zum = Zum::LAUFZEITENDE;
  r = rechne(str, d("2026-11-10"));
  pruefe("Streaming: Ende des laufenden Monats", t(r.fruehestes_ende) == "2026-12-04" && t(r.kuendigen_bis) == "2026-12-04", t(r.fruehestes_ende) + " " + t(r.kuendigen_bis));

  // Beginnt in der Zukunft; fehlende Angaben.
  Eingabe zuk = handy;
  zuk.gekuendigt_am.reset();
  zuk.bestaetigt_am.reset();
  zuk.beginn = d("2027-01-01");
  r = rechne(zuk, d("2026-11-10"));
  pruefe("Beginnt später", r.status.rfind("beginnt am 01.01.2027 – läuft – kündigen bis", 0) == 0, r.status);
  Eingabe leer;
  leer.kuendigungsfrist = monate(1);
  pruefe("Ohne Beginn", rechne(leer, d("2026-11-10")).status == "Beginn fehlt – ohne ihn rechnet das Paket nicht");
  Eingabe nichts;
  pruefe("Ohne Angaben: kein Status", rechne(nichts, d("2026-11-10")).status.empty());

  printf("%d ok, %d Fehler\n", ok, fehler);
  return fehler ? 1 : 0;
}
