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
    reihen: dict = {}
    for k in knoten:
        reihen.setdefault(reihe[k], []).append(k)
    # Reihenfolge in der Reihe: oben wie übergeben, darunter nach dem Mittel der Ziele (Schwerpunkt), dann Paket.
    x_mitte: dict = {}
    pos: dict = {}
    # Viele Pfeile an einem Kästchen (z. B. Organisation): breiter, damit die Spitzen nicht aufeinander liegen.
    anschluesse = {k: max(sum(1 for (v, n) in kanten if n == k), sum(1 for (v, n) in kanten if v == k)) for k in knoten}
    breiten = {k: max(_breite(index[k], fokus is not None and index[k]['paket'] != fokus), 16 * anschluesse[k] + 16) for k in knoten}
    hoehe_paket = fokus is None  # Gesamtseite: Paketname in jedem Kästchen
    for r in sorted(reihen):
        liste = reihen[r]
        if r > 0:
            def schwer(k):
                ziele = [x_mitte[n] for (v, n) in kanten if v == k and n in x_mitte]
                return (sum(ziele) / len(ziele)) if ziele else 1e9
            liste.sort(key=lambda k: (schwer(k), index[k]['paketname'].lower(), index[k]['name'].lower()))
        x = RAND
        for k in liste:
            pos[k] = (x, RAND + r * (KNOTEN_H + REIHE_ABSTAND))
            x_mitte[k] = x + breiten[k] / 2
            x += breiten[k] + LUECKE
    gesamt_b = max(pos[k][0] + breiten[k] for k in knoten) + RAND
    # Reihen mittig ausrichten
    for r, liste in reihen.items():
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
    rein = {k: verteilt(k, [v for (v, n) in kanten if n == k]) for k in knoten}
    raus = {k: verteilt(k, [n for (v, n) in kanten if v == k]) for k in knoten}

    pfeil = f'pfeil-{kennung}'
    teile = [f'<svg class="zusammenhang" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(gesamt_b)} {int(gesamt_h)}" '
             f'width="{int(gesamt_b)}" height="{int(gesamt_h)}" role="img" aria-labelledby="{kennung}-titel {kennung}-text">'
             f'<title id="{kennung}-titel">{e(titel)}</title><desc id="{kennung}-text">{e(beschreibung)}</desc>'
             f'<defs><marker id="{pfeil}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
             f'<path d="M0 0L10 5L0 10z" class="spitze"/></marker></defs>']
    for (von, nach), gehoert in sorted(kanten.items()):
        x1, y1 = raus[von][nach], pos[von][1]
        x2, y2 = rein[nach][von], pos[nach][1] + KNOTEN_H
        if y2 > y1:  # Kreis: Ziel liegt nicht darüber – von unten an die Oberkante
            y1, y2 = pos[von][1] + KNOTEN_H, pos[nach][1]
            biege = 30
            d = f'M{x1:.0f} {y1:.0f}C{x1:.0f} {y1 + biege:.0f} {x2:.0f} {y2 - biege:.0f} {x2:.0f} {y2:.0f}'
        else:
            mitte = (y1 + y2) / 2
            d = f'M{x1:.0f} {y1:.0f}C{x1:.0f} {mitte:.0f} {x2:.0f} {mitte:.0f} {x2:.0f} {y2:.0f}'
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
