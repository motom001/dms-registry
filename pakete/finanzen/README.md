# Finanzen

Das Paket **Finanzen** bringt Konten, Kontoauszüge, Freistellungsaufträge und Steuerjahre nach Ablago – für den Haushalt genauso wie für den Betrieb. Die Pakete **Haushalt** und **Rechnungen und Bestellungen** bauen darauf auf. **Ablago bucht nicht:** Kontostände, Buchungen, Kassenbuch und Budgets bleiben im Online-Banking bzw. in der Buchhaltung.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Konto | Girokonto, Sparkonto, Tagesgeld, Depot, Kreditkarte, Kredit, Bausparvertrag – auch PayPal und ähnliche Dienste | Bank, Art, Inhaber (Personen oder im Betrieb die Firma), IBAN, Konto- oder Kartennummer, Online-Zugang (Passwort), eröffnet/gekündigt am | – |
| Kontoauszug | Auszug zu einem Konto, je Monat oder Quartal | Konto, Auszugsnummer, Zeitraum, von, bis | – |
| Freistellungsauftrag | steuerfreie Kapitalerträge je Bank und Person | Bank, Betrag, Jahr, Person | – |
| Steuerjahr | die Steuern eines Jahres | Jahr (eindeutig), abgegeben am, Steuerberater | – |

**Konto:** Der Titel lautet „{Bank} von {Inhaber} ({Art})“, z. B. „Sparkasse Musterstadt von Lena Muster, Tom Muster (Girokonto)“. Bei PayPal und ähnlichen Diensten ist der Dienst die Bank, als Art wählst du das Konto oder die Karte dahinter. Unter *Kontoauszüge* stehen die Auszüge des Kontos, unter **Was läuft über dieses Konto?** alles, was darauf zeigt: Verträge mit *Abbuchung von Konto* (Paket Verträge), Rechnungen mit *Konto* (Paket Rechnungen und Bestellungen), Mietverträge mit *Kautionskonto* und die Auszüge. Das hilft beim Kontowechsel.

**Steuerjahr:** Unter *Belege* steht alles, was auf das Steuerjahr zeigt – ab 2.0.0 auch der Steuerbescheid (ein **Bescheid** aus dem Paket „Ämter & Papiere“ mit *Betrifft* = Steuerjahr, dort mit Einspruchsfrist und Erinnerung), dazu Rechnungen, Anschaffungen, Arztkosten, Fortbildungen, Arbeitsverhältnisse, Nebenkostenabrechnungen, je nachdem, welche Pakete installiert sind. Ist die Ablage als „beruflich genutzt“ eingerichtet, hat das Steuerjahr zusätzlich die Abschnitte **Umsatzsteuer**, **Gewerbesteuer** und **Jahresabschluss** (Einnahmenüberschussrechnung oder Bilanz). Ein eigenes Geschäftsjahr gibt es nicht.

**Ansichten:** *Finanzen* mit allem, darunter *Konten*, *Kontoauszüge*, *Freistellungsaufträge* und *Steuerjahre*.

**Tipps:** Zwei kurze Tipps führen zu *Belege* am Steuerjahr und zu den *Kontoauszügen* am Konto – auf Deutsch und Englisch, je nach Sprache der Person.

**Beispiele:** Das Paket bringt selbst keine mit. Mit dem Paket Haushalt kommen Konten, ein Kontoauszug, ein Freistellungsauftrag und das Steuerjahr 2025 der erfundenen Familie Muster; den Steuerbescheid dazu bringt „Ämter & Papiere“ mit.

## Voraussetzungen

- Ablago ab 0.293.2 (Tipps in mehreren Sprachen)
- Paket **Basis** ab 1.7.0 (Organisation für Bank und Steuerberater, Person für Inhaber) – kommt bei der Installation aus dem Katalog mit

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Ansichten, eine Automatisierung und Tipps an.

## Wer was sehen darf

Konten tragen die Zugangsdaten zum Online-Banking (Feldart Passwort – nur wer die Mappe bearbeiten darf, sieht sie). Wer Konten nur bestimmten Personen zeigen will, legt am Mappentyp **Konto** eine Regel unter **Berechtigungen** an; ein Beispiel steht im README des Pakets Haushalt.

## Nach der Installation

1. Die eigenen Banken und den Steuerberater als **Organisation** anlegen.
2. Je Konto eine Mappe anlegen; Auszüge, die noch auf Papier oder als PDF kommen, als **Kontoauszug** dazu.
3. Je Jahr ein **Steuerjahr** anlegen und an Rechnungen und Belegen eintragen.

## Haushalt 2.x

Bis Haushalt 2.x standen Konto und Steuerjahr im Paket Haushalt. Einen Umzug vorhandener Mappen gibt es nicht; Finanzen 1.0.0 und Haushalt 3.0.0 sind für eine neu aufgebaute Ablage gedacht.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Finanzen“ im Titel.
