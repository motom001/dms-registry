# Fremder Code im Modul

`code/modul.wasm` enthält zwei Bibliotheken, die beim Bau aus ihren Quellen übersetzt werden (feste Commits in `code/bauen.sh`):

| Bibliothek | Version | Lizenz |
| --- | --- | --- |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | 5.5.1 | Apache-2.0 (wie dieses Paket, siehe `../../LICENSE`) |
| [Leptonica](https://github.com/DanBloomberg/leptonica) | 1.85.0 | BSD-2-Clause-artig, siehe `leptonica.txt` |

Die Sprachdaten in `code/daten/` stammen aus [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) (Apache-2.0).
