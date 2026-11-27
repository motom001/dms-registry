// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung von Ablago und dem KBA: Importe dms.* und
// WASI, die beiden Mappenaktionen (dms_aktion mit dms:mappenaktion), Captcha, Abruf, Fehlerfälle. Alle Daten erfunden.
//
//   node tests/modul_test.mjs
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const hier = dirname(fileURLToPath(import.meta.url));
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const salt = 'abcdef0123456789abcdef01?expires=1700000000&';
const altcha = { algorithm: 'SHA-256', challenge: createHash('sha256').update(salt + '777').digest('hex'), maxnumber: 100000, salt, signature: 'sig' };
const dub = readFileSync(join(hier, 'dub_antwort.json'), 'utf8');
const ivi1 = readFileSync(join(hier, 'ivi1.xml'), 'utf8');

/** Eine Aktion wie im Paket-Läufer; kba(url, body) liefert [status, text]. */
function aktion(e, kba) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '';
  const memory = new WebAssembly.Memory({ initial: 32, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const dms = {
    netz: (pq, lq, pb, lb) => {
      const q = JSON.parse(text(pq, lq)), body = lb ? text(pb, lb) : '';
      aufrufe.push({ ...q, body });
      const [s, t] = kba(q.url, body);
      antwort = new TextEncoder().encode(t);
      return s;
    },
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    log: () => 0,
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = () => 52;
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const ein = new TextEncoder().encode(JSON.stringify({ aktion: 'dms:mappenaktion', ...e }));
  const p = inst.exports.dms_puffer(ein.length);
  u8().set(ein, p);
  const code = inst.exports.dms_aktion(p, ein.length);
  return { code, aufrufe, ergebnis: ergebnis ? JSON.parse(ergebnis) : null };
}
const kbaOk = (url, body) => {
  if (url.endsWith('/altcha')) return [200, JSON.stringify(altcha)];
  if (url.endsWith('/dubAnfrage')) {
    const b = JSON.parse(body);
    const c = JSON.parse(Buffer.from(b.captcha, 'base64').toString());
    assert.equal(c.number, 777);
    assert.equal(c.signature, 'sig');
    return b.dubsuchid === 'ABCD12EFG3H4' ? [200, dub] : [404, '{"code":"NICHT_GEFUNDEN"}'];
  }
  if (url.endsWith('/vin/data')) {
    const b = JSON.parse(body).publicAccessAbfrageArbeitsdaten;
    assert.equal(JSON.parse(Buffer.from(b.altchaPayload, 'base64').toString()).number, 777);
    return b.vin === 'WMEZZZ00000000001' ? [200, JSON.stringify({ vin: b.vin, ivi1xDataEntries: [ivi1], ivi2xDataEntries: [] })] : [404, '{}'];
  }
  return [404, '{}'];
};

let n = 0;
const ok = (was) => { n++; console.log('ok  ', was); };

// DUB, Schritt 1: Dialog mit den Angaben aus dem QR-Link, noch kein Netz.
let r = aktion({ mappenaktion: 'dub_abrufen', schritt: 1, mappe: { werte: { digitaler_bericht: 'https://www.kba-online.de/dub/#/zugriffsdaten/ABCD12EFG3H4/X000000000001/9999' } } }, kbaOk);
assert.equal(r.aufrufe.length, 0);
assert.deepEqual(r.ergebnis.dialog.felder.slice(1).map((f) => f.standard), ['ABCD12EFG3H4', 'X000000000001', '9999']);
ok('DUB: Dialog zeigt die Angaben, fragt das KBA noch nicht');

// DUB, Schritt 2: Captcha, Abruf, nur leere Felder.
r = aktion({ mappenaktion: 'dub_abrufen', schritt: 2, antworten: { suchid: 'abcd12efg3h4', bericht: 'X000000000001', kennnummer: '9999' }, mappe: { werte: { kilometerstand: 80000 } } }, kbaOk);
assert.deepEqual(r.aufrufe.map((a) => a.methode + ' ' + a.url.replace(/^.*\/api/, '')), ['GET /altcha', 'POST /dubAnfrage']);
assert.equal(r.ergebnis.ergebnis.felder.naechste_hu, '2028-11-01');
assert.equal(r.ergebnis.ergebnis.felder.kilometerstand, undefined);
assert.match(r.ergebnis.ergebnis.meldung, /Kilometerstand: laut KBA 81234, eingetragen 80000/);
ok('DUB: Abruf füllt leere Felder, Abweichung in der Meldung');

r = aktion({ mappenaktion: 'dub_abrufen', schritt: 2, antworten: { suchid: 'ZZZZ12EFG3H4', bericht: 'X1', kennnummer: '9999' }, mappe: { werte: {} } }, kbaOk);
assert.match(r.ergebnis.ergebnis.meldung, /keinen Bericht gefunden/);
assert.equal(r.ergebnis.ergebnis.felder, undefined);
ok('DUB: unbekannter Bericht → Meldung, nichts geändert');

r = aktion({ mappenaktion: 'dub_abrufen', schritt: 2, antworten: { suchid: 'KURZ', bericht: 'X1', kennnummer: '9999' }, mappe: { werte: {} } }, kbaOk);
assert.equal(r.aufrufe.length, 0);
ok('DUB: ungültige Such-ID → kein Netz');

r = aktion({ mappenaktion: 'dub_abrufen', schritt: 2, antworten: { suchid: 'ABCD12EFG3H4', bericht: 'X1', kennnummer: '9999' }, mappe: { werte: {} } }, () => [-2, 'nicht freigegeben']);
assert.match(r.ergebnis.ergebnis.meldung, /nicht freigegeben/);
ok('DUB: Netz nicht freigegeben → verständliche Meldung');

// CoC: Schritt 1 nennt die FIN, Schritt 2 holt und bildet ab.
r = aktion({ mappenaktion: 'coc_abrufen', schritt: 1, mappe: { werte: { fin: 'WMEZZZ00000000001' } } }, kbaOk);
assert.equal(r.aufrufe.length, 0);
assert.match(r.ergebnis.dialog.felder[0].text, /WMEZZZ00000000001/);
ok('CoC: Dialog nennt die FIN, fragt das KBA noch nicht');

r = aktion({ mappenaktion: 'coc_abrufen', schritt: 2, mappe: { werte: { fin: 'WMEZZZ00000000001', hubraum: 1802 } } }, kbaOk);
assert.equal(r.ergebnis.ergebnis.felder.hsn, '0005');
assert.equal(r.ergebnis.ergebnis.felder.typgenehmigung, 'e1*168/2013*00001*01');
assert.equal(r.ergebnis.ergebnis.felder.hubraum, undefined);
assert.match(r.ergebnis.ergebnis.meldung, /Version 1\.8\.2/);
ok('CoC: Abruf füllt technische Daten, gleicher Hubraum bleibt');

r = aktion({ mappenaktion: 'coc_abrufen', schritt: 2, mappe: { werte: { fin: 'WVWZZZ00000000009' } } }, kbaOk);
assert.match(r.ergebnis.ergebnis.meldung, /keinen elektronischen CoC/);
ok('CoC: keine Daten → Hinweis auf ältere Fahrzeuge');

r = aktion({ mappenaktion: 'coc_abrufen', schritt: 1, mappe: { werte: { fin: 'ZU-KURZ' } } }, kbaOk);
assert.match(r.ergebnis.ergebnis.meldung, /keine vollständige Fahrzeug-Identnummer/);
ok('CoC: ohne vollständige FIN kein Dialog');

console.log(`alle ${n} Prüfungen bestanden`);
