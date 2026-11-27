// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung des DMS: Importe dms.* und WASI,
// Aktionen dms:codes (alle Codes eines Dokuments) und dms:erkennen (Visitenkarte bei „Aus Dokument ausfüllen“),
// Seitenbilder (PGM) aus den Matrizen in tests/codes/ – auf Visitenkarte oder A4-Seite gesetzt, auch gedreht,
// verkleinert und verrauscht.
//
//   node tests/modul_test.mjs
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const matrix = (name) => readFileSync(join(hier, 'codes', `${name}.txt`), 'utf8').trim().split('\n');

/**
 * Graustufenbild w×h (hell), Codes darauf: { name, x, y, modul (Pixel je Modul), winkel (Grad), hoehe (Strichcodes:
 * Höhe in Modulen), loch ([x0, y0, x1, y1] als Anteile: dieser Teil des Codes ist weiß – „kaputt“) }. Eine Matrix mit nur einer Zeile ist ein Strichcode und wird auf hoehe Zeilen gezogen.
 */
function bild(w, h, codes, rauschen = 0) {
  const px = new Uint8Array(w * h).fill(235);
  let zufall = 7;
  const z = () => { zufall = (zufall * 1103515245 + 12345) & 0x7fffffff; return zufall / 0x7fffffff; };
  for (const c of codes) {
    let m = matrix(c.name);
    if (m.length === 1) m = Array(c.hoehe ?? 60).fill(m[0]);
    const mw = m[0].length, mh = m.length, n = Math.max(mw, mh), rz = mh < mw ? 10 : 4;  // Ruhezone ringsum
    const groesse = (n + 2 * rz) * c.modul;
    const cx = c.x + groesse / 2, cy = c.y + groesse / 2, a = ((c.winkel ?? 0) * Math.PI) / 180, cos = Math.cos(a), sin = Math.sin(a);
    const r = Math.ceil(groesse * 0.75);
    for (let y = Math.max(0, Math.floor(cy - r)); y < Math.min(h, cy + r); y++) {
      for (let x = Math.max(0, Math.floor(cx - r)); x < Math.min(w, cx + r); x++) {
        const dx = x - cx, dy = y - cy;
        const u = (cos * dx + sin * dy + groesse / 2) / c.modul - rz, v = (-sin * dx + cos * dy + groesse / 2) / c.modul - rz;
        if (u < -rz || v < -rz || u >= n + rz || v >= n + rz) continue;
        const iu = Math.floor(u), iv = Math.floor(v);
        const weg = c.loch && iu >= c.loch[0] * mw && iu < c.loch[2] * mw && iv >= c.loch[1] * mh && iv < c.loch[3] * mh;
        px[y * w + x] = !weg && iu >= 0 && iv >= 0 && iu < mw && iv < mh && m[iv][iu] === '1' ? 25 : 250;
      }
    }
  }
  if (rauschen) for (let i = 0; i < px.length; i++) px[i] = Math.max(0, Math.min(255, px[i] + Math.round((z() - 0.5) * 2 * rauschen)));
  const kopf = new TextEncoder().encode(`P5\n${w} ${h}\n255\n`);
  const aus = new Uint8Array(kopf.length + px.length);
  aus.set(kopf); aus.set(px, kopf.length);
  return aus;
}

// Felder wie bei den Mappentypen Person und Organisation aus dem Paket Basis (nur was die Tests brauchen).
const feld = (title, art, typ = 'text', extra = {}) => ({ title, type: 'object', properties: { wert: typ === 'zahl' ? { type: 'number' } : { type: 'string', ...extra } }, 'x-dms-feldtyp': typ, ...(art ? { 'x-dms-erkennung': art } : {}) });
const PERSON = { type: 'object', properties: {
  vorname: feld('Vorname', 'vorname'), nachname: feld('Nachname', 'nachname'), funktion: feld('Funktion', 'funktion'),
  email: feld('E-Mail', 'email'), telefon: feld('Telefon', 'telefon'), mobil: feld('Mobil', 'mobil'), notiz: feld('Notiz', null),
} };
const ORGANISATION = { type: 'object', properties: {
  name: feld('Name', 'name'), email: feld('E-Mail', 'email'), telefon: feld('Telefon', 'telefon'), fax: feld('Fax', 'fax'),
  internet: feld('Internetseite', 'internet'), strasse: feld('Straße', 'strasse'), hausnummer: feld('Hausnummer', 'hausnummer'),
  plz: feld('PLZ', 'plz', 'zahl'), ort: feld('Ort', 'ort', 'text', { maxLength: 40 }),
} };

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher, Aktion rein, Ergebnis und API-Aufrufe raus. */
function lauf({ seiten, schema = PERSON, dokumente = ['dok-1'], einstellungen = {}, codes = null }) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '';
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 256, maximum: 16384 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const api = (q) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    let m;
    if (q.methode === 'GET' && (m = /^\/dokumente\/(dok-\d)\/seiten$/.exec(q.pfad))) return json(200, { id: m[1], anzahl: seiten.length });
    if (q.methode === 'GET' && (m = /^\/dokumente\/dok-\d\/seiten\/(\d+)\/scan\?dpi=\d+$/.exec(q.pfad))) {
      const s = seiten[Number(m[1]) - 1];
      if (!s) return json(404, { fehler: 'keine Seite' });
      antwort = s;
      return 200;
    }
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
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
    fd_write: (fd, iov, n, aus) => { let s = 0; for (let i = 0; i < n; i++) s += dv().getUint32(iov + 8 * i + 4, true); dv().setUint32(aus, s, true); return 0; },
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
  // codes: { datei, seiten? } → Aktion dms:codes wie im Hintergrund nach volltext.fertig (dms #1723).
  const eingabe = codes
    ? { aktion: 'dms:codes', datei: codes.datei ?? 'dok-1', mime: 'application/pdf', ...(codes.seiten ? { seiten: codes.seiten } : {}), paket: { id: 'barcodes', version: '1.0.0' }, einstellungen: { dpi: 300, max_seiten: 3, ...einstellungen } }
    : { aktion: 'dms:erkennen', typ: 'Person', schema, text: 'Text der Texterkennung', dokumente, hinweis: '…', sprache: 'de', paket: { id: 'barcodes', version: '1.0.0' }, einstellungen: { dpi: 300, max_seiten: 3, ...einstellungen } };
  const eingang = new TextEncoder().encode(JSON.stringify(eingabe));
  const p = inst.exports.dms_puffer(eingang.length);
  u8().set(eingang, p);
  const t0 = Date.now();
  const code = inst.exports.dms_aktion(p, eingang.length);
  let werte = null;
  if (code === 0 && !codes) werte = Object.fromEntries(Object.entries(JSON.parse(ergebnis).vorschlaege).map(([k, v]) => [k, v.wert]));
  return { code, ergebnis, werte, protokoll, aufrufe, ms: Date.now() - t0, speicherMB: Math.round(memory.buffer.byteLength / 1048576) };
}

let fehler = 0;
const sortiert = (o) => o && Object.fromEntries(Object.entries(o).sort(([a], [b]) => a.localeCompare(b)));
function pruefe(name, r, erwartet) {
  if (erwartet.werte) { erwartet = { werte: sortiert(erwartet.werte) }; r = { ...r, werte: sortiert(r.werte) }; }
  const ist = erwartet.werte ? { code: r.code, werte: r.werte } : { code: r.code, ergebnis: r.ergebnis };
  const soll = erwartet.werte ? { code: 0, werte: erwartet.werte } : { code: 1, ergebnis: erwartet.ergebnis };
  const ok = erwartet.werte ? JSON.stringify(ist) === JSON.stringify(soll) : r.code === 1 && soll.ergebnis.test(r.ergebnis);
  if (!ok) { fehler++; console.log(`✗ ${name}: ${r.ergebnis}\n  ist  ${JSON.stringify(ist)}\n  soll ${JSON.stringify(soll, (k, v) => (v instanceof RegExp ? String(v) : v))}\n  ${r.protokoll.join('\n  ')}`); }
  else console.log(`✓ ${name} (${r.ms} ms)`);
}

const karte = (codes, rauschen = 0) => bild(1050, 600, codes, rauschen);  // Visitenkarte 85×55 mm bei 300 dpi (etwa)
const PERSON_30 = { vorname: 'Jonas', nachname: 'Beispiel', funktion: 'Leiter Vertrieb', email: 'jonas.beispiel@example.org', telefon: '+49 30 1234567', mobil: '+49 170 1234567' };

try {
  pruefe('vCard 3.0 → Person', lauf({ seiten: [karte([{ name: 'vcard30', x: 600, y: 120, modul: 4 }])] }), { werte: PERSON_30 });
  pruefe('vCard 3.0 → Organisation (Name aus ORG, Adresse geteilt, PLZ als Zahl)', lauf({ schema: ORGANISATION, seiten: [karte([{ name: 'vcard30', x: 600, y: 120, modul: 4 }])] }),
    { werte: { email: 'jonas.beispiel@example.org', fax: '+49 30 1234568', hausnummer: '12', internet: 'https://musterbau.example', name: 'Musterbau GmbH', ort: 'Musterstadt', plz: 1234, strasse: 'Musterweg', telefon: '+49 30 1234567' } });
  pruefe('vCard 3.0 gedreht, klein und verrauscht', lauf({ seiten: [karte([{ name: 'vcard30', x: 620, y: 150, modul: 3, winkel: 17 }], 40)] }), { werte: PERSON_30 });
  pruefe('vCard 2.1 mit Quoted-Printable und Umlauten', lauf({ schema: ORGANISATION, seiten: [karte([{ name: 'vcard21', x: 600, y: 120, modul: 4 }])] }),
    { werte: { email: 'petra@example.com', hausnummer: '5a', name: 'Beispiel & Söhne KG', ort: 'Beispielhausen', plz: 12345, strasse: 'Hauptstraße', telefon: '030 7654321' } });
  pruefe('vCard 2.1 → Person (Mobil, Name aus N)', lauf({ seiten: [karte([{ name: 'vcard21', x: 600, y: 120, modul: 4 }])] }),
    { werte: { vorname: 'Petra', nachname: 'Müller-Lüdenscheidt', email: 'petra@example.com', telefon: '030 7654321', mobil: '0170 7654321' } });
  pruefe('vCard 4.0 (ROLE, tel:-URI)', lauf({ seiten: [karte([{ name: 'vcard40', x: 600, y: 120, modul: 5 }])] }),
    { werte: { vorname: 'Katrin', nachname: 'Muster', funktion: 'Steuerberaterin', email: 'katrin@kanzlei.example', telefon: '+49-89-555-0100' } });
  pruefe('Visitenkarte auf Seite 2, daneben ein Link-Code', lauf({ seiten: [karte([]), karte([{ name: 'url', x: 80, y: 100, modul: 6 }, { name: 'vcard30', x: 600, y: 120, modul: 4 }])] }), { werte: PERSON_30 });
  pruefe('Präpariert: langer Name gekürzt, Steuerzeichen raus, Foto und leere Zeilen ignoriert', lauf({ schema: ORGANISATION, seiten: [bild(1400, 1000, [{ name: 'lang', x: 300, y: 100, modul: 4 }])] }),
    { werte: { name: 'Sehr lange Firma '.repeat(60).slice(0, 300).trim() } });
  pruefe('Präpariert → Person', lauf({ seiten: [bild(1400, 1000, [{ name: 'lang', x: 300, y: 100, modul: 4 }])] }), { werte: { vorname: 'Jonas', nachname: 'Beispiel' } });
  pruefe('Nur Internetadresse', lauf({ seiten: [karte([{ name: 'url', x: 300, y: 100, modul: 8 }])] }), { ergebnis: /^Code gefunden \(Internetadresse\), aber keine Visitenkarte/ });
  pruefe('GiroCode wird nicht ausgewertet', lauf({ seiten: [karte([{ name: 'girocode', x: 300, y: 100, modul: 6 }])] }), { ergebnis: /^Code gefunden \(GiroCode\)/ });
  pruefe('Kein QR-Code', lauf({ seiten: [karte([], 20)] }), { ergebnis: /Kein Code gefunden \(1 Seite geprüft\)/ });
  pruefe('Ohne Dokument', lauf({ seiten: [], dokumente: [] }), { ergebnis: /Kein Dokument mitgegeben/ });
  pruefe('Fremde Id wird nicht in den Pfad übernommen', lauf({ seiten: [karte([])], dokumente: ['../typen'] }), { ergebnis: /Kein Code gefunden \(0 Seiten geprüft\)/ });
  const r = lauf({ seiten: [karte([{ name: 'vcard30', x: 600, y: 120, modul: 4 }])] });
  if (r.aufrufe.some((a) => !a.startsWith('GET /dokumente/dok-1/'))) { fehler++; console.log(`✗ nur Seiten gelesen: ${r.aufrufe.join(', ')}`); } else console.log('✓ nur Seiten des mitgegebenen Dokuments gelesen');
  const notiz = JSON.parse(r.ergebnis).vorschlaege;
  if (notiz.notiz || notiz.email?.sicherheit !== 'hoch' || !/^QR-Code \(vCard\): EMAIL/.test(notiz.email?.fundstelle ?? '')) { fehler++; console.log(`✗ Fundstelle/Sicherheit: ${r.ergebnis}`); } else console.log('✓ Feld ohne Art bleibt leer, Fundstelle nennt die vCard-Zeile');

  // ---------- dms:codes ----------
  const a4 = (codes, rauschen = 0) => bild(2480, 3508, codes, rauschen);  // A4 bei 300 dpi
  const DUB = 'https://www.kba-online.de/dub/#/zugriffsdaten/A1B2C3D4E5F6/P0123456789/0815';
  const seite1 = a4([{ name: 'dub', x: 1900, y: 200, modul: 8 }, { name: 'ean13', x: 200, y: 3000, modul: 4 }, { name: 'code128', x: 1200, y: 3000, modul: 3 }], 15);
  const seite2 = a4([{ name: 'datamatrix', x: 300, y: 300, modul: 10 }, { name: 'aztec', x: 1500, y: 300, modul: 10, winkel: 90 }, { name: 'pdf417', x: 300, y: 1500, modul: 2 }, { name: 'itf', x: 300, y: 2600, modul: 4 }]);
  const liste = (r) => (r.code === 0 ? JSON.parse(r.ergebnis).codes.map((c) => `${c.seite} ${c.art} ${c.inhalt}`).sort() : r.ergebnis);
  function pruefeCodes(name, r, soll) {
    const ist = liste(r);
    if (JSON.stringify(ist) !== JSON.stringify([...soll].sort())) { fehler++; console.log(`✗ ${name}\n  ist  ${JSON.stringify(ist)}\n  soll ${JSON.stringify([...soll].sort())}\n  ${r.protokoll.join('\n  ')}`); }
    else console.log(`✓ ${name} (${r.ms} ms)`);
    return r;
  }
  const ALLE = [`1 qr ${DUB}`, '1 ean13 4006381333931', '1 code128 RE-2026-004711', '2 datamatrix Paket 00340434161094042557',
    '2 aztec Fahrkarte Musterstadt-Beispielhausen 2. Klasse', '2 pdf417 Bordkarte MUSTER/JONAS XY1234 Sitz 12A', '2 itf 12345678901231'];
  const r1 = pruefeCodes('dms:codes: alle Arten auf zwei A4-Seiten (QR, EAN-13, Code 128, Data Matrix, Aztec gedreht, PDF417, ITF)', lauf({ codes: {}, seiten: [seite1, seite2] }), ALLE);
  if (r1.aufrufe.some((a) => !a.startsWith('GET /dokumente/dok-1/'))) { fehler++; console.log(`✗ nur Seiten gelesen: ${r1.aufrufe.join(', ')}`); } else console.log('✓ dms:codes liest nur Seiten des genannten Dokuments');
  if (r1.protokoll.some((z) => /kba-online|4006381333931|Bordkarte/.test(z))) { fehler++; console.log(`✗ Inhalte im Protokoll: ${r1.protokoll.join(' | ')}`); } else console.log(`✓ Protokoll ohne Inhalte: ${r1.protokoll.join(' | ')}`);
  const reihe = JSON.parse(r1.ergebnis).codes.map((c) => `${c.seite} ${c.art}`).join(', ');
  if (reihe !== '1 qr, 1 ean13, 1 code128, 2 datamatrix, 2 aztec, 2 pdf417, 2 itf') { fehler++; console.log(`✗ Lesereihenfolge: ${reihe}`); } else console.log('✓ Lesereihenfolge: Seite für Seite, oben nach unten, links nach rechts');
  const r2 = pruefeCodes('dms:codes: Seitenzahl von Ablago; max_seiten gilt nur für Visitenkarten', lauf({ codes: { seiten: 2 }, seiten: [seite1, seite2], einstellungen: { max_seiten: 1 } }), ALLE);
  if (r2.aufrufe.some((a) => a === 'GET /dokumente/dok-1/seiten') || r2.aufrufe.length !== 2) { fehler++; console.log(`✗ Aufrufe: ${r2.aufrufe.join(', ')}`); } else console.log('✓ mit seiten fragt das Paket die Seitenzahl nicht nach');
  pruefeCodes('dms:codes: kaputter QR-Code (ein Drittel verdeckt) wird nicht gemeldet, der heile daneben schon',
    lauf({ codes: {}, seiten: [a4([{ name: 'dub', x: 300, y: 300, modul: 8, loch: [0.3, 0.3, 0.7, 0.75] }, { name: 'ean13', x: 300, y: 1500, modul: 4 }])] }), ['1 ean13 4006381333931']);
  console.log(`  Speicher nach zwei A4-Seiten: ${r1.speicherMB} MB`);
  const r3 = pruefeCodes('dms:codes: Seite ohne Code → leere Liste', lauf({ codes: {}, seiten: [a4([], 20)] }), []);
  if (r3.code !== 0 || r3.ergebnis !== '{"codes":[]}') { fehler++; console.log(`✗ leere Antwort: ${r3.ergebnis}`); }
  pruefeCodes('dms:codes: derselbe Code zweimal auf einer Seite nur einmal, auf zwei Seiten zweimal', lauf({ codes: {}, seiten: [karte([{ name: 'url', x: 80, y: 100, modul: 6 }, { name: 'url', x: 600, y: 100, modul: 6 }]), karte([{ name: 'url', x: 80, y: 100, modul: 6 }])] }),
    ['1 qr https://example.org/angebot', '2 qr https://example.org/angebot']);
  pruefeCodes('dms:codes: GiroCode mit Zeilenumbrüchen unverändert', lauf({ codes: {}, seiten: [karte([{ name: 'girocode', x: 300, y: 100, modul: 6 }])] }),
    ['1 qr ' + ['BCD', '002', '1', 'SCT', '', 'Musterbau GmbH', 'DE00000000000000000000', 'EUR12.50', '', '', 'Rechnung 4711'].join('\n')]);
  pruefe('dms:codes: fremde Id', lauf({ codes: { datei: '../typen' }, seiten: [seite1] }), { ergebnis: /^Kein gültiges Dokument/ });
  pruefe('dms:codes: keine Seite zu holen', lauf({ codes: { seiten: 1 }, seiten: [] }), { ergebnis: /^Keine Seite des Dokuments lesbar/ });
  pruefe('dms:erkennen: nur Strichcode', lauf({ seiten: [karte([{ name: 'ean13', x: 100, y: 200, modul: 4 }])] }), { ergebnis: /^Code gefunden \(EAN-13\), aber keine Visitenkarte/ });
} catch (e) { fehler++; console.log(`✗ Ausnahme: ${e.stack}`); }

if (fehler) { console.log(`${fehler} Prüfung(en) fehlgeschlagen`); process.exit(1); }
console.log('Alle Prüfungen bestanden');
