// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung des DMS: Importe dms.* und WASI,
// Ereignis „Datei umwandeln“, die Originaldatei über GET /dokumente/{id}/inhalt, die Fassung über
// PUT /dokumente/{id}/fassung. Legt jede Fassung als <name>.fassung in den Ordner (Vergleich: beispiele.py).
//
//   node tests/modul_test.mjs <ordner mit den Testbildern aus tests/beispiele.py>
//   node tests/modul_test.mjs <ordner> --messen     # nur Zeit, Speicher und Größe je Datei im Ordner
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const ordner = process.argv[2];
if (!ordner) { console.error('Aufruf: node tests/modul_test.mjs <ordner>'); process.exit(2); }
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const SHA = 'a'.repeat(64);

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher (höchstens 256 MB), Ereignis rein, Ergebnis und API-Aufrufe raus. */
function lauf({ datei, mime = 'image/tiff', inhalt = 200, fassung = 200, einstellungen = {}, art = 'datei.umwandeln' }) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '', gesetzt = null;
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 32, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const api = (q, body) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    if (q.methode === 'GET' && q.pfad === '/dokumente/dok-1/inhalt') {
      if (inhalt !== 200) return json(inhalt, { fehler: 'gibt es nicht' });
      antwort = new Uint8Array(readFileSync(join(ordner, datei)));
      return 200;
    }
    if (q.methode === 'PUT' && q.pfad === `/dokumente/dok-1/fassung?sha256=${SHA}`) {
      if (fassung !== 200) return json(fassung, { fehler: fassung === 409 ? 'Das Dokument hat inzwischen eine neue Version.' : 'Störung' });
      gesetzt = Buffer.from(body);
      return json(200, { dokument: 'dok-1', fassung: { groesse: body.length } });
    }
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(text(p, l))),
    api_binaer: (p, l, bp, bl) => api(JSON.parse(text(p, l)), u8().slice(bp, bp + bl)),
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
  const ereignis = new TextEncoder().encode(JSON.stringify({
    art, id: 'e-1', versuch: 1, erstellt: new Date().toISOString(),
    daten: { dokument: 'dok-1', mappe: 'mappe-1', name: datei, mime, groesse: 1, sha256: SHA },
    paket: { id: 'bildformate', version: '1.0.0' }, einstellungen: { max_seiten: 200, ...einstellungen },
  }));
  const p = inst.exports.dms_puffer(ereignis.length);
  u8().set(ereignis, p);
  const t0 = Date.now();
  const code = inst.exports.dms_ereignis(p, ereignis.length);
  return { code, ergebnis, protokoll, aufrufe, gesetzt, ms: Date.now() - t0, mb: memory.buffer.byteLength / 1048576 };
}

let fehler = 0;
const kopf = (b, k) => b && b.subarray(0, k.length).toString('latin1') === k;
function pruefe(name, ok, r) {
  if (!ok) { fehler++; console.log(`✗ ${name}: Code ${r.code}, ${r.ergebnis}\n  ${r.aufrufe.join('\n  ')}\n  ${r.protokoll.join('\n  ')}`); }
  else console.log(`✓ ${name}: ${r.ergebnis} (${r.ms} ms, ${r.mb} MB Speicher)`);
}

if (process.argv[3] === '--messen') {
  for (const datei of readdirSync(ordner).filter((n) => !n.endsWith('.fassung')).sort()) {
    const r = lauf({ datei });
    console.log(`${datei}: ${(readFileSync(join(ordner, datei)).length / 1048576).toFixed(2)} MB → ${r.gesetzt ? (r.gesetzt.length / 1048576).toFixed(2) : '–'} MB in ${r.ms} ms, Speicher ${r.mb} MB – ${r.ergebnis}`);
  }
  process.exit(0);
}

for (const [datei, art] of [['scan-g4.tif', '%PDF-'], ['farbe-lzw.tif', '%PDF-'], ['farbe-jpeg.tif', '%PDF-'], ['grau-ohne-dpi.tif', '%PDF-'], ['grau-cm.tif', '%PDF-'],
  ['foto.webp', '\xff\xd8\xff'], ['durchsichtig.webp', '\xff\xd8\xff'], ['animiert.gif', '\x89PNG'], ['grafik.bmp', '\x89PNG'], ['grau.bmp', '\x89PNG']]) {
  const r = lauf({ datei });
  pruefe(`${datei} → ${art === '%PDF-' ? 'PDF' : art === '\x89PNG' ? 'PNG' : 'JPEG'}`, r.code === 0 && kopf(r.gesetzt, art), r);
  if (r.gesetzt) writeFileSync(join(ordner, `${datei}.fassung`), r.gesetzt);
}
let r = lauf({ datei: 'scan-g4.tif' });
pruefe('Zwei Seiten im Ergebnis', r.ergebnis.includes('2 Seiten → PDF'), r);
r = lauf({ datei: 'scan-g4.tif', einstellungen: { max_seiten: 1 } });
pruefe('Höchstens 1 Seite', r.code === 0 && r.ergebnis.includes('nur die ersten 1 von 2'), r);
r = lauf({ datei: 'kaputt.tif' });
pruefe('Kaputtes TIFF: Code 0, Meldung, keine Fassung', r.code === 0 && r.gesetzt === null && r.ergebnis.startsWith('TIFF lässt sich nicht lesen'), r);
r = lauf({ datei: 'kein-tiff.tif' });
pruefe('PNG mit Endung .tif: am Inhalt erkannt, nichts umgewandelt', r.code === 0 && r.gesetzt === null && r.ergebnis.startsWith('Kein TIFF'), r);
r = lauf({ datei: 'foto.webp', inhalt: 404 });
pruefe('Dokument weg: Code 0', r.code === 0 && r.gesetzt === null && r.ergebnis.includes('gibt es nicht mehr'), r);
r = lauf({ datei: 'foto.webp', inhalt: 500 });
pruefe('Datei nicht lesbar (500): Fehlercode, Wiederholung', r.code !== 0, r);
r = lauf({ datei: 'foto.webp', fassung: 409 });
pruefe('Neue Version (409): Code 0, nichts zu wiederholen', r.code === 0 && r.ergebnis.includes('neue Version'), r);
r = lauf({ datei: 'foto.webp', fassung: 503 });
pruefe('DMS gestört (503): Fehlercode, Wiederholung', r.code !== 0, r);
r = lauf({ datei: 'foto.webp', art: 'paket.einstellungen_geaendert' });
pruefe('Anderes Ereignis: nichts zu tun', r.code === 0 && r.aufrufe.length === 0, r);

process.exit(fehler ? 1 : 0);
