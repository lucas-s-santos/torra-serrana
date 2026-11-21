"""
Torra Serrana — grãos avulsos (stills com fundo transparente) pras seções 5 (cards) e 7 (parallax).
Mesmo modelo, material e luz da cena 01, sem animação: uma sessão do Blender renderiza todos.
Uso (rodar da raiz do projeto):
  blender -b -P blender/graos.py -- --res 1000 --out blender/out/graos/
  (teste) ... -- --res 400 --samples 16 --out blender/test/graos/
Saída: card-1.png … card-3.png, solto-1.png … solto-6.png
"""
import bpy, bmesh, math, sys, argparse, os
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--res", type=int, default=1000)
p.add_argument("--samples", type=int, default=64)
p.add_argument("--out", default="blender/out/graos/")
p.add_argument("--only", default="")                 # ex: "card-1,solto-3"
a = p.parse_args(argv)

# ================= AJUSTES =================
TORRA = [  # mesma rampa da cena 01
    (0.00, (0.20, 0.29, 0.13)),
    (0.22, (0.40, 0.34, 0.15)),
    (0.45, (0.33, 0.16, 0.065)),
    (0.72, (0.12, 0.048, 0.02)),
    (1.00, (0.058, 0.024, 0.012)),
]
PELE = (0.42, 0.30, 0.17)
D = math.radians
# nome: (torra 0–1, rotação XYZ, semente do ruído de forma)
GRAOS = {
    "card-1": (0.56, (D(90), D(22), D(28)), 1),     # Serra Alta — torra clara (jasmim, fruta amarela)
    "card-2": (0.86, (D(90), D(-26), D(-30)), 2),   # Pé de Morro — torra média (cacau, caramelo)
    "card-3": (0.95, (D(78), D(14), D(-8)), 3),     # Cereja Doce — média-escura (frutas vermelhas, mel)
    "solto-1": (1.0, (D(90), D(35), D(20)), 4),     # sulco de frente
    "solto-2": (0.97, (D(-90), D(-20), D(15)), 5),  # costas (dorso arredondado)
    "solto-3": (1.0, (D(90), D(80), D(70)), 6),     # perfil
    "solto-4": (0.98, (D(60), D(-50), D(140)), 7),  # 3/4 de cima
    "solto-5": (1.0, (D(-70), D(30), D(-60)), 8),   # dorso inclinado
    "solto-6": (0.96, (D(100), D(-10), D(-45)), 9), # sulco quase vertical
}
CAMERA = {"lente": 85, "pos": (0.0, -6.6, 1.1), "alvo": (0, 0, 0)}
# ===========================================

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)

def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items(): n.inputs[k].default_value = v
    return n

def link(nt, a, b): nt.links.new(a, b)

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

def obj_noise(nt, scale, detail=4.0, rough=0.5):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = node(nt, "ShaderNodeTexNoise", Scale=scale, Detail=detail, Roughness=rough)
    link(nt, tc.outputs["Object"], n.inputs["Vector"])
    return n.outputs["Fac"]

def bump_chain(nt, bsdf, layers):
    prev = None
    for scale, strength, dist in layers:
        b = node(nt, "ShaderNodeBump", Strength=strength, Distance=dist)
        link(nt, obj_noise(nt, scale, 6, 0.6), b.inputs["Height"])
        if prev: link(nt, prev, b.inputs["Normal"])
        prev = b.outputs["Normal"]
    link(nt, prev, bsdf.inputs["Normal"])

def mat_grao():
    m = bpy.data.materials.new("Grao")
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = node(nt, "ShaderNodeValue").outputs[0]
    cor = mix_rgb(nt, 1.0, ramp(nt, t, TORRA), ramp(nt, obj_noise(nt, 7, 5, 0.6), [(0.3, (0.70,) * 3), (0.7, (1.15,) * 3)]), "MULTIPLY")
    sulco = nt.nodes.new("ShaderNodeAttribute"); sulco.attribute_name = "sulco"
    link(nt, mix_rgb(nt, map_range(nt, sulco.outputs["Fac"], 0, 0.85), cor, PELE), b.inputs["Base Color"])
    link(nt, map_range(nt, t, 0.62, 0.36), b.inputs["Roughness"])
    link(nt, map_range(nt, t, 0.0, 0.28), b.inputs["Coat Weight"])
    b.inputs["Coat Roughness"].default_value = 0.2
    bump_chain(nt, b, [(22, 0.12, 0.02), (180, 0.08, 0.003)])
    return m, t

def make_bean(seed):
    me = bpy.data.meshes.new("Grao"); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=160, v_segments=96, radius=1)
    off = Vector((seed * 3.1, seed * 1.7, seed * 2.3))     # cada grão com uma assimetria própria
    sulco = []
    for v in bm.verts:
        x, y, z = v.co.x, v.co.z, -v.co.y
        x *= 0.70; z *= 0.56
        if z > 0: z *= 0.42
        cx = 0.035 * math.sin(y * 2.6)
        g = math.exp(-((x - cx) ** 2) / (2 * 0.026 ** 2))
        taper = max(0.0, 1 - abs(y) ** 2.4)
        on_flat = smoothstep(-0.02, 0.10, z)
        z -= 0.13 * g * taper * on_flat
        lip = math.exp(-((abs(x - cx) - 0.065) ** 2) / (2 * 0.02 ** 2))
        z += 0.012 * lip * taper * on_flat
        co = Vector((x, y, z))
        co += co.normalized() * 0.022 * noise.noise(co * 2.2 + off)
        v.co = co
        sulco.append(g * taper * on_flat)
    bm.to_mesh(me); bm.free()
    at = me.attributes.new("sulco", "FLOAT", "POINT"); at.data.foreach_set("value", sulco)
    me.shade_smooth()
    o = bpy.data.objects.new("Grao", me); sc.collection.objects.link(o)
    s = o.modifiers.new("sub", "SUBSURF"); s.levels = s.render_levels = 1
    return o

# ---------- câmera + luz (iguais à cena 01) ----------
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); cam.data.lens = CAMERA["lente"]
sc.collection.objects.link(cam); sc.camera = cam; cam.location = CAMERA["pos"]
tgt = bpy.data.objects.new("Alvo", None); sc.collection.objects.link(tgt); tgt.location = CAMERA["alvo"]
tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

def area(name, loc, energy, shape, size, size_y, color):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.shape = shape
    d.size = size; d.size_y = size_y; d.color = color
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc
    c = o.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"
area("Key", (-4.2, -4.8, 4.4), 760, "ELLIPSE", 3.2, 3.2, (1.0, 0.92, 0.82))
area("RimD", (3.6, 3.4, 1.8), 1100, "RECTANGLE", 0.6, 4.0, (1.0, 0.76, 0.52))
area("RimE", (-3.6, 3.0, 1.2), 520, "RECTANGLE", 0.5, 3.5, (1.0, 0.88, 0.76))
area("Fill", (2.5, -5.5, -0.8), 70, "ELLIPSE", 5, 5, (0.92, 0.95, 1.0))

w = bpy.data.worlds.new("W"); sc.world = w
try: w.use_nodes = True
except Exception: pass
wn = w.node_tree
sep = wn.nodes.new("ShaderNodeSeparateXYZ")
link(wn, wn.nodes.new("ShaderNodeTexCoord").outputs["Generated"], sep.inputs["Vector"])
link(wn, ramp(wn, sep.outputs["Z"], [(0.35, (0.02, 0.014, 0.01)), (0.75, (0.5, 0.42, 0.34))]), wn.nodes["Background"].inputs["Color"])
wn.nodes["Background"].inputs["Strength"].default_value = 0.4

# ---------- render ----------
r = sc.render
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
r.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
for k, v in {"taa_render_samples": a.samples, "use_raytracing": True, "use_shadows": True}.items():
    try: setattr(sc.eevee, k, v)
    except Exception: pass
r.resolution_x = r.resolution_y = a.res
r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "8"
sc.view_settings.view_transform = "AgX"
looks = [l.identifier for l in sc.view_settings.bl_rna.properties["look"].enum_items]
sc.view_settings.look = next((l for l in looks if "Medium High Contrast" in l), "None")

out = os.path.abspath(a.out) + os.sep
only = set(filter(None, a.only.split(",")))
mat, torra = mat_grao()
for nome, (t, rot, seed) in GRAOS.items():
    if only and nome not in only: continue
    bean = make_bean(seed); bean.data.materials.append(mat)
    bean.rotation_euler = rot; bean.scale = (0.9,) * 3
    torra.default_value = t
    r.filepath = f"{out}{nome}.png"
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(bean)
print("OK ->", out)
