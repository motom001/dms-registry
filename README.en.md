# DMS Registry

[Deutsch](README.md) · **English**

The central place for **packages** for the [DMS](https://github.com/motom001/dms), the self-hosted document management for households and families.

> This is a translation. **If the German and English versions differ, the German version ([README.md](README.md)) applies.** The DMS itself, the check tool `pruefen.py`, the schema messages and the package contents are in German for now – see [Languages](#languages).

A package extends the DMS without anyone having to click through the workbench ("Werkbank") field by field:

- **Configuration:** Mappe types ("Mappentypen", structured folders) with fields, tabs and result lists, views ("Sichten"), sample Mappen. Examples are a base package with organisation and person, or the packages "Haushalt" (household), "Haus" (house) and "Fahrzeuge" (vehicles).
- **Code (from DMS 0.88.0):** A package reacts to events in the DMS, such as "document uploaded", and works through the [API](https://motom001.github.io/dms/admin/aktuell/api/) (German) with its own permissions that are confirmed during installation. Examples: [Texterkennung](pakete/texterkennung/) (text recognition, Tesseract as WebAssembly) and the small [Hallo Post](pakete/hallo_post/). The code runs as WebAssembly, isolated in the DMS package runner ("Paket-Läufer"), never in the DMS process itself; the CI builds it from source (`code/bauen.sh`, [`werkzeuge/bauen.py`](werkzeuge/bauen.py)).

In the DMS you install packages under **Werkbank → Pakete**. Package management is work in progress; until then, this repository collects the packages and sets the rules.

## Layout

```
pakete/<paket>/        one folder per package, name = package id
vorlage/               template for a new package – copy it and get started
schema/                JSON schemas for manifest.yaml and the contents
werkzeuge/             neues-paket.sh, pruefen.py, katalog.py, webseite.py (also run in the CI)
REGELN.md              what is allowed, what is not, which licences (English: REGELN.en.md)
CONTRIBUTING.md        how a package gets here (English: CONTRIBUTING.en.md)
```

Folder, file and field names are German and stay that way – they are part of the format.

Every package contains at least:

| File | Content |
| --- | --- |
| `manifest.yaml` | id, name, version, licence, required DMS version, dependencies, contents, code with permissions if any |
| `README.md` | what the package does, for whom, with an example |
| `LICENSE` | licence text (open source, see [REGELN.en.md](REGELN.en.md)) |
| `CHANGELOG.md` | changes per version |
| `inhalt/` | Mappe types, views, samples (YAML) |
| `code/` | only for packages with code: source code, built in the CI |
| `tests/` | expectations for the package |

## Catalogue

With every merge to `main`, the CI builds the **catalogue** and puts it on the branch `gh-pages`:

- **`https://raw.githubusercontent.com/motom001/dms-registry/gh-pages/katalog.json`** – the default catalogue address in the DMS
- `…/gh-pages/archive/<id>-<version>.zip` – one archive per package version containing exactly the files of the package folder (without a folder in front)

The same branch holds the **catalogue website** (`werkzeuge/webseite.py`): browse packages like in an app store – an overview with search and filters, and one page per package with description, what gets created, permissions, changes and older versions. **"In meinem DMS installieren"** (install in my DMS) asks for the address of your DMS the first time (remembered only in your browser, changeable) and opens `/werkbank/pakete?installieren=<id>@<version>` there; nothing is installed until you confirm it in the DMS. The website sends nothing to your DMS. The website is in German.

With GitHub Pages (source: branch `gh-pages`), the website is available at **`https://motom001.github.io/dms-registry/`**, and the catalogue also at `…/katalog.json`.

`katalog.json` (format: [`schema/katalog.schema.json`](schema/katalog.schema.json)) contains the format version, creation time, source and, per package, id, name, description, author, licence, current version and **all versions**, newest first. Per version it lists: required DMS version, dependencies, content overview (Mappe types and views with names, number of samples), whether the package has code, address of the archive (relative to `katalog.json`), **SHA-256** and size of the archive, time of publication, and links to the source folder, README and changelog.

```json
{
  "format": 1, "erstellt": "2026-11-01T10:00:00Z", "quelle": "https://github.com/motom001/dms-registry", "signatur": null,
  "pakete": [{
    "id": "basis", "name": "Basis", "beschreibung": "…", "autor": { "name": "…", "github": "…" }, "lizenz": "CC0-1.0", "aktuell": "1.0.0",
    "versionen": [{
      "version": "1.0.0", "dms": ">=0.63.0", "abhaengigkeiten": {},
      "inhalt": { "mappentypen": [{ "schluessel": "organisation", "name": "Organisation" }], "sichten": [ … ], "beispiele": 2 },
      "code": false, "archiv": "archive/basis-1.0.0.zip", "sha256": "…", "groesse": 4711, "veroeffentlicht": "…",
      "quelle": "…", "readme": "…", "changelog": "…"
    }]
  }]
}
```

Older versions remain in the catalogue and available as archives. An archive with the same id and version never changes: if a package changes without a new version, the check in the pull request fails. Locally, you build the catalogue with `python3 werkzeuge/katalog.py <folder>`. The field `signatur` is reserved for a later signature of the catalogue and is `null` today.

## Creating a package

```sh
git clone https://github.com/<you>/dms-registry && cd dms-registry
werkzeuge/neues-paket.sh my_package "My package"
# adjust pakete/my_package/: manifest.yaml, README.md, inhalt/ …
python3 werkzeuge/pruefen.py pakete/my_package
```

Then open a pull request. The details are in [CONTRIBUTING.en.md](CONTRIBUTING.en.md).

`pruefen.py` and the schema messages report in German for now. If a message is unclear, ask in the issue or the pull request – in English is fine.

## Package settings

Packages with code describe their settings in the manifest under `code.einstellungen`; the DMS builds a form from it (**Werkbank → Pakete → *package* → Einstellungen**), checks and stores the values and passes them to the package. At most two levels:

- **Section:** `abschnitt` (heading), optional `hilfe`, `felder`
- **List** of entries with the same structure: `liste` (key), `name`, `eintrag` (e.g. "Regel", rule), optional `hilfe`, `sortierbar`, `felder`

A **field** has `schluessel`, `name`, `typ` and optionally `hilfe`, `pflicht`, `standard`, `optionen` (choice), `min`/`max` (number), `mappentyp` (for the type `feld`). Types: `text`, `mehrzeilig` (multi-line), `zahl` (number), `janein` (yes/no), `datum` (date), `auswahl` (choice), `mehrfachauswahl` (multiple choice), `geheim` (secret) and the references `mappentyp`, `feld`, `benutzer`, `rolle`, `sicht` (the stable id is stored, chosen from lists). **`code.aktionen`** (`schluessel`, `name`, optional `hilfe`, `bestaetigen`) become buttons in the form. A commented example is in [`vorlage/manifest.yaml`](vorlage/manifest.yaml).

`werkzeuge/pruefen.py` additionally checks: keys are unique per level or list, `standard` matches the type, a choice has `optionen`, `geheim` and references have no default, references to Mappe types of other packages only as `<paket>:<schluessel>` and only to dependencies; to Mappe types of the DMS only `dms:ablageort`, `dms:benutzer` or `dms:rolle`.

## Principles

- **Everything is open source.** Every package here is under a free licence and is built from its source code. The registry does not accept ready-made binaries.
- **As few permissions as necessary.** A package states beforehand what it wants to read, write and where it wants to connect to. The DMS shows this before installation.
- **Packages add, they do not destroy.** An update adds things; it does not delete fields or Mappen.
- **Approval by the maintainer.** As in the DMS: first an issue, and what gets implemented or accepted is what [@motom001](https://github.com/motom001) has approved. The order is in the [roadmap](ROADMAP.md) (German).

## Licence

The tools, schemas, website and template of this repository are licensed under the [Apache-2.0](LICENSE), notices in [NOTICE](NOTICE) (until 1 November 2026: AGPL-3.0). **Every package has its own licence** in its folder – the allowed licences are listed in [REGELN.en.md](REGELN.en.md). The packages we (motom001) publish ourselves are licensed under **Apache-2.0**.

Anyone may use, modify and redistribute what is licensed under Apache-2.0, including in their own products. Whoever redistributes it includes the licence and the notices from NOTICE and marks modified files. Publishing the source code of a modified version is not required.

## Languages

README, [REGELN](REGELN.en.md), [CONTRIBUTING](CONTRIBUTING.en.md) and [SECURITY](SECURITY.en.md) are available in German and English. **If the versions differ, the German version applies.** Issues and pull requests are welcome in German or English.

Still German for now: the DMS and its manuals (an English user interface is planned, [dms #357](https://github.com/motom001/dms/issues/357)), the messages of `pruefen.py` and the JSON schemas, the catalogue website and the package contents (field names, views, package READMEs – see [REGELN.en.md](REGELN.en.md#mandatory)).
