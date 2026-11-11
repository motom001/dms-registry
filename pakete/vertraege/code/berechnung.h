// Berechnung eines Vertrags (dms-registry #159): Status, Kündigen bis, frühestes Ende, nächste Verlängerung, Ende,
// Laufzeit in Monaten und Betrag pro Monat – nur aus den Angaben der Mappe und dem heutigen Datum.
// Ohne Ablago und ohne WebAssembly testbar (tests/berechnung_test.cpp). Ohne Gewähr, keine Rechtsberatung.
//
// Regeln (Fristen nach § 188 BGB: ein Monat ab dem 15.01. endet am 15.02., ab dem 31.01. am Monatsletzten):
//  - Erste Laufzeit: Beginn + Mindestlaufzeit − 1 Tag (bzw. das Vertragsende bei „endet“).
//  - „verlängert sich um“: weitere Laufzeiten gleicher Länge hintereinander; gekündigt wird zum Ende einer Laufzeit.
//  - „läuft unbefristet weiter“ (oder leer): nach der ersten Laufzeit jederzeit mit der Frist, ggf. zum Monats-,
//    Quartals- oder Jahresende. Vorher frühestens zum Ende der ersten Laufzeit.
//  - „endet“: endet von selbst zum Vertragsende; eine Kündigung ändert daran nichts.
//  - Gekündigt ohne Kündigungsfrist, aber mit Vertragsende: Das Vertragsende gilt (Umbau aus Vermietung 1.x, #163).
//  - „Kündigen bis“ gibt es nur, wenn ein Laufzeitende wartet – nicht im unbefristeten Teil, sonst käme jeden Monat
//    eine Erinnerung.
#pragma once
#include <cstdio>
#include <optional>
#include <string>

namespace vertrag {

struct Datum {
  int j = 0, m = 0, t = 0;
  bool operator==(const Datum &o) const { return j == o.j && m == o.m && t == o.t; }
  bool operator!=(const Datum &o) const { return !(*this == o); }
  bool operator<(const Datum &o) const { return j != o.j ? j < o.j : m != o.m ? m < o.m : t < o.t; }
  bool operator<=(const Datum &o) const { return !(o < *this); }
  bool operator>(const Datum &o) const { return o < *this; }
};

inline bool schaltjahr(int j) { return (j % 4 == 0 && j % 100 != 0) || j % 400 == 0; }
inline int monatstage(int j, int m) {
  static const int t[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  return m == 2 && schaltjahr(j) ? 29 : t[m - 1];
}
inline bool gueltig(const Datum &d) { return d.j >= 1900 && d.j <= 2200 && d.m >= 1 && d.m <= 12 && d.t >= 1 && d.t <= monatstage(d.j, d.m); }

// Tage seit 1970-01-01 (proleptischer gregorianischer Kalender) und zurück.
inline long tagnummer(const Datum &d) {
  int j = d.j - (d.m <= 2);
  long era = (j >= 0 ? j : j - 399) / 400;
  long yoe = j - era * 400, mp = (d.m + 9) % 12;
  long doy = (153 * mp + 2) / 5 + d.t - 1, doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  return era * 146097 + doe - 719468;
}
inline Datum aus_tagnummer(long z) {
  z += 719468;
  long era = (z >= 0 ? z : z - 146096) / 146097, doe = z - era * 146097;
  long yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365, doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
  long mp = (5 * doy + 2) / 153, t = doy - (153 * mp + 2) / 5 + 1, m = mp < 10 ? mp + 3 : mp - 9;
  return {(int)(yoe + era * 400 + (m <= 2)), (int)m, (int)t};
}
inline Datum plus_tage(const Datum &d, long n) { return aus_tagnummer(tagnummer(d) + n); }
inline Datum plus_monate(const Datum &d, int n) {
  int g = d.j * 12 + (d.m - 1) + n, j = g / 12, m = g % 12 + 1;
  return {j, m, d.t < monatstage(j, m) ? d.t : monatstage(j, m)};
}

enum class Einheit { TAGE, WOCHEN, MONATE, JAHRE };
struct Zeitraum {
  int anzahl = 0;
  Einheit einheit = Einheit::MONATE;
};
inline Datum plus(const Datum &d, const Zeitraum &z, int vorzeichen = 1) {
  switch (z.einheit) {
    case Einheit::TAGE: return plus_tage(d, vorzeichen * (long)z.anzahl);
    case Einheit::WOCHEN: return plus_tage(d, vorzeichen * 7L * z.anzahl);
    case Einheit::MONATE: return plus_monate(d, vorzeichen * z.anzahl);
    case Einheit::JAHRE: return plus_monate(d, vorzeichen * 12 * z.anzahl);
  }
  return d;
}

enum class Danach { LEER, UM, UNBEFRISTET, ENDET };
enum class Zum { LEER, LAUFZEITENDE, MONATSENDE, QUARTALSENDE, JAHRESENDE, JEDERZEIT };

struct Eingabe {
  std::optional<Datum> beginn, vertragsende, gekuendigt_am, bestaetigt_am;
  std::optional<Zeitraum> mindestlaufzeit, verlaengerung_um, kuendigungsfrist;
  Danach danach = Danach::LEER;
  Zum zum = Zum::LEER;
  std::optional<double> betrag;
  std::string zahlweise;  // monatlich, vierteljährlich, halbjährlich, jährlich, einmalig
};

struct Ergebnis {
  std::string status;
  std::optional<Datum> kuendigen_bis, fruehestes_ende, naechste_verlaengerung, ende;
  std::optional<int> laufzeit_monate;
  std::optional<double> pro_monat;
};

inline std::string text(const Datum &d) {
  char b[16];
  snprintf(b, sizeof b, "%02d.%02d.%04d", d.t, d.m, d.j);
  return b;
}
inline std::string iso(const Datum &d) {
  char b[16];
  snprintf(b, sizeof b, "%04d-%02d-%02d", d.j, d.m, d.t);
  return b;
}
inline std::optional<Datum> lies_iso(const std::string &s) {
  Datum d;
  if (s.size() < 10 || sscanf(s.c_str(), "%4d-%2d-%2d", &d.j, &d.m, &d.t) != 3 || !gueltig(d)) return std::nullopt;
  return d;
}

// „mit 1 Monat“, „mit 3 Monaten“, „mit 2 Wochen“, „mit 14 Tagen“, „mit 1 Jahr“.
inline std::string frist_text(const Zeitraum &z) {
  const bool eins = z.anzahl == 1;
  const char *w = "";
  switch (z.einheit) {
    case Einheit::TAGE: w = eins ? "Tag" : "Tagen"; break;
    case Einheit::WOCHEN: w = eins ? "Woche" : "Wochen"; break;
    case Einheit::MONATE: w = eins ? "Monat" : "Monaten"; break;
    case Einheit::JAHRE: w = eins ? "Jahr" : "Jahren"; break;
  }
  return std::to_string(z.anzahl) + " " + w;
}

// Ende des Monats, Quartals bzw. Jahres, in dem d liegt (oder d selbst, wenn es schon eines ist).
inline Datum aufrunden(const Datum &d, Zum zum) {
  switch (zum) {
    case Zum::MONATSENDE: return {d.j, d.m, monatstage(d.j, d.m)};
    case Zum::QUARTALSENDE: { int m = ((d.m - 1) / 3 + 1) * 3; return {d.j, m, monatstage(d.j, m)}; }
    case Zum::JAHRESENDE: return {d.j, 12, 31};
    default: return d;
  }
}

class Rechner {
 public:
  explicit Rechner(const Eingabe &e) : e_(e) {
    frist_ = e.kuendigungsfrist ? *e.kuendigungsfrist : Zeitraum{0, Einheit::TAGE};
    danach_ = e.danach == Danach::LEER ? Danach::UNBEFRISTET : e.danach;
    zum_ = e.zum;
    if (zum_ == Zum::LEER) zum_ = danach_ == Danach::UM ? Zum::LAUFZEITENDE : Zum::JEDERZEIT;
    if (danach_ == Danach::ENDET && e.vertragsende) erste_ = e.vertragsende;
    else if (e.beginn && e.mindestlaufzeit && e.mindestlaufzeit->anzahl > 0) erste_ = plus_tage(plus(*e.beginn, *e.mindestlaufzeit), -1);
    else if (e.beginn && danach_ == Danach::UM && e.verlaengerung_um && e.verlaengerung_um->anzahl > 0)
      erste_ = plus_tage(plus(*e.beginn, *e.verlaengerung_um), -1);
  }

  // Frühestes Ende, wenn die Kündigung am Tag n ankommt.
  Datum ende_nach(const Datum &n) const {
    if (danach_ == Danach::ENDET && erste_) return *erste_;
    Datum basis = plus(n, frist_);
    if (danach_ == Danach::UM && zum_ == Zum::LAUFZEITENDE && erste_ && e_.verlaengerung_um && e_.verlaengerung_um->anzahl > 0) {
      // Laufzeiten: erste_, dann je um verlaengerung_um weiter (vom Beginn aus gerechnet, damit Monatsenden stimmen).
      Datum ende = *erste_;
      for (int k = 1; ende < basis && k < 2400; k++)
        ende = plus_tage(plus(plus_tage(*erste_, 1), Zeitraum{e_.verlaengerung_um->anzahl * k, e_.verlaengerung_um->einheit}), -1);
      return ende;
    }
    Datum d = basis;
    if (erste_ && d < *erste_) d = *erste_;
    Zum z = zum_ == Zum::LAUFZEITENDE ? Zum::JEDERZEIT : zum_;  // unbefristet: Laufzeitende gibt es nur einmal
    return aufrunden(d, z);
  }

  Ergebnis rechne(const Datum &heute) const {
    Ergebnis r;
    r.pro_monat = pro_monat();
    if (!e_.beginn) {
      if (e_.mindestlaufzeit || e_.kuendigungsfrist || e_.danach != Danach::LEER) r.status = "Beginn fehlt – ohne ihn rechnet das Paket nicht";
      return r;
    }
    const Datum beginn = *e_.beginn;
    std::string vorne = heute < beginn ? "beginnt am " + text(beginn) + " – " : "";
    if (danach_ == Danach::ENDET && !erste_) {
      r.status = vorne + "befristet – Vertragsende fehlt";
      r.laufzeit_monate = monate(beginn, heute);
      return r;
    }
    if (e_.gekuendigt_am) {
      // Ohne Kündigungsfrist, aber mit Vertragsende (z. B. ein Mietvertrag aus Vermietung 1.x nach dem Umbau, Registry
      // #163): Das eingetragene Ende gilt – sonst endete der Vertrag am Tag der Kündigung.
      const bool ende_steht = !e_.kuendigungsfrist && e_.vertragsende && !(*e_.vertragsende < *e_.gekuendigt_am);
      Datum ende = ende_steht ? *e_.vertragsende : ende_nach(*e_.gekuendigt_am);
      r.ende = ende;
      r.laufzeit_monate = monate(beginn, heute < ende ? heute : ende);
      if (ende < heute) r.status = "beendet am " + text(ende);
      else r.status = vorne + "gekündigt zum " + text(ende) + (e_.bestaetigt_am ? "" : " – Bestätigung fehlt noch");
      return r;
    }
    if (danach_ == Danach::ENDET) {
      r.ende = *erste_;
      r.fruehestes_ende = *erste_;
      r.laufzeit_monate = monate(beginn, heute < *erste_ ? heute : *erste_);
      r.status = *erste_ < heute ? "beendet am " + text(*erste_) : vorne + "läuft – endet am " + text(*erste_) + " von selbst";
      return r;
    }
    r.laufzeit_monate = monate(beginn, heute);
    const Datum frueh = ende_nach(heute);
    r.fruehestes_ende = frueh;
    // Wartet ein Laufzeitende? Dann gibt es einen letzten Tag zum Kündigen.
    const bool laufzeit = (danach_ == Danach::UM && zum_ == Zum::LAUFZEITENDE && erste_ && e_.verlaengerung_um && e_.verlaengerung_um->anzahl > 0) ||
                          (erste_ && plus(heute, frist_) <= *erste_);
    if (laufzeit) {
      Datum bis = plus(frueh, frist_, -1);
      // Rückwärts gerechnet kann ein Monatsende verrutschen (31.05. − 3 Monate = 28.02.): so spät wie möglich, aber passend.
      for (int i = 0; i < 4 && ende_nach(plus_tage(bis, 1)) == frueh; i++) bis = plus_tage(bis, 1);
      while (ende_nach(bis) != frueh && frueh > bis) bis = plus_tage(bis, -1);
      r.kuendigen_bis = bis;
      if (danach_ == Danach::UM) r.naechste_verlaengerung = plus_tage(frueh, 1);
      r.status = vorne + "läuft – kündigen bis " + text(bis) + ", Ende dann " + text(frueh);
    } else {
      std::string zum;
      switch (zum_) {
        case Zum::MONATSENDE: zum = " zum Monatsende"; break;
        case Zum::QUARTALSENDE: zum = " zum Quartalsende"; break;
        case Zum::JAHRESENDE: zum = " zum Jahresende"; break;
        default: break;
      }
      r.status = vorne + "läuft – jederzeit kündbar" + (frist_.anzahl > 0 ? " mit " + frist_text(frist_) : "") + zum +
                 ", frühestens zum " + text(frueh);
    }
    return r;
  }

 private:
  static int monate(const Datum &von, const Datum &bis) {
    if (bis < von) return 0;
    int n = (bis.j - von.j) * 12 + (bis.m - von.m);
    if (bis.t < von.t && !(bis.t == monatstage(bis.j, bis.m))) n--;
    return n < 0 ? 0 : n;
  }
  std::optional<double> pro_monat() const {
    if (!e_.betrag) return std::nullopt;
    double teiler = e_.zahlweise == "monatlich" ? 1 : e_.zahlweise == "vierteljährlich" ? 3 : e_.zahlweise == "halbjährlich" ? 6
                  : e_.zahlweise == "jährlich" ? 12 : 0;
    if (teiler == 0) return std::nullopt;
    double w = *e_.betrag / teiler;
    return (double)(long long)(w * 100 + (w >= 0 ? 0.5 : -0.5)) / 100;
  }

  Eingabe e_;
  Zeitraum frist_;
  Danach danach_;
  Zum zum_;
  std::optional<Datum> erste_;
};

inline Ergebnis rechne(const Eingabe &e, const Datum &heute) { return Rechner(e).rechne(heute); }

}  // namespace vertrag
