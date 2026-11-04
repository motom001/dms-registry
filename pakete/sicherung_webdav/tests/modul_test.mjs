// Test des gebauten Moduls (code/modul.wasm) mit einer Nachbildung des DMS (Importe dms.*, WASI, die Schnittstellen
// /sicherungen/…) und eines WebDAV-Servers im Speicher (Nextcloud mit Chunking v2, allgemeines WebDAV mit
// Content-Range, Dateiablage). Jeder Aufruf mit frischem Speicher – wie im Paket-Läufer. Die Fortsetzungen
// ({"weiter": …}) ruft die Nachbildung wie der Läufer gleich wieder auf; bei einem Fehler setzt die Wiederholung am
// zuletzt gespeicherten Stand an.
//
//   node tests/modul_test.mjs
import assert from 'node:assert/strict';
import { createHash, randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const enc = new TextEncoder(), dec = new TextDecoder();
const MB = 1024 * 1024;
const BASIS = 'https://cloud.example.org';

/* ---------- WebDAV-Server im Speicher ---------- */

class Webdav {
  constructor({ benutzer = 'lena', passwort = 'geheim', teile = true, range = true, ablage = null } = {}) {
    this.dateien = new Map(); this.ordner = new Set(['/', '/remote.php/dav/files/lena', '/remote.php/dav/uploads/lena', '/dav']);
    this.anmeldung = `Basic ${Buffer.from(`${benutzer}:${passwort}`).toString('base64')}`;
    this.ablage = ablage ? `Basic ${Buffer.from(`${ablage}:`).toString('base64')}` : null;
    this.teile = teile; this.range = range; this.anfragen = []; this.stoerung = null; this.verfaelschen = null;
  }
  eltern(p) { return p.slice(0, p.lastIndexOf('/')) || '/'; }
  antworte(q, body) {
    const u = new URL(q.url);
    const p = decodeURIComponent(u.pathname);
    const k = Object.fromEntries(Object.entries(q.kopf ?? {}).map(([a, b]) => [a.toLowerCase(), b]));
    const m = q.methode;
    this.anfragen.push(`${m} ${p}`);
    if (this.stoerung) { const s = this.stoerung(m, p, k); if (s) return s; }
    if (p.startsWith('/s/')) return { status: 200, text: '<html>Freigabe</html>' };
    const ablage = p.startsWith('/public.php/webdav');
    if (ablage ? k.authorization !== this.ablage : k.authorization !== this.anmeldung) return { status: 401, text: 'Unauthorized' };
    if (ablage && m !== 'PUT') return { status: 403, text: 'Nur Hochladen' };
    if (m === 'PROPFIND') {
      if (this.ordner.has(p)) {
        if (k.depth !== '1') return { status: 207, text: '<d:multistatus xmlns:d="DAV:"><d:response><d:href>' + p + '/</d:href></d:response></d:multistatus>' };
        const kinder = [...this.dateien.keys()].filter((x) => this.eltern(x) === p);
        return { status: 207, text: `<d:multistatus xmlns:d="DAV:">${kinder.map((x) => `<d:response><d:href>${encodeURI(x)}</d:href><d:propstat><d:prop><d:getcontentlength>${this.dateien.get(x).length}</d:getcontentlength></d:prop></d:propstat></d:response>`).join('')}</d:multistatus>` };
      }
      const d = this.dateien.get(p);
      return d ? { status: 207, text: `<d:multistatus xmlns:d="DAV:"><d:response><d:href>${p}</d:href><d:propstat><d:prop><d:getcontentlength>${d.length}</d:getcontentlength></d:prop></d:propstat></d:response></d:multistatus>` } : { status: 404, text: '' };
    }
    if (m === 'MKCOL') {
      if (this.ordner.has(p)) return { status: 405, text: '' };
      if (!this.ordner.has(this.eltern(p))) return { status: 409, text: '' };
      this.ordner.add(p); return { status: 201, text: '' };
    }
    if (m === 'PUT') {
      const ziel = ablage ? `/ablage${p.slice('/public.php/webdav'.length)}` : p;
      if (!ablage && !this.ordner.has(this.eltern(p))) return { status: 409, text: '' };
      const neu = Buffer.from(body ?? []);
      if (k['content-range']) {
        if (!this.teile) return { status: 501, text: 'Not Implemented' };
        const [, a, , gesamt] = /bytes (\d+)-(\d+)\/(\d+)/.exec(k['content-range']).map(Number);
        const alt = this.dateien.get(ziel) ?? Buffer.alloc(0);
        const x = Buffer.alloc(Math.max(alt.length, a + neu.length)); alt.copy(x); neu.copy(x, a);
        assert.ok(a + neu.length <= gesamt);
        this.dateien.set(ziel, x);
      } else this.dateien.set(ziel, neu);
      return { status: 201, text: '' };
    }
    if (m === 'MOVE') {
      const ziel = decodeURIComponent(new URL(k.destination).pathname);
      if (p.endsWith('/.file')) {
        const ordner = p.slice(0, -'/.file'.length);
        const teile = [...this.dateien.keys()].filter((x) => this.eltern(x) === ordner).sort();
        if (!teile.length) return { status: 404, text: '' };
        const alles = Buffer.concat(teile.map((x) => this.dateien.get(x)));
        if (Number(k['oc-total-length']) !== alles.length) return { status: 400, text: 'Länge' };
        for (const x of teile) this.dateien.delete(x);
        this.ordner.delete(ordner);
        this.dateien.set(ziel, alles);
        return { status: 201, text: '' };
      }
      const d = this.dateien.get(p);
      if (!d) return { status: 404, text: '' };
      this.dateien.delete(p); this.dateien.set(ziel, d);
      return { status: 201, text: '' };
    }
    if (m === 'GET') {
      let d = this.dateien.get(p);
      if (!d) return { status: 404, text: '' };
      if (this.verfaelschen) { d = Buffer.from(d); this.verfaelschen(d); }
      const r = /bytes=(\d+)-(\d+)/.exec(k.range ?? '');
      if (!r || !this.range) return d.length > 10 * MB ? { status: -3, text: 'Antwort zu groß.' } : { status: 200, bytes: d };
      return { status: 206, bytes: d.subarray(Number(r[1]), Number(r[2]) + 1) };
    }
    if (m === 'DELETE') {
      if (this.ordner.has(p)) { for (const x of [...this.dateien.keys()]) if (x.startsWith(`${p}/`)) this.dateien.delete(x); this.ordner.delete(p); return { status: 204, text: '' }; }
      return this.dateien.delete(p) ? { status: 204, text: '' } : { status: 404, text: '' };
    }
    return { status: 405, text: '' };
  }
}

/* ---------- DMS-Nachbildung ---------- */

function sicherung(groesse, name = '2026-11-02_0300-automatisch') {
  const daten = randomBytes(groesse);
  const sha256 = createHash('sha256').update(daten).digest('hex');
  const meta = { format: 1, schlank: true, datei: `${name}.dms-sicherung`, groesse, sha256, beginn: '2026-11-02T02:00:00.000Z', verschluesselung: { verfahren: 'AES-256-GCM', fingerabdruck: 'ab12cd34' } };
  return { name, daten, meta, ereignis: { name, ...meta } };
}

/** Ein Aufruf wie im Paket-Läufer. erlaubt: bestätigte Adresse; schrittMs: so viel „vergeht“ je Netzanfrage. */
function aufruf(eingabe, { server, s, speicher, meldungen, erlaubt = BASIS, schrittMs = 0, art = 'ereignis' }) {
  let antwort = new Uint8Array(0), ergebnis = '', spaeter = 0;
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 2, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => dec.decode(u8().subarray(p, p + l));
  const merke = (b) => { antwort = typeof b === 'string' ? enc.encode(b) : new Uint8Array(b); };
  const dms = {
    api: (p, l) => {
      const q = JSON.parse(text(p, l));
      const u = new URL(`http://dms${q.pfad}`);
      if (q.methode === 'GET' && u.pathname === `/sicherungen/${s.name}/datei`) {
        const ab = Number(u.searchParams.get('versatz')), n = Number(u.searchParams.get('laenge'));
        assert.ok(n <= 8 * MB, 'höchstens 8 MB je Stück');
        merke(s.daten.subarray(ab, ab + n)); return 200;
      }
      if (q.methode === 'GET' && u.pathname === `/sicherungen/${s.name}`) { merke(JSON.stringify({ name: s.name, ...s.meta })); return 200; }
      // Seit 1.1.0 (DMS #636) schreibt das Paket nichts: kein PUT mehr, der Schlüssel darf nur lesen.
      if (q.methode !== 'GET') assert.fail(`Das Paket schreibt im DMS: ${q.methode} ${q.pfad}`);
      merke('Nicht gemeldet'); return 403;
    },
    netz: (p, l, bp, bl) => {
      const q = JSON.parse(text(p, l));
      spaeter += schrittMs;
      if (!q.url.startsWith(erlaubt)) { merke('Netz gesperrt'); return -2; }
      const r = server.antworte(q, bl > 0 ? u8().slice(bp, bp + bl) : null);
      merke(r.bytes ?? r.text ?? ''); return r.status;
    },
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    speicher_lesen: (p, l) => { const k = text(p, l); if (!(k in speicher)) return -1; merke(speicher[k]); return antwort.length; },
    speicher_schreiben: (p, l, vp, vl) => { speicher[text(p, l)] = text(vp, vl); return 0; },
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: (st, p, l) => { protokoll.push(`${st} ${text(p, l)}`); return 0; },
  };
  const wasi = {
    fd_write: () => 0, fd_close: () => 0, fd_seek: () => 0,
    clock_time_get: (_id, _gen, aus) => { new DataView(memory.buffer).setBigUint64(aus, BigInt(Math.round((performance.now() + spaeter) * 1e6)), true); return 0; },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = wasi[i.name] ?? (() => 52);
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const ein = enc.encode(JSON.stringify({ ...eingabe, paket: { id: 'sicherung_webdav', version: '1.0.0' } }));
  const p = inst.exports.dms_puffer(ein.length);
  u8().set(ein, p);
  const code = art === 'aktion' ? inst.exports.dms_aktion(p, ein.length) : inst.exports.dms_ereignis(p, ein.length);
  // Wie Ablago (DMS #636): Stand aus „extern“ in der Antwort; ohne ihn Rückgabewert 2 → endgültig, 1 → läuft mit Grund.
  if (art === 'ereignis') {
    let extern;
    try { extern = JSON.parse(ergebnis).extern; } catch { /* Text */ }
    if (extern) meldungen.push(extern);
    else if (code !== 0) meldungen.push({ ...(meldungen.at(-1) ?? {}), status: code === 2 ? 'fehlgeschlagen' : 'laeuft', grund: ergebnis, ...(code === 2 ? { endgueltig: true } : { endgueltig: undefined }) });
  }
  return { code, ergebnis, protokoll };
}

/** Ein Ereignis mit Fortsetzungen wie im Läufer; gibt den zuletzt gespeicherten Stand (daten) für eine Wiederholung zurück. */
function ereignis(daten, einstellungen, o) {
  let d = { ...daten }, aufrufe = 0, r;
  for (;;) {
    r = aufruf({ art: 'sicherung.fertig', id: 'e1', versuch: 1, daten: d, einstellungen }, o);
    aufrufe++;
    if (r.code !== 0) break;
    let w = null;
    try { w = JSON.parse(r.ergebnis).weiter ?? null; } catch { /* kein JSON */ }
    if (!w) break;
    d = { ...d, weiter: w, abschnitt: (d.abschnitt ?? 0) + 1 };
    assert.ok(aufrufe < 100, 'zu viele Fortsetzungen');
  }
  return { ...r, aufrufe, daten: d };
}

const nextcloud = (x = {}) => ({ art: 'Nextcloud', adresse: BASIS, benutzer: 'lena', passwort: 'geheim', ordner: 'DMS-Sicherung', teil_mb: 8, voll_mb: 2048, extern_loeschen: false, extern_behalten: 14, ...x });
const umgebung = (server, s) => ({ server, s, speicher: {}, meldungen: [] });
const letzte = (o) => o.meldungen.at(-1);
const ZIEL = '/remote.php/dav/files/lena/DMS-Sicherung';

let tests = 0;
function test(name, f) { f(); tests++; console.log(`ok ${tests} - ${name}`); }

test('Nextcloud: in Teilen hochladen (Chunking v2), über mehrere Aufrufe, vollständig geprüft, Metadaten daneben', () => {
  const server = new Webdav(); const s = sicherung(20 * MB + 12345); const o = umgebung(server, s);
  const r = ereignis(s.ereignis, nextcloud(), { ...o, schrittMs: 20000 });
  assert.equal(r.code, 0, r.ergebnis);
  assert.ok(r.aufrufe > 1, 'Fortsetzung');
  assert.ok(server.dateien.get(`${ZIEL}/${s.meta.datei}`).equals(s.daten));
  const json = JSON.parse(server.dateien.get(`${ZIEL}/${s.name}.json`).toString());
  assert.deepEqual(json, s.meta, 'schlanke Metadaten ohne name');
  assert.deepEqual(letzte(o), { status: 'geprueft', ziel: `Nextcloud ${BASIS}${ZIEL}`, pruefung: 'pruefsumme', bytes: s.daten.length, gesamt: s.daten.length });
  assert.ok(o.meldungen.some((m) => m.status === 'laeuft' && m.bytes > 0 && m.bytes < s.daten.length), 'Fortschritt');
  assert.equal(server.anfragen.filter((a) => a.startsWith('PUT /remote.php/dav/uploads/lena/dms-')).length, 3, 'drei Teile');
  assert.ok(server.anfragen.includes(`MKCOL ${ZIEL}`));
  assert.equal(o.speicher.voll_am, '2026-11-02');
  assert.ok(!JSON.stringify(o.meldungen).includes('geheim'), 'kein Passwort in den Meldungen');
  assert.ok(!server.anfragen.some((a) => a.startsWith('DELETE')), 'löscht nichts');
});

test('kleine Sicherung: ein PUT, geprüft', () => {
  const server = new Webdav(); const s = sicherung(300_000); const o = umgebung(server, s);
  const r = ereignis(s.ereignis, nextcloud(), o);
  assert.equal(r.code, 0, r.ergebnis);
  assert.equal(server.anfragen.filter((a) => a.startsWith('PUT')).length, 2, 'Datei und .json');
  assert.equal(letzte(o).status, 'geprueft');
});

test('Netz bricht beim Hochladen ab: „läuft“ mit Grund, Wiederholung macht an der gespeicherten Stelle weiter, lokale Sicherung unberührt', () => {
  const server = new Webdav(); const s = sicherung(30 * MB); const vorher = Buffer.from(s.daten); const o = umgebung(server, s);
  let puts = 0;
  server.stoerung = (m, p) => (m === 'PUT' && p.includes('/uploads/') && ++puts === 3 ? { status: -4, text: 'Netzfehler: socket hang up' } : null);
  const r = ereignis(s.ereignis, nextcloud(), { ...o, schrittMs: 30000 });
  assert.equal(r.code, 1);
  assert.match(r.ergebnis, /nicht erreichbar.*neuer Versuch folgt/);
  assert.equal(letzte(o).status, 'laeuft');
  assert.match(letzte(o).grund, /neuer Versuch folgt/);
  assert.ok(!letzte(o).endgueltig);
  const vorWiederholung = server.anfragen.length;
  const w = ereignis(r.daten, nextcloud(), { ...o, schrittMs: 30000 });
  assert.equal(w.code, 0, w.ergebnis);
  assert.ok(r.daten.weiter && r.daten.weiter.versatz > 0, 'Stand war gespeichert');
  const teileDanach = server.anfragen.slice(vorWiederholung).filter((a) => a.startsWith('PUT /remote.php/dav/uploads/')).length;
  assert.ok(teileDanach < 4, `nicht von vorn (${teileDanach} Teile)`);
  assert.ok(server.dateien.get(`${ZIEL}/${s.meta.datei}`).equals(s.daten));
  assert.ok(s.daten.equals(vorher), 'lokal unverändert');
  assert.equal(letzte(o).status, 'geprueft');
});

test('falsche Prüfsumme am Ziel: fehlgeschlagen (endgültig), beim nächsten Versuch neu hochgeladen', () => {
  const server = new Webdav(); const s = sicherung(9 * MB); const o = umgebung(server, s);
  server.verfaelschen = (d) => { d[d.length - 1] ^= 0xff; };
  const r = ereignis(s.ereignis, nextcloud(), o);
  assert.equal(r.code, 2, "endgültig");
  assert.equal(letzte(o).status, 'fehlgeschlagen');
  assert.equal(letzte(o).endgueltig, true);
  assert.match(letzte(o).grund, /Prüfsumme am Ziel weicht ab/);
  assert.equal(o.speicher[`neu:${s.name}`], '1');
  server.verfaelschen = null;
  const puts = server.anfragen.filter((a) => a.startsWith('PUT /remote.php/dav/uploads/')).length;
  const w = ereignis(r.daten, nextcloud(), o);
  assert.equal(w.code, 0, w.ergebnis);
  assert.equal(server.anfragen.filter((a) => a.startsWith('PUT /remote.php/dav/uploads/')).length, puts + 2, 'neu hochgeladen');
  assert.equal(letzte(o).status, 'geprueft');
  assert.equal(o.speicher[`neu:${s.name}`], '');
});

test('große Sicherung: Stichproben statt vollständig, solange die letzte vollständige Prüfung frisch ist; Abweichung fällt auf', () => {
  const server = new Webdav(); const s = sicherung(20 * MB); const o = umgebung(server, s);
  o.speicher.voll_am = '2026-10-20';
  const r = ereignis(s.ereignis, nextcloud({ voll_mb: 10 }), o);
  assert.equal(r.code, 0, r.ergebnis);
  assert.equal(letzte(o).pruefung, 'stichprobe');
  assert.equal(letzte(o).status, 'geprueft');
  // Älter als 30 Tage: vollständig.
  const o2 = umgebung(new Webdav(), s); o2.speicher.voll_am = '2026-09-01';
  assert.equal(ereignis(s.ereignis, nextcloud({ voll_mb: 10 }), o2).code, 0);
  assert.equal(letzte(o2).pruefung, 'pruefsumme');
  // Stichprobe am Anfang verfälscht.
  const o3 = umgebung(new Webdav(), s); o3.speicher.voll_am = '2026-10-30';
  o3.server.verfaelschen = (d) => { d[10] ^= 1; };
  assert.equal(ereignis(s.ereignis, nextcloud({ voll_mb: 10 }), o3).code, 2);
  assert.match(letzte(o3).grund, /Stichprobe am Ziel weicht ab/);
});

test('WebDAV allgemein: Teile mit Content-Range, dann MOVE; ohne Content-Range: verständlicher Fehler', () => {
  const server = new Webdav(); server.ordner.add('/dav/sicherung');
  const s = sicherung(17 * MB); const o = umgebung(server, s);
  const einst = { art: 'WebDAV allgemein', adresse: `${BASIS}/dav/sicherung`, benutzer: 'lena', passwort: 'geheim', ordner: '', teil_mb: 8, voll_mb: 2048 };
  const r = ereignis(s.ereignis, einst, o);
  assert.equal(r.code, 0, r.ergebnis);
  assert.ok(server.dateien.get(`/dav/sicherung/${s.meta.datei}`).equals(s.daten));
  assert.ok(!server.dateien.has(`/dav/sicherung/${s.meta.datei}.teil`));
  assert.equal(letzte(o).status, 'geprueft');
  const ohne = new Webdav({ teile: false }); ohne.ordner.add('/dav/sicherung');
  const o2 = umgebung(ohne, s);
  assert.equal(ereignis(s.ereignis, einst, o2).code, 2);
  assert.equal(letzte(o2).endgueltig, true);
  assert.match(letzte(o2).grund, /keine Teile an \(Content-Range/);
});

test('Server ohne Range: nur „hochgeladen, Größe bestätigt“', () => {
  const server = new Webdav({ range: false }); const s = sicherung(12 * MB); const o = umgebung(server, s);
  assert.equal(ereignis(s.ereignis, nextcloud(), o).code, 0);
  assert.deepEqual([letzte(o).status, letzte(o).pruefung], ['hochgeladen', 'groesse']);
});

test('Nextcloud-Dateiablage: ein PUT, ehrlich „hochgeladen“ ohne Prüfung; zu groß für am Stück: verständlich', () => {
  const server = new Webdav({ ablage: 'AbCdEf123' }); const s = sicherung(5 * MB); const o = umgebung(server, s);
  const einst = { art: 'Nextcloud-Dateiablage', adresse: BASIS, freigabe: `${BASIS}/s/AbCdEf123`, passwort: '', teil_mb: 8 };
  const r = ereignis(s.ereignis, einst, o);
  assert.equal(r.code, 0, r.ergebnis);
  assert.ok(server.dateien.get(`/ablage/${s.meta.datei}`).equals(s.daten));
  assert.ok(server.dateien.has(`/ablage/${s.name}.json`));
  assert.deepEqual([letzte(o).status, letzte(o).pruefung], ['hochgeladen', 'keine']);
  assert.ok(!server.anfragen.some((a) => /^(GET|PROPFIND|DELETE)/.test(a)), 'kein Lesen, kein Löschen');
  const gross = { ...s.ereignis, groesse: 200 * MB };
  const o2 = umgebung(server, { ...s, meta: { ...s.meta, groesse: 200 * MB } });
  assert.equal(ereignis(gross, einst, o2).code, 2);
  assert.match(letzte(o2).grund, /nur Dateien bis 128,0 MB am Stück/);
});

test('falsches Passwort und nicht freigegebene Adresse: endgültig, ohne Zugangsdaten im Grund', () => {
  const s = sicherung(100_000);
  const o = umgebung(new Webdav(), s);
  assert.equal(ereignis(s.ereignis, nextcloud({ passwort: 'falsch' }), o).code, 2);
  assert.equal(letzte(o).endgueltig, true);
  assert.match(letzte(o).grund, /Benutzer oder Passwort falsch/);
  assert.ok(!letzte(o).grund.includes('falsch:') && !JSON.stringify(o.meldungen).includes('Basic'));
  const o2 = umgebung(new Webdav(), s);
  assert.equal(ereignis(s.ereignis, nextcloud(), { ...o2, erlaubt: 'https://anders.example.org' }).code, 2);
  assert.match(letzte(o2).grund, /nicht freigegeben/);
  const o3 = umgebung(new Webdav(), s);
  assert.equal(ereignis(s.ereignis, nextcloud({ benutzer: '' }), o3).code, 2);
  assert.match(letzte(o3).grund, /fehlt der Benutzer/);
});

test('Aufbewahrung am Ziel: aus = nichts auflisten, nichts löschen; an = nur ältere über der Anzahl', () => {
  const vorbereitet = () => {
    const server = new Webdav(); server.ordner.add(ZIEL);
    for (const t of ['2026-10-28', '2026-10-29', '2026-10-30', '2026-11-01']) { server.dateien.set(`${ZIEL}/${t}_0300-automatisch.dms-sicherung`, Buffer.from('x')); server.dateien.set(`${ZIEL}/${t}_0300-automatisch.json`, Buffer.from('{}')); }
    return server;
  };
  const s = sicherung(50_000);
  const aus = vorbereitet(); const o = umgebung(aus, s);
  assert.equal(ereignis(s.ereignis, nextcloud(), o).code, 0);
  assert.ok(!aus.anfragen.some((a) => a.startsWith('DELETE')));
  assert.equal([...aus.dateien.keys()].filter((x) => x.endsWith('.dms-sicherung')).length, 5);
  const an = vorbereitet(); const o2 = umgebung(an, s);
  assert.equal(ereignis(s.ereignis, nextcloud({ extern_loeschen: true, extern_behalten: 2 }), o2).code, 0);
  const bleibt = [...an.dateien.keys()].filter((x) => x.endsWith('.dms-sicherung')).map((x) => x.split('/').pop()).sort();
  assert.deepEqual(bleibt, ['2026-11-01_0300-automatisch.dms-sicherung', `${s.name}.dms-sicherung`]);
  assert.ok(!an.dateien.has(`${ZIEL}/2026-10-28_0300-automatisch.json`));
});

test('Verbindung testen: mit den gespeicherten Einstellungen, verständliche Antwort', () => {
  const s = sicherung(10);
  const server = new Webdav(); server.ordner.add(ZIEL);
  const o = umgebung(server, s);
  const r = aufruf({ aktion: 'verbindung_testen', einstellungen: nextcloud() }, { ...o, art: 'aktion' });
  assert.equal(r.code, 0); assert.match(r.ergebnis, /Verbindung in Ordnung/);
  const r2 = aufruf({ aktion: 'verbindung_testen', einstellungen: nextcloud({ ordner: 'Neu' }) }, { ...o, art: 'aktion' });
  assert.equal(r2.code, 0); assert.match(r2.ergebnis, /legt ihn bei der ersten Sicherung an/);
  const r3 = aufruf({ aktion: 'verbindung_testen', einstellungen: nextcloud({ passwort: 'x' }) }, { ...o, art: 'aktion' });
  assert.equal(r3.code, 1); assert.match(r3.ergebnis, /Passwort falsch/);
  const r4 = aufruf({ aktion: 'verbindung_testen', einstellungen: { art: 'Nextcloud-Dateiablage', adresse: BASIS, freigabe: 'AbC' } }, { ...o, art: 'aktion' });
  assert.equal(r4.code, 0); assert.match(r4.ergebnis, /Dateiablage .* ist erreichbar/);
});

console.log(`1..${tests}`);
