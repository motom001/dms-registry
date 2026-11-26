# Änderungen

## 5.6.0

- **„Woran man ihn erkennt“ kürzer** (dms-registry #267): je Mappentyp vier bis sechs Wörter, die fast jedes Dokument dieses Typs enthält, statt langer Listen. Lange Listen sprachen bei Ablago oft gegen den richtigen Typ, weil jedes Dokument nur wenige ihrer Wörter enthält. Ein Update übernimmt den Text, solange ihr ihn nicht selbst geändert habt.
- **Aus dem Dokument gefüllt:** Art und Anlass der arbeitsmedizinischen Vorsorge – steht der Wert wörtlich im Dokument, schlägt Ablago ihn vor.

## 5.5.0

- **„Woran man ihn erkennt“** für jeden Mappentyp, Deutsch und Englisch (dms-registry #254): Was auf dem Papier steht – Überschriften, Begriffe, Nummern. Hilft Ablago beim Vorschlag „Wohin gehört das?“. Ein Update setzt den Text, solange ihr ihn nicht selbst geändert habt. Das Arbeitsverhältnis liest Beginn, Ende und Tätigkeit.

## 5.4.0

- **Steuerjahr aus dem Datum** (dms-registry #261): Anschaffung aus dem Kaufdatum, Bildung aus „Bis“; beide Daten werden aus dem Dokument gelesen. Braucht Ablago ab 0.321.0.

## 5.3.0

- **Sprechendere Titel** (dms-registry #256, Thomas 24.11.2026): Anschaffung (Kaufmonat), Arbeitsverhältnis (Beginn), Arbeitsmedizin (Datum), Vorsorge. Lange Namen werden auf 25 Zeichen gekürzt. Gilt für neue Installationen – Ablago übernimmt eine geänderte Titel-Vorlage beim Update nicht.

## 5.2.0

- **Beispiele:** Die Kontoauszüge von Familie Muster ohne „Zeitraum“ – das Feld gibt es ab Finanzen 3.0.0 nicht mehr (dms-registry #252).

## 5.1.0

- **Tipp am Arbeitsverhältnis** (dms-registry #250): Die Lohnsteuerbescheinigung legst du als **Steuernachweis** (Paket Finanzen 2.2.0) an und wählst unter „Betrifft“ das Arbeitsverhältnis – dann steht sie dort unter „Verknüpfungen“ und am Steuerjahr unter „Belege“. Braucht Finanzen ab 2.2.0.
- **Beispiele:** Familie Muster hat jetzt eine Jahressteuerbescheinigung vom Depot und Toms Lohnsteuerbescheinigung 2025, beide am Steuerjahr 2025; der Kontoauszug nennt seine Art.

## 5.0.0

- **„Gesundheit“ ist umgezogen** (dms-registry #226): Gesundheitsunterlagen legst du im neuen Paket **Gesundheit** an – mit Behandlungsfall, Arztbrief & Befund, Therapie, Arbeitsunfähigkeit, Medikamentenplan, Gesundheitspass und Impfung. Mit dem Typ sind die Ansicht und das Beispiel weggefallen.
- **Ohne Update-Weg:** Ablago wird neu aufgesetzt.

## 4.0.0

- **„Ausweis & Urkunde“ ist umgezogen** (dms-registry #225): Ausweise und Urkunden legst du im Paket „Ämter & Papiere“ an (getrennt in Ausweis und Urkunde). Mit ihnen sind die Ansichten „Ausweise & Urkunden“ und „Läuft bald ab“, die Automatisierung „Ausweis läuft bald ab“, der Rundgang „Ausweis ablegen“ und die Beispiele dorthin gezogen; Zeugnisse bleiben bei Bildung.
- **Familie Muster** kommt jetzt aus den Beispielen von Basis (ab 1.10.0); die Beispiele hier zeigen darauf.
- **Ohne Update-Weg:** Ablago wird neu aufgesetzt.

## 3.3.0

- **Neuer Mappentyp „Arbeitsmedizinische Vorsorge“** (dms-registry #228): die Vorsorgebescheinigung nach ArbMedVV mit Person, Arbeitsverhältnis, Datum, Ärztin/Arzt, Anlass, Art (Pflicht-, Angebots-, Wunschvorsorge) und nächster Vorsorge. Eine Mappe je Anlass; am Arbeitsverhältnis erscheinen sie unter „Verknüpfungen“. Dazu eine Ansicht, ein Beispiel für Tom und die Automatisierung „Nächste arbeitsmedizinische Vorsorge“ (6 Wochen vorher, nach der Installation aus).
- **Rundgang „Ausweis ablegen“** mit einem Schritt mehr: Briefe gehören als Dokument zu ihrer Sache, sonst zum Absender (dms-registry #228).
- **Mehrzahl** für die Mappentypen (dms-registry #223): Listen zeigen jetzt z. B. „12 Arbeitsverhältnisse“ statt „12 × Arbeitsverhältnis“ (ab Ablago 0.302.0, ältere ignorieren es). Ein Update setzt die Mehrzahl nur, wo du noch keine eingetragen hast. Wo es keine echte Mehrzahl gibt, heißt es „Gesundheitsmappen“, „Vorsorgeverträge“ und „Bildungswege“.
- **Treffendere Symbole** der Ansichten aus den 259 Symbolen von Ablago 0.304 (dms-registry #230): Arbeitsverhältnisse (Aktentasche), Ausweise & Urkunden (Ausweis), „Läuft bald ab“ mit Kalender und Uhr, „Garantie läuft ab“ (Siegel). Ältere Ablago-Versionen zeigen ein neues Symbol einfach nicht.

## 3.2.0

- Ansichten mit Symbolen: *Haushalt*, darunter je Mappentyp eine Ansicht sowie *Läuft bald ab* und *Garantie läuft ab*. *Verträge*, *Versicherungen* (mit Sach- und Personenversicherungen) und *Kündigung in den nächsten 3 Monaten* entfallen – sie stehen im Paket Verträge. Ein Update nimmt keine Ansichten weg: In bestehenden Ablagen bleiben weggefallene Ansichten stehen, bis du sie löschst (Thomas, 20.11.2026).

## 3.1.0

- **Rundgang und Tipp auf Englisch** (Ablago #1307, dms-registry #202): Die Texte von „Ausweis ablegen“ und vom Tipp zu *Garantie bis* stehen jetzt in `texte/de/entdecken.json` und `texte/en/entdecken.json`. Ablago zeigt sie in der Sprache der Person. Braucht **Ablago 0.293.2**.

## 3.0.0

- **Konto und Steuerjahr kommen aus dem Paket Finanzen** (dms-registry #212). Haushalt hängt von Finanzen 1.0.0 ab; *Steuerjahr* an Arbeitsverhältnis, Gesundheit, Anschaffung und Bildung zeigt auf das Steuerjahr aus Finanzen. Ansichten *Konten* und *Steuerjahre*, die Automatisierung „Einspruchsfrist beim Steuerbescheid“ und die beiden Tipps zum Steuerjahr sind jetzt dort.
- **Bausparen** ist keine Art der Vorsorge mehr – ein Bausparvertrag ist ein Konto (Paket Finanzen).
- Beispiele: Konten und Steuerjahr sind Mappen aus Finanzen, dazu ein Kontoauszug zum Depot und ein Freistellungsauftrag.
- **Kein Umzug:** Vorhandene Konten und Steuerjahre aus Haushalt 2.x ziehen nicht mit. Haushalt 3.0.0 ist für eine neu aufgebaute Ablage gedacht.

## 2.2.0

- **Rechnungen kommen aus dem Paket Rechnungen und Bestellungen** (dms-registry #208), dem Nachfolger des Pakets Rechnungen. Register, Ansichten und Verweise zeigen auf dessen Rechnung. Einen Umzug aus dem alten Paket gibt es nicht (nur eine Installation, die neu aufgebaut wird). Ablago weiter ab 0.285.0.

## 2.1.1

- Beispiele (dms-registry #205): Das Girokonto nutzt die Test-IBAN aus REGELN.md (`DE89 3704 0044 0532 0130 00`); Jonas’ Impfung zeigt auf die „Hausarztpraxis am Lindenweg“ aus Basis 1.7.2. Bereits angelegte Beispiel-Mappen bleiben, wie sie sind.

## 2.1.0

- Neu: **Rundgang „Ausweis ablegen“** (dms-registry #132) – zeigt in vier Schritten an einem leeren Formular, wo Art, Person, „Gültig bis“ und der Ort des Originals hingehören; gespeichert wird dabei nichts. Ablago bietet ihn nach der Installation 30 Tage lang als Tipp an, danach steht er unter „Ablago entdecken“.
- Neu: **drei Tipps** – „Garantie bis“ an der Anschaffung, „Einspruch bis“ und „Belege“ am Steuerjahr.
- Braucht Ablago 0.285.0; ältere Versionen bleiben bei 2.0.0.

## 2.0.0

- **Breaking Change – Vertrag und Versicherung ziehen ins Paket Verträge** (dms-registry #163): Haushalt bringt die Mappentypen *Vertrag* und *Versicherung* nicht mehr mit. Verträge und Versicherungen legst du als **Vertrag** aus dem Paket Verträge an (Versicherung ist dort eine Vertragsart); es rechnet *Kündigen bis* selbst aus. Bestehende Mappen ziehen beim Installieren bzw. Aktualisieren von **Verträge 1.1.0** dorthin um – mit allen Werten, Dokumenten, Verknüpfungen, Ansichten und Rechten (Ablago 0.243.0, „Umbau“). Deshalb erst Verträge, dann Rechnungen, dann dieses Update.
- Neu an der **Anschaffung:** Register *Rechnungen* – Kassenbon und Rechnung sind Rechnungen aus dem Paket Rechnungen mit *Betrifft* = diese Anschaffung. Am **Steuerjahr** erscheinen unter *Belege* auch Rechnungen mit diesem Steuerjahr.
- Ansichten *Verträge*, *Versicherungen* (Verträge mit ausgefüllter Versicherung), *Sach-* und *Personenversicherungen* und *Kündigung in den nächsten 3 Monaten* zeigen jetzt Verträge aus dem Paket Verträge. Die Automatisierungen „Kündigung … bald fällig“ entfallen (das Paket Verträge bringt „Vertrag rechtzeitig kündigen“ mit); „Hauptfälligkeit einer Versicherung“ bleibt und gilt für Verträge.
- In einer bestehenden Ablage bleiben die bisherigen Ansichten, wie sie sind; nach dem Umzug zeigen *Verträge* und *Versicherungen* dort **alle** Verträge (auch Mietverträge). Am einfachsten setzt du bei *Versicherungen* die Bedingung „Versicherung ist nicht leer“.
- Die Beispiel-Verträge und -Versicherungen entfallen (Beispiele bringt das Paket Verträge mit).
- Hängt jetzt ab von **Basis 1.7.0, Verträge 1.1.0 und Rechnungen 1.1.0**; braucht Ablago 0.243.0.

## 1.4.1

- Das Feld **Verbleib Originaldokumente** verweist auf den Ablageort aus dem Paket **Basis** (`basis:ablageort` statt `dms:ablageort`, dms-registry #138, Ablago #883). Braucht Basis ab 1.6.0 und Ablago ab 0.212.0. In einer bestehenden Ablage ändert sich nichts: Basis übernimmt den bisherigen Ablageort mit allen Orten, das Feld zeigt weiter darauf.

## 1.4.0

- Neu: **englische Beschriftungen** für Mappentypen, Felder, Auswahlwerte, Register und Ansichten (`beschriftungen.en`, Registry #116 und #135). Ablago ab 0.200.0 zeigt sie, wenn jemand Englisch gewählt hat; ein Update ergänzt sie an installierten Mappentypen, ohne eigene Beschriftungen zu überschreiben. Ältere Ablago-Versionen übergehen sie – dafür braucht es kein höheres `dms`. Gespeicherte Werte ändern sich nicht.

## 1.3.0

- Neu: **vorgefertigte Automatisierungen** für jede Frist (6). Seit Ablago 0.177.0 erinnert ein Datumsfeld nicht mehr selbst – die Automatisierung „Datum erreicht“ tut es, Vorlaufzeit, Empfänger und Text stellst du selbst ein. Beim Installieren fragt Ablago, welche gleich eingeschaltet werden (Vorgabe: alle); bei einem Update ersetzt die mitgelieferte die übernommene Erinnerung, solange du sie nicht geändert hast.
- Braucht Ablago ab 0.177.0.

## 1.2.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.2.0

- **Formate** (dms-registry #55, DMS #535): Die **IBAN** eines Kontos prüft das DMS mit Länge und Prüfziffer und zeigt sie in Vierergruppen. Der Ausweis bleibt bei „Gültig bis“ ohne Grenze – das Datum liegt ja meist in der Zukunft.
- Braucht DMS ab 0.121.0. Gespeicherte Angaben bleiben gültig; das Update übernimmt das Format nur, wenn du am Feld nichts davon eingestellt hast.

## 1.1.0

- **Personen als Verweis** (dms-registry #52, DMS #534): Wo ein Mensch gemeint ist, steht jetzt ein Verweis auf eine **Person** aus dem Paket Basis statt Text – **Konto → Inhaber** (mehrere, z. B. Gemeinschaftskonto), **Versicherung → Versichert** (mehrere), **Arbeitsverhältnis, Vorsorge, Ausweis & Urkunde, Gesundheit, Bildung → Person**. Verweisart Bezug: Wer eine Person löscht, löscht damit nicht Konto oder Vertrag. An der Person siehst du unter *Verknüpfungen* alles, was zu ihr gehört.
  - Titel und Trefferlisten zeigen den Namen der verwiesenen Person. Sachen (z. B. das Auto) verweisen selbst auf ihre Versicherung und stehen dort unter *Verknüpfungen*.
  - **Update:** Die bisherigen Textfelder bleiben mit allen Werten; die Verweisfelder kommen dazu. Unter **Werkbank → Pakete → Haushalt → Text in Verweise umwandeln** schlägt das DMS je Name eine vorhandene Person vor oder legt eine neue an („Lena und Tom Muster“ wird zu zwei Personen) – erst nach deiner Vorschau, rückgängig zu machen. Updates ändern nichts heimlich.
  - Die Verweisfelder sind keine Pflicht (auch wo „Person“ als Text Pflicht war), damit vorhandene Mappen nach dem Update passen.
- **Beispiele:** Familie Muster heißt jetzt Lena, Tom und Jonas und ist als drei **Personen** dabei; Konten, Versicherungen, Arbeitsverhältnis, Vorsorge, Ausweis, Gesundheit und Bildung verweisen auf sie (18 Beispiele).
- Braucht DMS ab 0.120.0 und Basis ab 1.1.0 (Person).

## 1.0.3

- **Erkennung** (dms-registry #49, DMS #336/#391): **Vertragsnummer** (Vertrag, Vorsorge) und **Versicherungsnummer** sind „für die Erkennung“ markiert – Post mit dieser Nummer wird dem Vertrag bzw. der Versicherung vorgeschlagen und kann, wenn du es am Mappentyp einschaltest, automatisch zugeordnet werden.
- Die IBAN eines Kontos bleibt bewusst unmarkiert: Sie steht in fast jedem Lastschrift-Brief und würde dann jede Rechnung dem Konto zuordnen.
- Braucht DMS ab 0.113.0. Das Update übernimmt die Markierung nur an Feldern, an denen du nichts zur Erkennung eingestellt hast.

## 1.0.2

- Lizenz: ab dieser Version **Apache-2.0** (vorher MIT), wie alle Pakete von motom001. Inhalt unverändert.

## 1.0.1

- Beispiele zeigen jetzt aufeinander und auf Basis: Girokonto → Sparkasse, Strom → Stadtwerke, Impfung → Praxis Dr. Beispiel, Arbeitsverhältnis → Steuerjahr 2025. Neues Beispiel Kfz-Versicherung (für das Paket Fahrzeuge).
- Braucht DMS ab 0.79.0 (Verweise zwischen Beispielen).

## 1.0.0

- Erste Fassung.
