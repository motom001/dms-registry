"""Prüft ein Zusammenhangs-SVG (#115): Läuft ein Pfeil durch ein Kästchen, das weder Anfang noch Ziel ist?

    from zusammenhang_pruefen import schnitte; schnitte(svg) → [(pfeil-titel, kästchen-name), …]
"""
import re

_ZAHL = r'-?\d+(?:\.\d+)?'


def _punkte(d: str, schritte: int = 24) -> list[tuple[float, float]]:
    teile = re.findall(rf'([MLC])((?:\s*{_ZAHL})+)', d)
    pkt, aktuell = [], (0.0, 0.0)
    for befehl, zahlen in teile:
        z = [float(x) for x in re.findall(_ZAHL, zahlen)]
        if befehl in 'ML':
            aktuell = (z[0], z[1])
            if befehl == 'L' and pkt:
                a = pkt[-1]
                pkt += [(a[0] + (aktuell[0] - a[0]) * i / schritte, a[1] + (aktuell[1] - a[1]) * i / schritte) for i in range(1, schritte + 1)]
            else:
                pkt.append(aktuell)
        else:
            (x0, y0), (x1, y1, x2, y2, x3, y3) = aktuell, z
            for i in range(1, schritte + 1):
                s = i / schritte
                u = 1 - s
                pkt.append((u ** 3 * x0 + 3 * u * u * s * x1 + 3 * u * s * s * x2 + s ** 3 * x3,
                            u ** 3 * y0 + 3 * u * u * s * y1 + 3 * u * s * s * y2 + s ** 3 * y3))
            aktuell = (x3, y3)
    return pkt


def schnitte(svg: str, rand: float = 2.0) -> list[tuple[str, str]]:
    kaesten = [(float(x), float(y), float(b), float(h), n) for x, y, b, h, n in
               re.findall(rf'<rect x="({_ZAHL})" y="({_ZAHL})" width="({_ZAHL})" height="({_ZAHL})" rx="8"/><text [^>]*>([^<]*)</text>', svg)]
    funde = []
    for d, titel in re.findall(r'<path class="kante [a-z]+" d="([^"]+)"[^>]*><title>([^<]*)</title>', svg):
        von, nach = titel.split(' → ')[0], titel.split(' → ')[1].rsplit(' (', 1)[0]
        pkt = _punkte(d)
        for x, y, b, h, n in kaesten:
            if n in (von, nach):
                continue
            if any(x + rand < px < x + b - rand and y + rand < py < y + h - rand for px, py in pkt):
                funde.append((titel, n))
    return funde
