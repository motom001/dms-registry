# Rules for packages

[Deutsch](REGELN.md) · **English**

> This is a translation. If the German and English versions differ, the German version ([REGELN.md](REGELN.md)) applies.

## Licences

Every package is licensed under one of these open source licences (identifier according to [SPDX](https://spdx.org/licenses/), written like this in `manifest.yaml` under `lizenz`):

`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `MPL-2.0`, `LGPL-3.0-or-later`, `GPL-3.0-or-later`, `AGPL-3.0-or-later`, `CC0-1.0` (only for pure configuration)

The full licence text is in the package folder as `LICENSE`. Third-party code in the package needs a compatible licence and a note in the README.

## Allowed

- Mappe types, views, roles, sample Mappen
- Word lists: synonyms for the search (see [Word lists](#word-lists))
- Code that works through the DMS API (as soon as the package runner is available)
- Access to the network/internet only to addresses listed in the manifest (`code.netz`) whose purpose the README explains. Without `code.netz`, a package has no access to the network or the internet.

## Forbidden

- **Ready-made binaries** of any kind (`.wasm`, `.so`, `.dll`, `.exe`, `.jar`, `.bin` …). They are built in the CI from source code.
- Obfuscated or minified source code
- Telemetry, tracking, advertising
- Access to the network/internet to addresses not listed in the manifest – except to the service address the administrator enters and confirms in a setting of type `adresse`
- A preset service address of an external provider (cloud) – not even as `beispiel`
- More permissions than necessary, e.g. write access where read access is enough
- Real personal data in samples, tests or screenshots
- Deleting fields, tabs or Mappen during an update (a text field replaced by a reference with `aus_text` may leave the package – see [Turning text into a reference](#turning-text-into-a-reference))

## How administrators see the permissions

Before installation, the DMS shows the permissions of a package with code, and the catalogue website does the same. The wording is German:

- „Mappen lesen: …“ (read Mappen), „Mappen anlegen und ändern: …“ (create and change Mappen), „Dokumente lesen“ (read documents) or „Dokumente lesen und Volltext schreiben“ (read documents and write full text)
- „Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)“ (store vectors for documents and find similar documents) – only with `code.rechte.schnittstellen` and `dms: ">=0.122.0"`
- „Fragen an die Ablage beantworten („Frag deine Ablage“) – nur aus Ausschnitten, die das DMS mitgibt (dms:antworten)“ (answer questions about the files, only from excerpts the DMS passes along) – only with `code.rechte.schnittstellen` and `dms: ">=0.124.0"`
- „kein Zugriff auf Netzwerk und Internet“ (no access to network and internet) or „Zugriff auf Netzwerk/Internet nur zu: …“ (access to network/internet only to: …); with a service address as a setting additionally „der Adresse aus der Einstellung „…“ (trägst du ein und bestätigst sie)“ (the address from the setting „…“, which you enter and confirm)
- „Reagiert auf diese Ereignisse:“ (reacts to these events) with one event per line

They are explained in the administrator manual under [Pakete mit Code](https://motom001.github.io/dms/admin/aktuell/pakete/#rechte-eines-pakets) (packages with code, German). In the README of a package with code, describe in the section „Rechte und Netzwerkzugriff“ (permissions and network access, as in the [template](vorlage/README.md)) what the package may do and why, using the same words.

## Mandatory

- `manifest.yaml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `inhalt/` (empty if need be), `tests/`
- Package id = folder name: lower-case letters, digits, `_`, starts with a letter, at most 20 characters
- With every change, a higher version (SemVer) and an entry in `CHANGELOG.md`
- German texts in fields and views; the README in German, additionally in English if you like
- A maintainer for the package in `CODEOWNERS`

## Settings

- Packages with code **describe** their settings in the manifest (`code.einstellungen`, `code.aktionen`). The DMS shows the form, checks the values, stores them (as part of the backup) and passes them to the package.
- **Credentials only as `geheim`** (secret), never as `text` and never as `standard`. The DMS encrypts secrets and no longer shows them after saving.
- **Service address** (from DMS 0.124.0, `dms: ">=0.124.0"`): If a package needs a service that every household runs somewhere else (e.g. an AI service), it asks for the address as a setting of type `adresse` instead of a fixed address in `code.netz`. At most one per package, only in a section, **without** `standard` – at most a `beispiel` (example) for a service in the own network (e.g. `http://ollama:11434/v1`). The administrator confirms the address when saving; the package runner lets the package reach only this address. The README explains what is sent there and when.
- Changing settings is the job of the DMS. A package does not store its settings anywhere else itself and does not bring its own user interface for them.

## Names

Keys of Mappe types, fields and tabs are **local to the package**, e.g. `versicherung`. The DMS creates them with the package id in front (`haushalt_versicherung`) so that two packages do not get in each other's way. Only the name ("Versicherung") is displayed. You write references to types of other packages as `<paket>:<schluessel>`, e.g. `basis:organisation`. The other package must then be listed under `abhaengigkeiten` (dependencies). To Mappe types that the DMS brings itself, you refer with `dms:` – without a dependency: `dms:ablageort` (where an original is kept), `dms:benutzer` (user) and `dms:rolle` (role). This requires `dms: ">=0.75.0"` in the manifest. The package id `dms` is therefore taken.

Sample Mappen may refer to each other (from DMS 0.79.0): a sample gets a `schluessel`, a reference field of another sample gets the value `{ beispiel: strom }` – or `{ beispiel: "basis:stadtwerke" }` for a sample from a dependency. The manifest must then contain `dms: ">=0.79.0"`.

## Fields for recognition

The DMS recognises incoming post and fills Mappen from documents (DMS #336, #391) – without AI, using patterns and matching against existing Mappen. Which fields it uses for this is stated by the package with the field property `erkennung`:

```yaml
- key: kundennummer
  label: Kundennummer
  typ: text
  erkennung: { art: nummer, hinweis: "Steht meist oben rechts im Brief" }
- { key: email, label: E-Mail, typ: text, erkennung: {} }   # art follows from the label
```

- **Mark what clearly assigns a letter:** customer, contract, policy or file numbers, licence plates, IBAN, VAT id, e-mail address, website, phone, name. If a type has marked names or contact details (`name`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`), it counts as a possible **sender** (organisation, person); if it only marks numbers, as a possible **target Mappe**.
- **Mark what "Fill from document" should fill:** date, amount, address, first/last name, role, references (e.g. the garage of an invoice). If a type has marked fields, the DMS fills only these.
- **Do not mark** what appears in other people's letters all the time and assigns nothing – e.g. the IBAN of your own account (it is in every direct debit) or a number many Mappen share.
- Only for the field types `text`, `langtext`, `zahl`, `betrag`, `datum`, `auswahl` and `referenz`; never for `passwort`. `art` (optional) must match the field type: `name`, `vorname`, `nachname`, `funktion`, `nummer`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`, `strasse`, `hausnummer`, `plz`, `ort` for text; `nummer`, `plz`, `hausnummer`, `betrag` for numbers; `datum`, `betrag`, `auswahl`, `verweis` for the field type of the same name. `hinweis` has at most 300 characters; a pattern after the word *Muster* (`#` = digit, `A` = capital letter, e.g. "Muster 100-####") is searched for specifically.
- If you use `erkennung`, write `dms: ">=0.113.0"` in the manifest. A package update applies the marking to installed fields where the administrator has not set anything for recognition; that is a patch version (with new fields a minor version).

`werkzeuge/pruefen.py` checks field type, `art` and DMS version.

## Turning text into a reference

If a package holds a person, a company or another thing as **text** where a **reference** belongs (e.g. "Halter: Lena Muster" on a vehicle), you turn it into a reference field in a new version and state with `aus_text` from which previous text field it can be filled (DMS #534):

```yaml
- { key: halter_verweis, label: Halter, typ: referenz, ziel: "basis:person", verweisart: bezug, aus_text: halter }
```

- **New key:** The reference field gets its own key – usually the old one with `_verweis` appended. You remove the old text field from the package (field, tab, result list, title template). New installations only get the reference.
- **Nothing is lost:** On an update the DMS creates the reference field **in addition**; the old text field stays with all its values. This does not count as deleting a field. Only in the Werkbank (Pakete → package → *Text in Verweise umwandeln*) does the DMS suggest an existing Mappe per name, create a new one on request or skip it; only then is anything converted, recorded in the history and reversible. Updates change nothing behind your back.
- **Not mandatory:** A reference field with `aus_text` is never `pflicht` – otherwise existing Mappen would no longer fit after the update.
- **Reference kind:** For persons and organisations use `bezug` – deleting a person does not delete the car or the account.
- **Several names:** If the text often holds more than one ("Lena und Tom Muster"), use `mehrfach: true`; the DMS then splits the text at "und", comma, slash or "&".
- Only for reference fields; `aus_text` names another field, and if that is still in the package, it is `text` or `langtext`.
- If you use `aus_text`, write `dms: ">=0.120.0"` in the manifest. New fields or the conversion are a **minor version**.

`werkzeuge/pruefen.py` checks field type, source, `pflicht` and DMS version.

## Formats and date limits

The DMS checks values in text fields against a **format** and date fields against **limits** (DMS #535). This keeps postcodes with letters, phone numbers with letters and birthdays in the future out of the Mappen. On a phone the matching keyboard appears, and phone numbers and e-mail addresses can be tapped.

```yaml
- { key: telefon, label: Telefon, typ: text, maxLen: 40, format: telefon }
- { key: email, label: E-Mail, typ: text, maxLen: 200, format: email }
- { key: internet, label: Internetseite, typ: text, maxLen: 200, format: internetseite }
- { key: iban, label: IBAN, typ: text, maxLen: 42, format: iban }
- { key: plz, label: PLZ, typ: text, maxLen: 10, format: plz, landFeld: land }
- { key: land, label: Land, typ: text, maxLen: 60, standard: Deutschland }
- { key: geburtstag, label: Geburtstag, typ: datum, max: heute }
- { key: einzug, label: Einzug, typ: datum, min: "2000-01-01" }
```

- **`format`** only with `typ: text`: `email` (`name@beispiel.de`), `telefon` (digits, `+` at the start, spaces, `/`, `-`, brackets), `internetseite` (with or without `https://`), `iban` (length for the country and check digits, shown in groups of four) or `plz`.
- **`landFeld`** only with `format: plz`: the key of a text or choice field of the same Mappe type holding the country. If it says Germany or nothing (and the default is Deutschland), **exactly 5 digits** are required; for other countries the postcode is free. Without `landFeld` Germany always applies – so add a field *Land* to addresses.
- **`min`** and **`max`** with `typ: datum`: `heute` (today) or a date `"YYYY-MM-DD"` (in quotes, otherwise YAML reads it as a date). Only set limits where a value would otherwise certainly be wrong – `max: heute` for birthday, first registration or "read on"; never for deadlines such as "valid until".
- Stored values stay valid: the DMS only checks new and changed values. A package update applies format and limits to installed fields where the administrator has set neither; that is a minor version.
- **Samples must fit** – the DMS creates them with the same checks. Use invented but valid values: persona names, test numbers such as `+49 30 123456`, the test IBAN `DE89 3704 0044 0532 0130 00`.
- If you use `format`, `landFeld` or date limits, write `dms: ">=0.121.0"` in the manifest.

`werkzeuge/pruefen.py` checks field type, country field, limits, the samples and the DMS version.

## Word lists

A package can bring **synonyms** for the search (from DMS 0.127.0): whoever searches for one word also finds the others. The manifest contains `inhalt.wortlisten: inhalt/wortlisten.yaml` and `dms: ">=0.127.0"` – older DMS versions silently skip the section. The file is a list of groups:

```yaml
- woerter: [Kfz, Auto, PKW, Fahrzeug]
- woerter: [Nebenkosten, Betriebskosten]
```

- 2 to 20 different words per group, 2 to 60 characters each; upper/lower case and umlauts do not count when comparing ("Gebühr" and "gebuhr" are the same word). At most 1000 groups per package.
- Only words that really mean the same in everyday use and belong to the topic of the package – no generic terms ("Vertrag" for everything) and no names of companies or people.
- `tests/erwartung.yaml` states the number of groups: `wortlisten: 5`.
- The DMS creates the groups on installation, replaces them with those of the package on an update and removes them together with the package.

## Orphaned packages

If the maintainer of a package does not respond to bugs or necessary adjustments for three months, the package is marked as *orphaned* and can be taken over by someone else.
