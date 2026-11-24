# Änderungen

## 3.1.0

- **Sprechendere Titel** (dms-registry #256, Thomas 24.11.2026): Konto, Freistellungsauftrag, Kontoauszug (Zeitraum „01/2026–03/2026“). Lange Namen werden auf 25 Zeichen gekürzt. Gilt für neue Installationen – Ablago übernimmt eine geänderte Titel-Vorlage beim Update nicht.

## 3.0.0

- **Kontoauszug ohne „Zeitraum“** (dms-registry #252): Das Feld wurde nirgends ausgewertet und ergibt sich aus „Von“ und „Bis“. Es entfällt.
- **Titel sprechender:** z. B. „Kontoauszug 12: 01/2026 - 03/2026 – Girokonto Sparkasse“ (Art, Nummer, Monat/Jahr von–bis, Konto gekürzt auf 25 Zeichen).
- **Aus dem Dokument:** Art, Von und Bis werden bei „Aus Dokument ausfüllen“ gelesen; „Bis“ darf nicht in der Zukunft liegen.
- **„Woran man ihn erkennt“** ist vorbelegt (de/en) – hilft der Klassifizierung beim Übernehmen von Dokumenten. Ein Update setzt es nur, wenn das Feld in Ablago noch leer ist.

## 2.2.0

- **Neuer Typ Steuernachweis** (dms-registry #250): Jahresbescheinigungen für die Steuer, die nicht von der Bank kommen – Lohnsteuerbescheinigung, Beitragsbescheinigung, Altersvorsorge, Spendenquittung, haushaltsnahe Dienstleistungen, Kinderbetreuung. Mit Steuerjahr (Pflicht, steht dann unter „Belege“), Person, „Ausgestellt von“, „Betrifft“ (Arbeitsverhältnis, Vertrag, Vorsorge, Wohnung) und Betrag – bei der Lohnsteuerbescheinigung „Bruttoarbeitslohn“. Neue Ansicht *Steuernachweise*.
- **Art am Kontoauszug ist kein Pflichtfeld mehr** (Vorgabe bleibt „Kontoauszug“): Mit 2.1.0 ließen sich Pakete, deren Beispiele einen Kontoauszug ohne Art mitbringen (Haushalt 5.0.0), nicht mehr installieren.
- **Suchwörter:** Entgeltaufstellung/Gebührenübersicht, Jahressteuerbescheinigung/Steuerbescheinigung, Spendenquittung/Zuwendungsbestätigung, Beitragsbescheinigung/Beitragsnachweis.

## 2.1.0

- **Jahresbelege der Bank** (dms-registry #248): Der Kontoauszug hat jetzt eine **Art** (Kontoauszug, Entgeltaufstellung, Jahressteuerbescheinigung, Zinsbescheinigung, Saldenbestätigung), den Zeitraum **Jahr** und einen Verweis aufs **Steuerjahr** – damit steht z. B. die Entgeltaufstellung unter „Belege“ am Steuerjahr. Der Titel nennt die Art; bestehende Auszüge ohne Art zeigen sie erst nach dem Speichern.

## 2.0.0

- **Steuerbescheide sind Bescheide** (dms-registry #225): Am Steuerjahr entfallen „Bescheid vom“, „Erstattung/Nachzahlung“, „Einspruch bis“ und die Bescheid-Felder bei Umsatz- und Gewerbesteuer. Den Steuerbescheid legst du als **Bescheid** aus dem Paket „Ämter & Papiere“ an und wählst unter „Betrifft“ das Steuerjahr – dort steht er dann unter „Belege“. Die Automatisierung „Einspruchsfrist“ und der Tipp dazu sind mitgezogen.
- **Ohne Update-Weg:** Ablago wird neu aufgesetzt; bestehende Werte in den entfallenen Feldern zieht kein Umzug um.

## 1.2.1

- **Mehrzahl** für die Mappentypen (dms-registry #223): Listen zeigen jetzt z. B. „12 Kontoauszüge“ statt „12 × Kontoauszug“ (ab Ablago 0.302.0, ältere ignorieren es). Ein Update setzt die Mehrzahl nur, wo du noch keine eingetragen hast.
- **Treffendere Symbole** der Ansichten aus den 259 Symbolen von Ablago 0.304 (dms-registry #230): Konten (Bank), Kontoauszüge, Freistellungsaufträge, Steuerjahre. Ältere Ablago-Versionen zeigen ein neues Symbol einfach nicht.

## 1.2.0

- Ansichten mit Symbolen. Ein Update nimmt keine Ansichten weg: In bestehenden Ablagen bleiben weggefallene Ansichten stehen, bis du sie löschst (Thomas, 20.11.2026).

## 1.1.0

- **Tipps auf Englisch** (Ablago #1307, dms-registry #202): Die Texte der drei Tipps stehen jetzt in `texte/de/entdecken.json` und `texte/en/entdecken.json`. Ablago zeigt sie in der Sprache der Person. Braucht **Ablago 0.293.2**.

## 1.0.0

- Erste Fassung (dms-registry #212): **Konto** und **Steuerjahr** aus dem Paket Haushalt, dazu **Kontoauszug** und **Freistellungsauftrag**.
  - Konto: Titel „{Bank} von {Inhaber} ({Art})“; Register „Kontoauszüge“ und „Was läuft über dieses Konto?“.
  - Steuerjahr: bei „beruflich genutzt“ ein Abschnitt mit Umsatzsteuer, Gewerbesteuer und Jahresabschluss; „Belege“ zeigt alles, was auf das Jahr zeigt.
  - Automatisierung „Einspruchsfrist beim Steuerbescheid“ und zwei Tipps aus Haushalt.
- Braucht **Ablago 0.285.0** und **Basis 1.7.0**. Ein Umzug aus Haushalt 2.x ist nicht vorgesehen.
