// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung des DMS: Importe dms.* und WASI,
// Ereignis „Dokument hochgeladen“, die Datei über GET /dokumente/{id}/inhalt, der Volltext über
// PUT /dokumente/{id}/volltext. Die Fälle (was im Text stehen muss und was nicht) schreibt tests/beispiele.py.
//
//   node tests/modul_test.mjs <ordner mit den Testdateien aus tests/beispiele.py>
//   node tests/modul_test.mjs <ordner> --messen     # Zeit, Speicher und Textlänge je Datei im Ordner
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const ordner = process.argv[2];
if (!ordner) { console.error('Aufruf: node tests/modul_test.mjs <ordner>'); process.exit(2); }
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher (höchstens 256 MB), Ereignis rein, Ergebnis und API-Aufrufe raus. */
function lauf({ datei, name = datei, mime = '', inhalt = 200, volltext = 200, art = 'dokument.hochgeladen', groesse = 1 }) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '', text = null;
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 32, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const lies = (p, l) => new TextDecoder('utf-8', { fatal: true }).decode(u8().slice(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const api = (q) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    if (q.methode === 'GET' && q.pfad === '/dokumente/dok-1/inhalt') {
      if (inhalt !== 200) return json(inhalt, { fehler: 'gibt es nicht' });
      antwort = new Uint8Array(readFileSync(join(ordner, datei)));
      return 200;
    }
    if (q.methode === 'PUT' && q.pfad === '/dokumente/dok-1/volltext') {
      if (volltext !== 200) return json(volltext, { fehler: 'Störung' });
      if (typeof q.body?.text !== 'string' || Object.keys(q.body).length !== 1) return json(422, { fehler: 'text fehlt' });
      text = q.body.text;
      return json(200, { id: 'dok-1' });
    }
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(lies(p, l))),
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    ergebnis: (p, l) => { ergebnis = lies(p, l); return 0; },
    log: (s, p, l) => { protokoll.push(`${s} ${lies(p, l)}`); return 0; },
  };
  const dv = () => new DataView(memory.buffer);
  const wasi = {
    fd_write: (fd, iov, n, aus) => { let s = 0; for (let i = 0; i < n; i++) { const p = dv().getUint32(iov + 8 * i, true), l = dv().getUint32(iov + 8 * i + 4, true); protokoll.push(`stdout ${lies(p, l)}`); s += l; } dv().setUint32(aus, s, true); return 0; },
    clock_time_get: (_id, _p, aus) => { dv().setBigUint64(aus, BigInt(Date.now()) * 1000000n, true); return 0; },
    environ_sizes_get: (a, b) => { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; },
    environ_get: () => 0,
    proc_exit: (c) => { throw new Error(`proc_exit ${c}`); },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) {
    if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = wasi[i.name] ?? (() => 52 /* ENOSYS */);
    if (i.module === 'dms' && !dms[i.name]) throw new Error(`Import dms.${i.name} fehlt in der Nachbildung`);
  }
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const ereignis = new TextEncoder().encode(JSON.stringify({
    art, id: 'e-1', versuch: 1, erstellt: new Date().toISOString(),
    daten: { dokument: 'dok-1', mappe: 'mappe-1', name, mime, groesse, volltextGeplant: false },
    paket: { id: 'office_email', version: '1.0.0' }, einstellungen: {},
  }));
  const p = inst.exports.dms_puffer(ereignis.length);
  u8().set(ereignis, p);
  const t0 = Date.now();
  const code = inst.exports.dms_ereignis(p, ereignis.length);
  return { code, ergebnis, protokoll, aufrufe, text, ms: Date.now() - t0, mb: memory.buffer.byteLength / 1048576 };
}

let fehler = 0;
function pruefe(name, ok, r, grund = '') {
  if (!ok) { fehler++; console.log(`✗ ${name}: ${grund} – Code ${r.code}, ${r.ergebnis}\n  ${r.aufrufe.join('\n  ')}\n  ${r.protokoll.join('\n  ')}\n--- Text ---\n${r.text ?? '(keiner)'}\n---`); }
  else console.log(`✓ ${name}: ${r.ergebnis} (${r.ms} ms, ${r.mb} MB Speicher)`);
}

if (process.argv[3] === '--messen') {
  for (const datei of readdirSync(ordner).filter((n) => n !== 'faelle.json').sort()) {
    const r = lauf({ datei });
    console.log(`${datei}: ${(readFileSync(join(ordner, datei)).length / 1048576).toFixed(2)} MB → ${r.text ? r.text.length : '–'} Zeichen in ${r.ms} ms, Speicher ${r.mb} MB – ${r.ergebnis}`);
  }
  process.exit(0);
}

const faelle = JSON.parse(readFileSync(join(ordner, 'faelle.json'), 'utf8'));
for (const [datei, mime, muss, nicht, meldung, geschrieben] of faelle) {
  const r = lauf({ datei, mime });
  const fehlt = muss.filter((m) => !r.text?.includes(m));
  const zuviel = nicht.filter((m) => r.text?.includes(m));
  const ok = r.code === 0 && r.ergebnis.includes(meldung) && (r.text !== null) === geschrieben && !fehlt.length && !zuviel.length;
  pruefe(datei, ok, r, [fehlt.length ? `fehlt: ${fehlt.join(' | ')}` : '', zuviel.length ? `steht drin: ${zuviel.join(' | ')}` : ''].join(' '));
}
let r = lauf({ datei: 'foto.docx', name: 'Scan.pdf', mime: 'application/pdf' });
pruefe('PDF (liest das DMS): keine Anfrage', r.code === 0 && r.aufrufe.length === 0, r);
r = lauf({ datei: 'brief.docx', mime: 'application/octet-stream' });
pruefe('Dateityp unbekannt, Endung .docx: wird gelesen', r.code === 0 && r.text?.includes('Sehr geehrte'), r);
r = lauf({ datei: 'brief.docx', groesse: 60 * 1024 * 1024 });
pruefe('Größer als 50 MB: nicht geholt', r.code === 0 && r.aufrufe.length === 0 && r.ergebnis.includes('50 MB'), r);
r = lauf({ datei: 'brief.docx', inhalt: 404 });
pruefe('Dokument weg: Code 0', r.code === 0 && r.text === null && r.ergebnis.includes('gibt es nicht mehr'), r);
r = lauf({ datei: 'brief.docx', inhalt: 500 });
pruefe('Datei nicht lesbar (500): Fehlercode, Wiederholung', r.code !== 0, r);
r = lauf({ datei: 'brief.docx', volltext: 403 });
pruefe('Keine Rechte (403): Code 0, Meldung', r.code === 0 && r.ergebnis.includes('nicht angenommen'), r);
r = lauf({ datei: 'brief.docx', volltext: 503 });
pruefe('DMS gestört (503): Fehlercode, Wiederholung', r.code !== 0, r);
r = lauf({ datei: 'brief.docx', art: 'paket.einstellungen_geaendert' });
pruefe('Anderes Ereignis: nichts zu tun', r.code === 0 && r.aufrufe.length === 0, r);

process.exit(fehler ? 1 : 0);
