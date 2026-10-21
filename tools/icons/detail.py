"""Iconos pixel art 48x48 de mucho detalle: objetos con material, luz cálida, grano y desgaste.

Estilo: luz sodio desde arriba a la izquierda, sombras con matiz ámbar oscuro, contorno
marrón casi negro, texturas por material (papel, cartón, madera, latón, acero). Todo es
determinista: la semilla sale del nombre del icono, así que se regenera idéntico.
"""
import math, random
from PIL import Image, ImageDraw

import pixelart as px

N = 48
hx, mix = px.hx, px.mix
WARM, DARK, EMBER = hx("#FFE2A6"), hx("#120B09"), hx("#4A2316")
CLEAR = (0, 0, 0, 0)
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))

# materiales base (apagados y cálidos)
MAT = {
    "gold": "#C99A4B", "blue": "#5E86A6", "red": "#B5473A", "green": "#6E9A5E", "orange": "#C9773A",
    "purple": "#7E6A9E", "pink": "#B5667F", "teal": "#4F9A8E", "gray": "#8A8278", "brown": "#8E5E3A",
    "yellow": "#D4B545", "cyan": "#58A5B5", "navy": "#52709A", "black": "#4B433D", "white": "#CFC5B0",
    "lime": "#8FB04A", "paper": "#D9C8A0", "brass": "#C79A3B", "steel": "#7C8A8C", "wood": "#8C5A32",
    "leather": "#6B3F26", "rust": "#8A3E22", "ink": "#2B1F1A", "screen": "#7FC17B", "glass": "#8FB9B4",
}

def ramp(base):
    b = hx(MAT.get(base, base)) if isinstance(base, str) else base
    return [mix(b, DARK, .80), mix(b, EMBER, .58), mix(b, EMBER, .28), b,
            mix(b, WARM, .26), mix(b, WARM, .55), mix(b, WARM, .85)]

# ---------------------------------------------------------------- máscaras
def _mask(fn):
    im = Image.new("L", (N, N), 0)
    fn(ImageDraw.Draw(im))
    px_ = im.load()
    return {(x, y) for y in range(N) for x in range(N) if px_[x, y]}

def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}

def rrect(x0, y0, x1, y1, r=2):
    m = rect(x0, y0, x1, y1)
    for k in range(r):
        for dx in range(r - k):
            for p in ((x0 + dx, y0 + k), (x1 - dx, y0 + k), (x0 + dx, y1 - k), (x1 - dx, y1 - k)):
                m.discard(p)
    return m

def poly(pts):
    return _mask(lambda d: d.polygon(pts, fill=255))

def ellipse(cx, cy, rx, ry):
    return _mask(lambda d: d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255))

def line(p0, p1, w=1):
    return _mask(lambda d: d.line((p0, p1), fill=255, width=w))

def ring(cx, cy, r0, r1):
    return ellipse(cx, cy, r1, r1) - ellipse(cx, cy, r0, r0)

# ---------------------------------------------------------------- lienzo
class Cv:
    def __init__(self, seed="x"):
        self.im = Image.new("RGBA", (N, N), CLEAR)
        self.p = self.im.load()
        self.rng = random.Random(str(seed))

    def dot(self, x, y, c):
        if 0 <= x < N and 0 <= y < N:
            self.p[x, y] = c

    def get(self, x, y):
        return self.p[x, y] if 0 <= x < N and 0 <= y < N else CLEAR

    def fill(self, m, c):
        for x, y in m:
            self.dot(x, y, c)

    def shadow(self, cx, cy, rx, ry, a=90):
        for x, y in ellipse(cx, cy, rx, ry):
            if self.get(x, y)[3] == 0:
                self.dot(x, y, (18, 8, 4, a if (x + y) % 2 == 0 or (x - cx) ** 2 / rx ** 2 + (y - cy) ** 2 / ry ** 2 < .55 else a // 2))

    def paint(self, m, r, base=3.0, grad=1.1, grain=.06, outline=True, light=.8, tex=None):
        """Rellena una máscara con luz (arriba-izquierda), degradado, grano y contorno."""
        if not m:
            return
        ys = [y for _, y in m]
        y0, y1 = min(ys), max(ys)
        h = max(1, y1 - y0)
        for (x, y) in m:
            i = base + (0.5 - (y - y0) / h) * grad * 2
            if (x, y - 1) not in m: i += 1.2 * light
            if (x - 1, y) not in m: i += .8 * light
            if (x, y + 1) not in m: i -= 1.3 * light
            if (x + 1, y) not in m: i -= .9 * light
            if tex:
                i += tex(x, y, self.rng)
            if self.rng.random() < grain:
                i += self.rng.choice((-1, 1))
            i = max(1, min(5.99, i))
            k = int(i)
            c = r[k + 1] if (i - k) * 16 > BAYER[y % 4][x % 4] else r[k]
            self.dot(x, y, c)
        if outline:
            for (x, y) in m:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in m and self.get(*q)[3] == 0:
                        self.dot(*q, r[0])

    def text(self, s, x, y, c, wear=.12):
        for ch in s.upper():
            bits = px._F.get(ch)
            if bits:
                for j in range(5):
                    for i in range(3):
                        if bits[j * 3 + i] == "1" and self.rng.random() > wear:
                            self.dot(x + i, y + j, c)
            x += 4

    def stamp(self, name, ox, oy, c, wear=.16, scale=1):
        rows = px.GLYPHS[name]
        for j, row in enumerate(rows):
            for i, v in enumerate(row):
                if v == "#":
                    for a in range(scale):
                        for b in range(scale):
                            if self.rng.random() > wear:
                                self.dot(ox + i * scale + a, oy + j * scale + b, c)

    def lines(self, x0, x1, y0, y1, step, c, jitter=True, wear=.08):
        y = y0
        while y <= y1:
            e = x1 - (self.rng.randint(0, 9) if jitter else 0)
            for x in range(x0, e + 1):
                if self.rng.random() > wear:
                    self.dot(x, y, c)
            y += step

    def stain(self, cx, cy, r, c):
        for x, y in ring(cx, cy, r - 2, r):
            if self.get(x, y)[3] and self.rng.random() < .55:
                self.dot(x, y, mix(self.get(x, y), c, .35))

# ---------------------------------------------------------------- texturas
def paper_tex(x, y, rng):
    return (rng.random() - .5) * .5 + (0.25 if (x * 7 + y * 3) % 11 == 0 else 0)

def wood_tex(x, y, rng):
    return math.sin(y * 1.7 + (x // 6) * 2.1) * .55 + (rng.random() - .5) * .3

def metal_tex(x, y, rng):
    return (0.5 if (x + y * 2) % 9 == 0 else 0) + (rng.random() - .5) * .25

def card_tex(x, y, rng):
    return (0.3 if y % 3 == 0 else -.1) + (rng.random() - .5) * .3

# ---------------------------------------------------------------- carpeta
def folder(color="gold", glyph=None, opened=False, seed="folder"):
    cv = Cv(f"{seed}{color}{glyph}{opened}")
    rb, rp = ramp(color), ramp("paper")
    cv.shadow(24, 42, 19, 3)
    # trasera con pestaña
    cv.paint(rrect(4, 11, 43, 39, 2) | poly([(4, 12), (6, 7), (20, 7), (23, 12)]), ramp(mix(hx(MAT.get(color, color)), DARK, .22)),
             grad=.7, tex=card_tex)
    # hojas asomando
    sheet2 = poly([(7, 10), (40, 9), (41, 38), (7, 38)])
    cv.paint(sheet2, rp, base=2.6, grad=.4, tex=paper_tex)
    top = poly([(9, 9), (41, 8), (42, 38), (9, 38)]) if not opened else poly([(8, 5), (41, 4), (42, 38), (8, 38)])
    cv.paint(top, rp, base=3.4, grad=.5, tex=paper_tex)
    ytxt = 12 if not opened else 8
    for yy in range(ytxt, ytxt + (4 if not opened else 14), 3):
        cv.lines(12, 38, yy, yy, 3, mix(rp[2], DARK, .35))
    if opened:
        cv.dot(10, 9, rp[5]); cv.stain(33, 14, 4, hx("#8A5A2A"))
    # panel frontal
    if not opened:
        front = rrect(4, 18, 43, 40, 2)
    else:
        front = poly([(3, 41), (6, 25), (44, 24), (45, 41)])
    cv.paint(front, rb, base=3.2, grad=1.3, tex=card_tex)
    fy = 18 if not opened else 25
    for x in range(6 if not opened else 8, 42):          # labio de luz y pliegue
        cv.dot(x, fy + 1, rb[5]); cv.dot(x, fy + 2, rb[4])
    for x in range(7, 41, 3):                             # costura
        cv.dot(x, 37, rb[1]); cv.dot(x + 1, 37, rb[1])
    cv.fill({(5, y) for y in range(fy + 3, 38)}, rb[4])
    # etiqueta y emblema
    lab = rrect(8, fy + 5, 24, fy + 13, 1)
    cv.paint(lab, rp, base=3.6, grad=.3, tex=paper_tex)
    cv.dot(9, fy + 6, rp[6])
    cv.lines(10, 22, fy + 8, fy + 11, 3, mix(rp[1], DARK, .1))
    cv.fill({(8, y) for y in range(fy + 5, fy + 14)}, ramp("rust")[3])
    if glyph in px.GLYPHS:
        cv.stamp(glyph, 28, fy + 5, rb[5], wear=.3)
        cv.stamp(glyph, 28, fy + 4, mix(rb[0], DARK, .3), wear=.06)
    # remaches de latón y mancha
    for p in ((6, fy + 3), (41, fy + 3)):
        cv.dot(*p, ramp("brass")[5]); cv.dot(p[0] + 1, p[1] + 1, ramp("brass")[1])
    cv.stain(35, 33, 4, hx("#5A3A1C"))
    return cv.im

# ---------------------------------------------------------------- documento
def document(color="gray", label="", glyph=None, seed="doc"):
    cv = Cv(f"{seed}{color}{label}")
    rp, rc = ramp("paper"), ramp(color)
    cv.shadow(24, 44, 15, 2)
    cv.paint(poly([(10, 6), (36, 5), (38, 43), (11, 44)]), rp, base=2.3, grad=.3, tex=paper_tex)     # hoja trasera
    cv.paint(poly([(8, 4), (33, 3), (33, 3), (35, 41), (9, 42)]) | rect(9, 5, 34, 41), rp, base=3.4, grad=.7, tex=paper_tex)
    # esquina doblada
    cv.fill(poly([(26, 3), (35, 3), (35, 12)]), CLEAR)
    cv.paint(poly([(26, 3), (26, 12), (35, 12)]), rp, base=2.2, grad=.5, tex=paper_tex)
    cv.dot(27, 4, rp[6])
    # líneas de texto irregulares
    cv.lines(12, 31, 17, 20, 3, mix(rp[1], DARK, .1))
    cv.lines(12, 31, 24, 29, 3, mix(rp[1], DARK, .1))
    cv.lines(12, 25, 32, 32, 3, mix(rp[1], DARK, .1))
    # sello con la etiqueta
    if label:
        w = len(label[:4]) * 4 + 3
        sx, sy = 22 - w // 2, 31
        ink = rc[2]
        for x in range(sx, sx + w):
            for y in (sy, sy + 8):
                if cv.rng.random() > .1: cv.dot(x, y, ink)
        for y in range(sy, sy + 9):
            for x in (sx, sx + w - 1):
                if cv.rng.random() > .1: cv.dot(x, y, ink)
        cv.text(label[:4], sx + 2, sy + 2, ink, wear=.14)
    # clip metálico
    cv.paint(rrect(11, 1, 14, 11, 1), ramp("steel"), grad=.9, tex=metal_tex)
    cv.stain(30, 38, 3, hx("#7A4A1E"))
    return cv.im


# ================================================================ objetos por tipo
def _c(name):
    return hx(MAT.get(name, name))

def photo(color="purple", label="", glyph=None, seed="img"):
    """Polaroid con un paisaje al atardecer."""
    cv = Cv(f"{seed}{label}")
    rp = ramp("paper")
    cv.shadow(24, 44, 15, 2)
    cv.paint(poly([(8, 5), (39, 4), (40, 43), (9, 44)]), rp, base=3.5, grad=.5, tex=paper_tex)
    x0, y0, x1, y1 = 12, 9, 36, 32
    sky_a, sky_b = _c("#E6A55C"), _c("#4E6E7C")
    for y in range(y0, y1 + 1):
        t = (y - y0) / (y1 - y0)
        for x in range(x0, x1 + 1):
            tt = t + (BAYER[y % 4][x % 4] / 16 - .5) * .22
            cv.dot(x, y, mix(sky_b, sky_a, max(0, min(1, tt * 1.4))))
    for x, y in ellipse(28, 19, 4, 4):
        cv.dot(x, y, _c("#FFE9A8"))
    for x, y in ring(28, 19, 5, 7):
        if (x + y) % 2 == 0: cv.dot(x, y, _c("#F4C77A"))
    far = poly([(x0, 26), (17, 19), (21, 24), (26, 17), (31, 25), (36, 21), (36, 32), (x0, 32)])
    cv.paint(far, ramp("#4F6B66"), base=3, grad=.6, grain=.05, outline=False)
    near = poly([(x0, 32), (x0, 28), (18, 26), (25, 29), (31, 27), (36, 30), (36, 32)])
    cv.paint(near, ramp("#2F4A3A"), base=2.6, grad=.5, grain=.05, outline=False)
    for tx in (15, 18, 32):
        cv.fill(poly([(tx, 24), (tx - 2, 29), (tx + 2, 29)]), _c("#1E3326"))
    for x in range(x0 - 1, x1 + 2):
        cv.dot(x, y0 - 1, rp[1]); cv.dot(x, y1 + 1, rp[5])
    for y in range(y0, y1 + 1):
        cv.dot(x0 - 1, y, rp[1]); cv.dot(x1 + 1, y, rp[5])
    for x in range(x0 + 1, x0 + 7): cv.dot(x, y0 + 1, mix(sky_a, WARM, .4))     # brillo
    cv.lines(14, 30, 37, 37, 2, mix(rp[1], DARK, .1))
    if label:
        cv.text(label[:3], 14, 38, ramp(color)[2], wear=.1)
    cv.paint(poly([(15, 2), (24, 1), (25, 6), (16, 7)]), ramp("#D8C79A"), base=3.8, grad=.2, grain=.1, outline=False)
    return cv.im

def cassette(color="pink", label="", glyph=None, seed="aud"):
    cv = Cv(f"{seed}{label}")
    rb, rp, rc = ramp("ink"), ramp("paper"), ramp(color)
    cv.shadow(24, 42, 19, 3)
    cv.paint(rrect(4, 11, 43, 39, 2), rb, base=2.4, grad=.6, tex=card_tex)
    cv.paint(rrect(8, 13, 39, 24, 1), rp, base=3.6, grad=.3, tex=paper_tex)
    cv.fill(rect(9, 14, 38, 19), rc[3])
    cv.fill(rect(9, 14, 38, 14), rc[5])
    if label: cv.text(label[:4], 11, 15, WARM, wear=0.05)
    cv.lines(11, 36, 22, 23, 3, mix(rp[1], DARK, .1))
    cv.paint(rrect(14, 26, 33, 35, 2), ramp("#1A1410"), base=2, grad=.3, grain=.02)
    for cx in (19, 28):
        cv.fill(ring(cx, 30, 1, 3), rp[4]); cv.dot(cx, 30, rb[0])
        for a in range(6):
            cv.dot(round(cx + 2.2 * math.cos(a * 1.047)), round(30 + 2.2 * math.sin(a * 1.047)), rp[6])
    cv.fill({(x, 33) for x in range(16, 32)}, _c("#6B3F26"))
    cv.paint(poly([(11, 36), (14, 39), (33, 39), (36, 36)]), ramp("#3A2E28"), base=3, grad=.4, outline=False)
    for p in ((6, 13), (41, 13), (6, 37), (41, 37)):
        cv.dot(*p, ramp("brass")[5])
    if label:
        cv.text(label[:4], 24 - (len(label[:4]) * 4 - 1) // 2, 17, rp[5], wear=.05) if False else None
    return cv.im

def clapper(color="brown", label="", glyph=None, seed="vid"):
    cv = Cv(f"{seed}{label}")
    rb, rp = ramp("ink"), ramp("paper")
    cv.shadow(24, 43, 18, 3)
    cv.paint(rrect(6, 19, 41, 41, 1), rb, base=2.6, grad=.7, tex=metal_tex)
    for y in (24, 29, 34):                                   # tiza
        cv.lines(10, 37, y, y, 5, rp[4], wear=.22)
    if label: cv.text(label[:4], 10, 36, rp[5], wear=.12)
    cv.paint(rrect(5, 11, 40, 18, 1), rb, base=2.4, grad=.6)
    stripes = []
    for k in range(7):
        x = 6 + k * 5
        stripes.append(poly([(x, 12), (x + 3, 12), (x + 1, 17), (x - 2, 17)]) & rect(5, 11, 40, 18))
    for k, m in enumerate(stripes):
        cv.fill(m, rp[4] if k % 2 == 0 else rb[2])
    cv.paint(rrect(5, 6, 38, 11, 1), rb, base=2.6, grad=.5)
    for k in range(7):
        x = 7 + k * 5
        cv.fill(poly([(x, 7), (x + 3, 7), (x + 1, 10), (x - 2, 10)]) & rect(6, 7, 37, 10), rp[4] if k % 2 else rb[2])
    cv.dot(7, 14, ramp("brass")[5]); cv.dot(38, 14, ramp("brass")[5])
    return cv.im

def crate(color="teal", label="", glyph=None, seed="arc"):
    cv = Cv(f"{seed}{label}")
    rw = ramp("wood")
    cv.shadow(24, 43, 19, 3)
    cv.paint(poly([(8, 11), (41, 11), (43, 15), (6, 15)]), ramp("#A06C3C"), base=3.6, grad=.4, tex=wood_tex)
    for i, (a, b) in enumerate(((16, 22), (23, 29), (30, 40))):
        cv.paint(rect(6, a, 43, b), rw, base=3.0 + (i % 2) * .3, grad=.7, tex=wood_tex)
    for x in (6, 7, 38, 39, 40, 41, 42, 43):
        pass
    cv.paint(rect(8, 15, 12, 40), ramp("#6E4426"), base=3, grad=.5, tex=wood_tex)
    cv.paint(rect(37, 15, 41, 40), ramp("#6E4426"), base=3, grad=.5, tex=wood_tex)
    for p in ((10, 18), (10, 26), (10, 36), (39, 18), (39, 26), (39, 36)):
        cv.dot(*p, ramp("steel")[5]); cv.dot(p[0], p[1] + 1, ramp("steel")[1])
    rope = ramp("#B89A68")
    cv.paint(rect(22, 11, 25, 40), rope, base=3.3, grad=.3, tex=lambda x, y, r: (0.6 if (y % 3) == 0 else -.2))
    cv.paint(ellipse(24, 28, 4, 3), rope, base=3.5, grad=.2)
    cv.paint(rrect(13, 22, 21, 30, 1), ramp("paper"), base=3.5, grad=.2, tex=paper_tex)
    if label: cv.text(label[:2], 14, 24, ramp(color)[2], wear=.1)
    cv.lines(14, 20, 30 - 1, 30 - 1, 1, ramp("paper")[1])
    return cv.im

def disc(color="orange", label="", glyph=None, seed="iso"):
    cv = Cv(f"{seed}{label}")
    cv.shadow(24, 44, 17, 2)
    cx, cy, R = 24, 24, 19
    rs = ramp("#9AA3A4")
    cv.paint(ellipse(cx, cy, R, R), rs, base=3.2, grad=.5, grain=.03, tex=metal_tex)
    for x, y in ellipse(cx, cy, R - 1, R - 1):
        ang = math.atan2(y - cy, x - cx)
        d = math.hypot(x - cx, y - cy)
        if 9 < d < R - 2:
            t = (math.sin(ang * 2) + 1) / 2
            tint = mix(_c("#D9A85A"), _c("#5FA7B0"), t) if int(ang * 3 + d / 3) % 2 == 0 else _c("#8E6FB0")
            if BAYER[y % 4][x % 4] < 6:
                cv.dot(x, y, mix(cv.get(x, y), tint, .45))
    cv.paint(ring(cx, cy, 4, 9), ramp(color), base=3.1, grad=.6, grain=.04)
    cv.fill(ring(cx, cy, 4, 5), rs[5])
    for x, y in ellipse(cx, cy, 3, 3):
        cv.dot(x, y, CLEAR)
    cv.fill(ring(cx, cy, 3, 4), rs[1])
    for k in range(7):                                       # arañazos y brillo
        a = cv.rng.random() * 6.28; d0 = 11 + cv.rng.random() * 4
        for t in range(3):
            cv.dot(round(cx + (d0 + t) * math.cos(a)), round(cy + (d0 + t) * math.sin(a)), rs[6])
    for a in range(200, 260, 5):
        cv.dot(round(cx + 17 * math.cos(math.radians(a))), round(cy + 17 * math.sin(math.radians(a))), WARM)
    if label:
        cv.text(label[:3], cx - (len(label[:3]) * 4 - 1) // 2, cy + 9, ramp(color)[1], wear=.1) if False else None
    return cv.im

def cog(color="gray", label="", glyph=None, seed="bin"):
    cv = Cv(f"{seed}{label}")
    cv.shadow(24, 44, 17, 2)
    rbz = ramp("brass")
    def gear(cx, cy, r_out, r_in, teeth, hole):
        pts = []
        for k in range(teeth * 4):
            a = k * 2 * math.pi / (teeth * 4)
            r = r_out if k % 4 in (0, 1) else r_in
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return poly(pts), ellipse(cx, cy, hole, hole)
    m, h = gear(21, 22, 19, 15, 10, 5)
    cv.paint(m - h, rbz, base=3.2, grad=.8, tex=metal_tex)
    cv.fill(ring(21, 22, 7, 8), rbz[5]); cv.fill(ring(21, 22, 10, 11), rbz[2])
    for a in range(0, 360, 45):
        cv.dot(round(21 + 12.5 * math.cos(math.radians(a))), round(22 + 12.5 * math.sin(math.radians(a))), rbz[1])
    m2, h2 = gear(37, 36, 10, 7, 7, 2)
    cv.paint(m2 - h2, ramp("steel"), base=3.2, grad=.8, tex=metal_tex)
    cv.fill(ring(37, 36, 2, 3), ramp("steel")[5])
    return cv.im

def crt(color="green", label="", glyph=None, seed="crt", prompt=False):
    cv = Cv(f"{seed}{label}")
    rb = ramp("#B6A785")
    cv.shadow(24, 44, 18, 2)
    cv.paint(rrect(5, 4, 42, 34, 3), rb, base=3.2, grad=.8, tex=card_tex)
    scr = rrect(9, 8, 38, 29, 3)
    cv.paint(scr, ramp("#1E3A28"), base=2.2, grad=.4, grain=.02, light=-.5)
    for y in range(9, 29):
        for x in range(10, 38):
            if (x, y) in scr and y % 2 == 0 and cv.get(x, y)[3]:
                cv.dot(x, y, mix(cv.get(x, y), DARK, .25))
    g = ramp("screen")
    if prompt:
        cv.fill({(11, 12), (12, 13), (11, 14)}, g[5]); cv.fill({(14, 14), (15, 14), (16, 14)}, g[5])
        cv.lines(11, 30, 18, 24, 3, g[3], wear=.1)
    else:
        cv.lines(11, 30, 11, 11, 1, g[3]); cv.lines(11, 22, 14, 14, 1, g[3])
        if label: cv.text(label[:2], 24 - (len(label[:2]) * 4 - 1) // 2 + 1, 18, g[5], wear=0)
        cv.lines(11, 28, 25, 26, 3, g[2], wear=.1)
    for x in range(11, 18): cv.dot(x, 10, mix(g[5], WARM, .5)) if False else None
    cv.fill({(10, 9), (11, 9), (10, 10)}, mix(ramp("#1E3A28")[5], WARM, .35))
    cv.dot(36, 32, ramp("red")[5]); cv.dot(33, 32, rb[1]); cv.dot(31, 32, rb[1])
    cv.paint(rect(18, 35, 29, 38), rb, base=2.6, grad=.4, tex=card_tex)
    cv.paint(rrect(11, 38, 36, 41, 1), rb, base=2.8, grad=.5, tex=card_tex)
    return cv.im

def fontblock(color="pink", label="", glyph=None, seed="font"):
    cv = Cv(f"{seed}")
    rw = ramp("wood")
    cv.shadow(24, 44, 17, 2)
    cv.paint(poly([(9, 12), (14, 7), (40, 7), (36, 12)]), ramp("#A67440"), base=3.6, grad=.3, tex=wood_tex)
    cv.paint(rect(9, 12, 36, 41), rw, base=3.2, grad=.8, tex=wood_tex)
    cv.paint(poly([(36, 12), (40, 7), (40, 36), (36, 41)]), ramp("#5E3A20"), base=2.4, grad=.4, tex=wood_tex)
    letter = poly([(13, 40), (21, 14), (27, 14), (35, 40), (29, 40), (27, 34), (21, 34), (19, 40)]) - poly([(22, 29), (26, 29), (24, 21)])
    cv.fill({(x + 1, y + 1) for x, y in letter}, mix(rw[5], WARM, .3))
    for x, y in letter:
        cv.dot(x, y, ramp("#1E1410")[1] if cv.rng.random() > .08 else rw[2])
    return cv.im

def key(color="yellow", label="", glyph=None, seed="key"):
    cv = Cv(f"{seed}{label}")
    cv.shadow(24, 44, 15, 2)
    rbz = ramp("brass")
    cv.paint(ring(14, 14, 4, 9) | ellipse(14, 14, 2, 2) - ellipse(14, 14, 3, 3), rbz, base=3.3, grad=.8, tex=metal_tex)
    cv.paint(line((20, 20), (38, 38), 4), rbz, base=3.2, grad=.4, tex=metal_tex)
    cv.paint(rect(33, 34, 36, 40) | rect(36, 31, 39, 36), rbz, base=3, grad=.4)
    cv.paint(poly([(8, 30), (18, 27), (20, 35), (10, 38)]), ramp("paper"), base=3.5, grad=.3, tex=paper_tex)
    cv.dot(12, 28, ramp("steel")[5])
    if label: cv.text(label[:3], 10, 31, ramp(color)[1], wear=.1)
    return cv.im

def padlock(color="yellow", label="", glyph=None, seed="lock"):
    cv = Cv(f"{seed}")
    cv.shadow(24, 44, 14, 2)
    st = ramp("steel"); rbz = ramp("brass")
    sh = ring(24, 18, 7, 10) & rect(0, 0, 47, 22) | rect(14, 18, 16, 24) | rect(32, 18, 34, 24)
    cv.paint(sh, st, base=3.2, grad=.8, tex=metal_tex)
    cv.paint(rrect(10, 22, 37, 42, 2), rbz, base=3.2, grad=1, tex=metal_tex)
    cv.fill(ellipse(24, 31, 3, 3), ramp("ink")[1]); cv.fill(rect(23, 32, 25, 37), ramp("ink")[1])
    for p in ((12, 24), (35, 24), (12, 40), (35, 40)):
        cv.dot(*p, rbz[5]); cv.dot(p[0] + 1, p[1] + 1, rbz[1])
    return cv.im

def cabinet(color="purple", label="", glyph=None, seed="db"):
    cv = Cv(f"{seed}{label}")
    cv.shadow(24, 44, 17, 2)
    rs = ramp("#6F8582")
    cv.paint(rrect(8, 4, 39, 42, 2), rs, base=3, grad=.6, tex=metal_tex)
    for k, y in enumerate((6, 18, 30)):
        cv.paint(rrect(10, y, 37, y + 10, 1), rs, base=3.2, grad=.9, tex=metal_tex)
        cv.paint(rect(17, y + 1, 30, y + 7), ramp("paper"), base=3.5, grad=.2, tex=paper_tex)
        if label: cv.text(label[:3], 24 - (len(label[:3]) * 4 - 1) // 2, y + 2, ramp(color)[1], wear=.08)
        cv.paint(rrect(20, y + 8, 27, y + 9, 0), ramp("brass"), base=3.4, grad=.3, grain=.0)
    if label: cv.text(label[:3], 19, 8, ramp(color)[1], wear=.1) if False else None
    return cv.im

def ledger(color="green", label="", glyph=None, seed="xls"):
    cv = Cv(f"{seed}{label}")
    rp = ramp("paper")
    cv.shadow(24, 44, 15, 2)
    cv.paint(poly([(8, 5), (36, 4), (38, 43), (9, 44)]), rp, base=3.4, grad=.6, tex=paper_tex)
    gc = mix(ramp("teal")[3], rp[3], .35)
    for x in range(12, 35, 7):
        for y in range(8, 41): cv.dot(x, y, gc) if cv.rng.random() > .05 else None
    for y in range(11, 41, 5):
        for x in range(11, 35): cv.dot(x, y, gc) if cv.rng.random() > .05 else None
    for r_ in range(4):
        for c_ in range(3):
            cv.lines(13 + c_ * 7, 17 + c_ * 7, 13 + r_ * 5, 13 + r_ * 5, 1, ramp("ink")[2], jitter=True, wear=.1)
    cv.fill(rect(12, 8, 34, 10), ramp(color)[3])
    cv.paint(poly([(24, 36), (40, 24), (42, 27), (26, 39)]), ramp("yellow"), base=3.3, grad=.4)
    cv.fill(poly([(24, 36), (26, 39), (22, 40)]), rp[4]); cv.dot(23, 39, ramp("ink")[1])
    cv.fill(poly([(40, 24), (42, 27), (44, 25), (42, 22)]), ramp("pink")[3])
    if label: cv.text(label[:3], 15, 5, ramp(color)[0], wear=0) if False else None
    return cv.im

def board(color="orange", label="", glyph=None, seed="ppt"):
    cv = Cv(f"{seed}{label}")
    rw, rp = ramp("wood"), ramp("paper")
    cv.shadow(24, 45, 15, 2)
    for p0, p1 in (((15, 32), (10, 45)), ((32, 32), (37, 45)), ((24, 32), (24, 45))):
        cv.paint(line(p0, p1, 2), rw, base=3, grad=.3, tex=wood_tex)
    cv.paint(rrect(5, 4, 42, 33, 1), rw, base=3.2, grad=.7, tex=wood_tex)
    cv.paint(rect(8, 7, 39, 30), rp, base=3.6, grad=.4, tex=paper_tex)
    cols = [ramp(color)[3], ramp("teal")[3], ramp("gold")[3], ramp("red")[3]]
    for k, h in enumerate((8, 13, 10, 17)):
        cv.paint(rect(11 + k * 6, 28 - h, 15 + k * 6, 28), ramp(mix(hx(MAT[color]), hx(MAT["teal"]), k / 3)), base=3.2, grad=.6, grain=.04)
    cv.fill(line((11, 20), (35, 11), 1), ramp("ink")[2])
    return cv.im

def book(color="brown", label="", glyph=None, seed="book"):
    cv = Cv(f"{seed}{label}")
    rl, rp, rbz = ramp(color if color != "gray" else "leather"), ramp("paper"), ramp("brass")
    cv.shadow(24, 44, 16, 2)
    cv.paint(rect(36, 8, 41, 42), rp, base=3, grad=.4, tex=paper_tex)
    for y in range(10, 41, 2): cv.dot(38, y, rp[1])
    cv.paint(rrect(8, 5, 38, 43, 2), rl, base=2.8, grad=.8, tex=card_tex)
    cv.paint(rect(8, 5, 14, 43), ramp(mix(hx(MAT.get(color, color)), DARK, .3)), base=2.4, grad=.5, tex=card_tex)
    for y in (11, 24, 37):
        cv.fill(rect(8, y, 14, y + 1), rbz[4]); cv.dot(8, y, rbz[6])
    for x in range(17, 36): cv.dot(x, 9, rbz[3]); cv.dot(x, 39, rbz[3])
    for y in range(9, 40): cv.dot(17, y, rbz[3]); cv.dot(35, y, rbz[3])
    cv.stamp("book", 21, 19, rbz[4], wear=.1)
    if label: cv.text(label[:4], 17 + (19 - len(label[:4]) * 4) // 2, 33, rbz[4], wear=.1)
    cv.paint(rect(24, 42, 26, 47), ramp("red"), base=3, grad=.3, outline=False)
    return cv.im

def envelope(color="teal", label="", glyph=None, seed="mail"):
    cv = Cv(f"{seed}{label}")
    rp = ramp("#CDB88A")
    cv.shadow(24, 42, 19, 3)
    cv.paint(rrect(4, 10, 43, 39, 1), rp, base=3.2, grad=.7, tex=paper_tex)
    cv.paint(poly([(4, 10), (43, 10), (24, 28)]), ramp("#D9C79C"), base=3.5, grad=.5, tex=paper_tex)
    for x, y in line((4, 39), (18, 26), 1) | line((43, 39), (29, 26), 1):
        cv.dot(x, y, rp[1])
    cv.paint(ellipse(24, 28, 5, 5), ramp("#9B2E22"), base=3.3, grad=.9, grain=.05)
    cv.fill(ring(24, 28, 2, 3), ramp("#9B2E22")[1]); cv.dot(23, 26, ramp("#9B2E22")[6])
    cv.paint(rect(34, 12, 41, 20), ramp(color), base=3, grad=.5, outline=False)
    for x in range(34, 42, 2): cv.dot(x, 12, rp[5])
    cv.lines(8, 20, 32, 36, 2, rp[1], wear=.1)
    return cv.im

def calendar(color="red", label="", glyph=None, seed="ics"):
    cv = Cv(f"{seed}{label}")
    rp = ramp("paper")
    cv.shadow(24, 44, 15, 2)
    cv.paint(rrect(8, 7, 39, 42, 1), rp, base=3.6, grad=.5, tex=paper_tex)
    cv.paint(rect(8, 7, 39, 15), ramp(color), base=3, grad=.7, tex=card_tex)
    for x in (14, 24, 33):
        cv.paint(rrect(x, 3, x + 1, 10, 0), ramp("steel"), base=3.4, grad=.3, grain=0)
    d = str(cv.rng.randint(10, 28))
    for k, ch in enumerate(d):
        bits = px._F[ch]
        for j in range(5):
            for i in range(3):
                if bits[j * 3 + i] == "1":
                    for a in range(3):
                        for b in range(3):
                            cv.dot(16 + k * 9 + i * 3 + a, 20 + j * 3 + b, ramp("ink")[2])
    for x in range(11, 37, 4): cv.dot(x, 38, rp[1]); cv.dot(x + 1, 38, rp[1])
    return cv.im

def carton(color="brown", label="", glyph=None, seed="pkg"):
    cv = Cv(f"{seed}{label}")
    rc = ramp("#B98A52")
    cv.shadow(24, 43, 19, 3)
    cv.paint(poly([(8, 10), (41, 10), (43, 16), (6, 16)]), ramp("#CFA36A"), base=3.5, grad=.4, tex=card_tex)
    cv.paint(rect(6, 16, 43, 40), rc, base=3.1, grad=.9, tex=card_tex)
    cv.paint(rect(21, 10, 27, 40), ramp("#D8C28E"), base=3.6, grad=.3, grain=.03, outline=False)
    cv.fill(rect(22, 10, 22, 40), ramp("#D8C28E")[5])
    cv.paint(rrect(9, 22, 19, 33, 1), ramp("paper"), base=3.6, grad=.2, tex=paper_tex)
    cv.stamp("up", 10, 24, ramp("ink")[2], wear=.05)
    if label: cv.text(label[:3], 29, 24, ramp(color)[2], wear=.1)
    cv.lines(30, 40, 31, 34, 3, rc[1], wear=.1)
    return cv.im

def globe(color="teal", label="", glyph=None, seed="globe"):
    cv = Cv(f"{seed}")
    rbz = ramp("brass")
    cv.shadow(24, 45, 13, 2)
    cv.paint(ellipse(24, 40, 9, 3) | rect(22, 33, 26, 40), rbz, base=3, grad=.8, tex=metal_tex)
    sea = ramp("#3E7C86")
    cv.paint(ellipse(24, 20, 17, 17), sea, base=3.1, grad=1, grain=.05)
    for blob in ((16, 15, 5, 4), (30, 13, 4, 3), (28, 25, 6, 5), (18, 28, 3, 3)):
        for x, y in ellipse(*blob):
            if (x - 24) ** 2 + (y - 20) ** 2 < 15 ** 2: cv.dot(x, y, mix(_c("#6E8A4A"), WARM, .15 if y < 20 else 0))
    for a in range(0, 360, 4):
        cv.dot(round(24 + 18 * math.cos(math.radians(a)) * .45), round(20 + 18 * math.sin(math.radians(a))), sea[5]) if a % 8 == 0 else None
    cv.paint(ring(24, 20, 17, 19) & rect(0, 0, 47, 47), rbz, base=3.1, grad=.6, tex=metal_tex)
    for x, y in ellipse(18, 12, 3, 2): cv.dot(x, y, mix(cv.get(x, y), WARM, .45))
    return cv.im

def doc_code(color="navy", label="", glyph=None, seed="code"):
    return crt(color, label, glyph, seed)

BUILDERS = {"image": photo, "audio": cassette, "video": clapper, "archive": crate, "tar": crate, "disc": disc,
            "gear": cog, "code": crt, "term": lambda *a, **k: crt(*a, **k, prompt=True), "font": fontblock,
            "key": key, "lock": padlock, "db": cabinet, "table": ledger, "slides": board, "book": book,
            "mail": envelope, "cal": calendar, "pkg": carton, "globe": globe}

def page(color="gray", label="", glyph="text"):
    b = BUILDERS.get(glyph)
    return b(color, label, glyph) if b else document(color, label, glyph)
