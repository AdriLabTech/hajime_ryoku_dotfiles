#!/usr/bin/env python3
"""Fondo de Hajime: un amanecer plano, con crestas de montanas en teal y un sol azafran.

Original, generado por codigo (sin imagenes de terceros). Determinista: misma semilla, mismo fondo.

  python3 -I tools/gen-wallpaper.py SALIDA.png [--size 3840x2160] [--seed 7]
"""
import math, random, sys
import numpy as np
from PIL import Image, ImageDraw

W, H = 3840, 2160
seed = 7
args = sys.argv[1:]
out = args[0]
if "--size" in args:
    W, H = (int(v) for v in args[args.index("--size") + 1].split("x"))
if "--seed" in args:
    seed = int(args[args.index("--seed") + 1])
rnd = random.Random(seed)
S = H / 2160                                    # escala respecto a 4K

def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
def mix(a, b, t): return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

SKY_TOP, SKY_MID, SKY_LOW = hexrgb("#06141A"), hexrgb("#0E2D34"), hexrgb("#1D4F55")
SUN, SUN_HALO = hexrgb("#FF7A2F"), hexrgb("#FFC857")
RIDGES = ["#22555B", "#1A434A", "#133339", "#0D262B", "#081A1F"]   # de lejos a cerca

# cielo: degradado vertical en tres tramos
y = np.linspace(0, 1, H)[:, None]
top = np.array(SKY_TOP, float); mid = np.array(SKY_MID, float); low = np.array(SKY_LOW, float)
t1 = np.clip(y / 0.55, 0, 1); t2 = np.clip((y - 0.55) / 0.35, 0, 1)
sky = top + (mid - top) * t1
sky = sky + (low - mid) * t2 * (y > 0.55)
img = np.repeat(sky[:, None, :], W, axis=1)

# sol azafran con halo en anillos planos, medio tapado por las crestas
sx, sy, sr = int(W * 0.66), int(H * 0.60), int(H * 0.13)
yy, xx = np.mgrid[0:H, 0:W]
d = np.hypot(xx - sx, yy - sy)
for k, (mult, alpha) in enumerate([(3.4, 0.05), (2.5, 0.08), (1.8, 0.12), (1.35, 0.18)]):
    m = (d < sr * mult)[..., None]
    img = np.where(m, img * (1 - alpha) + np.array(SUN) * alpha, img)
disc = (d < sr)[..., None]
img = np.where(disc, np.array(SUN, float), img)

# estrellas: puntos sueltos en el cielo alto, lejos del reloj de arriba a la izquierda
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
dr = ImageDraw.Draw(im)
for _ in range(90):
    x, yv = rnd.randint(0, W), rnd.randint(0, int(H * 0.45))
    if x < W * 0.30 and yv < H * 0.22:
        continue
    r = rnd.choice([2, 2, 3, 4]) * S
    a = rnd.uniform(0.25, 0.8)
    c = mix(hexrgb("#0E2D34"), hexrgb("#F3EBDD"), a)
    dr.ellipse((x - r, yv - r, x + r, yv + r), fill=c)

# crestas: suma de senos con fases al azar; cada capa mas baja y mas oscura
base = [0.60, 0.67, 0.74, 0.82, 0.91]
amp = [0.060, 0.070, 0.075, 0.070, 0.055]
for i, col in enumerate(RIDGES):
    ph = [rnd.uniform(0, 2 * math.pi) for _ in range(4)]
    pts = []
    for x in range(0, W + 8, 8):
        u = x / W * 2 * math.pi
        v = (math.sin(u * 0.7 + ph[0]) * 0.55 + math.sin(u * 1.9 + ph[1]) * 0.30
             + math.sin(u * 4.3 + ph[2]) * 0.12 + math.sin(u * 9.1 + ph[3]) * 0.05)
        pts.append((x, (base[i] + amp[i] * v) * H))
    dr.polygon(pts + [(W, H), (0, H)], fill=hexrgb(col))

# grano fino para que el degradado no marque bandas
arr = np.asarray(im).astype(np.float32)
arr += np.random.default_rng(seed).normal(0, 2.2, arr.shape[:2])[..., None]
Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(out)
print(f"{out}: {W}x{H}")
