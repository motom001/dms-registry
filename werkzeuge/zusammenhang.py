"""Zusammenhänge der Mappentypen als Zeichnung im Seitentext (Registry #115 Punkt 4).

Die CI rechnet beim Bauen des Katalogs die Anordnung aus und schreibt ein Inline-SVG in die Seite: kein Bild zum
Herunterladen, nichts von Dritten, kein Skript. Farben kommen aus den Farbwerten der Seite (hell und dunkel),
Text im Bild ist echter Text. Die Textfassung steht daneben („Verweist auf“, „Wird verwendet von“).

Anordnung in Reihen: Mappentypen, auf die verwiesen wird, stehen oben; wer auf sie verweist, darunter. Ein Pfeil
zeigt vom Mappentyp auf den, auf den er verweist. Durchgezogen = gehört zu, gestrichelt = Bezug.

    knoten, kanten = netz(index, ['vermietung:mietobjekt', …])
    svg = zeichne(knoten, kanten, index, titel='…', fokus='vermietung')
"""
from html import escape as e

ABLAGEORT = 'basis:ablageort'
KNOTEN_H = 44
REIHE_ABSTAND = 70
LUECKE = 22
RAND = 12
PLATZHALTER_B = 14  # Breite der Lücke für einen langen Pfeil in einer Zwischenreihe


def _voll(ziel: str, pid: str) -> str:
    return ziel if ':' in ziel else f'{pid}:{ziel}'


def kanten_aller(index: dict, ohne: set = frozenset({ABLAGEORT})) -> dict:
    """(von, nach) → True, wenn mindestens ein Feld „gehört zu“ ist (sonst Bezug). Ohne Verweise auf sich selbst."""
    kanten: dict = {}
    for von, t in index.items():
        for f in t.get('felder') or []:
            if f.get('typ') != 'referenz' or not f.get('ziel'):
                continue
            nach = _voll(str(f['ziel']), t['paket'])
            if nach == von or nach in ohne or nach not in index:
                continue
            kanten[(von, nach)] = kanten.get((von, nach), False) or f.get('verweisart') == 'zugehoerigkeit'
    return kanten


def netz(index: dict, eigene: list[str], ohne: set = frozenset({ABLAGEORT})) -> tuple[list[str], dict]:
    """Die eigenen Mappentypen und ihre direkten Nachbarn in anderen Paketen, mit den Kanten zwischen ihnen."""
    alle = kanten_aller(index, ohne)
    drin = set(eigene)
    for von, nach in alle:
        if von in eigene:
            drin.add(nach)
        if nach in eigene:
            drin.add(von)
    kanten = {k: v for k, v in alle.items() if k[0] in drin and k[1] in drin and (k[0] in eigene or k[1] in eigene)}
    reihenfolge = list(eigene) + sorted(drin - set(eigene), key=lambda k: (index[k]['paketname'].lower(), index[k]['name'].lower()))
    return reihenfolge, kanten


def _breite(t: dict, fremd: bool) -> int:
    zeichen = max(len(t['name']) * 7.4, (len(t['paketname']) * 6.3 if fremd else 0))
    return int(zeichen) + 24


def anordnung(knoten: list[str], kanten: dict) -> dict:
    """Reihe je Knoten: 0 = oben (wird nur verwiesen), darunter, wer darauf verweist. Kreise brechen ab."""
    raus: dict = {k: [] for k in knoten}
    for von, nach in kanten:
        raus[von].append(nach)
    reihe: dict = {}

    def tiefe(k: str, unterwegs: frozenset) -> int:
        if k in reihe:
            return reihe[k]
        ziele = [z for z in raus[k] if z not in unterwegs]
        r = 1 + max((tiefe(z, unterwegs | {k}) for z in ziele), default=-1)
        reihe[k] = r
        return r

    for k in knoten:
        tiefe(k, frozenset())
    return reihe


def zeichne(knoten: list[str], kanten: dict, index: dict, titel: str, fokus: str | None = None, kennung: str = 'z',
            beschreibung: str = '') -> str:
    """Inline-SVG; fokus = Paket, dessen Mappentypen kräftig sind (andere blass mit Paketnamen)."""
    if not knoten:
        return ''
    reihe = anordnung(knoten, kanten)
    # Lange Pfeile (über mehr als eine Reihe) bekommen in jeder Zwischenreihe einen unsichtbaren Platzhalter (Ebenen-
    # Verfahren nach Sugiyama): Er hält eine Lücke frei, und die Kurve läuft hindurch statt durch fremde Kästchen.
    ketten: dict = {}
    platz: list[str] = []
    for (von, nach) in sorted(kanten):
        kette = [von]
        if reihe[von] - reihe[nach] > 1:
            for r in range(reihe[von] - 1, reihe[nach], -1):
                d = f'~{len(platz)}'
                platz.append(d)
                reihe[d] = r
                kette.append(d)
        kette.append(nach)
        ketten[(von, nach)] = kette
    alle = list(knoten) + platz
    oben: dict = {k: [] for k in alle}   # Nachbarn eine Reihe höher (Ziele)
    unten: dict = {k: [] for k in alle}  # Nachbarn eine Reihe tiefer
    for kette in ketten.values():
        for a_, b_ in zip(kette, kette[1:]):
            oben[a_].append(b_)
            unten[b_].append(a_)
    reihen: dict = {}
    for k in alle:
        reihen.setdefault(reihe[k], []).append(k)
    # Viele Pfeile an einem Kästchen (z. B. Organisation): breiter, damit die Spitzen nicht aufeinander liegen.
    breiten = {k: max(_breite(index[k], fokus is not None and index[k]['paket'] != fokus), 16 * max(len(oben[k]), len(unten[k])) + 16)
               for k in knoten}
    breiten.update({d: PLATZHALTER_B for d in platz})
    hoehe_paket = fokus is None  # Gesamtseite: Paketname in jedem Kästchen

    def ordne():
        """Reihenfolge je Reihe nach dem Schwerpunkt der Nachbarn – ab- und aufwärts, damit sich wenig kreuzt."""
        lage = {k: i for r in reihen.values() for i, k in enumerate(r)}
        for _ in range(4):
            for r in sorted(reihen)[1:]:
                reihen[r].sort(key=lambda k: (sum(lage[n] for n in oben[k]) / len(oben[k])) if oben[k] else lage[k])
                lage.update({k: i for i, k in enumerate(reihen[r])})
            for r in sorted(reihen, reverse=True)[1:]:
                reihen[r].sort(key=lambda k: (sum(lage[n] for n in unten[k]) / len(unten[k])) if unten[k] else lage[k])
                lage.update({k: i for i, k in enumerate(reihen[r])})
    ordne()
    pos: dict = {}
    for r in sorted(reihen):
        x = RAND
        for k in reihen[r]:
            pos[k] = (x, RAND + r * (KNOTEN_H + REIHE_ABSTAND))
            x += breiten[k] + (LUECKE if k in index else 6)
    gesamt_b = max(pos[k][0] + breiten[k] for k in alle) + RAND
    for r, liste in reihen.items():  # Reihen mittig ausrichten
        rb = pos[liste[-1]][0] + breiten[liste[-1]] - RAND
        versatz = (gesamt_b - 2 * RAND - rb) / 2
        for k in liste:
            pos[k] = (pos[k][0] + versatz, pos[k][1])
    gesamt_h = RAND + (max(reihen) + 1) * (KNOTEN_H + REIHE_ABSTAND) - REIHE_ABSTAND + RAND

    # Anschlusspunkte verteilen, damit sich Pfeile an einem Kästchen nicht decken.
    def verteilt(k, nachbarn):
        nachbarn = sorted(nachbarn, key=lambda n: pos[n][0])
        x0, b = pos[k][0], breiten[k]
        return {n: x0 + b * (i + 1) / (len(nachbarn) + 1) for i, n in enumerate(nachbarn)}
    rein = {k: verteilt(k, unten[k]) for k in knoten}
    raus = {k: verteilt(k, oben[k]) for k in knoten}

    pfeil = f'pfeil-{kennung}'
    teile = [f'<svg class="zusammenhang" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(gesamt_b)} {int(gesamt_h)}" '
             f'width="{int(gesamt_b)}" height="{int(gesamt_h)}" role="img" aria-labelledby="{kennung}-titel {kennung}-text">'
             f'<title id="{kennung}-titel">{e(titel)}</title><desc id="{kennung}-text">{e(beschreibung)}</desc>'
             f'<defs><marker id="{pfeil}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
             f'<path d="M0 0L10 5L0 10z" class="spitze"/></marker></defs>']
    for (von, nach), gehoert in sorted(kanten.items()):
        kette = ketten[(von, nach)]
        if reihe[von] <= reihe[nach]:  # Kreis: Ziel liegt nicht darüber – von unten an die Oberkante
            x1, y1 = raus[von][kette[1]], pos[von][1] + KNOTEN_H
            x2, y2 = rein[nach][kette[-2]], pos[nach][1]
            d = f'M{x1:.0f} {y1:.0f}C{x1:.0f} {y1 + 30:.0f} {x2:.0f} {y2 - 30:.0f} {x2:.0f} {y2:.0f}'
        else:
            # Punkte: Oberkante des Anfangs, durch jeden Platzhalter senkrecht hindurch, Unterkante des Ziels.
            punkte = [(raus[von][kette[1]], pos[von][1])]
            for d_ in kette[1:-1]:
                xm = pos[d_][0] + PLATZHALTER_B / 2
                punkte += [(xm, pos[d_][1] + KNOTEN_H), (xm, pos[d_][1])]
            punkte.append((rein[nach][kette[-2]], pos[nach][1] + KNOTEN_H))
            d = f'M{punkte[0][0]:.0f} {punkte[0][1]:.0f}'
            for (xa, ya), (xb, yb) in zip(punkte, punkte[1:]):
                if xa == xb:
                    d += f'L{xb:.0f} {yb:.0f}'
                else:
                    m = (ya + yb) / 2
                    d += f'C{xa:.0f} {m:.0f} {xb:.0f} {m:.0f} {xb:.0f} {yb:.0f}'
        art = 'gehoert' if gehoert else 'bezug'
        teile.append(f'<path class="kante {art}" d="{d}" marker-end="url(#{pfeil})"><title>{e(index[von]["name"])} → '
                     f'{e(index[nach]["name"])} ({"gehört zu" if gehoert else "Bezug"})</title></path>')
    for k in knoten:
        t = index[k]
        x, y = pos[k]
        fremd = fokus is not None and t['paket'] != fokus
        klasse = 'knoten fremd' if fremd else 'knoten'
        unter = t['paketname'] if (fremd or hoehe_paket) else ''
        ty = y + (17 if unter else 27)
        teile.append(f'<g class="{klasse}"><rect x="{x:.0f}" y="{y:.0f}" width="{breiten[k]}" height="{KNOTEN_H}" rx="8"/>'
                     f'<text x="{x + breiten[k] / 2:.0f}" y="{ty:.0f}" class="name">{e(t["name"])}</text>'
                     + (f'<text x="{x + breiten[k] / 2:.0f}" y="{y + 34:.0f}" class="paket">{e(unter)}</text>' if unter else '')
                     + '</g>')
    teile.append('</svg>')
    return ''.join(teile)


LESEHILFE = ('<p class="leise klein lesehilfe"><span class="linie gehoert" aria-hidden="true"></span> gehört zu · '
             '<span class="linie bezug" aria-hidden="true"></span> Bezug · Der Pfeil zeigt auf den Mappentyp, auf den verwiesen wird.')
