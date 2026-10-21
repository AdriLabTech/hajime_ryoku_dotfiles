#!/usr/bin/env python3
"""Vista previa: logo ASCII de Arch (el de fastfetch/neofetch) girando sobre su eje vertical.

El logo se lee en el momento de `fastfetch` (no se distribuye ningun logo). Cada
caracter conserva su forma y solo cambia de columna: x' = centro + (x - centro) * cos.
De canto el logo se convierte en una columna de `|`.

  python3 -I tools/ascii-spin-preview.py gif SALIDA.gif   escribe un GIF animado
  python3 -I tools/ascii-spin-preview.py play             lo reproduce en la terminal (Ctrl+C sale)
"""
import math, subprocess, sys, time

FONT = "/usr/share/fonts/TTF/FiraCodeNerdFontMono-Bold.ttf"
BLUE, BG = (0x17, 0x93, 0xD1), (20, 22, 27)
FRAMES, MS, SIZE = 72, 40, 18


def read_logo():
    out = subprocess.run(["fastfetch", "-c", "none", "-l", "arch", "--pipe", "true"],
                         check=True, capture_output=True, text=True).stdout.splitlines()
    rows = [l[:40].rstrip() for l in out[:19]]          # el logo ocupa las 19 primeras lineas
    w = max(len(r) for r in rows)
    return [r.ljust(w) for r in rows]


def frame(rows, n):
    th = 2 * math.pi * n / FRAMES
    c, s = math.cos(th), math.sin(th)
    w = len(rows[0])
    cx = (w - 1) / 2
    sx = max(abs(c), 0.02)
    edge = abs(c) < 0.16
    out = []
    for r in rows:
        line = [" "] * (w + 2)
        depth = [-1e9] * (w + 2)
        for x, ch in enumerate(r):
            if ch == " ":
                continue
            u = (x - cx) * sx                       # reverso sin espejar: se usa |cos|
            z = (x - cx) * s * (1 if c >= 0 else -1)
            t = int(round(cx + u)) + 1
            if z > depth[t] or line[t] == " ":
                depth[t] = z
                line[t] = "|" if edge else ch
        out.append("".join(line))
    return out


def to_gif(path):
    from PIL import Image, ImageDraw, ImageFont
    rows = read_logo()
    font = ImageFont.truetype(FONT, SIZE)
    cw = font.getlength("M")
    ch = int(SIZE * 1.25)
    W, H = int(cw * (len(rows[0]) + 4)), ch * (len(rows) + 2)
    imgs = []
    for n in range(FRAMES):
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        for i, line in enumerate(frame(rows, n)):
            for j, chr_ in enumerate(line):
                if chr_ != " ":
                    d.text((cw * (j + 1), ch * (i + 1)), chr_, font=font, fill=BLUE)
        imgs.append(im)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=MS, loop=0)
    print(f"{path}: {FRAMES} fotogramas, {W}x{H}")


def play():
    rows = read_logo()
    n = 0
    sys.stdout.write("\x1b[?25l")
    try:
        while True:
            sys.stdout.write("\x1b[H\x1b[38;2;23;147;209m" + "\n".join(frame(rows, n)) + "\x1b[0m\n")
            sys.stdout.flush()
            n = (n + 1) % FRAMES
            time.sleep(MS / 1000)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\x1b[0m")


if len(sys.argv) >= 3 and sys.argv[1] == "gif":
    to_gif(sys.argv[2])
elif sys.argv[1:] == ["play"]:
    play()
else:
    sys.exit(__doc__)
