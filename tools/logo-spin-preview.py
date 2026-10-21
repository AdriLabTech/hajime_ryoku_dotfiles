#!/usr/bin/env python3
"""Vista previa: logo oficial de Arch, plano y sin retocar, girando sobre su eje vertical.

Lee el SVG que ya trae el sistema (/usr/share/pixmaps/archlinux-logo.svg, paquete
`filesystem`); no se distribuye ninguna imagen del logo. Escribe un GIF animado.

  python3 -I tools/logo-spin-preview.py SALIDA.gif [--bg RRGGBB]
"""
import io, math, re, subprocess, sys
import numpy as np
from PIL import Image

SVG = "/usr/share/pixmaps/archlinux-logo.svg"
ARCH_BLUE = (0x17, 0x93, 0xD1)          # color oficial del logo
FRAMES, MS = 90, 33
W, H, SS = 270, 342, 3                  # 30x19 celdas de kitty (9x18 px), supersampling


def logo_mask(size):
    # el SVG trae ademas dos trazos pequenos con el "TM": primero el logo, luego el resto
    paths = re.findall(r"<path[^>]*/>", open(SVG).read())
    svg = ('<svg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg"><g fill="#000">'
           + paths[0] + "</g></svg>")
    png = subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size)], check=True,
                         capture_output=True, input=svg.encode()).stdout
    m = Image.open(io.BytesIO(png)).convert("RGBA").getchannel("A")
    return m.crop(m.getbbox())


def main():
    out = sys.argv[1]
    bg = tuple(int(sys.argv[sys.argv.index("--bg") + 1][i:i + 2], 16) for i in (0, 2, 4)) \
        if "--bg" in sys.argv else (20, 22, 27)
    w, h = W * SS, H * SS
    m = logo_mask(int(h * 0.8))
    mw, mh = m.size
    thick = 0.08 * mw                    # canto fino para que no desaparezca de perfil
    layers = 24
    frames = []
    for n in range(FRAMES):
        th = 2 * math.pi * n / FRAMES
        c, s = math.cos(th), math.sin(th)
        canvas = Image.new("RGB", (w, h), bg)
        order = range(layers) if c >= 0 else range(layers - 1, -1, -1)   # lejos -> cerca
        for i in order:
            z = -thick / 2 + thick * i / (layers - 1)
            face = i == (layers - 1 if c >= 0 else 0)          # cara visible
            # ortografica: x' = x*c + z*s ; el reverso se ve igual (no en espejo)
            src = m
            sx = max(abs(c), 0.02)
            sw = max(int(mw * sx), 1)
            piece = src.resize((sw, mh), Image.LANCZOS)
            cx = w / 2 + z * s
            if face:
                col = Image.new("RGB", piece.size, ARCH_BLUE)
            else:
                k = 0.55 + 0.25 * i / (layers - 1)
                col = Image.new("RGB", piece.size, tuple(int(v * k) for v in ARCH_BLUE))
            canvas.paste(col, (int(cx - sw / 2), int((h - mh) / 2)), piece)
        frames.append(canvas.resize((W, H), Image.LANCZOS))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=MS, loop=0)
    print(f"{out}: {FRAMES} fotogramas, {W}x{H}")


main()
