// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung von Ablago: Importe dms.* und WASI,
// API-Antworten für eine Post mit einem Scan; Seitenbilder rastert pdftoppm wie Ablago (Graustufen, PGM).
//
//   node tests/modul_test.mjs <ordner mit den Scans aus tests/scans.py>
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const ordner = process.argv[2];
if (!ordner) { console.error('Aufruf: node tests/modul_test.mjs <ordner>'); process.exit(2); }
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const tmp = mkdtempSync(join(tmpdir(), 'leerseiten-'));
const bilder = new Map();
const SHA = 'a'.repeat(64);

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
function lauf({ pdf, werte = {}, einstellungen = {}, mime = 'application/pdf', system = 'post', markieren = 200, ohneEinstellung = [] }) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '';
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 256, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const post = { id: 'post-1', typId: 'typ-post', werte: { stand: 'Neu', richtung: 'Eingehend', kanal: 'Scan', betreff: 'Scan', ...werte } };
  const api = (q) => {
    aufrufe.push(q);
    const { methode, pfad } = q;
    let m;
    if (methode === 'GET' && pfad === '/mappen/post-1') return json(200, { mappe: post, dokumente: [{ id: 'dok-1', sha256: SHA, mime }] });
    if (methode === 'GET' && pfad === '/typen') return json(200, [{ id: 'typ-rechnung', system: null }, { id: 'typ-post', system }]);
    if (methode === 'GET' && pfad === '/dokumente/dok-1/seiten') return json(200, { id: 'dok-1', anzahl: seitenzahl(pdf) });
    if (methode === 'GET' && (m = /^\/dokumente\/dok-1\/seiten\/(\d+)\/scan\?dpi=(\d+)$/.exec(pfad))) {
      if (Number(m[1]) > seitenzahl(pdf)) return json(404, { fehler: 'keine Seite' });
      antwort = new Uint8Array(seite(pdf, Number(m[1]), Number(m[2])));
      return 200;
    }
    if (methode === 'PUT' && pfad === '/dokumente/dok-1/leerseiten') return json(markieren, { dokument: 'dok-1', sha256: SHA, seiten: seitenzahl(pdf), leerseiten: null, wegfallend: [] });
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
  const einst = { empfindlichkeit: 'vorsichtig', kanaele: ['Scan', 'Eingangsordner', 'Hochgeladen'], max_seiten: 100, ...einstellungen };
  for (const k of ohneEinstellung) delete einst[k];
  const ereignis = new TextEncoder().encode(JSON.stringify({
    art: 'dokument.hochgeladen', id: 'e-1', versuch: 1, erstellt: new Date().toISOString(),
    daten: { dokument: 'dok-1', mappe: 'post-1', name: pdf, mime, groesse: 1, volltextGeplant: true },
    paket: { id: 'leerseiten', version: '1.0.0' },
    einstellungen: einst,
  }));
  const p = inst.exports.dms_puffer(ereignis.length);
  u8().set(ereignis, p);
  const t0 = Date.now();
  const code = inst.exports.dms_ereignis(p, ereignis.length);
  return { code, ergebnis, protokoll, aufrufe, ms: Date.now() - t0 };
}

let fehler = 0;
/** erwartet: die markierten Seiten (null = nicht markiert) und ggf. der Text des Ergebnisses. */
function pruefe(name, r, seiten, ergebnisMuster) {
  const put = r.aufrufe.find((a) => a.methode === 'PUT');
  const ist = { code: r.code, seiten: put ? put.body.seiten : null, sha: put ? put.body.sha256 === SHA : null };
  const soll = { code: 0, seiten, sha: seiten ? true : null };
  const schreibt = r.aufrufe.filter((a) => a.methode !== 'GET' && !(a.methode === 'PUT' && a.pfad === '/dokumente/dok-1/leerseiten'));
  const ok = JSON.stringify(ist) === JSON.stringify(soll) && !schreibt.length && (!ergebnisMuster || ergebnisMuster.test(r.ergebnis));
  if (!ok) { fehler++; console.log(`✗ ${name}: ${JSON.stringify(ist)} – erwartet ${JSON.stringify(soll)}${schreibt.length ? ` – schreibt sonst: ${JSON.stringify(schreibt)}` : ''}\n  ${r.ergebnis}\n  ${r.protokoll.join('\n  ')}`); }
  else console.log(`✓ ${name}: ${r.ergebnis} (${r.ms} ms)`);
}

try {
  // Seiten von scans.pdf: 1 Brief · 2 leer · 3 Lochung + Schatten · 4 Bleistift · 5 Stempel · 6 durchscheinend · 7 Staub · 8 Brief
  pruefe('vorsichtig (Vorgabe): leer, Lochung, Staub – Bleistift, Stempel, Durchscheinendes bleiben', lauf({ pdf: 'scans.pdf' }), [2, 3, 7], /^3 von 8 Seiten leer \(2, 3, 7\)$/);
  pruefe('normal: dazu durchscheinende Schrift', lauf({ pdf: 'scans.pdf', einstellungen: { empfindlichkeit: 'normal' } }), [2, 3, 6, 7]);
  pruefe('streng: dazu die Bleistiftnotiz – der Stempel bleibt', lauf({ pdf: 'scans.pdf', einstellungen: { empfindlichkeit: 'streng' } }), [2, 3, 4, 6, 7]);
  pruefe('Unbekannte Empfindlichkeit wie vorsichtig', lauf({ pdf: 'scans.pdf', einstellungen: { empfindlichkeit: 'irgendwas' } }), [2, 3, 7]);
  pruefe('Brief ohne Leerseite: nichts markiert', lauf({ pdf: 'brief.pdf' }), null, /^keine leere Seite \(2 Seiten\)$/);
  pruefe('Ganz leer: markiert (Ablago lässt ein Dokument nie ganz weg)', lauf({ pdf: 'leer.pdf' }), [1]);
  pruefe('Bild (PNG): eine Seite, Auflösung geschätzt', lauf({ pdf: 'leer.pdf', mime: 'image/png' }), [1]);
  pruefe('Kanal Eingangsordner (Vorgabe)', lauf({ pdf: 'scans.pdf', werte: { kanal: 'Ordner' } }), [2, 3, 7]);
  pruefe('Kanal E-Mail nicht in der Vorgabe', lauf({ pdf: 'scans.pdf', werte: { kanal: 'E-Mail' } }), null, /nicht gewählt/);
  pruefe('Einstellung fehlt: Vorgabe Scan, Eingangsordner, Hochgeladen', lauf({ pdf: 'scans.pdf', werte: { kanal: 'API' }, ohneEinstellung: ['kanaele'] }), null, /nicht gewählt/);
  pruefe('Kanäle leer: alle', lauf({ pdf: 'scans.pdf', werte: { kanal: 'E-Mail' }, einstellungen: { kanaele: [] } }), [2, 3, 7]);
  pruefe('Post nicht mehr neu', lauf({ pdf: 'scans.pdf', werte: { stand: 'Zugeordnet' } }), null, /nicht mehr neu/);
  pruefe('Ausgehende Post', lauf({ pdf: 'scans.pdf', werte: { richtung: 'Ausgehend' } }), null, /ausgehend/);
  pruefe('Keine Post', lauf({ pdf: 'scans.pdf', system: null }), null, /keine Post/);
  pruefe('Kein PDF und kein Bild', lauf({ pdf: 'scans.pdf', mime: 'application/vnd.ms-excel' }), null, /kein PDF/);
  pruefe('Zu viele Seiten', lauf({ pdf: 'scans.pdf', einstellungen: { max_seiten: 4 } }), null, /mehr als eingestellt/);
  pruefe('Datei inzwischen geändert (409): nichts weiter', lauf({ pdf: 'scans.pdf', markieren: 409 }), [2, 3, 7], /geändert/);
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
if (fehler) { console.log(`${fehler} Fehler`); process.exit(1); }
console.log('Alles gut.');
