// Text aus E-Mails für den Volltext: Kopf (Von, An, Cc, Datum, Betreff), Text der Nachricht (Klartext bevorzugt,
// sonst HTML ohne Tags), Namen der Anhänge – und der Text von Anhängen, die das Paket selbst liest (Office, Text,
// weitere E-Mails; begrenzte Tiefe). Zerlegt werden die Mails vom gemeinsamen Zerleger (gemeinsam/mail/mail.h), den
// auch das Paket PDF/A nutzt. Nichts wird ausgeführt: kein Skript aus HTML, keine Links, keine Bilder, nichts aus dem Netz.
#pragma once
#include <string>

#include "cfb.h"
#include "mail.h"
#include "zeichen.h"

// Text eines Anhangs, wenn das Paket den Typ liest (erkennen.h). Liefert, ob etwas gelesen wurde.
inline bool anhangText(const std::string &name, const std::string &daten, zeichen::Sammler &s, int tiefe);

namespace mailtext {

struct Ergebnis {
  int anhaenge = 0;
  bool verschluesselt = false;
};

inline void nachricht(const mail::Nachricht &n, zeichen::Sammler &s, Ergebnis &e, int tiefe, const cfb::Datei *c);

inline void bloecke(const std::vector<mail::Block> &liste, zeichen::Sammler &s, Ergebnis &e, int tiefe, const cfb::Datei *c) {
  for (const mail::Block &b : liste) {
    if (s.voll) return;
    switch (b.art) {
      case mail::Block::TEXT: s.text(b.text); s.zeile(); break;
      case mail::Block::HTML: zeichen::html(b.text, s); s.zeile(); break;
      case mail::Block::ALTERNATIVE: bloecke(b.schlicht.empty() ? b.reich : b.schlicht, s, e, tiefe, c); break;
      case mail::Block::VERSCHLUESSELT:
        e.verschluesselt = true;
        s.absatz(); s.text("(verschlüsselter Inhalt)"); s.zeile();
        break;
      case mail::Block::NACHRICHT:
        s.absatz();
        if (tiefe < mail::TIEFE_MAX) nachricht(mail::eml(b.daten), s, e, tiefe + 1, nullptr);
        break;
      case mail::Block::ANHANG: {
        e.anhaenge++;
        s.absatz();
        const bool istMail = b.typ == "message/rfc822";
        s.text("Anhang: " + (!b.name.empty() ? b.name : istMail ? std::string("E-Mail") : c || b.typ.empty() ? std::string("ohne Namen") : b.typ));
        s.zeile();
        if (tiefe >= mail::TIEFE_MAX) break;
        if (b.msgOrdner >= 0 && c) nachricht(mail::Msg(*c).lies((uint32_t)b.msgOrdner, false), s, e, tiefe + 1, c);
        else anhangText(istMail ? "anhang.eml" : b.name, b.daten, s, tiefe + 1);
        break;
      }
    }
  }
}

inline void nachricht(const mail::Nachricht &n, zeichen::Sammler &s, Ergebnis &e, int tiefe, const cfb::Datei *c) {
  for (auto &f : n.kopf) { s.text(f.first + ": " + f.second); s.zeile(); }
  s.absatz();
  if (n.verschluesselt) e.verschluesselt = true;
  bloecke(n.bloecke, s, e, tiefe, c);
}

inline Ergebnis eml(const std::string &t, zeichen::Sammler &s, int tiefe = 0) {
  Ergebnis e;
  nachricht(mail::eml(t), s, e, tiefe, nullptr);
  return e;
}

inline Ergebnis msg(const cfb::Datei &c, zeichen::Sammler &s, int tiefe = 0) {
  Ergebnis e;
  nachricht(mail::Msg(c).lies(0, true), s, e, tiefe, &c);
  return e;
}

}  // namespace mailtext
