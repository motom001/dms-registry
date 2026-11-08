# Rules for packages

[Deutsch](REGELN.md) · **English**

> This is a translation. If the German and English versions differ, the German version ([REGELN.md](REGELN.md)) applies.

## Licences

Every package is licensed under one of these open source licences (identifier according to [SPDX](https://spdx.org/licenses/), written like this in `manifest.yaml` under `lizenz`):

`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `MPL-2.0`, `LGPL-3.0-or-later`, `GPL-3.0-or-later`, `AGPL-3.0-or-later`, `CC0-1.0` (only for pure configuration)

The full licence text is in the package folder as `LICENSE`. Third-party code in the package needs a compatible licence and a note in the README.

## Allowed

- Mappe types, views, roles, sample Mappen
- Labels per language on Mappe types, fields, choice values, tabs and views (see [Labels per language](#labels-per-language))
- Language packages: further languages for Ablago, texts only (see [Language packages](#language-packages))
- Views across **all Mappe types** with `typen: ["*"]` – including future ones, e.g. a "Favoriten" view (alone in `typen`, from Ablago 0.182.0, `dms: ">=0.182.0"`)
- Word lists: synonyms for the search (see [Word lists](#word-lists))
- Ready-made automations (see [Automations](#automations))
- Code that works through Ablago API (as soon as the package runner is available)
- Access to the network/internet only to addresses listed in the manifest (`code.netz`) whose purpose the README explains. Without `code.netz`, a package has no access to the network or the internet.

## Forbidden

- **Ready-made binaries** of any kind (`.wasm`, `.so`, `.dll`, `.exe`, `.jar`, `.bin` …). They are built in the CI from source code.
- Obfuscated or minified source code
- Telemetry, tracking, advertising
- Access to the network/internet to addresses not listed in the manifest – except to the service address the administrator enters and confirms in a setting of type `adresse`
- A preset service address of an external provider (cloud) – not even as `beispiel`
- More permissions than necessary, e.g. write access where read access is enough
- Real personal data in samples, example documents, tests or screenshots
- Deleting fields, tabs or Mappen during an update (a text field replaced by a reference with `aus_text` may leave the package – see [Turning text into a reference](#turning-text-into-a-reference))

## How administrators see the permissions

Before installation, Ablago shows the permissions of a package with code, and the catalogue website does the same. The wording is German:

- „Mappen lesen: …“ (read Mappen), „Mappen anlegen und ändern: …“ (create and change Mappen), „Dokumente lesen“ (read documents) or „Dokumente lesen und Volltext schreiben“ (read documents and write full text)
- „Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)“ (store vectors for documents and find similar documents) – only with `code.rechte.schnittstellen` and `dms: ">=0.122.0"`
- „Fragen an die Ablage beantworten („Frag deine Ablage“) – nur aus Ausschnitten, die Ablago mitgibt (dms:antworten)“ (answer questions about the files, only from excerpts Ablago passes along) – only with `code.rechte.schnittstellen` and `dms: ">=0.124.0"`
- „Felder aus Dokumenten vorschlagen („Aus Dokument ausfüllen“) – nur aus dem Text, den Ablago mitgibt (dms:erkennen)“ (suggest fields from documents for “fill from document”, only from the text Ablago passes along) – only with `code.rechte.schnittstellen` and `dms: ">=0.125.0"`
- „Texterkennung für Scans und Bilder übernehmen – Ablago meldet Dokumente ohne Text und zeigt „wartet auf Texterkennung“, bis das Paket den Volltext schreibt (dms:texterkennung)“ (take over text recognition for scans and images – Ablago reports documents without text and shows „waiting for text recognition“ until the package writes the full text) – only with `code.rechte.schnittstellen`, `dokumente: schreiben` and `dms: ">=0.133.0"`
- „Dateien umwandeln, die Ablago nicht selbst lesen kann – das Paket liest die Originaldatei und liefert eine Fassung (PDF, PNG oder JPEG) für Vorschaubild und Volltext; das Original bleibt unverändert (dms:umwandeln): TIFF, WebP, …“ (convert files Ablago cannot read itself – the package reads the original file and returns a version as PDF, PNG or JPEG for thumbnail and full text; the original stays unchanged) – only with `code.rechte.schnittstellen`, `code.umwandeln`, the event `datei.umwandeln`, `dokumente: lesen` and `dms: ">=0.137.0"` (see [Converting files](#converting-files))
- „Volltext für Dateien liefern, die Ablago nicht selbst lesen kann – das Paket liest die Datei und schreibt nur ihren Volltext; Dokumente ändern, ersetzen oder löschen kann es nicht (dms:volltext): Word, E-Mail, …“ (deliver the full text of files Ablago cannot read itself – the package reads the file and writes only its full text; it cannot change, replace or delete documents) – only with `code.rechte.schnittstellen`, `code.volltext`, the event `datei.volltext`, `dokumente: lesen` and `dms: ">=0.145.0"` (see [Text only](#text-only))
- „Mappentyp vorschlagen („Wohin gehört das?“) – nur aus dem Anfang des Dokuments und der Liste der Mappentypen, die Ablago mitgibt (dms:klassifizieren)“ (suggest a folder type, “where does this belong?”, only from the start of the document and the list of folder types Ablago passes along) – only with `code.rechte.schnittstellen` and `dms: ">=0.226.0"`; call and answer in the developer handbook under [Suggest a folder type](https://help.ablago.app/entwickler/aktuell/pakete-code/#klassifizieren)
- „Archivfassung (PDF/A) ablegen – das Paket liest Dokumente mit ihrem Volltext und den Wortpositionen und legt daneben ein durchsuchbares PDF/A ab; das Original bleibt unverändert, ändern, ersetzen oder löschen kann es nichts (dms:archivfassung): PDF, JPEG, PNG, …“ (store an archival copy (PDF/A) – the package reads documents with their full text and word positions and stores a searchable PDF/A next to them; the original stays unchanged, it cannot change, replace or delete anything) – only with `code.rechte.schnittstellen`, `code.archivfassung`, the event `datei.archivfassung`, `dokumente: lesen` and `dms: ">=0.149.0"` (see [Archival copy (PDF/A)](#archival-copy-pdfa))
- „Die verschlüsselte Sicherung lesen, um sie außer Haus zu kopieren – kann sie nicht öffnen (kein Schlüssel, keine Inhalte) (dms:sicherung-lesen)“ (read the encrypted backup to copy it off-site – cannot open it: no key, no contents) – only with `code.rechte.schnittstellen`, the event `sicherung.fertig` and `dms: ">=0.142.0"` (see [Off-site backup](#off-site-backup))
- „kein Zugriff auf Netzwerk und Internet“ (no access to network and internet) or „Zugriff auf Netzwerk/Internet nur zu: …“ (access to network/internet only to: …); with a service address as a setting additionally „der Adresse aus der Einstellung „…“ (trägst du ein und bestätigst sie)“ (the address from the setting „…“, which you enter and confirm)
- „Reagiert auf diese Ereignisse:“ (reacts to these events) with one event per line

They are explained in the administrator manual under [Pakete mit Code](https://help.ablago.app/admin/aktuell/pakete/#rechte-eines-pakets) (packages with code, German). In the README of a package with code, describe in the section „Rechte und Netzwerkzugriff“ (permissions and network access, as in the [template](vorlage/README.md)) what the package may do and why, using the same words.

## Mandatory

- `manifest.yaml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `inhalt/` (empty if need be), `tests/`
- Package id = folder name: lower-case letters, digits, `_`, starts with a letter, at most 20 characters
- With every change, a higher version (SemVer) and an entry in `CHANGELOG.md`
- German texts in fields and views; the README in German, additionally in English if you like. English labels (`beschriftungen.en`) are welcome – the bundled packages with Mappe types have them.
- A maintainer for the package in `CODEOWNERS`

## Settings

- Packages with code **describe** their settings in the manifest (`code.einstellungen`, `code.aktionen`). Ablago shows the form, checks the values, stores them (as part of the backup) and passes them to the package.
- **Credentials only as `geheim`** (secret), never as `text` and never as `standard`. Ablago encrypts secrets and no longer shows them after saving.
- **Service address** (from Ablago 0.124.0, `dms: ">=0.124.0"`): If a package needs a service that every household runs somewhere else (e.g. an AI service), it asks for the address as a setting of type `adresse` instead of a fixed address in `code.netz`. At most one per package, only in a section, **without** `standard` – at most a `beispiel` (example) for a service in the own network (e.g. `http://ollama:11434/v1`). The administrator confirms the address when saving; the package runner lets the package reach only this address. The README explains what is sent there and when.
- Changing settings is the job of Ablago. A package does not store its settings anywhere else itself and does not bring its own user interface for them.

## Categories

Every package belongs to **one or two categories** from a fixed list in [`werkzeuge/kategorien.yaml`](werkzeuge/kategorien.yaml). The catalog website filters by them, and “Similar packages” shows packages of the same category. A new package names them in its manifest, e.g. `kategorien: [dateiformate, volltext]`; CI checks it (`python3 werkzeuge/vorlagen.py --pruefen`). Packages whose manifest does not have the field yet are listed under `pakete:` in `kategorien.yaml` for the time being – **the manifest wins**, and `pruefen.py` points out differences. New categories only via an issue; there are no free tags. Ablago does not read the field; it reads the manifest field by field and skips fields it does not know – older Ablago versions install such packages as well. Whether a package runs **locally only**, connects to **a service you enter** (setting of type `adresse`) or uses **fixed internet addresses** (`code.netz`) is read from the manifest by the website – there is no category for that.

## Icon

In the catalogue every package has a small **icon**, so you can see at a glance what it is about. You choose it in the manifest with `symbol:` from a **fixed list** of [Lucide](https://lucide.dev) icons – the same single-colour line icons as in Ablago. All icons have **the same colour**; the colour does not stand for a category (the category chips do that). Without `symbol` the catalogue shows the first letter, and `pruefen.py` prints a notice (not an error). An unknown name is an error.

```yaml
symbol: languages
kuerzel: FR        # optional, only with symbol: at most 3 capital letters at the bottom right of the icon
```

- **Choosing:** take the icon that shows **what the package does for the user** – not how it does it technically. No logos, no emoji, no flags (flags stand for countries, not languages). Additional languages use `languages` with the language code as `kuerzel` (FR, ES, IT …).
- **Abbreviation:** at most 3 capital letters; the schema and `pruefen.py` reject longer ones. For languages it is the **ISO 639 code of the language, not of the country**: two letters from ISO 639-1 in capitals (FR French, PT Portuguese, AR Arabic, **UK Ukrainian** – not UA), three letters from ISO 639-2/3 only for languages without a two-letter code.
- **Allowed** are exactly the SVG files in [`werkzeuge/symbole/`](werkzeuge/symbole/) (the schema has the same list):

| Icon | fits |
| --- | --- |
| `car` | vehicles |
| `cloud-upload` | backup, upload |
| `contact` | people, contacts, basics |
| `file-text` | documents, office |
| `files` | several documents, similarity |
| `house` | house, flat |
| `image` | images, image formats |
| `key-round` | renting, keys |
| `languages` | languages (with `kuerzel`) |
| `mail` | post, e-mail |
| `message-circle-question-mark` | questions, assistant |
| `scan-barcode` | separator sheets, barcodes |
| `scan-text` | text recognition |
| `wallet` | money, household |

- **New icon:** via an issue. The SVG is then copied unchanged from `lucide-static` to `werkzeuge/symbole/<name>.svg` and the name added to `schema/manifest.schema.json` (`symbol`); CI checks that both match and that the SVG contains only simple shapes. The website embeds the SVG directly in the page; nothing is loaded from the internet. Licence of the icons: ISC ([`werkzeuge/symbole/LICENSE`](werkzeuge/symbole/LICENSE), NOTICE).
- **Existing packages:** their icons are listed under `symbole:` in [`werkzeuge/kategorien.yaml`](werkzeuge/kategorien.yaml) for the time being; with the next version the icon moves into the manifest. The manifest wins. Like `kategorien`, Ablago does not read `symbol` and `kuerzel`; older Ablago versions keep installing such packages.
- **View symbol** (dms #428): in `sichten.yaml` each view may have `symbol: <name>` – a Lucide name from the fixed list in Ablago ([`shared/src/ansichtsymbole.ts`](https://github.com/motom001/dms/blob/main/shared/src/ansichtsymbole.ts)), e.g. `house`, `car`, `euro`, `mail`. Ablago shows it before the view name; an unknown name is shown without a symbol. Older Ablago versions ignore the field.

## Names

Keys of Mappe types, fields and tabs are **local to the package**, e.g. `versicherung`. Ablago creates them with the package id in front (`haushalt_versicherung`) so that two packages do not get in each other's way. Only the name ("Versicherung") is displayed. You write references to types of other packages as `<paket>:<schluessel>`, e.g. `basis:organisation`. The other package must then be listed under `abhaengigkeiten` (dependencies). To Mappe types that Ablago brings itself, you refer with `dms:` – without a dependency: `dms:benutzer` (user) and `dms:rolle` (role). This requires `dms: ">=0.75.0"` in the manifest. The **storage location** (where an original is kept) comes with the Basis package since Ablago 0.212.0: `basis:ablageort` with `basis: ">=1.6.0"` under `abhaengigkeiten` (Ablago #883, Registry #138). Ablago still understands the former `dms:ablageort` as an alias until 1.0; `pruefen.py` warns about it. The package id `dms` is therefore taken.

Sample Mappen may refer to each other (from Ablago 0.79.0): a sample gets a `schluessel`, a reference field of another sample gets the value `{ beispiel: strom }` – or `{ beispiel: "basis:stadtwerke" }` for a sample from a dependency. The manifest must then contain `dms: ">=0.79.0"`.

### Example documents { #beispiel-dokumente }

From Ablago 0.223.0 (motom001/dms#878, registry #137) a sample can bring documents – for instance a maintenance contract and invoices for the sample Mappe "Heating". The files are under `inhalt/beispiele/`, the sample names them under `dokumente`:

```yaml
- typ: vertrag
  schluessel: heizung_wartung
  werte: { bezeichnung: Wartungsvertrag Heizung }
  dokumente:
    - { datei: beispiele/heizung/wartungsvertrag.pdf, titel: Wartungsvertrag, datum: "2023-04-01" }
    - { datei: beispiele/heizung/rechnung-2026.png, register: rechnungen }
```

- `datei` is relative to `inhalt/` and starts with `beispiele/`; folders and names only of letters, digits, `.`, `-` and `_`. `titel` becomes the name in Ablago, `datum` "uploaded on", `register` the document tab (without it, the first one).
- **Only PDF, PNG and JPEG** – recognised by the content, the extension must match. Each file at most 100 MB as when uploading in Ablago, all together at most 128 MB; still keep them small (reduced PDFs, pictures as JPEG). The 2 MB per file limit doesn't apply here.
- **Every named file must exist, and every file under `inhalt/beispiele/` must be named.** `pruefen.py` reports the size per file and in total on every check.
- Packages with example documents require `dms: ">=0.223.0"`.
- **No real data:** only invented people and companies (persona names such as Lena, Jonas, Markus, Petra, Herr Özdemir, Katrin), example domains (`example.org`, `example.com`, `example.net`), invalid or explicitly sample values for IBAN, tax and insurance numbers. No scanned real letters, not even redacted – metadata, signatures and logos often reveal more than you think.
- **Large packages:** the catalogue lives on the branch `gh-pages` (registry #133), and git doesn't accept files over 100 MB. A package whose archive would be larger can't be published that way; `pruefen.py` points this out from 90 MB.

## Add-ons (`ergaenzt`)

A package that extends another one – e.g. an additional language for Texterkennung – says so with `ergaenzt` (motom001/dms#405). The extended package is also listed under `abhaengigkeiten`:

```yaml
abhaengigkeiten:
  texterkennung: ">=2.0.0"
ergaenzt: { paket: texterkennung, gruppe: Weitere Sprachen }   # or short: ergaenzt: texterkennung
```

Ablago from 0.151.0 shows add-ons as checkboxes below the extended package during installation, grouped by `gruppe` (a short question without question mark, at most 40 characters; without a group: "Ergänzungen") – also afterwards, in the setup assistant and in the bundle file. Every add-on stays a package of its own with its own version. Older Ablago versions ignore the field, so no higher `dms` is needed. In the catalogue it appears per version as `ergaenzt: { paket, gruppe }`, on the catalogue website as a group of its own under "Passt dazu".

## Labels per language

Mappe types, fields, choice values, tabs and views of a package can carry labels in further languages (Ablago #728, Registry #135) – an English Ablago then shows them in English:

```yaml
- schluessel: vertrag
  name: Vertrag                     # German base text, as before
  beschriftungen: { en: { name: Contract } }
  felder:
    - key: art
      label: Art
      typ: auswahl
      optionen: [Strom, Gas, Wasser]   # the fixed values – exactly these are stored in Mappen
      beschriftungen:
        en: { label: Type, optionen: { Strom: Electricity, Gas: Gas, Wasser: Water } }
  register:
    - { key: allgemein, name: Allgemein, art: felder, felder: [art], beschriftungen: { en: { name: General } } }
```

- **Where:** on Mappe types and views `name` and `beschreibung`, on fields `label`, `hilfe` and `optionen` (fixed value → text), on tabs `name`.
- **Languages:** codes like `en`, `fr` or `pt-BR`; at most 30 per entry, at most 500 characters per text, no angle brackets (no HTML).
- **`optionen` stays a list of strings** – the fixed values stored in Mappen. Keys under `beschriftungen.<language>.optionen` must appear under `optionen`, and only on choice fields.
- **German is the base text.** `beschriftungen.de` exists only for `optionen`, e.g. a neutral value `strom` labelled “Strom”.
- **No higher `dms` needed:** Ablago from 0.200.0 takes the labels on install; an update only adds what the administrator hasn't labelled yet. Older versions skip the field. New labels are a minor version.

## Language packages

Further languages for Ablago come as a **language package** (Ablago #731, Registry #116, from Ablago 0.203.0). It contains **texts only** – no code, no Mappe types, no HTML: `texte/<bereich>.json` (same areas, keys and placeholders as Ablago's language files) and optionally `beschriftungen/<paket>.yaml` (labels for packages of this registry). The manifest has `id: sprache_<kennung>`, `dms: ">=0.203.0"`, `symbol: languages`, `kuerzel` = the language code in capitals, `kategorien: [sprachen]`, `inhalt: {}` and:

```yaml
sprache:
  kennung: fr            # German and English are built in
  gebietsschema: fr-FR   # dates, numbers, amounts
  ablago: 0.203.0        # Ablago version the texts were made for
  maschinell: true       # machine-translated → notice in Ablago and in the catalogue
  # geprueft_von: "@github-name"
```

- Always the **familiar form of address** of the language; no formal version. At most 4000 characters per text, 4 MB in total, no control characters, angle brackets only where the German text has them.
- Forbidden: `code`, entries under `inhalt`, `abhaengigkeiten`, `ergaenzt` and any other files. Missing texts appear in English; keys unknown to an Ablago version are skipped.
- Help improve: issue template “Improve a translation” or a pull request. `python3 werkzeuge/sprachen.py --ablago <checkout of motom001/dms>` shows the coverage and, with `--fehlend`, the missing texts in English; the CI compares against the newest released Ablago version.

The German version ([REGELN.md](REGELN.md#sprachpakete)) has the details.

## Fields for recognition

Ablago recognises incoming post and fills Mappen from documents (DMS #336, #391) – without AI, using patterns and matching against existing Mappen. Which fields it uses for this is stated by the package with the field property `erkennung`:

```yaml
- key: kundennummer
  label: Kundennummer
  typ: text
  erkennung: { art: nummer, hinweis: "Steht meist oben rechts im Brief" }
- { key: email, label: E-Mail, typ: text, erkennung: {} }   # art follows from the label
```

- **Mark what clearly assigns a letter:** customer, contract, policy or file numbers, licence plates, IBAN, VAT id, e-mail address, website, phone, name. If a type has marked names or contact details (`name`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`), it counts as a possible **sender** (organisation, person); if it only marks numbers, as a possible **target Mappe**.
- **Mark what "Fill from document" should fill:** date, amount, address, first/last name, role, references (e.g. the garage of an invoice). If a type has marked fields, Ablago fills only these.
- **Do not mark** what appears in other people's letters all the time and assigns nothing – e.g. the IBAN of your own account (it is in every direct debit) or a number many Mappen share.
- Only for the field types `text`, `langtext`, `zahl`, `betrag`, `datum`, `auswahl` and `referenz`; never for `passwort`. `art` (optional) must match the field type: `name`, `vorname`, `nachname`, `funktion`, `nummer`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`, `strasse`, `hausnummer`, `plz`, `ort` for text; `nummer`, `plz`, `hausnummer`, `betrag` for numbers; `datum`, `betrag`, `auswahl`, `verweis` for the field type of the same name. `hinweis` has at most 300 characters; a pattern after the word *Muster* (`#` = digit, `A` = capital letter, e.g. "Muster 100-####") is searched for specifically.
- If you use `erkennung`, write `dms: ">=0.113.0"` in the manifest. A package update applies the marking to installed fields where the administrator has not set anything for recognition; that is a patch version (with new fields a minor version).

`werkzeuge/pruefen.py` checks field type, `art` and Ablago version.

## Turning text into a reference

If a package holds a person, a company or another thing as **text** where a **reference** belongs (e.g. "Halter: Lena Muster" on a vehicle), you turn it into a reference field in a new version and state with `aus_text` from which previous text field it can be filled (DMS #534):

```yaml
- { key: halter_verweis, label: Halter, typ: referenz, ziel: "basis:person", verweisart: bezug, aus_text: halter }
```

- **New key:** The reference field gets its own key – usually the old one with `_verweis` appended. You remove the old text field from the package (field, tab, result list, title template). New installations only get the reference.
- **Nothing is lost:** On an update Ablago creates the reference field **in addition**; the old text field stays with all its values. This does not count as deleting a field. Only in the Werkbank (Pakete → package → *Text in Verweise umwandeln*) does Ablago suggest an existing Mappe per name, create a new one on request or skip it; only then is anything converted, recorded in the history and reversible. Updates change nothing behind your back.
- **Not mandatory:** A reference field with `aus_text` is never `pflicht` – otherwise existing Mappen would no longer fit after the update.
- **Reference kind:** For persons and organisations use `bezug` – deleting a person does not delete the car or the account.
- **Several names:** If the text often holds more than one ("Lena und Tom Muster"), use `mehrfach: true`; Ablago then splits the text at "und", comma, slash or "&".
- Only for reference fields; `aus_text` names another field, and if that is still in the package, it is `text` or `langtext`.
- If you use `aus_text`, write `dms: ">=0.120.0"` in the manifest. New fields or the conversion are a **minor version**.

`werkzeuge/pruefen.py` checks field type, source, `pflicht` and Ablago version.

## Restricting the choice and references that follow from others

A reference field can offer only fitting folders – with `auswahlFilter`, conditions as in a view (DMS #172). With `wert: { art: eigenesFeld, feld: … }` a condition takes the value of another field of the same folder (DMS #173), e.g. for the person (Basis): only branches of the chosen organisation.

```yaml
- key: niederlassung
  label: Niederlassung
  typ: referenz
  ziel: niederlassung
  auswahlFilter: [{ art: feld, feld: organisation, op: zeigtAuf, wert: { art: eigenesFeld, feld: organisation } }]
```

- `feld` is a field of the **target** folder type, `wert.feld` **another** field of this folder type. If it is empty, the condition doesn't apply – then all appear.
- **Strict:** a newly chosen value that doesn't fit is rejected on saving; saved ones stay valid, and Ablago then shows on the field what they don't match (from 0.225.0, DMS #887). Only use the filter where it has to be like that (a branch belongs to exactly one organisation).

The **other direction** is called `folgtAus` (DMS #886): a reference field fills in from another reference field of this folder, via a reference field of its target – e.g. *Organisation* from *Branch* → *Organisation*.

```yaml
- { key: organisation, label: Organisation, typ: referenz, ziel: organisation, folgtAus: { feld: niederlassung, zielFeld: organisation } }
```

- `feld` is another reference field of this folder type with **one** folder, `zielFeld` a reference field with one folder in its target that points to the same folder type as this field. No circles.
- Ablago only fills an **empty** field, never overwrites and asks when the details don't match. Existing folders stay as they are.
- If you use `folgtAus`, write `dms: ">=0.225.0"` in the manifest. A selection filter alone needs no new version.

`werkzeuge/pruefen.py` checks field type, the fields named (as far as they are in the package), circles and the Ablago version.

## Formats and date limits

Ablago checks values in text fields against a **format** and date fields against **limits** (DMS #535). This keeps postcodes with letters, phone numbers with letters and birthdays in the future out of the Mappen. On a phone the matching keyboard appears, and phone numbers and e-mail addresses can be tapped.

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
- Stored values stay valid: Ablago only checks new and changed values. A package update applies format and limits to installed fields where the administrator has set neither; that is a minor version.
- **Samples must fit** – Ablago creates them with the same checks. Use invented but valid values: persona names, test numbers such as `+49 30 123456`, the test IBAN `DE89 3704 0044 0532 0130 00`.
- If you use `format`, `landFeld` or date limits, write `dms: ">=0.121.0"` in the manifest.

`werkzeuge/pruefen.py` checks field type, country field, limits, the samples and the Ablago version.

## Word lists

A package can bring **synonyms** for the search (from Ablago 0.127.0): whoever searches for one word also finds the others. The manifest contains `inhalt.wortlisten: inhalt/wortlisten.yaml` and `dms: ">=0.127.0"` – older Ablago versions silently skip the section. The file is a list of groups:

```yaml
- woerter: [Kfz, Auto, PKW, Fahrzeug]
- woerter: [Nebenkosten, Betriebskosten]
```

- 2 to 20 different words per group, 2 to 60 characters each; upper/lower case and umlauts do not count when comparing ("Gebühr" and "gebuhr" are the same word). At most 1000 groups per package.
- Only words that really mean the same in everyday use and belong to the topic of the package – no generic terms ("Vertrag" for everything) and no names of companies or people.
- General words found in every archive (Rechnung/Beleg, Vertrag/Vereinbarung) belong in the **Basis** package; subject packages only bring their subject-specific words. A word appears in at most one package of the catalogue (checked by `werkzeuge/test_pruefen.py`).
- `tests/erwartung.yaml` states the number of groups: `wortlisten: 5`.
- Ablago creates the groups on installation, replaces them with those of the package on an update and removes them together with the package.

## Automations

A package can bring **ready-made automations** (from Ablago 0.177.0, Ablago #712): When · And · Then as in the editor under *Workbench → Build the filing → Automations*. The manifest contains `inhalt.automatisierungen: inhalt/automatisierungen.yaml` and `dms: ">=0.177.0"`.

```yaml
- schluessel: hu_bald
  name: HU wird bald fällig
  beschreibung: Einen Monat vor der Hauptuntersuchung bekommt der Verantwortliche eine Frist.
  wenn: { art: datum, typ: fahrzeug, feld: hu_faellig, vorlauf: 1, einheit: monate, uhrzeit: "07:00" }
  dann:
    - { art: aufgabe, als: aufgabe, empfaenger: [{ art: feld, feld: verantwortlich, sonst: ersteller }], text: "Für {kennzeichen} wird bald die HU fällig: {datum}." }
```

- **Off after installation.** When installing, Ablago lists every automation by name and asks whether to switch it on right away (default: yes). In the workbench they show as “from package …”. An update replaces only unchanged ones; removing the package removes unchanged, switched-off ones.
- **Exactly one When card:** `datum` (*Date reached*, with `typ`, `feld` as a date field, `vorlauf`, `einheit` tage/wochen/monate, optional `uhrzeit`, `wiederholung` in months) or an event such as `mappe.angelegt`, `mappe.geaendert`, `dokument.hochgeladen`, `post.angelegt`, `benutzer.abwesenheit_gesetzt`. Mappe types as the package's own key or `package:type` of a dependency.
- **Schedule** (Ablago 0.181.0 or later, DMS #678): `{ art: zeitplan, uhrzeit: "07:00", tage: [1, 2, 3, 4, 5], feiertage: true, jeBenutzer: true, profilzeit: true }` – weekdays 1 = Monday … 7 = Sunday; `jeBenutzer` runs once a day for every active user, `profilzeit` takes time, weekdays and holidays from the profile. `rolle` is not allowed in packages. Also the when card `favorit.geaendert`.
- **Then cards:** `aufgabe` (task or notification with text and placeholders), `feld` (set fields), `stopp`; from 0.181.0 also `zusammenfassung` (only with a per-user schedule), `favoriten` (only with `favorit.geaendert`) and `anmeldeschutz` with `was: sammel` (schedule, not per user) or `was: konto` (`benutzer.gesperrt`). Cards that send data out (e-mail, calling an address) are not available in packages yet.
- **No fixed people or roles:** the recipient is a field of the Mappe that points to users (`ziel: dms:benutzer`), optionally with `sonst: ersteller`, or `ersteller` (whoever created the Mappe).
- **Every deadline reminds:** since Ablago 0.177.0 a date field with `frist` no longer creates tasks itself. A package with `dms: ">=0.177.0"` therefore brings a *Date reached* automation for every deadline field; `frist.vorlauf` is only the default. `pruefen.py` reports deadlines without an automation.
- `tests/erwartung.yaml` states the number: `automatisierungen: 3`.

## Converting files

Ablago itself only reads PDF, JPEG and PNG (DMS #577). A package with the permission `dms:umwandeln` turns other file types into a **version** (“Fassung”) from which Ablago creates the thumbnail and the full text – e.g. [Bildformate](pakete/bildformate/) for TIFF, WebP, GIF and BMP:

```yaml
dms: ">=0.137.0"
code:
  ereignisse: [datei.umwandeln]
  umwandeln: [image/tiff, image/webp]      # file types (MIME) the package handles; not PDF, JPEG or PNG
  rechte:
    lesen: ["*"]
    dokumente: lesen                       # read the original – no write access needed
    schnittstellen: ["dms:umwandeln"]
```

- It may only **return** what Ablago reads itself: the version as **PDF, PNG or JPEG** (`PUT /dokumente/{id}/fassung`, at most 50 MB) and, if it likes, a thumbnail as **JPEG or PNG**. Multi-page files as PDF. It never changes the original.
- **No network:** converting happens inside the package. Sending a file to an outside service to convert it is not allowed.
- **Third-party libraries** (decoders, encoders) need a suitable licence (see [Licences](#licences)), are built from fixed commits, with their licence texts under `code/lizenzen/` and a note in the README. Formats whose decoders require patent licences (e.g. HEVC in HEIC) only go into the catalogue after consulting the maintainers; the README says so openly.
- The interface (flow, event, formats, limits, responses) is described in Ablago developer manual under [Dateien umwandeln](https://help.ablago.app/entwickler/aktuell/pakete-code/#dateien-umwandeln) (German).

### Text only

If a file type needs no thumbnail but only the full text (e.g. [Office und E-Mail](pakete/office_email/) for Word, Excel, e-mails), the package uses the permission `dms:volltext` (DMS #614, from 0.145.0) – **no** write access to documents. Ablago reports every file of its types with the event `datei.volltext` (on upload, for new versions, for existing files and on “Volltext neu erzeugen”); the package reads it and writes the text with `PUT /dokumente/{id}/volltext` (up to 5 million characters):

```yaml
dms: ">=0.145.0"
code:
  ereignisse: [datei.volltext]
  volltext: [message/rfc822, text/plain]   # file types (MIME) the package handles; not PDF, JPEG or PNG
  rechte:
    lesen: ["*"]
    dokumente: lesen                       # read the file – no write access needed
    schnittstellen: ["dms:volltext"]
```

The following applies:

- **Run nothing:** macros, scripts and embedded objects are neither started nor evaluated; only read the parts of Office files that hold the text, XML without DTD and external entities, limits against ZIP bombs.
- **No network**, as with converting. The file type is determined by the content, not the name; files Ablago reads itself (PDF, JPEG, PNG) are left alone.
- **Give a reason:** if the package cannot read a file, it ends with code `0` and a short sentence as its result (e.g. „Word lässt sich nicht lesen: mit einem Passwort verschlüsselt“) – Ablago shows it on the document.
- Flow, event and limits are described in Ablago developer manual under [Volltext liefern](https://help.ablago.app/entwickler/aktuell/pakete-code/#volltext-liefern) (German).

### Archival copy (PDF/A)

A package with the permission `dms:archivfassung` (DMS #631, from 0.149.0) stores an **archival copy** next to documents – a searchable PDF/A with an invisible text layer exactly on the words –, e.g. [PDF/A](pakete/pdfa/). Ablago reports a document with the event `datei.archivfassung` only once its full text is final; the package reads the file and the word positions and returns the PDF/A with `PUT /dokumente/{id}/archivfassung` (up to 100 MB). Manifest: `code.archivfassung` with `typen` (MIME types; PDF, JPEG and PNG allowed) and optionally `auswahl` (from 0.176.0: per kind – `pdf_text` PDFs with text, `pdf_scan` scanned PDFs, `bilder` photos and images – the key of a yes/no setting; on = these documents get an archival copy, a missing kind always does), `dokumente: lesen`, `schnittstellen: ["dms:archivfassung"]`.

- **Never load anything:** the archival copy contains only what is in the file – no JavaScript, no actions, no references to external content; Ablago rejects it otherwise.
- **Exactly on the words:** the text layer sits on Ablago word positions. If they are missing, the package does not place the text “roughly” but ends with code `0` and the reason.
- **Few settings:** one fixed PDF/A level instead of a choice; the pull request justifies every further setting.
- **Tools with a matching licence** (e.g. no AGPL tool in a package under Apache-2.0), licence texts under `code/lizenzen/`. Conformance is checked in the package's tests (e.g. with veraPDF), not in the package.
- Flow, event, word positions and limits: Ablago developer handbook, [Archivfassung ablegen](https://help.ablago.app/entwickler/aktuell/pakete-code/#archivfassung).

## Signed catalogue

- The published catalogue is signed (see [README, "Signing the catalogue"](README.en.md#signing-the-catalogue)). Pull requests do not change that: signing happens only in the CI on `main`.
- **Private keys** (`*.pem`) never belong in the repository, in issues or in pull requests. If one ends up there anyway: report it to the maintainer immediately (confidentially, see [SECURITY.en.md](SECURITY.en.md)).
- Only the maintainer changes `schluessel/*.pub`, `werkzeuge/signieren.py` and the workflow "Katalog veröffentlichen" (CODEOWNERS).

## Off-site backup

A package with the permission `dms:sicherung-lesen` copies every backup of Ablago to external storage and verifies it there (DMS #585) – e.g. [Sicherungsziel WebDAV](pakete/sicherung_webdav/):

```yaml
dms: ">=0.142.0"
code:
  ereignisse: [sicherung.fertig]
  rechte:
    schnittstellen: ["dms:sicherung-lesen"]   # no folders, no documents
  netz: []                                     # target as a setting of type adresse
```

- The package only gets the **encrypted** backup from its event, in chunks – never the key, never contents. It uploads it **in parts** and never loads it into memory as a whole.
- **Credentials** only as `geheim`; the target as a setting of type `adresse`.
- **Deletion protection:** the package lists nothing on the target and deletes nothing. “Delete old backups on the target” may at most be a setting that is **off** by default, with the note that it needs delete permissions – exactly what removes the protection against ransomware. The README recommends write-only access (e.g. Nextcloud file drop, S3 without `DeleteObject` with Object Lock).
- **Report honestly:** `geprueft` only when the checksum is confirmed or the file was read back; otherwise `hochgeladen`.
- Flow, event, chunked reading and reporting are described in Ablago developer manual under [Sicherung außer Haus](https://help.ablago.app/entwickler/aktuell/pakete-code/#sicherung-ausser-haus) (German).

## Events on folders

From Ablago 0.153.0 (DMS #670) a package can react to folders – to `mappe.angelegt`, `mappe.geaendert`, `mappe.geloescht`, `mappe.wiederhergestellt` and `frist.erreicht`. It only gets them for its **own** folder types listed under `code.mappentypen`:

```yaml
dms: ">=0.153.0"
code:
  ereignisse: [mappe.geaendert, frist.erreicht]
  mappentypen: [vertrag]      # own keys, without prefix
  rechte:
    lesen: [vertrag]          # required: the package must be allowed to read the types
```

- `code.mappentypen` is required with these events and only allowed with them. Events for other packages' folder types do not exist yet.
- An event only contains ids, field keys and dates – never values. The package reads the rest with its permissions.
- Events arrive **at least once**; `daten.ereignis` is the id in the event catalogue – the package recognises a repeat by it. `mappe.geaendert` combines quick successions.
- The preview shows the events with „– zu: *types*“. Flow and fields: Ablago developer handbook, [Pakete mit Code](https://help.ablago.app/entwickler/aktuell/pakete-code/#ereignisse) and [Ereigniskatalog](https://help.ablago.app/entwickler/aktuell/aufbau/#ereigniskatalog).

## Orphaned packages

If the maintainer of a package does not respond to bugs or necessary adjustments for three months, the package is marked as *orphaned* and can be taken over by someone else.
