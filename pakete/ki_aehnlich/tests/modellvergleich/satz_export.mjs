import { readFileSync, writeFileSync } from 'node:fs';
// Modellvergleich (registry #242), Schritt 1: Satz „Lebensläufe“ nach satz.json.
const { liesSatz, typKennung } = await import(`${process.env.PRUEFSTAND}/satz.mjs`);
const satz = liesSatz(process.env.SATZ);
const doks = satz.dokumente.filter((d) => d.erwartung.mappe !== 'keine' && satz.mappen.get(d.erwartung.mappe));
writeFileSync(`${process.env.MV}/satz.json`, JSON.stringify(doks.map((d) => ({ id: d.id, mappe: d.erwartung.mappe, typ: typKennung(satz, satz.mappen.get(d.erwartung.mappe).typ),
  titel: d.titel ?? '', text: readFileSync(d.md, 'utf8').replace(/^---\n[\s\S]*?\n---\n/, '') }))));
console.log(doks.length);
