// Kleiner Dienst mit OpenAI-kompatibler Schnittstelle als Attrappe – zum Ausprobieren ohne echtes Modell und für
// den Test im Paket-Läufer des DMS. Antwortet Stück für Stück („stream": true) oder auf einmal.
//
//   node tests/attrappe.mjs [port]        # Standard 11434, Adresse im DMS: http://<rechner>:<port>/v1
//
// Modell: „attrappe:1b“. Die Antwort nennt die erste Ausschnitt-Nummer aus den Nachrichten und die Frage.
// Schreibt nichts mit außer der Anzahl der Anfragen.
import { createServer } from 'node:http';

const MODELL = 'attrappe:1b';
const port = Number(process.argv[2] ?? 11434);
let anfragen = 0;

function antwortFuer(nachrichten) {
  const daten = nachrichten.filter((m) => m.role === 'user').map((m) => m.content).join('\n');
  const nr = /<ausschnitt nr="(\d+)"/.exec(daten)?.[1];
  const frage = (/Frage: (.*)$/m.exec(daten)?.[1] ?? '').slice(0, 200);
  return nr ? `Laut Ausschnitt [${nr}] steht die Antwort auf „${frage}“ in deiner Ablage.` : `Zu „${frage}“ finde ich in den Ausschnitten nichts.`;
}

const server = createServer((q, a) => {
  anfragen++;
  let roh = '';
  q.on('data', (d) => { roh += d; });
  q.on('end', () => {
    if (q.method === 'GET' && q.url === '/v1/models') {
      a.writeHead(200, { 'content-type': 'application/json' }).end(JSON.stringify({ object: 'list', data: [{ id: MODELL, object: 'model' }] }));
      return;
    }
    if (q.method !== 'POST' || q.url !== '/v1/chat/completions') { a.writeHead(404, { 'content-type': 'application/json' }).end('{"error":{"message":"not found"}}'); return; }
    let j;
    try { j = JSON.parse(roh); } catch { a.writeHead(400).end('{"error":{"message":"invalid json"}}'); return; }
    if (j.model !== MODELL) { a.writeHead(404, { 'content-type': 'application/json' }).end(JSON.stringify({ error: { message: `model "${j.model}" not found, try pulling it first` } })); return; }
    const text = antwortFuer(j.messages ?? []);
    if (!j.stream) { a.writeHead(200, { 'content-type': 'application/json' }).end(JSON.stringify({ choices: [{ index: 0, message: { role: 'assistant', content: text } }] })); return; }
    a.writeHead(200, { 'content-type': 'text/event-stream' });
    const teile = text.match(/.{1,12}/gsu) ?? [];
    const weiter = () => {
      const t = teile.shift();
      if (t === undefined) { a.end('data: [DONE]\n\n'); return; }
      a.write(`data: ${JSON.stringify({ choices: [{ index: 0, delta: { content: t } }] })}\n\n`);
      setTimeout(weiter, 20);
    };
    weiter();
  });
});
server.listen(port, () => console.log(`Attrappe auf http://127.0.0.1:${server.address().port}/v1 (Modell ${MODELL})`));
process.on('SIGINT', () => { console.log(`${anfragen} Anfragen`); process.exit(0); });
