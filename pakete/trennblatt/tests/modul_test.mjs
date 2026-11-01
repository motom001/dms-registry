// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung des DMS: Importe dms.* und WASI,
// API-Antworten für eine Post mit einem Sammelscan; Seitenbilder rastert pdftoppm wie im DMS.
//
//   node tests/modul_test.mjs <ordner mit den Beispiel-PDFs aus tests/beispiel.py>
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const ordner = process.argv[2];
if (!ordner) { console.error('Aufruf: node tests/modul_test.mjs <ordner>'); process.exit(2); }
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const tmp = mkdtempSync(join(tmpdir(), 'trennblatt-'));
const bilder = new Map();

function seite(pdf, nr, dpi) {
  const k = `${pdf}:${nr}:${dpi}`;
  if (!bilder.has(k)) {
    const ziel = join(tmp, `s${bilder.size}`);
    execFileSync('pdftoppm', ['-gray', '-r', String(dpi), '-f', String(nr), '-l', String(nr), '-singlefile', join(ordner, pdf), ziel]);
    bilder.set(k, readFileSync(`${ziel}.pgm`));
  }
  return bilder.get(k);
}
const seitenzahl = (pdf) => Number(/Pages:\s+(\d+)/.exec(execFileSync('pdfinfo', [join(ordner, pdf)]).toString())[1]);

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher, Ereignis rein, Ergebnis und API-Aufrufe raus. */
function lauf({ pdf, werte = {}, einstellungen = {}, dokumente = 1, mime = 'application/pdf' }) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '', protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 256, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const post = { id: 'post-1', typId: 'typ-post', werte: { stand: 'Neu', richtung: 'Eingehend', kanal: 'Scan', betreff: 'Sammelscan', ...werte } };
  const api = (q) => {
    aufrufe.push(q);
    const { methode, pfad, body } = q;
    let m;
    if (methode === 'GET' && pfad === '/mappen/post-1') return json(200, { mappe: post, dokumente: Array.from({ length: dokumente }, (_, i) => ({ id: i ? `dok-${i + 1}` : 'dok-1' })) });
    if (methode === 'GET' && pfad === '/typen') return json(200, [{ id: 'typ-rechnung', system: null }, { id: 'typ-post', system: 'post' }]);
    if (methode === 'GET' && pfad === '/dokumente/dok-1/seiten') return json(200, { id: 'dok-1', anzahl: seitenzahl(pdf) });
    if (methode === 'GET' && (m = /^\/dokumente\/dok-1\/seiten\/(\d+)\/scan\?dpi=(\d+)$/.exec(pfad))) {
      if (Number(m[1]) > seitenzahl(pdf)) return json(404, { fehler: 'keine Seite' });
      antwort = new Uint8Array(seite(pdf, Number(m[1]), Number(m[2])));
      return 200;
    }
    if (methode === 'POST' && pfad === '/dokumente/dok-1/seiten') {
      const n = (body.teile?.length ?? 0) + 1;
      return json(201, { dokumente: Array.from({ length: n }, (_, i) => ({ id: `neu-${i + 1}` })), posten: Array.from({ length: n }, (_, i) => ({ id: `post-neu-${i + 1}` })) });
    }
    if (methode === 'PUT' && (m = /^\/dokumente\/([\w-]+)\/archivnummer$/.exec(pfad))) return json(200, { id: m[1], archivnummer: body.archivnummer });
    return json(404, { fehler: `unbekannt: ${methode} ${pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(text(p, l))),
    api_binaer: () => 400, netz: () => -1, datei: () => -1,
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    speicher_lesen: () => -1, speicher_schreiben: () => 0,
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: (s, p, l) => { protokoll.push(`${s} ${text(p, l)}`); return 0; },
  };
  const dv = () => new DataView(memory.buffer);
  const wasi = {
    fd_write: (fd, iov, n, aus) => { let s = 0; for (let i = 0; i < n; i++) { const p = dv().getUint32(iov + 8 * i, true), l = dv().getUint32(iov + 8 * i + 4, true); protokoll.push(`stdout ${text(p, l)}`); s += l; } dv().setUint32(aus, s, true); return 0; },
    random_get: (p, l) => { u8().fill(4, p, p + l); return 0; },
    clock_time_get: (_id, _p, aus) => { dv().setBigUint64(aus, BigInt(Date.now()) * 1000000n, true); return 0; },
    environ_sizes_get: (a, b) => { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; },
    environ_get: () => 0, args_sizes_get: (a, b) => { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; }, args_get: () => 0,
    proc_exit: (c) => { throw new Error(`proc_exit ${c}`); },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) {
    if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = wasi[i.name] ?? (() => 52 /* ENOSYS */);
  }
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const ereignis = new TextEncoder().encode(JSON.stringify({
    art: 'dokument.hochgeladen', id: 'e-1', versuch: 1, erstellt: new Date().toISOString(),
    daten: { dokument: 'dok-1', mappe: 'post-1', name: pdf, mime, groesse: 1, volltextGeplant: true },
    paket: { id: 'trennblatt', version: '1.0.0' },
    einstellungen: { barcode: 'DMS-TRENNEN', behalten: false, rueckseite: true, kanaele: [], archivnummer: true, dpi: 300, max_seiten: 60, ...einstellungen },
  }));
  const p = inst.exports.dms_puffer(ereignis.length);
  u8().set(ereignis, p);
  const t0 = Date.now();
  const code = inst.exports.dms_ereignis(p, ereignis.length);
  return { code, ergebnis, protokoll, aufrufe, ms: Date.now() - t0 };
}

let fehler = 0;
function pruefe(name, r, erwartet) {
  const teilen = r.aufrufe.find((a) => a.methode === 'POST');
  const asn = r.aufrufe.filter((a) => a.methode === 'PUT').map((a) => `${a.pfad.split('/')[2]}=${a.body.archivnummer}`);
  const ist = {
    code: r.code,
    seiten: teilen ? teilen.body.seiten.map((s) => s.nr) : null,
    teile: teilen ? teilen.body.teile : null,
    asn,
  };
  const ok = JSON.stringify(ist) === JSON.stringify({ code: 0, seiten: null, teile: null, asn: [], ...erwartet });
  if (!ok) { fehler++; console.log(`✗ ${name}: ${JSON.stringify(ist)} – erwartet ${JSON.stringify(erwartet)}\n  ${r.ergebnis}\n  ${r.protokoll.join('\n  ')}`); }
  else console.log(`✓ ${name}: ${r.ergebnis} (${r.ms} ms)`);
}

try {
  pruefe('Sammelscan: 3 Briefe, 2 Trennblätter', lauf({ pdf: 'sammelscan.pdf' }), { seiten: [1, 3, 5], teile: [1, 2], asn: ['neu-2=A-000123'] });
  pruefe('Gescannt, beidseitig, schief, mit Staub', lauf({ pdf: 'sammelscan-gescannt.pdf' }), { seiten: [1, 4, 7, 8], teile: [1, 2], asn: ['neu-2=A-000123'] });
  pruefe('Gescannt mit 150 dpi (ohne Archivnummer)', lauf({ pdf: 'sammelscan-gescannt.pdf', einstellungen: { dpi: 150, archivnummer: false } }), { seiten: [1, 4, 7, 8], teile: [1, 2] });
  pruefe('Trennblatt behalten', lauf({ pdf: 'sammelscan.pdf', einstellungen: { behalten: true } }), { seiten: [1, 2, 3, 4, 5], teile: [1, 3], asn: ['neu-2=A-000123'] });
  pruefe('Leere Rückseite behalten', lauf({ pdf: 'sammelscan-gescannt.pdf', einstellungen: { rueckseite: false, archivnummer: false } }), { seiten: [1, 3, 4, 6, 7, 8], teile: [1, 3] });
  pruefe('Ohne Trennblatt: nur Archivnummer', lauf({ pdf: 'ohne-trennblatt.pdf' }), { asn: ['dok-1=A-000123'] });
  pruefe('Anderer Barcode-Inhalt', lauf({ pdf: 'sammelscan.pdf', einstellungen: { barcode: 'ANDERS', archivnummer: false } }), {});
  pruefe('Kanal nicht gewählt', lauf({ pdf: 'sammelscan.pdf', einstellungen: { kanaele: ['Eingangsordner', 'E-Mail-Postfach'] } }), {});
  pruefe('Kanal Eingangsordner gewählt', lauf({ pdf: 'sammelscan.pdf', werte: { kanal: 'Ordner' }, einstellungen: { kanaele: ['Eingangsordner'] } }), { seiten: [1, 3, 5], teile: [1, 2], asn: ['neu-2=A-000123'] });
  pruefe('Post nicht mehr neu', lauf({ pdf: 'sammelscan.pdf', werte: { stand: 'Erledigt' } }), {});
  pruefe('Post mit zwei Dokumenten', lauf({ pdf: 'sammelscan.pdf', dokumente: 2 }), {});
  pruefe('Zu viele Seiten', lauf({ pdf: 'sammelscan.pdf', einstellungen: { max_seiten: 4 } }), {});
  pruefe('Kein PDF', lauf({ pdf: 'sammelscan.pdf', mime: 'image/jpeg' }), {});
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
if (fehler) { console.log(`${fehler} Fehler`); process.exit(1); }
console.log('Alles gut.');
