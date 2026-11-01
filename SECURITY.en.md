# Security

[Deutsch](SECURITY.md) · **English**

This repository belongs to the DMS ([motom001/dms](https://github.com/motom001/dms)) and contains: packages, the catalogue and the check tools.

## Reporting a vulnerability

Please **do not open a public issue** for security vulnerabilities. Report them confidentially via GitHub: **Security → Report a vulnerability** in this repository ([private vulnerability reporting](https://github.com/motom001/dms-registry/security/advisories/new)). Reports in German or English are welcome.

If the vulnerability affects the DMS itself, please report it directly in the repository [motom001/dms](https://github.com/motom001/dms/security/advisories/new).

## What is checked automatically

| What | With | When |
| --- | --- | --- |
| Check tools (Python), workflows | CodeQL | every pull request, every push to `main` |
| Packages in the catalogue | `pruefen.py` (schema, rules, Signed-off-by) | every pull request |
| GitHub Actions | Dependabot (alerts and updates) | every pull request, weekly |
| Secrets (tokens, passwords) | Secret scanning with push protection | every push |

Findings are listed under **Security** in this repository.

This is a translation. If the German and English versions differ, the German version ([SECURITY.md](SECURITY.md)) applies.
