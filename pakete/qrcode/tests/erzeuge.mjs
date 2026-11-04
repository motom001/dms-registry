// Erzeugt die QR-Matrizen für die Tests (tests/qr/*.txt) – nur von Hand nötig, wenn sich die Beispiele ändern.
// Braucht das npm-Paket „qrcode“ (z. B. aus einem Checkout von dms):  NODE_PATH=…/node_modules node tests/erzeuge.mjs
// Je Datei: eine Zeile je Modulreihe, „1“ = dunkel, „0“ = hell; ohne Ruhezone (die setzt der Test).
import { mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const QR = createRequire(import.meta.url)('qrcode');
const ziel = join(dirname(fileURLToPath(import.meta.url)), 'qr');
mkdirSync(ziel, { recursive: true });

// Nur erfundene Namen und reservierte Beispiel-Domains.
const beispiele = {
  vcard30: ['BEGIN:VCARD', 'VERSION:3.0', 'N:Beispiel;Jonas;;Dr.;', 'FN:Dr. Jonas Beispiel', 'ORG:Musterbau GmbH;Vertrieb',
    'TITLE:Leiter Vertrieb', 'TEL;TYPE=WORK,VOICE:+49 30 1234567', 'TEL;TYPE=CELL:+49 170 1234567', 'TEL;TYPE=FAX:+49 30 1234568',
    'EMAIL;TYPE=INTERNET,WORK:jonas.beispiel@example.org', 'URL:https://musterbau.example', 'ADR;TYPE=WORK:;;Musterweg 12;Musterstadt;;01234;Deutschland',
    'END:VCARD'].join('\r\n'),
  vcard21: ['BEGIN:VCARD', 'VERSION:2.1', 'N;CHARSET=UTF-8:Müller-Lüdenscheidt;Petra', 'FN;ENCODING=QUOTED-PRINTABLE;CHARSET=UTF-8:Petra M=C3=BCller-L=C3=BCdenscheidt',
    'ORG:Beispiel & Söhne KG', 'TEL;CELL:0170 7654321', 'TEL;WORK;VOICE:030 7654321', 'EMAIL;INTERNET:petra@example.com',
    'ADR;WORK;ENCODING=QUOTED-PRINTABLE:;;Hauptstra=C3=9Fe 5a;Beispielhausen;;12345;', 'END:VCARD'].join('\r\n'),
  vcard40: ['BEGIN:VCARD', 'VERSION:4.0', 'FN:Katrin Muster', 'N:Muster;Katrin;;;', 'ROLE:Steuerberaterin', 'TEL;VALUE=uri;TYPE="voice,work":tel:+49-89-555-0100',
    'EMAIL:katrin@kanzlei.example', 'NOTE:Komma\\, Semikolon\; Zeilen\\numbruch', 'END:VCARD'].join('\n'),
  // Präpariert: sehr langer Name, Steuerzeichen, eingebettetes Foto, unvollständige Zeilen.
  lang: ['BEGIN:VCARD', 'VERSION:3.0', `ORG:${'Sehr lange Firma '.repeat(60)}`, 'FN:Jonas\u0007 Beispiel', 'N:Beispiel;Jonas', 'PHOTO;ENCODING=b;TYPE=JPEG:/9j/4AAQSkZJRgABAQ', 'EMAIL', 'TEL;TYPE=CELL:', 'END:VCARD'].join('\r\n'),
  url: 'https://example.org/angebot',
  girocode: ['BCD', '002', '1', 'SCT', '', 'Musterbau GmbH', 'DE00000000000000000000', 'EUR12.50', '', '', 'Rechnung 4711'].join('\n'),
};
for (const [name, text] of Object.entries(beispiele)) {
  const q = QR.create(text, { errorCorrectionLevel: 'M' });
  const n = q.modules.size, z = [];
  for (let y = 0; y < n; y++) { let s = ''; for (let x = 0; x < n; x++) s += q.modules.get(y, x) ? '1' : '0'; z.push(s); }
  writeFileSync(join(ziel, `${name}.txt`), z.join('\n') + '\n');
  console.log(`${name}: ${n}×${n}`);
}
