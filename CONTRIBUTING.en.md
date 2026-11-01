# Contributing a package

[Deutsch](CONTRIBUTING.md) · **English**

**Issues and pull requests are welcome in German or English.** This is a translation; if the German and English versions differ, the German version ([CONTRIBUTING.md](CONTRIBUTING.md)) applies.

1. **Open an issue** – as a user story: "As a … I want a package …, so that …", with acceptance criteria. For a change to an existing package, name the package.
2. **Wait for approval.** Only what carries the label `freigegeben` (approved) is accepted; this label is set by the maintainer alone.
3. **Fork, create the package:** `werkzeuge/neues-paket.sh <id> "<Name>"` copies the template to `pakete/<id>/`.
4. **Fill it in:** `manifest.yaml`, `README.md`, `LICENSE` (year and name), `CHANGELOG.md`, contents under `inhalt/`, expectations under `tests/`. Examples are given as comments in the template.
5. **Check:** `python3 werkzeuge/pruefen.py pakete/<id>` (requires `pip install pyyaml jsonschema`). The same check runs in the pull request.
6. **Pull request** with `Closes #…`. Every commit carries a `Signed-off-by:` (`git commit -s`). With it you confirm, according to the [Developer Certificate of Origin](https://developercertificate.org/), that you have the right to submit the contribution under the licence of the package.
7. **Maintenance:** Add yourself to `.github/CODEOWNERS` for your package. You take care of bugs and new DMS versions; the maintainer approves and merges.

What to watch out for is in the [rules for packages](REGELN.en.md) – licences, permissions, what is forbidden.

**Language:** The messages of `pruefen.py` and of the JSON schemas are in German for now, as are the comments in the template. Folder, file and field names (`pakete/`, `inhalt/`, `lizenz`, `abhaengigkeiten` …) are part of the format and stay German. Field names and views of a package are German; the package README is German, additionally in English if you like (see [REGELN.en.md](REGELN.en.md#mandatory)). If something is unclear, ask in the issue – in English is fine.

Contributions to the tools, schemas, website and template are licensed under the [Apache-2.0](LICENSE) of this repository. Please do not commit real documents or personal data.

How work on the DMS itself is done is described in the [developer manual](https://motom001.github.io/dms/entwickler/aktuell/) (German) and in [CONTRIBUTING.en.md of the DMS](https://github.com/motom001/dms/blob/main/CONTRIBUTING.en.md).

## Code of conduct

Our [code of conduct](CODE_OF_CONDUCT.md) applies to how we treat each other. The German text there is a translation of the [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) – read the English original there. Reports go to [dms.github@thomas.meissner.me](mailto:dms.github@thomas.meissner.me), in German or English.
