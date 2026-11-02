# Rules for packages

[Deutsch](REGELN.md) · **English**

> This is a translation. If the German and English versions differ, the German version ([REGELN.md](REGELN.md)) applies.

## Licences

Every package is licensed under one of these open source licences (identifier according to [SPDX](https://spdx.org/licenses/), written like this in `manifest.yaml` under `lizenz`):

`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `MPL-2.0`, `LGPL-3.0-or-later`, `GPL-3.0-or-later`, `AGPL-3.0-or-later`, `CC0-1.0` (only for pure configuration)

The full licence text is in the package folder as `LICENSE`. Third-party code in the package needs a compatible licence and a note in the README.

## Allowed

- Mappe types, views, roles, sample Mappen
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
- Deleting fields, tabs or Mappen during an update

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

## Orphaned packages

If the maintainer of a package does not respond to bugs or necessary adjustments for three months, the package is marked as *orphaned* and can be taken over by someone else.
