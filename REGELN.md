# Regeln für Pakete

## Lizenzen

Jedes Paket steht unter einer dieser Open-Source-Lizenzen (Kennung nach [SPDX](https://spdx.org/licenses/), so in `manifest.yaml` unter `lizenz`):

`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `MPL-2.0`, `LGPL-3.0-or-later`, `GPL-3.0-or-later`, `AGPL-3.0-or-later`, `CC0-1.0` (nur für reine Konfiguration)

Der vollständige Lizenztext liegt als `LICENSE` im Paketordner. Fremder Code im Paket braucht eine dazu passende Lizenz und einen Hinweis im README.

## Erlaubt

- Mappentypen, Sichten, Rollen, Beispiel-Mappen
- Code, der über die API des DMS arbeitet (sobald der Paket-Läufer verfügbar ist)
- Zugriff auf Netzwerk/Internet nur zu Adressen, die im Manifest stehen (`code.netz`) und deren Zweck das README erklärt. Ohne `code.netz` hat ein Paket keinen Zugriff auf Netzwerk und Internet.

## Verboten

- **Fertige Programmdateien** jeder Art (`.wasm`, `.so`, `.dll`, `.exe`, `.jar`, `.bin` …). Gebaut wird in der CI aus dem Quellcode.
- Verschleierter oder minifizierter Quellcode
- Telemetrie, Tracking, Werbung
- Zugriff auf Netzwerk/Internet zu Adressen, die nicht im Manifest stehen
- Mehr Rechte als nötig, z. B. Schreibrecht, wo Lesen reicht
- Echte persönliche Daten in Beispielen, Tests oder Screenshots
- Löschen von Feldern, Registern oder Mappen bei einem Update

## So sehen Administratoren die Rechte

Vor der Installation zeigt das DMS die Rechte eines Pakets mit Code, die Katalog-Webseite genauso:

- „Mappen lesen: …“, „Mappen anlegen und ändern: …“, „Dokumente lesen“ bzw. „Dokumente lesen und Volltext schreiben“
- „kein Zugriff auf Netzwerk und Internet“ bzw. „Zugriff auf Netzwerk/Internet nur zu: …“
- „Reagiert auf diese Ereignisse:“ mit einem Ereignis je Zeile

Erklärt sind sie im Administratorhandbuch unter [Pakete mit Code](https://motom001.github.io/dms/admin/aktuell/pakete/#rechte-eines-pakets). Schreibe im README eines Pakets mit Code im Abschnitt „Rechte und Netzwerkzugriff“ (wie in der [Vorlage](vorlage/README.md)) mit denselben Worten, was das Paket darf und wozu.

## Pflicht

- `manifest.yaml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `inhalt/` (ggf. leer), `tests/`
- Paket-Id = Ordnername: Kleinbuchstaben, Ziffern, `_`, beginnt mit einem Buchstaben, höchstens 20 Zeichen
- Bei jeder Änderung eine höhere Version (SemVer) und ein Eintrag im `CHANGELOG.md`
- Deutsche Texte in Feldern und Sichten; das README auf Deutsch, gern zusätzlich auf Englisch
- Ein Pfleger in `CODEOWNERS`

## Einstellungen

- Pakete mit Code **beschreiben** ihre Einstellungen im Manifest (`code.einstellungen`, `code.aktionen`). Das DMS zeigt das Formular, prüft die Werte, speichert sie (Teil der Sicherung) und gibt sie dem Paket.
- **Zugangsdaten nur als `geheim`**, nie als `text` und nie als `standard`. Das DMS verschlüsselt Geheimnisse und zeigt sie nach dem Speichern nicht mehr an.
- Einstellungen ändern ist Sache des DMS. Ein Paket speichert seine Einstellungen nicht selbst irgendwo anders und bringt keine eigene Oberfläche dafür mit.

## Namen

Schlüssel von Mappentypen, Feldern und Registern sind **im Paket lokal**, z. B. `versicherung`. Das DMS legt sie mit der Paket-Id davor an (`haushalt_versicherung`), damit sich zwei Pakete nicht in die Quere kommen. Angezeigt wird nur der Name („Versicherung“). Verweise auf Typen anderer Pakete schreibst du als `<paket>:<schluessel>`, z. B. `basis:organisation`. Das andere Paket muss dann unter `abhaengigkeiten` stehen. Auf Mappentypen, die das DMS selbst mitbringt, verweist du mit `dms:` – ohne Abhängigkeit: `dms:ablageort` (wo ein Original liegt), `dms:benutzer` und `dms:rolle`. Dafür muss im Manifest `dms: ">=0.75.0"` stehen. Die Paket-Id `dms` ist deshalb vergeben.

Beispiel-Mappen dürfen aufeinander verweisen (ab DMS 0.79.0): Ein Beispiel bekommt einen `schluessel`, ein Verweisfeld eines anderen Beispiels den Wert `{ beispiel: strom }` – oder `{ beispiel: "basis:stadtwerke" }` für ein Beispiel einer Abhängigkeit. Dann muss im Manifest `dms: ">=0.79.0"` stehen.

## Felder für die Erkennung

Das DMS erkennt Post und füllt Mappen aus Dokumenten (DMS #336, #391) – ohne KI, mit Mustern und dem Abgleich mit vorhandenen Mappen. Welche Felder es dafür nutzt, sagt das Paket mit der Feld-Eigenschaft `erkennung`:

```yaml
- key: kundennummer
  label: Kundennummer
  typ: text
  erkennung: { art: nummer, hinweis: "Steht meist oben rechts im Brief" }
- { key: email, label: E-Mail, typ: text, erkennung: {} }   # art ergibt sich aus der Bezeichnung
```

- **Markiere, was ein Schreiben eindeutig zuordnet:** Kunden-, Vertrags-, Versicherungs- oder Aktenzeichen, Kennzeichen, IBAN, Umsatzsteuer-Id, E-Mail-Adresse, Internetseite, Telefon, Name. Hat ein Typ markierte Namen oder Kontaktangaben (`name`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`), gilt er als möglicher **Absender** (Organisation, Person); markiert er nur Nummern, als mögliche **Zielmappe**.
- **Markiere, was „Aus Dokument ausfüllen“ füllen soll:** Datum, Betrag, Anschrift, Vorname/Nachname, Funktion, Verweise (z. B. Werkstatt einer Rechnung). Hat ein Typ markierte Felder, füllt das DMS nur diese.
- **Nicht markieren**, was in fremden Briefen ständig vorkommt und nichts zuordnet – z. B. die IBAN des eigenen Kontos (steht in jeder Lastschrift) oder eine Nummer, die viele Mappen gemeinsam haben.
- Nur bei den Feldarten `text`, `langtext`, `zahl`, `betrag`, `datum`, `auswahl` und `referenz`; nie bei `passwort`. `art` (optional) muss zur Feldart passen: `name`, `vorname`, `nachname`, `funktion`, `nummer`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`, `strasse`, `hausnummer`, `plz`, `ort` bei Text; `nummer`, `plz`, `hausnummer`, `betrag` bei Zahl; `datum`, `betrag`, `auswahl`, `verweis` bei der gleichnamigen Feldart. `hinweis` hat höchstens 300 Zeichen; ein Muster nach dem Wort *Muster* (`#` = Ziffer, `A` = Großbuchstabe, z. B. „Muster 100-####“) sucht das DMS gezielt.
- Wer `erkennung` nutzt, schreibt im Manifest `dms: ">=0.113.0"`. Ein Update des Pakets übernimmt die Markierung an installierten Feldern, an denen der Administrator nichts zur Erkennung eingestellt hat; das ist eine Patch-Version (mit neuen Feldern eine Minor-Version).

`werkzeuge/pruefen.py` prüft Feldart, Art und DMS-Version.

## Verwaiste Pakete

Antwortet der Pfleger auf Fehler oder nötige Anpassungen drei Monate lang nicht, wird das Paket als *verwaist* markiert und kann von jemand anderem übernommen werden.
