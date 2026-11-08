// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung des DMS: Importe dms.* und WASI, Ereignis
// „Archivfassung erstellen“ (datei.archivfassung), Datei über GET /dokumente/{id}/inhalt bzw. …/fassung, Seitenbilder
// über GET …/seiten/{nr}/scan (pdftoppm, wie im DMS), Wortpositionen über GET …/wortpositionen (Textebene mit
// pdftotext -bbox, sonst <name>.woerter.json als „Texterkennung“), Ablage über PUT …/archivfassung.
// E-Mails (#143) holt das Modul nur über …/inhalt und setzt sie selbst; die Zeitzone steht im Ereignis (Feld zeitzone, DMS #946).
// Legt jede Archivfassung als <name>.pdfa.pdf in den Ordner (Prüfung: beispiele.py vergleiche, veraPDF).
//
//   node tests/modul_test.mjs <ordner mit den Testdateien aus tests/beispiele.py> [--messen]
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const ordner = process.argv[2];
if (!ordner) { console.error('Aufruf: node tests/modul_test.mjs <ordner>'); process.exit(2); }
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const DATEN = join(hier, '..', 'code', 'daten');
const SHA = 'b'.repeat(64);
const MIME = { jpg: 'image/jpeg', png: 'image/png', pdf: 'application/pdf', eml: 'message/rfc822', msg: 'application/vnd.ms-outlook' };
const istMail = (mime) => mime === 'message/rfc822' || mime === 'application/vnd.ms-outlook';

const seitenzahl = (pdf) => Number(/Pages:\s+(\d+)/.exec(execFileSync('pdfinfo', [pdf]).toString())[1]);
function seitenGroessen(pdf) {
  const t = execFileSync('pdfinfo', ['-f', '1', '-l', '9999', pdf]).toString();
  return [...t.matchAll(/Page\s+\d+ size:\s+([\d.]+) x ([\d.]+) pts/g)].map((m) => [Number(m[1]), Number(m[2])]);
}
/** Wörter der Textebene je Seite wie das DMS (Poppler): relativ, oben links. */
function textebene(pdf) {
  const html = execFileSync('pdftotext', ['-bbox', pdf, '-'], { maxBuffer: 64 << 20, stdio: ['ignore', 'pipe', 'ignore'] }).toString();
  const seiten = [];
  let s = null;
  for (const z of html.split('\n')) {
    const p = /<page width="([\d.]+)" height="([\d.]+)">/.exec(z);
    if (p) { s = { breite: Number(p[1]), hoehe: Number(p[2]), woerter: [] }; seiten.push(s); continue; }
    const w = /<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*)<\/word>/.exec(z);
    if (w && s) {
      const [x1, y1, x2, y2] = w.slice(1, 5).map(Number);
      s.woerter.push([w[5].replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"'), x1 / s.breite, y1 / s.hoehe, (x2 - x1) / s.breite, (y2 - y1) / s.hoehe]);
    }
  }
  return seiten;
}
const mitText = (s) => s.woerter.map((w) => w[0]).join('').replace(/\s/g, '').length >= 20;

/** Wortpositionen wie GET /dokumente/{id}/wortpositionen. */
function wortpositionen(datei, mime) {
  if (istMail(mime)) return { dokument: 'dok-1', sha256: SHA, quelle: 'original', mime, vollstaendig: false, seiten: [] };
  const pfad = join(ordner, datei);
  const ocr = existsSync(`${pfad}.woerter.json`) ? JSON.parse(readFileSync(`${pfad}.woerter.json`, 'utf8')) : null;
  if (mime !== 'application/pdf') {
    const b = readFileSync(pfad);
    const g = mime === 'image/png' ? { breite: b.readUInt32BE(16), hoehe: b.readUInt32BE(20) } : (() => {
      for (let i = 2; i + 9 < b.length;) { const m = b[i + 1]; const l = b.readUInt16BE(i + 2); if (m >= 0xc0 && m <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(m)) return { hoehe: b.readUInt16BE(i + 5), breite: b.readUInt16BE(i + 7) }; i += 2 + l; }
      return {};
    })();
    return { dokument: 'dok-1', sha256: SHA, quelle: 'original', mime, vollstaendig: !!ocr, seiten: [{ seite: 1, quelle: ocr ? 'texterkennung' : 'keine', ...g, woerter: ocr?.[0] ?? [] }] };
  }
  const ebene = textebene(pfad);
  const seiten = ebene.map((e, i) => mitText(e) ? { seite: i + 1, quelle: 'textebene', breite: e.breite, hoehe: e.hoehe, woerter: e.woerter }
    : ocr?.[i] ? { seite: i + 1, quelle: 'texterkennung', breite: e.breite, hoehe: e.hoehe, woerter: ocr[i] } : { seite: i + 1, quelle: 'keine', breite: e.breite, hoehe: e.hoehe, woerter: [] });
  return { dokument: 'dok-1', sha256: SHA, quelle: 'original', mime, vollstaendig: seiten.every((s) => s.quelle !== 'keine'), seiten };
}

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher (höchstens 256 MB), Ereignis rein, Ergebnis und API-Aufrufe raus. */
function lauf({ datei, daten = {}, archiv = 404, ablegen = 200, vorhanden = null, art = 'datei.archivfassung', version = '1.0.0', zeitzone = 'Europe/Berlin', mime: typ }) {
  const mime = typ ?? MIME[datei.split('.').pop()];
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '', gesetzt = null;
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 32, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const pfad = join(ordner, datei);
  const api = (q, body) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    if (q.methode === 'GET' && q.pfad === '/dokumente/dok-1/archivfassung') {
      if (vorhanden) { antwort = new Uint8Array(vorhanden); return 200; }
      return json(archiv, { fehler: 'Zu diesem Dokument gibt es keine Archivfassung.' });
    }
    if (q.methode === 'GET' && q.pfad === '/dokumente/dok-1/wortpositionen') return json(200, wortpositionen(datei, mime));
    if (q.methode === 'GET' && (q.pfad === '/dokumente/dok-1/inhalt' || q.pfad === '/dokumente/dok-1/fassung')) { antwort = new Uint8Array(readFileSync(pfad)); return 200; }
    const s = /^\/dokumente\/dok-1\/seiten\/(\d+)\/scan\?dpi=(\d+)$/.exec(q.pfad);
    if (q.methode === 'GET' && s && mime === 'application/pdf') {
      const nr = Number(s[1]);
      if (nr > seitenzahl(pfad)) return json(404, { fehler: `Seite ${nr} gibt es nicht.` });
      antwort = new Uint8Array(execFileSync('pdftoppm', ['-gray', '-r', s[2], '-f', String(nr), '-l', String(nr), pfad], { maxBuffer: 256 << 20 }));
      return 200;
    }
    if (q.methode === 'PUT' && q.pfad === `/dokumente/dok-1/archivfassung?sha256=${SHA}`) {
      if (ablegen !== 200) return json(ablegen, { fehler: ablegen === 409 ? 'Das Dokument hat inzwischen eine andere Datei.' : ablegen === 422 ? 'Dem PDF fehlen die XMP-Metadaten.' : 'Störung' });
      gesetzt = Buffer.from(body);
      return json(200, { dokument: 'dok-1', archivfassung: { groesse: body.length } });
    }
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(text(p, l))),
    api_binaer: (p, l, bp, bl) => api(JSON.parse(text(p, l)), u8().slice(bp, bp + bl)),
    datei: (p, l) => { const n = text(p, l); const f = join(DATEN, n); if (n.includes('/') || !existsSync(f)) return -1; antwort = new Uint8Array(readFileSync(f)); return antwort.length; },
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: (s, p, l) => { protokoll.push(`${s} ${text(p, l)}`); return 0; },
  };
  const dv = () => new DataView(memory.buffer);
  const wasi = {
    fd_write: (fd, iov, n, aus) => { let s = 0; for (let i = 0; i < n; i++) { const p = dv().getUint32(iov + 8 * i, true), l = dv().getUint32(iov + 8 * i + 4, true); protokoll.push(`stdout ${text(p, l)}`); s += l; } dv().setUint32(aus, s, true); return 0; },
    clock_time_get: (_id, _p, aus) => { dv().setBigUint64(aus, BigInt(Date.now()) * 1000000n, true); return 0; },
    environ_sizes_get: (a, b) => { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; },
    environ_get: () => 0,
    proc_exit: (c) => { throw new Error(`proc_exit ${c}`); },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) {
    if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = wasi[i.name] ?? (() => 52 /* ENOSYS */);
  }
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const wp = wortpositionen(datei, mime);
  const ereignis = new TextEncoder().encode(JSON.stringify({
    art, id: 'e-1', versuch: 1, erstellt: '2026-11-03T10:00:00.000Z',
    daten: { dokument: 'dok-1', mappe: 'mappe-1', name: datei, mime, groesse: 1, sha256: SHA, quelle: 'original', seiten: istMail(mime) ? null : wp.seiten.length,
      textebene: 'keine', wortpositionen: istMail(mime) ? true : wp.vollstaendig, sprache: 'deu', signiert: false, erechnung: false, formular: false, extern: datei === 'extern.pdf', ...(zeitzone ? { zeitzone } : {}), ...daten },
    paket: { id: 'pdfa', version }, einstellungen: { pdf_text: true, pdf_scan: true, bilder: true, emails: true },
  }));
  const p = inst.exports.dms_puffer(ereignis.length);
  u8().set(ereignis, p);
  const t0 = Date.now();
  const code = inst.exports.dms_ereignis(p, ereignis.length);
  return { code, ergebnis, protokoll, aufrufe, gesetzt, ms: Date.now() - t0, mb: memory.buffer.byteLength / 1048576 };
}

let fehler = 0;
function pruefe(name, ok, r) {
  if (!ok) { fehler++; console.log(`✗ ${name}: Code ${r.code}, ${r.ergebnis}\n  ${r.aufrufe.slice(0, 12).join('\n  ')}\n  ${r.protokoll.join('\n  ')}`); }
  else console.log(`✓ ${name}: ${r.ergebnis} (${r.ms} ms, ${r.mb} MB Speicher)`);
}
const kopf = (b) => b && b.subarray(0, 5).toString('latin1') === '%PDF-';

const DATEIEN = ['foto.jpg', 'exif6.jpg', 'cmyk.jpg', 'durchsichtig.png', 'grau.png', 'rechnung.pdf', 'extern.pdf', 'scan.pdf', 'lang.pdf'];
if (process.argv[3] === '--messen') {
  for (const datei of DATEIEN) {
    const r = lauf({ datei });
    console.log(`${datei}: ${(readFileSync(join(ordner, datei)).length / 1024).toFixed(0)} KB → ${r.gesetzt ? (r.gesetzt.length / 1024).toFixed(0) : '–'} KB in ${r.ms} ms, Speicher ${r.mb} MB – ${r.ergebnis}`);
  }
  process.exit(0);
}

for (const datei of DATEIEN) {
  const r = lauf({ datei });
  pruefe(`${datei} → PDF/A`, r.code === 0 && kopf(r.gesetzt) && r.ergebnis.startsWith('PDF/A-2b'), r);
  if (r.gesetzt) writeFileSync(join(ordner, `${datei}.pdfa.pdf`), r.gesetzt);
}
let r = lauf({ datei: 'foto.jpg' });
pruefe('JPEG kommt unverändert ins PDF/A', r.ergebnis.includes('JPEG unverändert übernommen'), r);
r = lauf({ datei: 'cmyk.jpg' });
pruefe('CMYK-JPEG wird umgerechnet', r.ergebnis.includes('JPEG umgerechnet'), r);
r = lauf({ datei: 'lang.pdf' });
pruefe('60 Seiten: 200 dpi', r.ergebnis.includes('60 Seiten') && r.ergebnis.includes('200 dpi'), r);
r = lauf({ datei: 'extern.pdf' });
pruefe('Externe Inhalte: weggelassen, im Ergebnis genannt', r.ergebnis.includes('externe Inhalte weggelassen'), r);
r = lauf({ datei: 'scan.pdf', daten: { wortpositionen: false } });
pruefe('Ohne Wortpositionen: Code 0, Grund, nichts abgelegt', r.code === 0 && r.gesetzt === null && r.ergebnis.startsWith('Wortpositionen fehlen'), r);
r = lauf({ datei: 'foto.jpg', vorhanden: readFileSync(join(ordner, 'foto.jpg.pdfa.pdf')) });
pruefe('Wiederholung: eigene Archivfassung da → nichts zu tun', r.code === 0 && r.gesetzt === null && r.ergebnis === 'Archivfassung schon vorhanden', r);
r = lauf({ datei: 'foto.jpg', vorhanden: readFileSync(join(ordner, 'foto.jpg.pdfa.pdf')), version: '1.1.0' });
pruefe('Archivfassung einer anderen Version → neu', r.code === 0 && kopf(r.gesetzt), r);
r = lauf({ datei: 'foto.jpg', vorhanden: readFileSync(join(ordner, 'foto.jpg.pdfa.pdf')), daten: { neu: true } });
pruefe('neu: true → neu erzeugen, ohne nachzusehen', r.code === 0 && kopf(r.gesetzt) && !r.aufrufe.includes('GET /dokumente/dok-1/archivfassung'), r);
r = lauf({ datei: 'foto.jpg', ablegen: 409 });
pruefe('Andere Datei (409): Code 0, Grund', r.code === 0 && r.ergebnis.includes('andere Datei'), r);
r = lauf({ datei: 'foto.jpg', ablegen: 422 });
pruefe('Abgelehnt (422): Code 0, Grund', r.code === 0 && r.ergebnis.startsWith('Archivfassung nicht angenommen'), r);
r = lauf({ datei: 'foto.jpg', ablegen: 503 });
pruefe('DMS gestört (503): Fehlercode, Wiederholung', r.code !== 0, r);
r = lauf({ datei: 'foto.jpg', art: 'paket.einstellungen_geaendert' });
pruefe('Anderes Ereignis: nichts zu tun', r.code === 0 && r.aufrufe.length === 0, r);

/* ---------- E-Mails (#143) ---------- */

const MAILS = ['text.eml', 'html.eml', 'anhaenge.eml', 'weitergeleitet.eml', 'latin1.eml', 'kyrillisch.eml', 'lang.eml', 'outlook.msg'];
const textVon = (pdf) => execFileSync('pdftotext', ['-layout', pdf, '-'], { maxBuffer: 64 << 20 }).toString();
const kurz = (t) => t.replace(/\s+/g, ' ');
function enthaelt(name, datei, muss, nicht = []) {
  const pdf = join(ordner, `${datei}.pdfa.pdf`);
  if (!existsSync(pdf)) { fehler++; console.log(`✗ ${name}: keine Archivfassung`); return; }
  const t = kurz(textVon(pdf));
  const fehlt = muss.filter((m) => !t.includes(m)), zuviel = nicht.filter((m) => t.includes(m));
  if (fehlt.length || zuviel.length) { fehler++; console.log(`✗ ${name}: fehlt ${JSON.stringify(fehlt)}, zu viel ${JSON.stringify(zuviel)}\n  ${t.slice(0, 600)}`); }
  else console.log(`✓ ${name}`);
}
for (const datei of MAILS) {
  const r = lauf({ datei });
  pruefe(`${datei} → PDF/A`, r.code === 0 && kopf(r.gesetzt) && r.ergebnis.startsWith('PDF/A-2b') && !r.aufrufe.some((a) => a.includes('wortpositionen') || a.includes('volltext')), r);
  if (r.gesetzt) writeFileSync(join(ordner, `${datei}.pdfa.pdf`), r.gesetzt);
}
enthaelt('Text-Mail: Kopf, Datum in Berlin, Text, Zitat', 'text.eml', ['Ihre Abschlagszahlung ab Dezember', 'Von Stadtwerke Musterstadt <service@example.org>', 'An Lena Muster <lena@example.org>',
  'Datum 02.11.2026, 10:15 Uhr', 'Ihr monatlicher Abschlag ändert sich ab 01.12.2026 auf 84,00 €', 'Vertragskonto: 4711-0815', 'Bitte den Abschlag anpassen.', 'Ältere Nachricht ganz unten.',
  'Freundliche Grüße', 'Seite 1 von 1']);
enthaelt('HTML-Mail: Überschrift, Fett, Tabelle, Listen, Link mit Adresse, Platzhalter; kein Skript, kein Titel, kein Formularwert', 'html.eml',
  ['Ihre Rechnung November', 'Cc Tom Muster', 'Fällig am 15.11.2026', 'bitte pünktlich', 'Posten', 'Grundpreis', '12,50 €', 'Erster Punkt', '2. Schritt zwei',
    'Kundenportal (https://example.org/portal)', 'E-Mail (service@example.org)', 'Zitierter Absatz', 'externes Bild nicht geladen: Werbung'],
  ['SKRIPTINHALT', 'TITELTEXT', 'Klartext-Fassung', 'font-family', 'FORMULARWERT']);
enthaelt('Anhänge: Liste mit Name, Art und Größe; Inhalt nicht', 'anhaenge.eml', ['Anhänge (3)', 'Mietvertrag.pdf · PDF', 'Hausordnung.docx · Word', 'Zählerstand.jpg · Bild (JPEG)', 'Von Herr Özdemir'], ['ANHANGINHALT']);
enthaelt('Weitergeleitet: drei Ebenen gesetzt, die vierte nur in der Liste', 'weitergeleitet.eml', ['WG: Ablesetermin', 'Weitergeleitete E-Mail', 'Ebene 1: Ablesetermin', 'Text der Ebene 1.',
  'Ebene 2: Ablesetermin', 'Text der Ebene 2.', 'Ebene 3: Ablesetermin', 'Text der Ebene 3.', 'Ebene 4: Ablesetermin'], ['Text der Ebene 4.']);
enthaelt('Windows-1252 und kodierte Kopfzeilen', 'latin1.eml', ['Überweisung für Oktober', 'Jürgen Müller', '1.250 € wird „am Monatsende“ fällig – Grüße', 'Datum 03.11.2026, 10:00 Uhr']);
enthaelt('Kyrillisch und Griechisch; fehlende Zeichen nie als „?“', 'kyrillisch.eml', ['Привет из Москвы', 'Ирина Петрова', 'Здравствуйте, Лена!', 'Καλημέρα από την Αθήνα', 'Datum 04.11.2026, 10:00 Uhr'], ['?']);
enthaelt('Lange Mail: mehrere Seiten, Kopf- und Fußzeile', 'lang.eml', ['Seite 1 von', 'Seite 2 von', 'E-Mail · Protokoll der Eigentümerversammlung', 'Punkt 59:', 'Datum 01.08.2026, 18:30 Uhr']);
enthaelt('Outlook: HTML-Text, Anhang, eingebettete Nachricht', 'outlook.msg', ['Angebot Dachrinne – Petra', 'Petra Sommer <petra@example.org>', 'Markus Weber <markus@example.org>', 'Datum 02.11.2026, 10:30 Uhr',
  'anbei das Angebot über 1.250 €', 'Angebot.pdf · PDF', 'Altes Angebot.msg · Outlook-Nachricht', 'Eingebettet: Angebot alt', 'Text der eingebetteten Nachricht.'], ['Klartext des Angebots']);
const schriften = execFileSync('pdffonts', [join(ordner, 'html.eml.pdfa.pdf')]).toString();
pruefe('Schriften als Teilmenge eingebettet (Noto Sans)', /[A-Z]{6}\+NotoSans-Regular\s+CID TrueType\s+Identity-H\s+yes\s+yes\s+yes/.test(schriften) && /NotoSans-Bold/.test(schriften),
  { code: 0, ergebnis: schriften, aufrufe: [], protokoll: [] });
const bilder = execFileSync('pdfimages', ['-list', join(ordner, 'html.eml.pdfa.pdf')]).toString().trim().split('\n').length - 2;
pruefe('cid:-Bild in der Seite, externes nicht', bilder === 1, { code: 0, ergebnis: `${bilder} Bilder`, aufrufe: [], protokoll: [] });
r = lauf({ datei: 'text.eml', zeitzone: 'America/New_York' });
writeFileSync(join(ordner, 'zeitzone.pdfa.pdf'), r.gesetzt ?? Buffer.alloc(0));
pruefe('Zeitzone der Ablage (New York)', r.code === 0 && kurz(textVon(join(ordner, 'zeitzone.pdfa.pdf'))).includes('Datum 02.11.2026, 04:15 Uhr'), r);
r = lauf({ datei: 'text.eml', zeitzone: null });
pruefe('Ohne Feld zeitzone (ältere Ablago): Europe/Berlin', r.code === 0 && kopf(r.gesetzt), r);
pruefe('E-Mail: kein Aufruf von /region, /wortpositionen, /volltext', !r.aufrufe.some((a) => /\/region|\/wortpositionen|\/volltext/.test(a)), r);
r = lauf({ datei: 'text.eml', mime: 'application/octet-stream' });
pruefe('Dateityp octet-stream mit Endung .eml', r.code === 0 && kopf(r.gesetzt), r);
r = lauf({ datei: 'foto.jpg', mime: 'message/rfc822' });
pruefe('Keine E-Mail am Inhalt: Grund, nichts abgelegt', r.code === 0 && r.gesetzt === null && r.ergebnis.includes('keine lesbare E-Mail'), r);
r = lauf({ datei: 'html.eml', vorhanden: readFileSync(join(ordner, 'html.eml.pdfa.pdf')) });
pruefe('Wiederholung bei E-Mails: nichts zu tun', r.code === 0 && r.gesetzt === null && r.ergebnis === 'Archivfassung schon vorhanden', r);

process.exit(fehler ? 1 : 0);
