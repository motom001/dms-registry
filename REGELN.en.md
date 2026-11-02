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
- Access to the network/internet to addresses not listed in the manifest
- More permissions than necessary, e.g. write access where read access is enough
- Real personal data in samples, tests or screenshots
- Deleting fields, tabs or Mappen during an update

## How administrators see the permissions

Before installation, the DMS shows the permissions of a package with code, and the catalogue website does the same. The wording is German:

- „Mappen lesen: …“ (read Mappen), „Mappen anlegen und ändern: …“ (create and change Mappen), „Dokumente lesen“ (read documents) or „Dokumente lesen und Volltext schreiben“ (read documents and write full text)
- „kein Zugriff auf Netzwerk und Internet“ (no access to network and internet) or „Zugriff auf Netzwerk/Internet nur zu: …“ (access to network/internet only to: …)
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
- Changing settings is the job of the DMS. A package does not store its settings anywhere else itself and does not bring its own user interface for them.

## Names

Keys of Mappe types, fields and tabs are **local to the package**, e.g. `versicherung`. The DMS creates them with the package id in front (`haushalt_versicherung`) so that two packages do not get in each other's way. Only the name ("Versicherung") is displayed. You write references to types of other packages as `<paket>:<schluessel>`, e.g. `basis:organisation`. The other package must then be listed under `abhaengigkeiten` (dependencies). To Mappe types that the DMS brings itself, you refer with `dms:` – without a dependency: `dms:ablageort` (where an original is kept), `dms:benutzer` (user) and `dms:rolle` (role). This requires `dms: ">=0.75.0"` in the manifest. The package id `dms` is therefore taken.

Sample Mappen may refer to each other (from DMS 0.79.0): a sample gets a `schluessel`, a reference field of another sample gets the value `{ beispiel: strom }` – or `{ beispiel: "basis:stadtwerke" }` for a sample from a dependency. The manifest must then contain `dms: ">=0.79.0"`.

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
