"""
Gera o Fraunces enxuto do site: fixa peso 400 e SOFT 50 (os únicos valores usados) e mantém só o eixo
opsz variável (corte display nos títulos grandes). Recorta pra latim + pontuação do português.
O variável do Google (opsz+wght+SOFT) pesa 118/146 KB; a instância fica bem menor e melhora o LCP mobile.

Uso (precisa de fonttools + brotli):
  python scripts/fraunces.py <Fraunces-Regular-var.woff2> <Fraunces-Italic-var.woff2>
Saída: src/app/fonts/fraunces.woff2, src/app/fonts/fraunces-italic.woff2
Licença: Fraunces é SIL OFL 1.1 (instanciar/recortar é permitido).
"""
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

UNICODES = "U+0020-007E,U+00A0-00FF,U+2013-2014,U+2018-201E,U+2022,U+2026,U+2032-2033,U+2192"
OUT = Path(__file__).resolve().parent.parent / "src" / "app" / "fonts"
OUT.mkdir(parents=True, exist_ok=True)

for src, nome in zip(sys.argv[1:3], ["fraunces", "fraunces-italic"]):
    font = TTFont(src)
    font = instancer.instantiateVariableFont(font, {"wght": 400, "SOFT": 50}, updateFontNames=False)
    # o itálico do Google vem sem entrada de variação pra alguns glifos (.notdef): o subsetter exige todas
    gvar = font["gvar"]
    variacoes = {}
    for g in font.getGlyphOrder():
        try:
            variacoes[g] = gvar.variations[g]
        except KeyError:
            variacoes[g] = []
    gvar.variations = variacoes
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]           # kerning, ligaduras, numerais
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=subset.parse_unicodes(UNICODES))
    sub.subset(font)
    dest = OUT / f"{nome}.woff2"
    font.flavor = "woff2"
    font.save(dest)
    print(f"{dest.name}: {dest.stat().st_size // 1024} KB, eixos {[a.axisTag for a in font['fvar'].axes]}")
