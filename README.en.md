# DMS Registry

[Deutsch](README.md) · **English**

The central place for **packages** for the [DMS](https://github.com/motom001/dms), the self-hosted document management for households and families.

> This is a translation. **If the German and English versions differ, the German version ([README.md](README.md)) applies.** The DMS itself, the check tool `pruefen.py`, the schema messages and the package contents are in German for now – see [Languages](#languages).

A package extends the DMS without anyone having to click through the workbench ("Werkbank") field by field:

- **Configuration:** Mappe types ("Mappentypen", structured folders) with fields, tabs and result lists, views ("Sichten"), sample Mappen. Examples are a base package with organisation and person, or the packages "Haushalt" (household), "Haus" (house) and "Fahrzeuge" (vehicles).
- **Code (from DMS 0.88.0):** A package reacts to events in the DMS, such as "document uploaded", and works through the [API](https://motom001.github.io/dms/admin/aktuell/api/) (German) with its own permissions that are confirmed during installation. Examples: [Texterkennung](pakete/texterkennung/) (text recognition, Tesseract as WebAssembly), [KI lokal – Ähnlichkeit](pakete/ki_aehnlich/) (similar documents with a small embedding model, no network), [KI-Assistent](pakete/ki_assistent/) ("ask your files" through your own AI service such as Ollama), [Bildformate](pakete/bildformate/) (thumbnail and full text for TIFF, WebP, GIF and BMP), [Office und E-Mail](pakete/office_email/) (full text for Word, Excel, PowerPoint, OpenDocument and e-mails), [Sicherungsziel WebDAV](pakete/sicherung_webdav/) (every backup off-site to Nextcloud, a NAS or a hosting provider, verified there) and the small [Hallo Post](pakete/hallo_post/). The code runs as WebAssembly, isolated in the DMS package runner ("Paket-Läufer"), never in the DMS process itself; the CI builds it from source (`code/bauen.sh`, [`werkzeuge/bauen.py`](werkzeuge/bauen.py)).

In the DMS you install packages under **Werkbank → Pakete**. Package management is work in progress; until then, this repository collects the packages and sets the rules.

## Layout

```
pakete/<paket>/        one folder per package, name = package id
vorlage/               template for a new package – copy it and get started
schema/                JSON schemas for manifest.yaml and the contents
werkzeuge/             neues-paket.sh, pruefen.py, katalog.py, signieren.py, webseite.py, sammeldatei.py (also run in the CI);
                       kategorien.yaml: categories of the packages in the catalogue
schluessel/            public keys the catalogue is signed with (see "Signing the catalogue")
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
- `…/gh-pages/katalog.sig` – the signature of the catalogue (see [Signing the catalogue](#signing-the-catalogue))

The same branch holds the **catalogue website** (`werkzeuge/webseite.py`): browse packages like in an app store – an overview with search and filters by type, **category** and **author** (also via the address, e.g. `index.html?kategorie=dateiformate&autor=motom001`), and one page per package with description, what gets created, permissions, changes and older versions. **"In meinem DMS installieren"** (install in my DMS) asks for the address of your DMS the first time (remembered only in your browser, changeable) and opens `/werkbank/pakete?installieren=<id>@<version>` there; nothing is installed until you confirm it in the DMS. The website sends nothing to your DMS. The overview is available in German and English (`en/index.html`, switch "Deutsch · English" at the top, works without JavaScript); package pages and package descriptions are in German for now. Categories appear as chips on tiles and package pages; "Ähnliche Pakete ›" (similar packages) on a package page are packages of the same category (see [REGELN.en.md, "Categories"](REGELN.en.md#categories)).

**Packages without internet** (`sammeldatei.html`, motom001/dms#461; page in German for now): tick packages, choose the DMS version (default: the newest; the DMS links here with `?dms=<version>`), dependencies are added automatically. The browser downloads the archives, checks each against SHA-256 and size from `katalog.json` and packs them together with the index `sammeldatei.json` (format: [`schema/sammeldatei.schema.json`](schema/sammeldatei.schema.json)) into **one bundle file**, together with the signed catalogue (`katalog.json` and `katalog.sig`) – nothing is uploaded. When uploading, the DMS checks every archive against size and checksum in the index and against the signed catalogue (and against the official catalogue if it has already fetched it), rejects unknown files and then installs package by package. If the signature is valid, nobody needs to confirm the origin any more. `werkzeuge/sammeldatei.py` creates the same file on the command line and checks a bundle the way the DMS does (`--pruefen <file> [--katalog katalog.json] [--oeffentlich <x.pub> …]`).

With GitHub Pages (source: branch `gh-pages`), the website is available at **`https://motom001.github.io/dms-registry/`**, and the catalogue also at `…/katalog.json`.

`katalog.json` (format: [`schema/katalog.schema.json`](schema/katalog.schema.json)) contains the format version, creation time, source and, per package, id, name, description, author, licence, current version, categories (`kategorien`, 1–2 identifiers from `werkzeuge/kategorien.yaml` – for the website only, the DMS does not read this field) and **all versions**, newest first. Per version it lists: required DMS version, dependencies, content overview (Mappe types and views with names, number of samples), whether the package has code, address of the archive (relative to `katalog.json`), **SHA-256** and size of the archive, time of publication, and links to the source folder, README and changelog.

```json
{
  "format": 1, "erstellt": "2026-11-01T10:00:00Z", "quelle": "https://github.com/motom001/dms-registry", "signatur": null,
  "pakete": [{
    "id": "basis", "name": "Basis", "beschreibung": "…", "autor": { "name": "…", "github": "…" }, "lizenz": "CC0-1.0", "aktuell": "1.0.0", "kategorien": ["vorlagen"],
    "versionen": [{
      "version": "1.0.0", "dms": ">=0.63.0", "abhaengigkeiten": {},
      "inhalt": { "mappentypen": [{ "schluessel": "organisation", "name": "Organisation" }], "sichten": [ … ], "beispiele": 2 },
      "code": false, "archiv": "archive/basis-1.0.0.zip", "sha256": "…", "groesse": 4711, "veroeffentlicht": "…",
      "quelle": "…", "readme": "…", "changelog": "…"
    }]
  }]
}
```

Older versions remain in the catalogue and available as archives. An archive with the same id and version never changes: if a package changes without a new version, the check in the pull request fails. Locally, you build the catalogue with `python3 werkzeuge/katalog.py <folder>`. The field `signatur` stays `null`: the signature is kept separately in `katalog.sig`.

## Signing the catalogue

The CI **signs** every published catalogue (#74; in the DMS: motom001/dms#594). Because `katalog.json` contains the checksum of every archive, **one** signature proves that all packages come from the DMS project – also offline in a bundle file.

- **Method:** Ed25519 over the **exact bytes** of `katalog.json`, using `openssl pkeyutl` (`werkzeuge/signieren.py`).
- **`katalog.sig`** sits next to `katalog.json` (separate, so older DMS versions read the catalogue unchanged):

    ```json
    { "format": 1, "verfahren": "ed25519", "schluessel": "<key id>", "signatur": "<base64>", "erstellt": "2026-11-02T10:00:00Z" }
    ```

- **`erstellt`** is part of `katalog.json` (time of the build). Online, the DMS rejects signed catalogues that are older than the newest one it has seen.
- **Key id and fingerprint:** SHA-256 over the 32 bytes of the public key, in hex – key id = the first 16 characters, fingerprint = all 64 in groups of four (`python3 werkzeuge/signieren.py fingerabdruck <file.pub>`).
- **Two keys:** the **signing key** exists only as the secret `KATALOG_SIGNIERSCHLUESSEL` in the environment `katalog` (branch `main` only). The **backup key** is kept offline by the maintainer. Both public keys are built into the DMS and stored here as `schluessel/signier.pub` and `schluessel/reserve.pub`; after signing, the CI verifies the signature with them.
- **Without the secret** (in forks, or as long as it has not been created), the build continues **without** a signature and prints a clear warning in the run. An old `katalog.sig` is removed, because it would no longer match.
- **Bundle files** contain the signed catalogue (`katalog.json` and `katalog.sig`, byte for byte). The DMS then no longer asks to confirm the origin. `python3 werkzeuge/sammeldatei.py --pruefen <file> --oeffentlich schluessel/signier.pub --oeffentlich schluessel/reserve.pub` verifies the signature as well.

**Fingerprints** (SHA-256 over the 32 bytes of the public key, as shown by the DMS and `werkzeuge/signieren.py`; same as in the [SECURITY.md of the DMS](https://github.com/motom001/dms/blob/main/SECURITY.en.md)):

| Key | ID | Fingerprint |
| --- | --- | --- |
| Signing key | `6d868387314e64df` | `6d86 8387 314e 64df 715c a3bd 9856 58d5 f888 c0ea 7cab ac91 a43f 9b99 6052 e728` |
| Backup key | `4543c81b5ccf522d` | `4543 c81b 5ccf 522d f5a3 5e76 6660 8774 5f6c ae42 4722 3b6d 91c9 63cc 34b0 3954` |

The DMS knows these keys from version 0.144.2; older versions (0.141.0–0.144.1) still verify with test keys and report “signature invalid” once the catalogue is signed.

### What only the maintainer can do (once)

On **your own computer** – not in a chat session, not in the CI:

```sh
openssl genpkey -algorithm ed25519 -out signier.pem
openssl pkey -in signier.pem -pubout -out signier.pub
openssl genpkey -algorithm ed25519 -out reserve.pem
openssl pkey -in reserve.pem -pubout -out reserve.pub
python3 werkzeuge/signieren.py fingerabdruck signier.pub reserve.pub
```

1. In dms-registry, go to **Settings → Environments → New environment** and create the environment `katalog` (the CI also creates it on its first run; then only configure it). Under **Deployment branches and tags**, choose "Selected branches and tags" and allow only `main`.
2. In this environment, under **Environment secrets → Add secret**, create the secret `KATALOG_SIGNIERSCHLUESSEL`. Content: the **complete** file `signier.pem` (including the lines `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----`).
3. Keep `reserve.pem` **offline** (a safe place, plus a printout) – **never** on GitHub.
4. Post `signier.pub` and `reserve.pub` as a comment in #74 (public keys are not sensitive). They then go into `schluessel/` here and into `server/src/projektschluessel.ts` of the DMS; the fingerprints go into this README and into the SECURITY.md of the DMS.
5. Afterwards, delete `signier.pem` and `reserve.pem` from your computer. The backup stays only in its safe place.

The next run of "Katalog veröffentlichen" (push to `main` or **Actions → Katalog veröffentlichen → Run workflow**) then signs. If the key in the secret does not match `schluessel/*.pub`, the run fails – nothing is published with a wrong key.

**Key lost or leaked?** Put the backup key into the secret; the DMS accepts it without an update. Then generate a new backup pair and ship it with a DMS release.

### Your own catalogue with your own key

If you run your own catalogue, you can sign it with `werkzeuge/signieren.py` in the same way and put your public key next to it as `katalog.schluessel`. When adding the catalogue, the DMS shows the fingerprint and only accepts it after confirmation (like SSH on first contact). A key change is announced with `katalog.schluessel.sig` (the new key, signed with the old one: `signieren.py signieren-datei`). Instructions: [DMS developer manual](https://motom001.github.io/dms/entwickler/aktuell/pakete/#eigener-katalog-mit-eigenem-schluessel) (German).

## Creating a package

```sh
git clone https://github.com/<you>/dms-registry && cd dms-registry
werkzeuge/neues-paket.sh my_package "My package"
# adjust pakete/my_package/: manifest.yaml, README.md, inhalt/ …
# propose a category: in werkzeuge/kategorien.yaml under "pakete:", e.g. "my_package: [vorlagen]"
python3 werkzeuge/pruefen.py pakete/my_package
```

You propose the **category** yourself: one line `<id>: [<identifier>]` in [`werkzeuge/kategorien.yaml`](werkzeuge/kategorien.yaml), one or two identifiers from the list there (the first one is the main category). Without an entry, `pruefen.py` fails; the maintainer may still change the assignment in the pull request. New categories only via an issue ([REGELN.en.md, "Categories"](REGELN.en.md#categories)).

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
