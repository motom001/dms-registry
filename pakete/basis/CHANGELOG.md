# Änderungen

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
