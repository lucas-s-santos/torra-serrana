"""
Torra Serrana — Cena 02, crema em macro (seção Crema, vídeo com scroll-scrub). Fundo opaco, 9:16.
EXPERIMENTAL (20/11): o teste não chegou no nível dos vídeos do Flow e não é usado no site. A gota com ondas
funciona; a textura da crema ainda parece CG. Cada render recompila o shader (~40 s fixos no EEVEE).
  1–120  duas últimas gotas caem e abrem buracos escuros na crema, que se fecham; a crema gira devagar
         (o centro mais rápido que a borda: as manchas tigradas viram estrias) e a câmera desce até o macro.
Uso (rodar da raiz do projeto):
  blender -b -P blender/cena02_crema.py -- --res 1080 --out blender/out/crema/
  (teste rápido) ... -- --res 360 --samples 16 --frames 1,10,30,70,120 --out blender/test/crema/
Depois: ffmpeg -framerate 24 -i blender/out/crema/%04d.png -c:v libx264 -crf 12 -pix_fmt yuv420p flow/raw/crema.mp4
        bash: RAW=flow/raw bash scripts/videos.sh crema
Ajustes de cor, timing e câmera ficam no bloco logo abaixo.
"""
import bpy, bmesh, math, sys, argparse, os
import numpy as np

# ---------- args ----------
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--engine", default="EEVEE")          # EEVEE | CYCLES
p.add_argument("--res", type=int, default=1080)      # largura; altura = 16/9 da largura
p.add_argument("--samples", type=int, default=64)
p.add_argument("--out", default="blender/out/crema/")
p.add_argument("--frames", default="")               # ex: "1,30,120" ou "1-60" (vazio = todos)
p.add_argument("--save", default="")
a = p.parse_args(argv)

# ================= AJUSTES =================
COR = {  # linear
    "dourada": (0.48, 0.19, 0.040),          # centro, onde o fio caiu
    "avela": (0.25, 0.082, 0.016),
    "ruiva": (0.10, 0.028, 0.006),           # anel perto da parede
    "tigre": (0.060, 0.018, 0.0045),         # manchas tigradas
    "espuma": (0.46, 0.24, 0.09),            # menisco claro colado na parede
    "espresso": (0.018, 0.0065, 0.002),      # o que aparece no buraco da gota
    "ceramica": (0.66, 0.55, 0.42),
    "barro": (0.36, 0.25, 0.16),
    "mesa": ((0.004, 0.002, 0.001), (0.012, 0.006, 0.003), (0.025, 0.012, 0.005)),
}
FIM = 120
NIVEL = 0.93                                  # altura da crema dentro da xícara (borda em 1.115)
GIRO = (0.9, 3.4)                             # rotação acumulada do centro (rad) no 1º e no último frame
GOTAS = [  # (frame do impacto, x, y): duas últimas gotas do fio
    (9, 0.10, 0.05),
    (27, -0.16, -0.10),
]
# planos de câmera: (frame, alvo x, y, azimute°, elevação°, distância, f-stop). smootherstep entre eles
PLANOS = [
    (1, 0.00, 0.10, 0, 66, 14.0, 1.2),        # xícara inteira de cima, gota entrando
    (40, 0.00, 0.10, 6, 54, 10.5, 0.6),
    (120, 0.05, 0.25, 16, 36, 7.2, 0.28),     # macro: a crema enche o quadro, bordas desfocadas
]
LENTE = 100
# ===========================================

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FIM
sc.render.fps = 24

def sms(f, e0, e1):
    t = max(0.0, min(1.0, (f - e0) / (e1 - e0)))
    return t * t * t * (t * (6 * t - 15) + 10)

def lerp(x, y, t): return x + (y - x) * t

def faixa(f, pontos):
    if f <= pontos[0][0]: return pontos[0][1]
    for (f0, v0), (f1, v1) in zip(pontos, pontos[1:]):
        if f <= f1:
            t = sms(f, f0, f1)
            return tuple(lerp(x, y, t) for x, y in zip(v0, v1))
    return pontos[-1][1]

def key(target, path, frame, value):
    setattr(target, path, value); target.keyframe_insert(path, frame=frame)

def por_frame(target, path, fn):
    for f in range(1, FIM + 1): key(target, path, f, fn(f))

def por_frame_socket(sock, fn):
    for f in range(1, FIM + 1): key(sock, "default_value", f, fn(f))

# ---------- nós ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
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

def faixa_suave(nt, src, de0, de1, para0=0.0, para1=1.0):
    n = nt.nodes.new("ShaderNodeMapRange"); n.interpolation_type = "SMOOTHSTEP"
    link(nt, src, n.inputs["Value"])
    for k, v in (("From Min", de0), ("From Max", de1), ("To Min", para0), ("To Max", para1)): plug(nt, v, n.inputs[k])
    return n.outputs["Result"]

def op(nt, kind, x, y=None):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = kind
    plug(nt, x, n.inputs[0])
    if y is not None: plug(nt, y, n.inputs[1])
    return n.outputs[0]

def valor(nt, v=0.0):
    n = nt.nodes.new("ShaderNodeValue"); n.outputs[0].default_value = v
    return n.outputs[0]

def noise(nt, vec, scale, detail=4.0, rough=0.5, distort=0.0, w=None):
    n = node(nt, "ShaderNodeTexNoise", Scale=scale, Detail=detail, Roughness=rough, Distortion=distort)
    if w is not None:
        n.noise_dimensions = "4D"; plug(nt, w, n.inputs["W"])
    link(nt, vec, n.inputs["Vector"])
    return n.outputs["Fac"]

def obj_vec(nt): return nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]

def xyz(nt, vec):
    s = nt.nodes.new("ShaderNodeSeparateXYZ"); link(nt, vec, s.inputs[0])
    return s.outputs["X"], s.outputs["Y"], s.outputs["Z"]

def bump(nt, height, strength, dist, normal=None):
    b = node(nt, "ShaderNodeBump", Strength=strength, Distance=dist)
    link(nt, height, b.inputs["Height"])
    if normal: link(nt, normal, b.inputs["Normal"])
    return b.outputs["Normal"]

# ---------- materiais ----------
def mat_ceramica():
    m, nt, b = new_mat("Ceramica")
    v = obj_vec(nt); _, _, z = xyz(nt, v)
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 38; link(nt, v, vor.inputs["Vector"])
    pinta = op(nt, "MULTIPLY", faixa_suave(nt, vor.outputs["Distance"], 0.035, 0.06, 1.0, 0.0),
               faixa_suave(nt, noise(nt, v, 4, 2), 0.45, 0.6))
    cor = mix_rgb(nt, op(nt, "MULTIPLY", pinta, 0.85), COR["ceramica"], (0.06, 0.035, 0.02))
    cru = faixa_suave(nt, z, 0.05, 0.02)
    link(nt, mix_rgb(nt, cru, cor, COR["barro"]), b.inputs["Base Color"])
    link(nt, faixa_suave(nt, cru, 0, 1, 0.16, 0.8), b.inputs["Roughness"])
    link(nt, faixa_suave(nt, cru, 0, 1, 0.45, 0.0), b.inputs["Coat Weight"])
    b.inputs["Coat Roughness"].default_value = 0.05
    link(nt, bump(nt, noise(nt, v, 18, 6, 0.6), 0.03, 0.01), b.inputs["Normal"])
    return m

def mat_mesa():
    m, nt, b = new_mat("Mesa")
    w = node(nt, "ShaderNodeTexWave", Scale=0.35, Distortion=6.0, Detail=4.0)
    w.wave_type = "BANDS"; w.bands_direction = "X"; link(nt, obj_vec(nt), w.inputs["Vector"])
    e, md, c = COR["mesa"]
    link(nt, ramp(nt, w.outputs["Fac"], [(0.15, e), (0.55, md), (0.95, c)]), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    return m

def mat_crema(R):
    """crema no espaço girado: tudo (manchas, bolhas, buracos) anda junto com o fluxo"""
    m, nt, b = new_mat("Crema")
    v = obj_vec(nt); x, y, _ = xyz(nt, v)
    r = op(nt, "SQRT", op(nt, "ADD", op(nt, "MULTIPLY", x, x), op(nt, "MULTIPLY", y, y)))
    rn = op(nt, "DIVIDE", r, R)
    giro = valor(nt); vida = valor(nt)                  # rotação do centro; W do ruído (a crema "respira")
    ang = op(nt, "MULTIPLY", giro, op(nt, "SUBTRACT", 1.0, op(nt, "MULTIPLY", rn, rn)))   # parede não escorrega
    rot = nt.nodes.new("ShaderNodeVectorRotate"); rot.rotation_type = "Z_AXIS"
    link(nt, v, rot.inputs["Vector"]); link(nt, ang, rot.inputs["Angle"])
    P = rot.outputs["Vector"]

    # base: dourada no centro -> avelã -> ruiva na borda, com variação larga
    larga = noise(nt, P, 1.4, 3, 0.5, w=vida)
    base = ramp(nt, op(nt, "ADD", rn, op(nt, "MULTIPLY", op(nt, "SUBTRACT", larga, 0.5), 0.55)),
                [(0.05, COR["dourada"]), (0.5, COR["avela"]), (0.92, COR["ruiva"])])
    # manchas tigradas: ruído com distorção, cortado alto
    tig = noise(nt, P, 4.5, 5, 0.6, 0.2, w=vida)
    tig_m = op(nt, "MULTIPLY", faixa_suave(nt, tig, 0.55, 0.68), 0.6)
    cor = mix_rgb(nt, tig_m, base, COR["tigre"])
    flecks = noise(nt, P, 16, 4, 0.6, 0.3)
    cor = mix_rgb(nt, op(nt, "MULTIPLY", faixa_suave(nt, flecks, 0.6, 0.7), 0.35), cor, COR["tigre"])
    fino = noise(nt, P, 70, 4, 0.6)
    cor = mix_rgb(nt, 1.0, cor, ramp(nt, fino, [(0.3, (0.9,) * 3), (0.7, (1.08,) * 3)]), "MULTIPLY")
    # pontinhos escuros de pó fino
    vp = nt.nodes.new("ShaderNodeTexVoronoi"); vp.inputs["Scale"].default_value = 90; link(nt, P, vp.inputs["Vector"])
    sp = nt.nodes.new("ShaderNodeSeparateColor"); link(nt, vp.outputs["Color"], sp.inputs[0])
    pinta = op(nt, "MULTIPLY", faixa_suave(nt, vp.outputs["Distance"], 0.06, 0.12, 1.0, 0.0), op(nt, "GREATER_THAN", sp.outputs["Red"], 0.86))
    cor = mix_rgb(nt, op(nt, "MULTIPLY", pinta, 0.7), cor, COR["tigre"])
    # menisco claro na parede
    cor = mix_rgb(nt, faixa_suave(nt, rn, 0.955, 0.995), cor, COR["espuma"])

    # bolhas: duas camadas de voronoi; raio aleatório por célula; densas perto da parede
    def bolhas(escala, dens):
        vb = nt.nodes.new("ShaderNodeTexVoronoi"); vb.inputs["Scale"].default_value = escala; link(nt, P, vb.inputs["Vector"])
        sb = nt.nodes.new("ShaderNodeSeparateColor"); link(nt, vb.outputs["Color"], sb.inputs[0])
        raio = op(nt, "ADD", op(nt, "MULTIPLY", sb.outputs["Red"], 0.28), 0.12)
        q = op(nt, "DIVIDE", vb.outputs["Distance"], raio)
        h = op(nt, "SQRT", op(nt, "MAXIMUM", op(nt, "SUBTRACT", 1.0, op(nt, "MULTIPLY", q, q)), 0.0))
        return op(nt, "MULTIPLY", h, op(nt, "LESS_THAN", sb.outputs["Green"], dens))
    grandes = bolhas(14, faixa_suave(nt, rn, 0.80, 0.98, 0.0, 0.55))
    miudas = bolhas(48, faixa_suave(nt, rn, 0.55, 0.96, 0.0, 0.45))
    poros = bolhas(150, 0.3)                            # espuma fina no corpo todo
    tem_bolha = op(nt, "MINIMUM", op(nt, "MULTIPLY", op(nt, "ADD", grandes, miudas), 3.0), 1.0)
    cor = mix_rgb(nt, op(nt, "MULTIPLY", tem_bolha, 0.12), cor, COR["espuma"])

    # buracos das gotas (centro e raio chaveados por frame) + anel claro em volta
    buraco = None; anel = None
    socks = []
    for _ in GOTAS:
        cx, cy, rad = valor(nt), valor(nt), valor(nt)
        socks.append((cx, cy, rad))
        px, py, _ = xyz(nt, P)
        dx, dy = op(nt, "SUBTRACT", px, cx), op(nt, "SUBTRACT", py, cy)
        d = op(nt, "SQRT", op(nt, "ADD", op(nt, "MULTIPLY", dx, dx), op(nt, "MULTIPLY", dy, dy)))
        d = op(nt, "ADD", d, op(nt, "MULTIPLY", op(nt, "SUBTRACT", noise(nt, P, 30, 3), 0.5), 0.05))    # borda irregular
        h = op(nt, "MULTIPLY", faixa_suave(nt, d, op(nt, "MULTIPLY", rad, 0.6), rad, 1.0, 0.0), op(nt, "GREATER_THAN", rad, 0.002))
        an = op(nt, "MULTIPLY", faixa_suave(nt, op(nt, "ABSOLUTE", op(nt, "SUBTRACT", d, op(nt, "MULTIPLY", rad, 1.35))),
                                            0.0, op(nt, "MULTIPLY", rad, 0.5), 1.0, 0.0), op(nt, "GREATER_THAN", rad, 0.002))
        buraco = h if buraco is None else op(nt, "MAXIMUM", buraco, h)
        anel = an if anel is None else op(nt, "MAXIMUM", anel, an)
    cor = mix_rgb(nt, op(nt, "MULTIPLY", anel, 0.5), cor, COR["dourada"])
    cor = mix_rgb(nt, buraco, cor, COR["espresso"])

    link(nt, cor, b.inputs["Base Color"])
    rough = faixa_suave(nt, buraco, 0, 1, 0.2, 0.06)
    link(nt, op(nt, "SUBTRACT", rough, op(nt, "MULTIPLY", tem_bolha, 0.2)), b.inputs["Roughness"])
    for k, val in {"Specular IOR Level": 0.45, "Subsurface Weight": 0.1,
                   "Subsurface Radius": (1.0, 0.45, 0.2), "Subsurface Scale": 0.02}.items():
        b.inputs[k].default_value = val
    nrm = bump(nt, grandes, 0.55, 0.012)
    nrm = bump(nt, miudas, 0.4, 0.004, nrm)
    nrm = bump(nt, poros, 0.3, 0.0015, nrm)
    nrm = bump(nt, fino, 0.12, 0.003, nrm)
    link(nt, nrm, b.inputs["Normal"])
    return m, giro, vida, socks

def mat_gota():
    m, nt, b = new_mat("Gota")
    b.inputs["Base Color"].default_value = (*COR["espresso"], 1)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.02
    return m

def mat_bokeh(forca, cor):
    m = bpy.data.materials.new("Bokeh")
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = node(nt, "ShaderNodeEmission", Strength=forca); e.inputs["Color"].default_value = (*cor, 1)
    link(nt, e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m

# ---------- geometria ----------
def novo(name, me):
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o

def lathe(name, perfil, seg=192, fechar=False):
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

def suave(o, levels=2):
    o.data.shade_smooth()
    s = o.modifiers.new("sub", "SUBSURF"); s.levels = s.render_levels = levels

# mesma xícara e pires da cena 01
XICARA = [(0, 0.005), (0.46, 0.005), (0.50, 0.0), (0.56, 0.0), (0.585, 0.02), (0.60, 0.06), (0.62, 0.075), (0.80, 0.16),
          (0.98, 0.30), (1.10, 0.48), (1.18, 0.70), (1.225, 0.92), (1.245, 1.08), (1.245, 1.11), (1.23, 1.125),
          (1.21, 1.115), (1.19, 1.0), (1.15, 0.80), (1.07, 0.58), (0.93, 0.38), (0.72, 0.21), (0.45, 0.135), (0.0, 0.12)]
INTERNO = XICARA[15:][::-1]
PIRES = [(0, 0.02), (0.80, 0.02), (0.84, 0.0), (0.95, 0.0), (0.99, 0.03), (1.30, 0.08), (1.70, 0.15), (1.98, 0.24),
         (2.06, 0.29), (2.065, 0.31), (2.04, 0.32), (1.95, 0.29), (1.65, 0.20), (1.25, 0.13), (0.80, 0.10),
         (0.66, 0.08), (0.62, 0.07), (0, 0.07)]
Z_XIC = 0.07

m_cer = mat_ceramica()
pires = lathe("Pires", PIRES); xicara = lathe("Xicara", XICARA); xicara.location = (0, 0, Z_XIC)
for o in (pires, xicara): o.data.materials.append(m_cer); suave(o)
cu = bpy.data.curves.new("Asa", "CURVE"); cu.dimensions = "3D"
cu.bevel_depth = 0.07; cu.bevel_resolution = 6; cu.resolution_u = 24
sp = cu.splines.new("BEZIER"); pts = [(1.20, 0.93), (1.55, 0.97), (1.78, 0.80), (1.74, 0.52), (1.45, 0.36), (1.04, 0.42)]
sp.bezier_points.add(len(pts) - 1)
for bp, (x, z) in zip(sp.bezier_points, pts):
    bp.co = (x, 0, z); bp.handle_left_type = bp.handle_right_type = "AUTO"
asa = novo("Asa", cu); cu.materials.append(m_cer)
asa.location = (0, 0, Z_XIC); asa.rotation_euler = (0, 0, math.radians(-38)); asa.scale = (1, 1.55, 1)

mesa = bpy.data.meshes.new("Mesa"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=40); bm.to_mesh(mesa); bm.free()
mesa = novo("Mesa", mesa); mesa.data.materials.append(mat_mesa())

# crema: disco em anéis, reescrito por frame (ondas das gotas + menisco)
R = float(np.interp(NIVEL, [z for _, z in INTERNO], [r for r, _ in INTERNO])) - 0.004
KL, SL = 110, 400
rho = R * np.arange(1, KL + 1) / KL
ang = np.linspace(0, 2 * math.pi, SL, endpoint=False)
faces = [(0, 1 + j, 1 + (j + 1) % SL) for j in range(SL)]
faces += [(1 + k * SL + j, 1 + (k + 1) * SL + j, 1 + (k + 1) * SL + (j + 1) % SL, 1 + k * SL + (j + 1) % SL)
          for k in range(KL - 1) for j in range(SL)]
me = bpy.data.meshes.new("Crema"); me.from_pydata([(0, 0, 0)] * (1 + KL * SL), [], faces); me.update()
crema = novo("Crema", me); crema.location = (0, 0, Z_XIC); me.shade_smooth()
m_crema, giro, vida, socks = mat_crema(R); me.materials.append(m_crema)
XS = np.concatenate([[0.0], (rho[:, None] * np.cos(ang)[None]).ravel()])
YS = np.concatenate([[0.0], (rho[:, None] * np.sin(ang)[None]).ravel()])

def giro_em(f): return lerp(GIRO[0], GIRO[1], 1 - (1 - (f - 1) / (FIM - 1)) ** 1.6)   # desacelera
por_frame_socket(giro, giro_em)
por_frame_socket(vida, lambda f: 0.004 * f)

def no_fluxo(x, y, f):
    """ponto da superfície -> coordenada girada (onde o shader procura o buraco)"""
    t = giro_em(f) * (1 - (x * x + y * y) / R ** 2)
    c, s = math.cos(t), math.sin(t)
    return x * c - y * s, x * s + y * c

for (fi, gx, gy), (cx, cy, rad) in zip(GOTAS, socks):
    px, py = no_fluxo(gx, gy, fi)
    cx.default_value, cy.default_value = px, py
    por_frame_socket(rad, lambda f, fi=fi: 0.11 * sms(f, fi, fi + 3) * (1 - sms(f, fi + 5, fi + 34)))

def atualiza(f):
    z = NIVEL + 0.022 * (np.hypot(XS, YS) / R) ** 10
    for fi, gx, gy in GOTAS:
        dt = f - fi
        if dt <= 0: continue
        d = np.hypot(XS - gx, YS - gy)
        c = 0.055 * dt
        amp = 0.010 * math.exp(-dt / 14)
        z = z + amp * np.cos(2 * math.pi * (d - c) / 0.13) * np.exp(-((d - c) / 0.16) ** 2)
        z = z - 0.025 * math.exp(-dt / 2.5) * np.exp(-(d / 0.07) ** 2)          # covinha do impacto
    co = np.column_stack([XS, YS, z])
    crema.data.vertices.foreach_set("co", co.ravel()); crema.data.update()

# gotas: caem de cima do quadro até o impacto
m_gota = mat_gota()
for i, (fi, gx, gy) in enumerate(GOTAS):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=24, radius=1)
    gme = bpy.data.meshes.new(f"Gota{i}"); bm.to_mesh(gme); bm.free()
    g = novo(f"Gota{i}", gme); gme.shade_smooth(); gme.materials.append(m_gota)
    g.scale = (0.045, 0.045, 0.075)
    zi = Z_XIC + NIVEL
    por_frame(g, "location", lambda f, fi=fi, gx=gx, gy=gy, zi=zi: (gx, gy, zi + 0.04 + 0.09 * max(0, fi - f) ** 2))
    por_frame(g, "hide_render", lambda f, fi=fi: not (fi - 7 <= f < fi))

# ---------- câmera ----------
cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = LENTE; cam_data.sensor_fit = "VERTICAL"; cam_data.sensor_height = 36
cam = novo("Cam", cam_data); sc.camera = cam
alvo = bpy.data.objects.new("Alvo", None); sc.collection.objects.link(alvo)
tc = cam.constraints.new("TRACK_TO"); tc.target = alvo; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_data.dof.use_dof = True; cam_data.dof.focus_object = alvo
planos = [(f, tuple(v)) for f, *v in PLANOS]
zc = Z_XIC + NIVEL

def camera_em(f):
    ax, ay, az_, el, dist, fstop = faixa(f, planos)
    A, E = math.radians(az_), math.radians(el)
    return (ax, ay, zc), (ax + dist * math.sin(A) * math.cos(E), ay - dist * math.cos(A) * math.cos(E), zc + dist * math.sin(E)), fstop

por_frame(alvo, "location", lambda f: camera_em(f)[0])
por_frame(cam, "location", lambda f: camera_em(f)[1])
por_frame(cam_data.dof, "aperture_fstop", lambda f: camera_em(f)[2])

# ---------- luz: softbox atrás da xícara (o brilho largo da crema) + key quente lateral ----------
def area(name, loc, energy, size, size_y, color):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.shape = "RECTANGLE"
    d.size = size; d.size_y = size_y; d.color = color
    o = novo(name, d); o.location = loc
    c = o.constraints.new("TRACK_TO"); c.target = alvo; c.track_axis = "TRACK_NEGATIVE_Z"
area("Softbox", (0.6, 8.0, 5.0), 1600, 2.5, 0.8, (1.0, 0.92, 0.82))
area("Key", (-6.0, -2.5, 6.0), 420, 2.5, 2.5, (1.0, 0.84, 0.66))
area("Rim", (5.5, 1.5, 2.2), 260, 0.8, 4.0, (1.0, 0.72, 0.48))

# luzes do café ao fundo, bem desfocadas
m_bk = mat_bokeh(18, (1.0, 0.62, 0.30))
for i, (x, y, z, s) in enumerate([(-5.5, 16, 3.5, 0.22), (-1.0, 19, 4.6, 0.3), (3.8, 17, 3.0, 0.18), (7.5, 22, 5.5, 0.35), (-9, 24, 6.0, 0.28)]):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=s)
    bme = bpy.data.meshes.new(f"Bokeh{i}"); bm.to_mesh(bme); bm.free()
    o = novo(f"Bokeh{i}", bme); o.location = (x, y, z); bme.materials.append(m_bk)

w = bpy.data.worlds.new("W"); sc.world = w
try: w.use_nodes = True
except Exception: pass
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.001, 0.0006, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

# ---------- render ----------
r = sc.render
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
r.engine = "CYCLES" if a.engine.upper() == "CYCLES" else "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
if r.engine == "CYCLES":
    sc.cycles.samples = a.samples; sc.cycles.use_denoising = True
else:
    for k, v in {"taa_render_samples": a.samples, "use_raytracing": True, "use_shadows": True,
                 "shadow_ray_count": 2, "shadow_step_count": 8}.items():
        try: setattr(sc.eevee, k, v)
        except Exception: pass
r.resolution_x = a.res; r.resolution_y = round(a.res * 16 / 9)
r.film_transparent = False
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"; r.image_settings.color_depth = "8"
sc.view_settings.view_transform = "AgX"
looks = [l.identifier for l in sc.view_settings.bl_rna.properties["look"].enum_items]
sc.view_settings.look = next((l for l in looks if "Medium High Contrast" in l), "None")

def lista_frames(txt):
    if not txt: return list(range(1, FIM + 1))
    fr = []
    for parte in txt.split(","):
        i, _, j = parte.partition("-")
        fr += list(range(int(i), int(j) + 1)) if j else [int(i)]
    return fr

out = os.path.abspath(a.out) + os.sep
if a.save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
fr = lista_frames(a.frames)
import time
for f in fr:
    t0 = time.time()
    sc.frame_set(f); atualiza(f)
    print(f"frame {f}: prep {time.time() - t0:.1f}s", flush=True)
    r.filepath = f"{out}{f:04d}.png"
    bpy.ops.render.render(write_still=True)
print("OK", len(fr), "frames ->", out)
