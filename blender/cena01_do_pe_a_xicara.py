"""
Torra Serrana — Cena 01, do pé à xícara (frames 1–214), uma tomada contínua:
  1–70    cereja gira -> abre -> grão verde -> torra média
  71–214  o grão vira pó num redemoinho -> cai no cesto (dose) -> tamper compacta ->
          extração num fio sobre a xícara -> o leite desenha a espiral
  --giro N: em vez da sequência, renderiza a xícara final girando 360° em N frames
            (frame 1 do giro == frame 214 da sequência; o site emenda um no outro).
Uso (rodar da raiz do projeto):
  blender -b -P blender/cena01_do_pe_a_xicara.py -- --engine EEVEE --res 1600 --out blender/out/cena01/
  blender -b -P blender/cena01_do_pe_a_xicara.py -- --engine EEVEE --res 1600 --giro 72 --out blender/out/xicara360/
  (teste rápido) ... -- --engine EEVEE --res 480 --samples 24 --frames 70,96,140,180,214 --out blender/test/
Fundo transparente (PNG RGBA): o site controla a cor e permite o "sanduíche" de tipografia.
Ajustes de cor, timing e câmera ficam nos blocos logo abaixo.
"""
import bpy, bmesh, math, sys, argparse, os
import numpy as np
from mathutils import Vector, noise

# ---------- args ----------
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--engine", default="EEVEE")          # EEVEE | CYCLES
p.add_argument("--device", default="GPU")            # GPU | CPU (só Cycles)
p.add_argument("--res", type=int, default=1600)
p.add_argument("--samples", type=int, default=64)
p.add_argument("--out", default="blender/out/cena01/")
p.add_argument("--frames", default="")               # ex: "1,36,70" ou "71-214" (vazio = todos)
p.add_argument("--giro", type=int, default=0)        # >0: giro 360° da xícara final em N frames
p.add_argument("--save", default="")                 # caminho .blend opcional
a = p.parse_args(argv)

# ================= AJUSTES =================
COR = {  # linear
    "cereja": (0.32, 0.012, 0.016),         # carmim maduro (leve azul tira o "tomate")
    "cereja_escura": (0.25, 0.010, 0.014),
    "cereja_clara": (0.42, 0.035, 0.022),
    "umbigo": (0.035, 0.016, 0.008),
    "cabo": (0.06, 0.045, 0.02),
    "polpa": (0.86, 0.72, 0.40),            # mucilagem
    "pele": (0.42, 0.30, 0.17),             # película no sulco do grão
    "po": ((0.030, 0.014, 0.007), (0.085, 0.040, 0.018)),   # pó de torra média (escuro, claro)
    "aco": (0.80, 0.78, 0.75),
    "nogueira": ((0.022, 0.011, 0.005), (0.060, 0.030, 0.014), (0.115, 0.062, 0.030)),
    "ceramica": (0.66, 0.55, 0.42),         # creme da marca: sob a key forte o AgX lava pra branco, então mais quente
    "barro": (0.36, 0.25, 0.16),            # pé da xícara sem esmalte
    "crema": ((0.30, 0.13, 0.045), (0.10, 0.040, 0.013)),   # centro, borda
    "leite": (0.86, 0.78, 0.64),
    "espresso": ((0.030, 0.010, 0.003), (0.15, 0.055, 0.016), (0.36, 0.16, 0.05)),
}
TORRA = [  # (posição na rampa, cor) verde -> palha -> canela -> marrom -> torra média
    (0.00, (0.20, 0.29, 0.13)),
    (0.22, (0.40, 0.34, 0.15)),
    (0.45, (0.33, 0.16, 0.065)),
    (0.72, (0.12, 0.048, 0.02)),
    (1.00, (0.058, 0.024, 0.012)),
]
TEMPO = {
    "gira": (1, 28),       # cereja inteira girando
    "abre": (28, 44),      # metades abrem como concha
    "some": (44, 52),      # metades recuam e somem (alpha), sempre dentro do quadro
    "cresce": (28, 50),    # grão cresce de dentro da cereja
    "torra": (46, 66),     # verde -> torrado (+ expansão)
    "torrado": 70,         # pose final do grão
}
PROC = {
    "solta": (72, 82),     # partículas se soltam da superfície do grão
    "quebra": (73, 84),    # grão encolhe até sumir
    "voo": (20, 30),       # duração do voo de cada partícula (min, max)
    "cesto": (76, 98),     # porta-filtro sobe até o lugar
    "enche": (92, 118),    # monte cresce no cesto
    "tamper": (122, 134, 140, 143, 154),   # entra, encosta, compacta, segura, sai
    "xicara": (148, 166),  # xícara entra por baixo
    "sobe_pf": (152, 166), # porta-filtro sobe pra extração
    "gota": (166, 170),    # gota se forma embaixo do cesto
    "fio": (170, 174),     # frente do fio desce até a xícara
    "corta": (188, 193),   # fio solta do cesto e cai
    "nivel": (172, 192),   # espresso enche
    "sai_pf": (192, 206),  # porta-filtro sai por cima
    "espiral": (196, 212), # leite sobe e desenha a espiral
    "fim": 214,
}
CAMERA = {"lente": 85, "ini": (0.0, -9.5, 2.3), "fim": (0.5, -6.9, 1.4), "alvo": (0, 0, 0.05)}
# planos depois da torra: (frame, alvo x, y, z, azimute°, elevação°, distância). Entre um e outro a câmera
# faz arco com smootherstep (sai e chega parada: o scroll nunca dá tranco).
PLANOS = [
    (100, -0.40, 0.0, -0.50, 5, 31, 13.4),   # moagem/dose: de cima, vê dentro do cesto
    (150, -0.40, 0.0, -0.58, 3, 28, 12.4),   # compactação: aproxima devagar
    (172, -0.35, 0.0, -1.20, 5, 5, 16.8),    # extração: de lado, fio inteiro no quadro
    (190, -0.30, 0.0, -1.30, 2, 6, 16.4),
    (210, 0.00, 0.0, -2.40, 0, 30, 15.2),    # xícara: 30° de cima, pra espiral aparecer
]
GRAO_POSE = (math.radians(90), math.radians(24), math.radians(32))   # pose final: sulco pra câmera, diagonal
GRAO_GIRO = math.radians(-320)                                       # quanto gira (eixo Z) até a pose final
PF_DIR = math.radians(122)        # cabo do porta-filtro: pra trás e pra esquerda (encurta no quadro)
ALCA_DIR = math.radians(-32)      # asa da xícara: lado direito, um pouco virada pra câmera
XIC_ESC = 1.15
N_PO = 2200                       # partículas de pó
# ===========================================

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
T0, FIM = TEMPO["torrado"], PROC["fim"]
sc.frame_start, sc.frame_end = 1, FIM
sc.render.fps = 30

def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)

def sms(f, e0, e1):                 # smootherstep: começa e termina com velocidade zero
    t = max(0.0, min(1.0, (f - e0) / (e1 - e0)))
    return t * t * t * (t * (6 * t - 15) + 10)

def lerp(x, y, t): return x + (y - x) * t

def faixa(f, pontos):
    """[(frame, valor ou tupla), ...] -> valor em f, smootherstep entre pontos."""
    if f <= pontos[0][0]: return pontos[0][1]
    for (f0, v0), (f1, v1) in zip(pontos, pontos[1:]):
        if f <= f1:
            t = sms(f, f0, f1)
            return tuple(lerp(x, y, t) for x, y in zip(v0, v1)) if isinstance(v0, tuple) else lerp(v0, v1, t)
    return pontos[-1][1]

def shade_smooth(o, levels=1):
    o.data.shade_smooth()
    if levels:
        s = o.modifiers.new("sub", "SUBSURF"); s.levels = s.render_levels = levels

def key(target, path, frame, value):
    setattr(target, path, value); target.keyframe_insert(path, frame=frame)

def key_socket(sock, frame, value):
    sock.default_value = value; sock.keyframe_insert("default_value", frame=frame)

def por_frame(target, path, fn, f0=1, f1=FIM):
    """keyframe em todo frame (valores exatos nos inteiros, que são os únicos renderizados)"""
    for f in range(f0, f1 + 1):
        setattr(target, path, fn(f)); target.keyframe_insert(path, frame=f)

def visivel(o, ini, fim):
    por_frame(o, "hide_render", lambda f: not (ini <= f <= fim))

# ---------- nós ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True                       # obrigatório < 5.0, deprecated depois
    except Exception: pass
    return m, m.node_tree, m.node_tree.nodes["Principled BSDF"]

def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items(): n.inputs[k].default_value = v
    return n

def link(nt, a, b): nt.links.new(a, b)

def plug(nt, v, sock):
    if isinstance(v, bpy.types.NodeSocket): link(nt, v, sock)
    else: sock.default_value = v

def mix_rgb(nt, fac, a, b, blend="MIX"):
    n = nt.nodes.new("ShaderNodeMix"); n.data_type = "RGBA"; n.blend_type = blend
    for i, v in ((0, fac), (6, a), (7, b)):
        if isinstance(v, bpy.types.NodeSocket): link(nt, v, n.inputs[i])
        else: n.inputs[i].default_value = (*v, 1) if i else v
    return n.outputs[2]

def ramp(nt, fac, stops):
    n = nt.nodes.new("ShaderNodeValToRGB"); cr = n.color_ramp
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, col in stops[1:-1]: cr.elements.new(pos).color = (*col, 1)
    link(nt, fac, n.inputs["Fac"])
    return n.outputs["Color"]

def map_range(nt, src, lo, hi):
    n = node(nt, "ShaderNodeMapRange", **{"To Min": lo, "To Max": hi}); link(nt, src, n.inputs["Value"])
    return n.outputs["Result"]

def faixa_suave(nt, src, de0, de1, para0=0.0, para1=1.0):
    """map range com smoothstep; limites podem ser sockets"""
    n = nt.nodes.new("ShaderNodeMapRange"); n.interpolation_type = "SMOOTHSTEP"
    link(nt, src, n.inputs["Value"])
    for k, v in (("From Min", de0), ("From Max", de1), ("To Min", para0), ("To Max", para1)): plug(nt, v, n.inputs[k])
    return n.outputs["Result"]

def op(nt, kind, x, y=None):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = kind
    plug(nt, x, n.inputs[0])
    if y is not None: plug(nt, y, n.inputs[1])
    return n.outputs[0]

def obj_noise(nt, scale, detail=4.0, rough=0.5):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = node(nt, "ShaderNodeTexNoise", Scale=scale, Detail=detail, Roughness=rough)
    link(nt, tc.outputs["Object"], n.inputs["Vector"])
    return n.outputs["Fac"]

def bump_chain(nt, bsdf, layers):      # [(escala, força, distância), ...]
    prev = None
    for scale, strength, dist in layers:
        b = node(nt, "ShaderNodeBump", Strength=strength, Distance=dist)
        link(nt, obj_noise(nt, scale, 6, 0.6), b.inputs["Height"])
        if prev: link(nt, prev, b.inputs["Normal"])
        prev = b.outputs["Normal"]
    link(nt, prev, bsdf.inputs["Normal"])
    return prev

def attr(nt, name):
    n = nt.nodes.new("ShaderNodeAttribute"); n.attribute_name = name
    return n.outputs["Fac"]

def set_attr(mesh, name, values):
    at = mesh.attributes.new(name, "FLOAT", "POINT"); at.data.foreach_set("value", values)

def obj_coords(nt):
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    link(nt, nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], sep.inputs[0])
    return sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]

# ---------- materiais ----------
def mat_cereja():
    m, nt, b = new_mat("Cereja")
    cor = ramp(nt, obj_noise(nt, 2.0, 2, 0.4), [(0.38, COR["cereja_escura"]), (0.50, COR["cereja"]), (0.66, COR["cereja_clara"])])
    cor = mix_rgb(nt, map_range(nt, attr(nt, "umbigo"), 0, 1), cor, COR["umbigo"])
    link(nt, cor, b.inputs["Base Color"])
    link(nt, map_range(nt, attr(nt, "umbigo"), 0.34, 0.85), b.inputs["Roughness"])
    for k, v in {"Coat Weight": 0.55, "Coat Roughness": 0.07, "Subsurface Weight": 0.22,
                 "Subsurface Radius": (1.0, 0.22, 0.12), "Subsurface Scale": 0.08}.items():
        b.inputs[k].default_value = v
    bump_chain(nt, b, [(3.5, 0.05, 0.05), (70, 0.035, 0.01)])
    return m

def mat_polpa():
    m, nt, b = new_mat("Polpa")
    link(nt, ramp(nt, obj_noise(nt, 5, 3), [(0.35, tuple(c * 0.75 for c in COR["polpa"])), (0.7, COR["polpa"])]), b.inputs["Base Color"])
    for k, v in {"Roughness": 0.22, "Coat Weight": 0.4, "Coat Roughness": 0.05, "Subsurface Weight": 0.5,
                 "Subsurface Radius": (1.0, 0.7, 0.35), "Subsurface Scale": 0.1}.items():
        b.inputs[k].default_value = v
    bump_chain(nt, b, [(9, 0.12, 0.03)])
    return m

def mat_cabo():
    m, nt, b = new_mat("Cabo")
    link(nt, ramp(nt, obj_noise(nt, 20, 4), [(0.3, tuple(c * 0.6 for c in COR["cabo"])), (0.7, COR["cabo"])]), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.65
    return m

def mat_grao():
    m, nt, b = new_mat("GraoTorra")
    torra = node(nt, "ShaderNodeValue"); torra.label = "torra"
    t = torra.outputs[0]
    cor = ramp(nt, t, TORRA)
    mancha = ramp(nt, obj_noise(nt, 7, 5, 0.6), [(0.3, (0.70,) * 3), (0.7, (1.15,) * 3)])
    cor = mix_rgb(nt, 1.0, cor, mancha, "MULTIPLY")
    cor = mix_rgb(nt, map_range(nt, attr(nt, "sulco"), 0, 0.85), cor, COR["pele"])
    link(nt, cor, b.inputs["Base Color"])
    link(nt, map_range(nt, t, 0.62, 0.36), b.inputs["Roughness"])
    link(nt, map_range(nt, t, 0.0, 0.28), b.inputs["Coat Weight"])
    link(nt, map_range(nt, t, 0.18, 0.0), b.inputs["Subsurface Weight"])
    b.inputs["Coat Roughness"].default_value = 0.2
    b.inputs["Subsurface Radius"].default_value = (0.8, 0.9, 0.5)
    b.inputs["Subsurface Scale"].default_value = 0.05
    bump_chain(nt, b, [(22, 0.12, 0.02), (180, 0.08, 0.003)])
    return m, t

def mat_aco():
    m, nt, b = new_mat("Aco")
    b.inputs["Base Color"].default_value = (*COR["aco"], 1)
    b.inputs["Metallic"].default_value = 1.0
    link(nt, map_range(nt, obj_noise(nt, 6, 3), 0.14, 0.26), b.inputs["Roughness"])
    bump_chain(nt, b, [(260, 0.03, 0.002)])
    return m

def mat_nogueira():
    m, nt, b = new_mat("Nogueira")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    w = node(nt, "ShaderNodeTexWave", Scale=2.2, Distortion=7.0, Detail=4.0)
    w.wave_type = "BANDS"; w.bands_direction = "X"
    link(nt, tc.outputs["Object"], w.inputs["Vector"])
    escura, media, clara = COR["nogueira"]
    veio = ramp(nt, w.outputs["Fac"], [(0.15, escura), (0.55, media), (0.95, clara)])
    link(nt, mix_rgb(nt, 1.0, veio, ramp(nt, obj_noise(nt, 30, 4), [(0.3, (0.8,) * 3), (0.7, (1.1,) * 3)]), "MULTIPLY"), b.inputs["Base Color"])
    for k, v in {"Roughness": 0.42, "Coat Weight": 0.35, "Coat Roughness": 0.18}.items():
        b.inputs[k].default_value = v
    bump_chain(nt, b, [(120, 0.05, 0.004)])
    return m

def mat_po_monte():
    """monte/pastilha no cesto; força do relevo cai quando o tamper alisa (chaveada por frame)"""
    m, nt, b = new_mat("PoMonte")
    escuro, claro = COR["po"]
    link(nt, ramp(nt, obj_noise(nt, 45, 5, 0.7), [(0.3, escuro), (0.75, claro)]), b.inputs["Base Color"])
    rough = node(nt, "ShaderNodeValue"); rough.outputs[0].default_value = 0.78
    link(nt, rough.outputs[0], b.inputs["Roughness"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 70
    link(nt, nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], vor.inputs["Vector"])
    b1 = node(nt, "ShaderNodeBump", Strength=0.9, Distance=0.02); link(nt, vor.outputs["Distance"], b1.inputs["Height"])
    b2 = node(nt, "ShaderNodeBump", Strength=0.5, Distance=0.004); link(nt, obj_noise(nt, 280, 4), b2.inputs["Height"])
    link(nt, b1.outputs["Normal"], b2.inputs["Normal"]); link(nt, b2.outputs["Normal"], b.inputs["Normal"])
    return m, b1.inputs["Strength"], rough.outputs[0]

def mat_fragmento():
    m, nt, b = new_mat("PoFragmento")
    escuro, claro = COR["po"]
    link(nt, ramp(nt, attr(nt, "var"), [(0.0, escuro), (1.0, claro)]), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    return m

def mat_ceramica():
    m, nt, b = new_mat("Ceramica")
    _, _, z = obj_coords(nt)
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 38
    link(nt, nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], vor.inputs["Vector"])
    pinta = op(nt, "MULTIPLY", faixa_suave(nt, vor.outputs["Distance"], 0.035, 0.06, 1.0, 0.0),
               faixa_suave(nt, obj_noise(nt, 4, 2), 0.45, 0.6))             # stoneware salpicado, em manchas
    cor = mix_rgb(nt, op(nt, "MULTIPLY", pinta, 0.85), COR["ceramica"], (0.06, 0.035, 0.02))
    cru = faixa_suave(nt, z, 0.05, 0.02)                                     # pé sem esmalte
    link(nt, mix_rgb(nt, cru, cor, COR["barro"]), b.inputs["Base Color"])
    link(nt, map_range(nt, cru, 0.16, 0.8), b.inputs["Roughness"])
    link(nt, map_range(nt, cru, 0.45, 0.0), b.inputs["Coat Weight"])
    b.inputs["Coat Roughness"].default_value = 0.05
    bump_chain(nt, b, [(18, 0.03, 0.01)])
    return m

def mat_espresso():
    m, nt, b = new_mat("Espresso")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (9, 9, 1.6)
    link(nt, tc.outputs["Object"], mp.inputs["Vector"])
    fluxo = mp.inputs["Location"]                                            # z chaveado: listras descem
    n = node(nt, "ShaderNodeTexNoise", Scale=1.0, Detail=3.0, Roughness=0.55); link(nt, mp.outputs["Vector"], n.inputs["Vector"])
    e0, e1, e2 = COR["espresso"]
    cor = ramp(nt, n.outputs["Fac"], [(0.3, e0), (0.55, e1), (0.78, e2)])
    link(nt, cor, b.inputs["Base Color"]); link(nt, cor, b.inputs["Emission Color"])
    for k, v in {"Roughness": 0.05, "Coat Weight": 0.6, "Coat Roughness": 0.02, "Emission Strength": 0.55}.items():
        b.inputs[k].default_value = v
    return m, fluxo

def mat_liquido(passo=0.215, raio_arte=0.9):
    """crema + espiral de leite. Espiral de Arquimedes em coordenadas polares; o raio revelado é chaveado."""
    m, nt, b = new_mat("Liquido")
    x, y, _ = obj_coords(nt)
    r = op(nt, "SQRT", op(nt, "ADD", op(nt, "MULTIPLY", x, x), op(nt, "MULTIPLY", y, y)))
    th = op(nt, "ARCTAN2", y, x)
    rn = op(nt, "ADD", r, op(nt, "MULTIPLY", op(nt, "SUBTRACT", obj_noise(nt, 1.8, 3), 0.5), 0.13))   # traço de mão, não de compasso
    t = op(nt, "SUBTRACT", op(nt, "DIVIDE", rn, passo), op(nt, "DIVIDE", th, 2 * math.pi))
    d = op(nt, "ABSOLUTE", op(nt, "SUBTRACT", op(nt, "FRACT", t), 0.5))
    linha = faixa_suave(nt, d, 0.08, 0.17, 1.0, 0.0)
    centro = faixa_suave(nt, r, 0.05, 0.10, 1.0, 0.0)
    rev = node(nt, "ShaderNodeValue"); rev.label = "revela"
    revela = faixa_suave(nt, r, op(nt, "SUBTRACT", rev.outputs[0], 0.08), rev.outputs[0], 1.0, 0.0)
    borda = faixa_suave(nt, r, raio_arte - 0.1, raio_arte, 1.0, 0.0)
    leite = op(nt, "MULTIPLY", op(nt, "MULTIPLY", op(nt, "MAXIMUM", linha, centro), revela), borda)
    centro_c, borda_c = COR["crema"]
    mancha = op(nt, "ADD", op(nt, "MULTIPLY", r, 0.9), op(nt, "MULTIPLY", obj_noise(nt, 9, 4, 0.6), 0.45))
    crema = ramp(nt, mancha, [(0.25, centro_c), (1.15, borda_c)])
    link(nt, mix_rgb(nt, leite, crema, COR["leite"]), b.inputs["Base Color"])
    link(nt, map_range(nt, leite, 0.2, 0.38), b.inputs["Roughness"])
    b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Coat Roughness"].default_value = 0.08
    bump_chain(nt, b, [(60, 0.04, 0.005)])
    return m, rev.outputs[0]

def fade(mats, f0, f1):
    for m in mats:
        al = m.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
        key_socket(al, f0, 1.0); key_socket(al, f1, 0.0)

# ---------- geometria ----------
def novo(name, me):
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o

def lathe(name, perfil, seg=128, fechar=False):
    """gira o perfil [(r, z), ...] em torno do eixo Z; pontos com r=0 viram polo"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    aneis = []
    for r, z in perfil:
        if r < 1e-6: aneis.append([bm.verts.new((0, 0, z))])
        else: aneis.append([bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)])
    pares = list(zip(aneis, aneis[1:])) + ([(aneis[-1], aneis[0])] if fechar else [])
    for A, B in pares:
        for k in range(seg):
            q = list(dict.fromkeys([A[k % len(A)], A[(k + 1) % len(A)], B[(k + 1) % len(B)], B[k % len(B)]]))
            if len(q) >= 3: bm.faces.new(q)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    return novo(name, me)

def make_bean(name="Grao"):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=160, v_segments=96, radius=1)
    sulco = []
    for v in bm.verts:
        x, y, z = v.co.x, v.co.z, -v.co.y          # polos nas pontas do grão (eixo Y)
        x *= 0.70; z *= 0.56
        if z > 0: z *= 0.42                       # face plana
        cx = 0.035 * math.sin(y * 2.6)            # sulco levemente em S
        g = math.exp(-((x - cx) ** 2) / (2 * 0.026 ** 2))
        taper = max(0.0, 1 - abs(y) ** 2.4)
        on_flat = smoothstep(-0.02, 0.10, z)
        z -= 0.13 * g * taper * on_flat
        lip = math.exp(-((abs(x - cx) - 0.065) ** 2) / (2 * 0.02 ** 2))
        z += 0.012 * lip * taper * on_flat        # bordas do sulco levemente salientes
        co = Vector((x, y, z))
        co += co.normalized() * 0.018 * noise.noise(co * 2.2)   # assimetria orgânica
        v.co = co
        sulco.append(g * taper * on_flat)
    bm.to_mesh(me); bm.free()
    set_attr(me, "sulco", sulco)
    o = novo(name, me)
    shade_smooth(o, 1)
    return o

def cherry_mesh(name, keep=0):
    """keep=0: cereja inteira. keep=±1: só a metade x>0 / x<0, com polos no eixo X
    pra que o corte caia exatamente no anel do equador (borda limpa, sem serrilhado)."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=128, v_segments=128, radius=1)
    umbigo = []
    for v in bm.verts:
        x, y, z = (v.co.z, v.co.y, -v.co.x) if keep else v.co
        r = math.hypot(x, y)
        if z < 0:                                  # umbigo (cicatriz da flor) embaixo
            z += 0.07 * max(0.0, 1 - (r / 0.15) ** 2)
            z -= 0.014 * math.exp(-((r - 0.16) / 0.03) ** 2)
            umbigo.append(max(0.0, 1 - r / 0.17) ** 0.6)
        else:                                      # encaixe do cabo em cima
            z -= 0.035 * max(0.0, 1 - (r / 0.11) ** 2)
            umbigo.append(0.0)
        co = Vector((x * 0.94, y * 0.94, z * 1.08))
        co += co.normalized() * 0.012 * noise.noise(co * 1.7)
        v.co = co
    lay = bm.verts.layers.float.new("umbigo")
    for v, u in zip(bm.verts, umbigo): v[lay] = u
    if keep:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x * keep < -1e-5], context="VERTS")
    bm.to_mesh(me); bm.free()
    return me

def half(sign, name, mats):
    me = cherry_mesh(name, keep=sign)
    o = novo(name, me)
    sol = o.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.21; sol.offset = -1   # polpa grossa (casca fina parece ovo de brinquedo)
    sol.use_rim = True; sol.material_offset = 1; sol.material_offset_rim = 1
    for m in mats: me.materials.append(m)
    shade_smooth(o, 1)
    return o

def make_stem(parent, mat):          # pedúnculo curto (cabo comprido lembra maçã)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.055, depth=0.13, location=(0, 0, 1.08 - 0.035 + 0.045))
    o = bpy.context.object; o.name = "Cabo"
    for v in o.data.vertices:
        if v.co.z > 0: v.co.x *= 0.75; v.co.y *= 0.75
    o.rotation_euler = (math.radians(6), math.radians(-5), 0)
    bev = o.modifiers.new("bev", "BEVEL"); bev.width = 0.012; bev.segments = 3
    o.data.materials.append(mat); shade_smooth(o, 1)
    o.parent = parent
    return o

# ================= CENA 1–70: cereja -> grão -> torra =================
m_cereja, m_polpa, m_cabo = mat_cereja(), mat_polpa(), mat_cabo()
m_grao, torra = mat_grao()

piv = bpy.data.objects.new("CerejaPivo", None); sc.collection.objects.link(piv)
piv.rotation_mode = "ZXY"                    # gira no próprio eixo, depois inclina (umbigo fica à vista)
inteira = novo("CerejaInteira", cherry_mesh("CerejaInteira"))
inteira.data.materials.append(m_cereja); shade_smooth(inteira, 1)
hl = half(-1, "CerejaE", (m_cereja, m_polpa))
hr = half(1, "CerejaD", (m_cereja, m_polpa))
for o in (inteira, hl, hr): o.parent = piv
cabo = make_stem(hr, m_cabo)

bean = make_bean(); bean.data.materials.append(m_grao)

g0, g1 = TEMPO["gira"]; a0, a1 = TEMPO["abre"]; s0, s1 = TEMPO["some"]
key(piv, "rotation_euler", g0, (math.radians(-32), math.radians(6), 0))
key(piv, "rotation_euler", (g0 + a0) // 2, (math.radians(-22), math.radians(-6), math.radians(90)))
key(piv, "rotation_euler", a0, (math.radians(-14), math.radians(0), math.radians(180)))   # corte de frente pra câmera
key(piv, "location", g0, (0, 0, -0.22)); key(piv, "location", a0, (0, 0, 0))              # sobe e cresce: o scroll
key(piv, "scale", g0, (0.84,) * 3); key(piv, "scale", a0, (1, 1, 1))                      # sempre tem resposta visível

# deslocamentos pensados no espaço da câmera (x = tela, +y = pra longe) e convertidos pro espaço do pivô
sc.frame_set(a0)
to_local = piv.matrix_world.to_3x3().inverted()
def offset(x, y, z): return tuple(to_local @ Vector((x, y, z)))

# inteira até abrir, depois troca pelas metades (sem emenda visível antes)
key(inteira, "hide_render", a0 - 1, False); key(inteira, "hide_render", a0, True)
for h, s in ((hl, -1), (hr, 1)):
    lado = 1 if (piv.matrix_world.to_3x3() @ Vector((s, 0, 0))).x > 0 else -1   # lado da metade na tela
    abre = lambda deg: (0, 0, math.radians(lado * deg))        # porta abrindo: interior vira pra câmera
    key(h, "hide_render", a0 - 1, True); key(h, "hide_render", a0, False); key(h, "hide_render", s1 + 1, True)
    key(h, "location", a0, (0, 0, 0)); key(h, "rotation_euler", a0, (0, 0, 0))
    key(h, "location", a1, offset(lado * 0.6, 0.7, -0.05)); key(h, "rotation_euler", a1, abre(48))
    key(h, "location", s1, offset(lado * 0.75, 2.8, -0.35)); key(h, "rotation_euler", s1, abre(75))
    key(h, "scale", a1, (1, 1, 1)); key(h, "scale", s1, (0.7,) * 3)
key(cabo, "hide_render", s1, False); key(cabo, "hide_render", s1 + 1, True)
fade((m_cereja, m_polpa, m_cabo), s0, s1)

c0, c1 = TEMPO["cresce"]; t0, t1 = TEMPO["torra"]
key(bean, "scale", c0, (0.42,) * 3); key(bean, "scale", c1, (0.80,) * 3); key(bean, "scale", t1, (0.90,) * 3)  # expansão na torra
key_socket(torra, t0, 0.0); key_socket(torra, t1, 1.0)
rx, ry, rz = GRAO_POSE
key(bean, "rotation_euler", c0, (rx, ry, rz + GRAO_GIRO)); key(bean, "rotation_euler", T0, GRAO_POSE)
key(bean, "location", a1, (0, 0, 0)); key(bean, "location", T0, (0, 0, 0.1))

# ---------- câmera ----------
cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = CAMERA["lente"]
cam = novo("Cam", cam_data); sc.camera = cam
tgt = bpy.data.objects.new("Alvo", None); sc.collection.objects.link(tgt); tgt.location = CAMERA["alvo"]
tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
key(cam, "location", 1, CAMERA["ini"]); key(cam, "location", T0, CAMERA["fim"])

# ---------- luz (still de produto: key suave, dois recortes quentes pro fundo café) ----------
rig = bpy.data.objects.new("LuzRig", None); sc.collection.objects.link(rig)   # acompanha o alvo depois da torra
def area(name, loc, energy, shape, size, size_y, color):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.shape = shape
    d.size = size; d.size_y = size_y; d.color = color
    o = novo(name, d); o.location = loc; o.parent = rig
    c = o.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"
area("Key", (-4.2, -4.8, 4.4), 760, "ELLIPSE", 3.2, 3.2, (1.0, 0.92, 0.82))
area("RimD", (3.6, 3.4, 1.8), 1100, "RECTANGLE", 0.6, 4.0, (1.0, 0.76, 0.52))
area("RimE", (-3.6, 3.0, 1.2), 520, "RECTANGLE", 0.5, 3.5, (1.0, 0.88, 0.76))
area("Fill", (2.5, -5.5, -0.8), 70, "ELLIPSE", 5, 5, (0.92, 0.95, 1.0))

w = bpy.data.worlds.new("W"); sc.world = w
try: w.use_nodes = True
except Exception: pass
wn = w.node_tree
sep = wn.nodes.new("ShaderNodeSeparateXYZ")          # céu claro em cima, escuro embaixo (reflexo mais fotográfico)
link(wn, wn.nodes.new("ShaderNodeTexCoord").outputs["Generated"], sep.inputs["Vector"])
link(wn, ramp(wn, sep.outputs["Z"], [(0.35, (0.02, 0.014, 0.01)), (0.75, (0.5, 0.42, 0.34))]), wn.nodes["Background"].inputs["Color"])
wn.nodes["Background"].inputs["Strength"].default_value = 0.4

# ================= CENA 71–214: moagem -> dose -> compactação -> extração -> xícara =================
# Tudo é função do frame. Transforms viram keyframe em todo frame; as malhas que mudam de forma
# (pó, monte, fio, líquido) são reescritas em atualiza(f) antes de cada render.

# câmera: amostra a curva original 1–70 e chaveia todo frame (as chaves novas não mexem no trecho já renderizado)
cx, cy, cz = (c - o for c, o in zip(CAMERA["fim"], CAMERA["alvo"]))
d0 = math.sqrt(cx * cx + cy * cy + cz * cz)
planos = [(T0, (*CAMERA["alvo"], math.degrees(math.atan2(cx, -cy)), math.degrees(math.asin(cz / d0)), d0))]
planos += [(f, tuple(v)) for f, *v in PLANOS] + [(FIM, tuple(PLANOS[-1][1:]))]

def camera_em(f):
    ax, ay, az, azim, elev, dist = faixa(f, planos)
    A, E = math.radians(azim), math.radians(elev)
    return (ax, ay, az), (ax + dist * math.sin(A) * math.cos(E), ay - dist * math.cos(A) * math.cos(E), az + dist * math.sin(E))

antes = {}
for f in range(1, T0 + 1):
    sc.frame_set(f); antes[f] = tuple(cam.location)
por_frame(cam, "location", lambda f: antes[f] if f <= T0 else camera_em(f)[1])
por_frame(tgt, "location", lambda f: CAMERA["alvo"] if f <= T0 else camera_em(f)[0])
por_frame(rig, "location", lambda f: (0, 0, 0) if f <= T0 else (0, 0, camera_em(f)[0][2] - CAMERA["alvo"][2]))

# grão: encolhe em torno do centro enquanto vira pó (pai novo, transform idêntico até a quebra)
sc.frame_set(T0)
quebra = bpy.data.objects.new("GraoQuebra", None); sc.collection.objects.link(quebra)
quebra.location = bean.matrix_world.translation.copy()
bpy.context.view_layer.update()
bean.parent = quebra; bean.matrix_parent_inverse = quebra.matrix_world.inverted()
encolhe = lambda f: 1 - sms(f, *PROC["quebra"])
por_frame(quebra, "scale", lambda f: (max(encolhe(f), 1e-3),) * 3)
visivel(bean, 1, PROC["quebra"][1])

m_aco, m_nog, m_frag, m_cer = mat_aco(), mat_nogueira(), mat_fragmento(), mat_ceramica()
m_monte, relevo_monte, rough_monte = mat_po_monte()
m_esp, fluxo_esp = mat_espresso()
m_liq, revela = mat_liquido()

# ---------- porta-filtro (sem fundo, "naked") ----------
pf = bpy.data.objects.new("PortaFiltro", None); sc.collection.objects.link(pf)
CESTO = [(0, -1.0), (1.22, -1.0), (1.31, -0.975), (1.355, -0.92), (1.47, -0.08), (1.60, -0.05), (1.625, -0.02),
         (1.61, 0.01), (1.45, 0.01), (1.425, -0.03), (1.315, -0.90), (1.28, -0.935), (1.20, -0.955), (0, -0.955)]
ANEL = [(1.47, 0.035), (1.82, 0.035), (1.87, 0.0), (1.88, -0.25), (1.82, -0.40), (1.70, -0.47), (1.52, -0.47), (1.47, -0.43)]
cesto = lathe("Cesto", CESTO); anel = lathe("Anel", ANEL, fechar=True)
pecas_pf = [cesto, anel]
eixo_cabo = (0, math.radians(98), PF_DIR)             # eixo local Z -> direção do cabo, 8° pra baixo
dir_cabo = Vector((math.sin(math.radians(98)) * math.cos(PF_DIR), math.sin(math.radians(98)) * math.sin(PF_DIR), math.cos(math.radians(98))))
pescoco = lathe("Pescoco", [(0, 0), (0.24, 0), (0.24, 0.05), (0.2, 0.15), (0.19, 0.85), (0.22, 0.9), (0.22, 0.95), (0, 0.95)], seg=48)
pescoco.location = Vector((math.cos(PF_DIR) * 1.7, math.sin(PF_DIR) * 1.7, -0.22)); pescoco.rotation_euler = eixo_cabo
punho = lathe("Punho", [(0, 0), (0.25, 0), (0.28, 0.06), (0.31, 0.3), (0.355, 0.9), (0.37, 1.45), (0.35, 1.85),
                         (0.29, 2.02), (0.16, 2.1), (0, 2.12)], seg=64)
punho.location = pescoco.location + dir_cabo * 0.92; punho.rotation_euler = eixo_cabo
pecas_pf += [pescoco, punho]
for o in pecas_pf:
    o.parent = pf
    (o.data.materials.append(m_nog if o is punho else m_aco))
    shade_smooth(o, 1)

def z_aro(f):
    c0_, c1_ = PROC["cesto"]; e0_, e1_ = PROC["sobe_pf"]; x0_, x1_ = PROC["sai_pf"]
    return faixa(f, [(c0_, -5.2), (c1_, -0.5), (e0_, -0.5), (e1_, 1.05), (x0_, 1.05), (x1_, 7.5)])
por_frame(pf, "location", lambda f: (0, 0, z_aro(f)))
por_frame(pf, "rotation_euler", lambda f: (0, 0, faixa(f, [(PROC["cesto"][0], -0.5), (PROC["cesto"][1], 0.0),
                                                         (PROC["sobe_pf"][0], 0.0), (PROC["sobe_pf"][1], 0.6)])))
for o in pecas_pf: visivel(o, PROC["cesto"][0], PROC["sai_pf"][1])

# ---------- monte de pó / pastilha (no espaço do cesto: aro em z=0) ----------
Z_FUNDO, Z_PUCK = -0.955, -0.33
def r_parede(z): return np.interp(z, [-0.93, -0.04], [1.28, 1.42])
tp = PROC["tamper"]
def z_tamper(f):          # base do tamper no espaço do cesto
    return faixa(f, [(tp[0], 4.8), (tp[1], 0.2), (tp[2], Z_PUCK), (tp[3], Z_PUCK), (tp[4], 4.8)])

def monte(rho, f):
    """altura da superfície do pó (espaço do cesto) no raio rho; também devolve o raio da borda"""
    fill = sms(f, *PROC["enche"]); press = sms(f, tp[1], tp[2])
    zw = Z_FUNDO + 0.02 + 0.52 * fill
    R = float(r_parede(lerp(zw, Z_PUCK, press))) - 0.004
    dome = 0.6 * fill ** 1.3 * np.clip(1 - (np.asarray(rho) / R) ** 2, 0, 1) ** 1.2
    z = (zw + dome) * (1 - press) + Z_PUCK * press
    if tp[0] <= f <= tp[4]: z = np.minimum(z, z_tamper(f))
    return z, R

KM, SM = 40, 96
ang_m = np.linspace(0, 2 * math.pi, SM, endpoint=False)
faces = [(0, 1 + j, 1 + (j + 1) % SM) for j in range(SM)]
faces += [(1 + k * SM + j, 1 + (k + 1) * SM + j, 1 + (k + 1) * SM + (j + 1) % SM, 1 + k * SM + (j + 1) % SM)
          for k in range(KM - 1) for j in range(SM)]
me = bpy.data.meshes.new("Monte"); me.from_pydata([(0, 0, 0)] * (1 + KM * SM), [], faces); me.update()
monte_o = novo("Monte", me); monte_o.parent = pf; me.materials.append(m_monte); me.shade_smooth()
visivel(monte_o, PROC["enche"][0] + 1, PROC["sai_pf"][1])
por_frame_socket = lambda sock, fn: [key_socket(sock, f, fn(f)) for f in range(T0, FIM + 1)]
por_frame_socket(relevo_monte, lambda f: lerp(0.9, 0.22, sms(f, tp[1], tp[2])))   # tamper alisa
por_frame_socket(rough_monte, lambda f: lerp(0.8, 0.55, sms(f, tp[1], tp[2])))

def atualiza_monte(f):
    z_c, R = monte(0.0, f)
    rho = R * np.arange(1, KM + 1) / KM
    z, _ = monte(rho, f)
    co = np.zeros((1 + KM * SM, 3))
    co[0] = (0, 0, float(np.atleast_1d(z_c)[0]))
    co[1:, 0] = (rho[:, None] * np.cos(ang_m)[None]).ravel()
    co[1:, 1] = (rho[:, None] * np.sin(ang_m)[None]).ravel()
    co[1:, 2] = np.repeat(z, SM)
    me = monte_o.data; me.vertices.foreach_set("co", co.ravel()); me.update()

# ---------- tamper ----------
tamper = bpy.data.objects.new("Tamper", None); sc.collection.objects.link(tamper)
t_aco = lathe("TamperBase", [(0, 0), (1.36, 0), (1.385, 0.02), (1.39, 0.06), (1.39, 0.28), (1.36, 0.32), (0.40, 0.34),
                              (0.30, 0.40), (0.26, 0.55), (0.26, 0.72), (0, 0.72)])
t_cabo = lathe("TamperCabo", [(0, 0.70), (0.36, 0.70), (0.42, 0.78), (0.40, 1.05), (0.34, 1.35), (0.42, 1.7), (0.56, 2.05),
                               (0.60, 2.25), (0.52, 2.45), (0.30, 2.57), (0, 2.60)], seg=64)
for o, m in ((t_aco, m_aco), (t_cabo, m_nog)):
    o.parent = tamper; o.data.materials.append(m); shade_smooth(o, 1); visivel(o, tp[0], tp[4])
por_frame(tamper, "location", lambda f: (0, 0, z_aro(f) + z_tamper(f)))
por_frame(tamper, "rotation_euler", lambda f: (0, 0, faixa(f, [(tp[1], 0.0), (tp[3], 0.45)])))

# ---------- xícara + pires (grupo gira no --giro) ----------
xic = bpy.data.objects.new("Xicara", None); sc.collection.objects.link(xic); xic.scale = (XIC_ESC,) * 3
XICARA = [(0, 0.005), (0.46, 0.005), (0.50, 0.0), (0.56, 0.0), (0.585, 0.02), (0.60, 0.06), (0.62, 0.075), (0.80, 0.16),
          (0.98, 0.30), (1.10, 0.48), (1.18, 0.70), (1.225, 0.92), (1.245, 1.08), (1.245, 1.11), (1.23, 1.125),
          (1.21, 1.115), (1.19, 1.0), (1.15, 0.80), (1.07, 0.58), (0.93, 0.38), (0.72, 0.21), (0.45, 0.135), (0.0, 0.12)]
INTERNO = XICARA[15:][::-1]           # (r, z) da parede de dentro, z crescente
PIRES = [(0, 0.02), (0.80, 0.02), (0.84, 0.0), (0.95, 0.0), (0.99, 0.03), (1.30, 0.08), (1.70, 0.15), (1.98, 0.24),
         (2.06, 0.29), (2.065, 0.31), (2.04, 0.32), (1.95, 0.29), (1.65, 0.20), (1.25, 0.13), (0.80, 0.10),
         (0.66, 0.08), (0.62, 0.07), (0, 0.07)]
Z_XIC = 0.07                          # xícara apoiada no fundo do pires
pires = lathe("Pires", PIRES); xicara = lathe("XicaraCorpo", XICARA); xicara.location = (0, 0, Z_XIC)
for o in (pires, xicara): o.data.materials.append(m_cer); shade_smooth(o, 2)
cu = bpy.data.curves.new("Asa", "CURVE"); cu.dimensions = "3D"
cu.bevel_depth = 0.07; cu.bevel_resolution = 6; cu.resolution_u = 24
sp = cu.splines.new("BEZIER"); pts = [(1.20, 0.93), (1.55, 0.97), (1.78, 0.80), (1.74, 0.52), (1.45, 0.36), (1.04, 0.42)]
sp.bezier_points.add(len(pts) - 1)
for bp, (x, z) in zip(sp.bezier_points, pts):
    bp.co = (x, 0, z); bp.handle_left_type = bp.handle_right_type = "AUTO"
sp.use_smooth = True
asa = novo("Asa", cu); cu.materials.append(m_cer)
asa.location = (0, 0, Z_XIC); asa.rotation_euler = (0, 0, ALCA_DIR); asa.scale = (1, 1.55, 1)

KL, SL = 30, 128
ang_l = np.linspace(0, 2 * math.pi, SL, endpoint=False)
faces = [(0, 1 + j, 1 + (j + 1) % SL) for j in range(SL)]
faces += [(1 + k * SL + j, 1 + (k + 1) * SL + j, 1 + (k + 1) * SL + (j + 1) % SL, 1 + k * SL + (j + 1) % SL)
          for k in range(KL - 1) for j in range(SL)]
me = bpy.data.meshes.new("Liquido"); me.from_pydata([(0, 0, 0)] * (1 + KL * SL), [], faces); me.update()
liq = novo("Liquido", me); liq.location = (0, 0, Z_XIC); me.materials.append(m_liq); me.shade_smooth()
for o in (pires, xicara, asa, liq): o.parent = xic

def z_xic(f): return faixa(f, [(PROC["xicara"][0], -7.8), (PROC["xicara"][1], -3.1)])
def nivel(f): return 0.12 + 0.31 * sms(f, *PROC["nivel"]) + 0.40 * sms(f, *PROC["espiral"])
por_frame(xic, "location", lambda f: (0, 0, z_xic(f)))
for o in (pires, xicara, asa): visivel(o, PROC["xicara"][0], FIM)
visivel(liq, PROC["nivel"][0] + 1, FIM)
por_frame_socket(revela, lambda f: 1.3 * sms(f, PROC["espiral"][0] + 2, PROC["espiral"][1]))

def z_liquido_mundo(f): return z_xic(f) + XIC_ESC * (Z_XIC + nivel(f))

def atualiza_liquido(f):
    L = nivel(f)
    R = float(np.interp(L, [z for _, z in INTERNO], [r for r, _ in INTERNO])) - 0.006
    rho = R * np.arange(1, KL + 1) / KL
    onda = 0.012 * (sms(f, 172, 175) - sms(f, 189, 196))          # ondas onde o fio cai
    z = L + 0.018 * (rho / R) ** 8 + onda * np.sin(26 * rho - 1.1 * f) * np.exp(-1.4 * rho)
    co = np.zeros((1 + KL * SL, 3))
    co[0] = (0, 0, L + onda)
    co[1:, 0] = (rho[:, None] * np.cos(ang_l)[None]).ravel()
    co[1:, 1] = (rho[:, None] * np.sin(ang_l)[None]).ravel()
    co[1:, 2] = np.repeat(z, SL)
    me = liq.data; me.vertices.foreach_set("co", co.ravel()); me.update()

# ---------- fio de espresso (espaço do mundo) ----------
KF, SF = 72, 20
ang_f = np.linspace(0, 2 * math.pi, SF, endpoint=False)
faces = [(k * SF + j, (k + 1) * SF + j, (k + 1) * SF + (j + 1) % SF, k * SF + (j + 1) % SF) for k in range(KF - 1) for j in range(SF)]
faces += [tuple(range(SF))[::-1], tuple((KF - 1) * SF + j for j in range(SF))]
me = bpy.data.meshes.new("Fio"); me.from_pydata([(0, 0, 0)] * (KF * SF), [], faces); me.update()
fio = novo("Fio", me); me.materials.append(m_esp); me.shade_smooth()
visivel(fio, PROC["gota"][0], PROC["corta"][1])
por_frame_socket(fluxo_esp, lambda f: (0, 0, 0.09 * f))

def atualiza_fio(f):
    zc = z_aro(f) - 1.0                       # fundo externo do cesto
    zl = z_liquido_mundo(f)
    g = sms(f, *PROC["gota"])
    t_frente = max(0.0, min(1.0, (f - PROC["fio"][0]) / (PROC["fio"][1] - PROC["fio"][0])))
    t_corte = max(0.0, min(1.0, (f - PROC["corta"][0]) / (PROC["corta"][1] - PROC["corta"][0])))
    topo = lerp(zc, zl, t_corte ** 2)                         # a cauda cai acelerando
    base = lerp(zc - 0.24 * g, zl, t_frente ** 2)
    zs = np.linspace(topo, base, KF)
    dcesto = zc - zs
    r = (0.058 + 0.27 * np.exp(-dcesto / 0.085)) * (g if f < PROC["fio"][0] else 1.0)
    ponta = max(1e-3, min(0.07, (topo - base) / 2))
    if base > zl + 1e-3: r *= np.sqrt(np.clip(1 - ((base + ponta - zs) / ponta).clip(0) ** 2, 0, 1))       # gota redonda na frente
    if topo < zc - 1e-3: r *= np.sqrt(np.clip(1 - ((zs - (topo - ponta)) / ponta).clip(0) ** 2, 0, 1))     # e na cauda
    bal = np.clip(dcesto, 0, 1)
    ox = 0.014 * np.sin(7 * dcesto + 0.9 * f) * bal
    oy = 0.012 * np.cos(5.3 * dcesto + 0.7 * f) * bal
    co = np.zeros((KF, SF, 3))
    co[..., 0] = ox[:, None] + r[:, None] * np.cos(ang_f)[None]
    co[..., 1] = oy[:, None] + r[:, None] * np.sin(ang_f)[None]
    co[..., 2] = zs[:, None]
    me = fio.data; me.vertices.foreach_set("co", co.ravel()); me.update()

# ---------- pó: partículas saem da superfície do grão e descem em redemoinho até o monte ----------
rng = np.random.default_rng(11)
sc.frame_set(T0)
Mg = bean.matrix_world.copy(); C = np.array(Mg.translation)
vs = bean.data.vertices
W = np.array([tuple(Mg @ vs[i].co) for i in rng.choice(len(vs), N_PO, replace=False)])
u = rng.random((N_PO, 8))
altura = (W[:, 2] - W[:, 2].min()) / np.ptp(W[:, 2])
fs = PROC["solta"][0] + (PROC["solta"][1] - PROC["solta"][0]) * np.clip(0.8 * altura + 0.2 * u[:, 0], 0, 1)   # desfaz de baixo pra cima, como ampulheta
dur = PROC["voo"][0] + (PROC["voo"][1] - PROC["voo"][0]) * u[:, 1]
rho_t = 1.18 * np.sqrt(u[:, 2])
volta = 2 * math.pi * (0.6 + 0.6 * u[:, 3])     # redemoinho estreito: meia a uma volta e pouco até pousar
abre_r = 0.06 + 0.3 * u[:, 4]
tam = 0.018 + 0.028 * u[:, 5] ** 2
eixo = rng.normal(size=(N_PO, 3)); eixo /= np.linalg.norm(eixo, axis=1, keepdims=True)
spin = (4 + 8 * u[:, 6]) * rng.choice([-1, 1], N_PO)
forma = 0.55 + 0.9 * rng.random((N_PO, 3))
S = C + (W - C) * np.array([[encolhe(x)] for x in fs])      # onde cada uma se solta (superfície encolhendo)
rho0, th0, z0 = np.hypot(S[:, 0], S[:, 1]), np.arctan2(S[:, 1], S[:, 0]), S[:, 2]

ico = bmesh.new(); bmesh.ops.create_icosphere(ico, subdivisions=1, radius=1.0)
BASE = np.array([v.co[:] for v in ico.verts]); FACES = [[v.index for v in fc.verts] for fc in ico.faces]; ico.free()
NV = len(BASE)
me = bpy.data.meshes.new("Po")
me.from_pydata([(0, 0, 0)] * (N_PO * NV), [], [[i * NV + j for j in fc] for i in range(N_PO) for fc in FACES]); me.update()
set_attr(me, "var", np.repeat(u[:, 7], NV).tolist())
po = novo("Po", me); me.materials.append(m_frag)
FIM_PO = tp[1] + 1                                           # some quando o tamper cobre o monte
visivel(po, PROC["solta"][0], FIM_PO)

def atualiza_po(f):
    tau = np.clip((f - fs) / dur, 0, 1)
    alvo_z = z_aro(f) + monte(rho_t, f)[0] + 0.3 * tam
    te = 1 - (1 - tau) ** 2
    th = th0 + volta * te
    s = tau * tau * (3 - 2 * tau)
    rho = rho0 + (rho_t - rho0) * s + abre_r * np.sin(np.pi * tau) ** 1.5
    z = z0 + (alvo_z - z0) * tau ** 1.4 + 0.12 * np.sin(np.pi * tau) * (1 - tau)
    P = np.stack([rho * np.cos(th), rho * np.sin(th), z], 1)
    vis = ((f >= fs) & (f < FIM_PO)).astype(float)
    ang = spin * tau; c, sn = np.cos(ang), np.sin(ang)
    v = BASE[None] * (forma * tam[:, None])[:, None, :]
    kv = np.cross(eixo[:, None, :], v)
    kd = np.einsum("pj,pij->pi", eixo, v)
    vr = v * c[:, None, None] + kv * sn[:, None, None] + eixo[:, None, :] * kd[:, :, None] * (1 - c)[:, None, None]
    co = vr * vis[:, None, None] + P[:, None, :]
    po.data.vertices.foreach_set("co", co.ravel()); po.data.update()

def atualiza(f):
    atualiza_po(f); atualiza_monte(f); atualiza_fio(f); atualiza_liquido(f)

# ---------- render ----------
r = sc.render
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
r.engine = "CYCLES" if a.engine.upper() == "CYCLES" else "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
if r.engine == "CYCLES":
    sc.cycles.samples = a.samples; sc.cycles.use_denoising = True; sc.cycles.device = "CPU"
    if a.device.upper() == "GPU":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
            try: prefs.compute_device_type = kind
            except TypeError: continue
            prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices: d.use = d.type == kind
                sc.cycles.device = "GPU"; break
    print("Cycles device:", sc.cycles.device)
else:
    ee = sc.eevee
    for k, v in {"taa_render_samples": a.samples, "use_raytracing": True, "use_shadows": True,
                 "shadow_ray_count": 2, "shadow_step_count": 8}.items():
        try: setattr(ee, k, v)
        except Exception: pass
    for m in (m_cereja, m_polpa, m_cabo, m_grao):
        try: m.surface_render_method = "DITHERED"
        except Exception: pass
r.resolution_x = r.resolution_y = a.res
r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "8"
sc.view_settings.view_transform = "AgX"
looks = [l.identifier for l in sc.view_settings.bl_rna.properties["look"].enum_items]
sc.view_settings.look = next((l for l in looks if "Medium High Contrast" in l), "None")

def lista_frames(txt):
    if not txt: return list(range(sc.frame_start, sc.frame_end + 1))
    fr = []
    for parte in txt.split(","):
        i, _, j = parte.partition("-")
        fr += list(range(int(i), int(j) + 1)) if j else [int(i)]
    return fr

out = os.path.abspath(a.out) + os.sep  # relativo ao cwd (Blender resolveria a partir da raiz do drive)
if a.save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
if a.giro:   # xícara final girando: mesmo frame, grupo gira em volta do próprio eixo
    trabalhos = [(FIM, k) for k in (lista_frames(a.frames) if a.frames else range(1, a.giro + 1))]
else:
    trabalhos = [(f, None) for f in lista_frames(a.frames)]
for f, k in trabalhos:
    sc.frame_set(f)
    if k is not None: xic.rotation_euler = (0, 0, 2 * math.pi * (k - 1) / a.giro)
    atualiza(f)
    if r.engine != "CYCLES":                   # alpha dithered do fade das metades pede mais amostras
        sc.eevee.taa_render_samples = a.samples * (3 if s0 <= f <= s1 else 1)
    r.filepath = f"{out}{(k if k is not None else f):04d}.png"
    bpy.ops.render.render(write_still=True)
print("OK", len(trabalhos), "frames ->", out)
