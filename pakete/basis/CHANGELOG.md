# Änderungen

## 1.5.0

- Neu: **englische Beschriftungen** für Mappentypen, Felder, Auswahlwerte, Register und Ansichten (`beschriftungen.en`, Registry #116 und #135). Ablago ab 0.200.0 zeigt sie, wenn jemand Englisch gewählt hat; ein Update ergänzt sie an installierten Mappentypen, ohne eigene Beschriftungen zu überschreiben. Ältere Ablago-Versionen übergehen sie – dafür braucht es kein höheres `dms`. Gespeicherte Werte ändern sich nicht.

## 1.4.2

- Text: Hinweis am Geburtstag – eine jährliche Erinnerung legt man seit Ablago 0.177.0 als Automatisierung „Datum erreicht“ an.

## 1.4.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.4.0

- Neu: **gleichbedeutende Wörter** für die Suche (DMS #356) – wer „Rechnung“ sucht, findet auch „Beleg“; dazu Quittung/Kassenbon/Kassenzettel, Vertrag/Vereinbarung, Kündigung/Beendigung, Police/Versicherungsschein, Mahnung/Zahlungserinnerung, Gutschrift/Erstattung, Lastschrift/Abbuchung und Anschrift/Adresse. Nur allgemeine Wörter; fachliche bringen die Fachpakete mit (z. B. Fahrzeuge, Vermietung).
- Braucht DMS ab 0.127.0 (Wortlisten). Mappentypen, Sichten und Beispiele sind unverändert.

## 1.3.0

- **Formate** (dms-registry #55, DMS #535): Telefon, Fax und Mobil prüft das DMS als Telefonnummer, E-Mail als E-Mail-Adresse, Internetseite als Internetseite und die IBAN der Organisation mit Länge und Prüfziffer. Die PLZ hat in Deutschland genau 5 Ziffern; steht im Feld *Land* ein anderes Land, ist sie frei. Am Handy erscheint die passende Tastatur, Telefon und E-Mail lassen sich antippen.
- Person: Der **Geburtstag** darf nicht in der Zukunft liegen.
- Braucht DMS ab 0.121.0. Gespeicherte Angaben bleiben gültig; das Update übernimmt Formate und Grenzen nur an Feldern, an denen du in der Werkbank nichts davon eingestellt hast. Welche Angaben nicht passen, zeigt Werkbank → Wartungsoperationen.

## 1.2.0

- **Erkennung** (dms-registry #49, DMS #336/#391): Die Felder sind „für die Erkennung“ markiert. Post wird so ohne eigene Einrichtung dem richtigen Absender zugeordnet – an Kundennummer, IBAN, Umsatzsteuer-Id, E-Mail-Adresse bzw. -Domain, Internetseite, Telefon oder Name. „Visitenkarte scannen“ füllt bei einer Person Name, Funktion, Organisation, Telefon, Mobil, E-Mail und Anschrift.
  - Organisation: Name, Kürzel, Kundennummer (mit Erkennungshinweis), Telefon, Fax, E-Mail, Internetseite, Anschrift.
  - Niederlassung: Organisation, Name, Nummer, Kontakt und Anschrift. Person: Vorname, Nachname, Funktion, Organisation, Telefon, Mobil, E-Mail, Anschrift.
- Neu in Organisation: Felder **IBAN** und **Umsatzsteuer-Id** (Register Stammdaten) – starke Merkmale für die Erkennung.
- Braucht DMS ab 0.113.0. Das Update ergänzt die beiden Felder und übernimmt die Markierung nur an Feldern, an denen du in der Werkbank nichts zur Erkennung eingestellt hast.

## 1.1.1

- Lizenz: ab dieser Version **Apache-2.0** (vorher MIT), wie alle Pakete von motom001. Inhalt unverändert.

## 1.1.0

- Neu: Mappentyp **Niederlassung** (Filiale, Zweigstelle, Praxis, Außenstelle einer Organisation) mit eigener Anschrift, Kontakt und Ansprechpartnern.
- Neu: Mappentyp **Person** (Kontakt – kein Benutzer des DMS) mit Beziehung, Arbeit (Organisation, Niederlassung, Funktion), Kontakt und Anschrift.
- Organisation: neue Register **Niederlassungen** und **Ansprechpartner**; Register „Protokoll“ heißt wie im DMS „Historie“ (nur bei Neuinstallation – vorhandene hat das DMS schon umbenannt).
- Neue Sichten *Niederlassungen*, *Personen* mit *Familie und Freunde* und *Ansprechpartner*.
- Beispiele: Sparkasse Musterstadt mit zwei Filialen, eine Kundenberaterin, ein Hausarzt, Oma Muster – mit Verweisen untereinander.
- Braucht DMS ab 0.79.0 (Verweise zwischen Beispielen). Das Update von 1.0.0 ergänzt nur; vorhandene Organisationen bleiben unverändert.

## 1.0.0

- Erste Fassung.
