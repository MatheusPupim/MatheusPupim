#!/usr/bin/env python3
"""Aplica acabamento visual ao SVG gerado pelo Platane/snk.

Faz duas coisas que a action sozinha não entrega:

1. Normaliza a paleta. O snk espera cinco cores em `color_dots` (célula vazia
   + quatro níveis de intensidade). Passar menos que isso deixa variáveis CSS
   indefinidas e achata o degradê — foi o que aconteceu com `green,red`.
2. Monta um "palco" atrás da grade: fundo em degradê, textura sutil,
   moldura arredondada e brilho na cobra.

Uso: embelezar-snake.py ENTRADA.svg SAIDA.svg [--tema dark|light]
"""

import argparse
import pathlib
import re
import sys

TEMAS = {
    # (vazio, nivel1, nivel2, nivel3, nivel4, cobra, borda, fundo_a, fundo_b, textura)
    "dark": dict(
        dots=("#151b23", "#2b1d63", "#4324a8", "#6d3fe0", "#a274ff"),
        snake="#39d353",
        borda="#8957e5",
        fundo=("#0d1117", "#161b22"),
        textura="#8957e5",
        stroke="#1b1f2333",
    ),
    "light": dict(
        dots=("#ebedf0", "#dcd0fb", "#b79cf0", "#8a5fe0", "#512BD4"),
        snake="#239120",
        borda="#c2b3f0",
        fundo=("#ffffff", "#f3f0fc"),
        textura="#512BD4",
        stroke="#1b1f230a",
    ),
}


def normalizar_paleta(svg: str, t: dict) -> str:
    """Reescreve o bloco :root com a paleta completa dos cinco níveis."""
    d = t["dots"]
    novo = (
        ":root{"
        f"--cb:{t['stroke']};"
        f"--cs:{t['snake']};"
        f"--ce:{d[0]};"
        f"--c0:{d[1]};--c1:{d[2]};--c2:{d[3]};--c3:{d[4]};--c4:{d[4]}"
        "}"
    )
    svg, n = re.subn(r":root\{[^}]*\}", novo, svg, count=1)
    if n != 1:
        sys.exit("erro: bloco :root não encontrado — o formato do snk mudou?")
    return svg


def montar_palco(svg: str, t: dict) -> str:
    """Injeta fundo, textura, moldura e brilho logo após o </style>."""
    m = re.search(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"', svg)
    if not m:
        sys.exit("erro: viewBox não encontrado no SVG de entrada.")
    x, y, w, h = (float(v) for v in m.groups())

    # margem extra para o palco respirar em volta da grade
    mx, my = 14.0, 12.0
    px, py, pw, ph = x - mx, y - my, w + 2 * mx, h + 2 * my
    fa, fb = t["fundo"]

    palco = f"""<defs>\
<linearGradient id="fundoPalco" x1="0" y1="0" x2="1" y2="1">\
<stop offset="0%" stop-color="{fa}"/><stop offset="100%" stop-color="{fb}"/>\
</linearGradient>\
<linearGradient id="bordaPalco" x1="0" y1="0" x2="1" y2="0">\
<stop offset="0%" stop-color="{t['borda']}" stop-opacity="0.75"/>\
<stop offset="50%" stop-color="{t['snake']}" stop-opacity="0.55"/>\
<stop offset="100%" stop-color="{t['borda']}" stop-opacity="0.75"/>\
</linearGradient>\
<pattern id="texturaPalco" width="16" height="16" patternUnits="userSpaceOnUse">\
<circle cx="1.5" cy="1.5" r="0.9" fill="{t['textura']}" fill-opacity="0.14"/>\
</pattern>\
<radialGradient id="brilhoPalco" cx="0.5" cy="0.5" r="0.5">\
<stop offset="0%" stop-color="{t['snake']}" stop-opacity="0.16"/>\
<stop offset="100%" stop-color="{t['snake']}" stop-opacity="0"/>\
</radialGradient>\
<filter id="brilhoCobra" x="-50%" y="-50%" width="200%" height="200%">\
<feGaussianBlur stdDeviation="1.6" result="desfoque"/>\
<feMerge><feMergeNode in="desfoque"/><feMergeNode in="SourceGraphic"/></feMerge>\
</filter>\
</defs>\
<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="url(#fundoPalco)"/>\
<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="url(#texturaPalco)"/>\
<ellipse cx="{x + w / 2}" cy="{y + h / 2}" rx="{w * 0.42}" ry="{h * 0.6}" fill="url(#brilhoPalco)"/>\
<rect x="{px + 0.75}" y="{py + 0.75}" width="{pw - 1.5}" height="{ph - 1.5}" rx="13.25" \
fill="none" stroke="url(#bordaPalco)" stroke-width="1.5"/>"""

    svg = svg.replace("</style>", "</style>" + palco, 1)

    # o palco é maior que a grade: amplia o viewBox para não cortar a moldura
    svg = svg.replace(
        m.group(0), f'viewBox="{px} {py} {pw} {ph}"', 1
    )
    svg = re.sub(r'width="[\d.]+" height="[\d.]+"',
                 f'width="{pw:.0f}" height="{ph:.0f}"', svg, count=1)

    # brilho na cobra (classe .s no output do snk)
    svg = svg.replace("</style>", "", 0)
    svg = svg.replace(
        "<style>", "<style>.s{filter:url(#brilhoCobra)}", 1
    )
    return svg


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("saida")
    p.add_argument("--tema", choices=("dark", "light"), default="dark")
    a = p.parse_args()

    t = TEMAS[a.tema]
    svg = pathlib.Path(a.entrada).read_text(encoding="utf-8")
    svg = normalizar_paleta(svg, t)
    svg = montar_palco(svg, t)

    saida = pathlib.Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(svg, encoding="utf-8")
    print(f"{a.tema}: {a.entrada} -> {a.saida} ({saida.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
