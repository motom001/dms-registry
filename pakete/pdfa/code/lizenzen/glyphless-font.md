# GlyphLessFont (Tesseract)

`code/daten/glyphless.ttf` ist die Datei `tessdata/pdf.ttf` aus [Tesseract](https://github.com/tesseract-ocr/tesseract)
(Commit `3b7c70e34dea179549ed3e995872e2e019eb8477`, Version 5.5.1), unverändert; `code/bauen.sh` holt sie und prüft
ihre SHA-256-Prüfsumme. Tesseract nutzt sie für die unsichtbare Textebene seiner PDFs: eine TrueType-Schrift ohne
sichtbare Zeichen, jede Glyphe ein halbes Geviert breit.

Lizenz: Apache License 2.0, wie Tesseract (den vollständigen Text enthält `LICENSE` im Paketordner).

    (C) Copyright 2011, Google Inc.
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
