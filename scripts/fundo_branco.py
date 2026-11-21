"""Still life do Flow (fundo creme liso) -> fundo branco puro, pra entrar no card com mix-blend-multiply.

O fundo do Flow é creme com vinheta (cantos de cima mais escuros) e nunca bate com a cor do card. Aqui o fundo é
modelado por uma superfície suave (polinômio de grau 3 em x, y por canal, ajustado só onde não tem objeto) e a
imagem é dividida por ele: o fundo vira 1.0 (branco) e os objetos e as sombras ficam como eram em relação a ele.
No site, multiply sobre o card = o fundo some e sobra só o arranjo com a sombra.

Uso: python scripts/fundo_branco.py <entrada.jpg> <saida.webp> [largura=900]
"""

import sys

import numpy as np
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
largura = int(sys.argv[3]) if len(sys.argv) > 3 else 900

im = Image.open(src).convert("RGB")
im = im.resize((largura, round(im.height * largura / im.width)), Image.Resampling.LANCZOS)
a = np.asarray(im, dtype=np.float64) / 255
h, w, _ = a.shape
yy, xx = np.mgrid[0:h, 0:w]
x, y = xx / w, yy / h

# onde ajustar: fora do arranjo (terço de baixo, miolo). Duas passadas: a 2ª tira o que ficou longe da 1ª superfície
# (sombra, flor solta). Não filtrar por "mais escuro": a vinheta do fundo também é mais escura e precisa entrar no ajuste
livre = ~((y > 0.6) & (x > 0.12) & (x < 0.88))
GRAU = 5


def termos(x, y):
    return np.stack([x**i * y**j for i in range(GRAU + 1) for j in range(GRAU + 1 - i)], axis=-1)


def ajusta(livre):
    T = termos(x[livre], y[livre])
    fundo = np.empty_like(a)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(T, a[..., c][livre], rcond=None)
        fundo[..., c] = termos(x, y) @ coef
    return fundo


fundo = ajusta(livre)
livre &= np.abs(a - fundo).max(axis=2) < 0.03
fundo = ajusta(livre)

n = np.clip(a / np.clip(fundo, 0.05, None), 0, None)
# ruído e restinho de vinheta no fundo: tudo que está a 1,5% do branco vira branco
n = np.clip(n / 0.985, 0, 1)
Image.fromarray((n * 255 + 0.5).astype(np.uint8)).save(out, "WEBP", quality=86, method=6)

resto = n[livre]
print(f"{out}: {w}x{h}, fundo -> branco em {100 * (resto > 0.99).mean():.1f}% da área livre")
