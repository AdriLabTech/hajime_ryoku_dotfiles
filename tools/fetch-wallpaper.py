#!/usr/bin/env python3
"""Descarga el fondo de Hajime: «Cosmic Cliffs» del telescopio espacial James Webb (NASA).

Imagen: NASA, ESA, CSA, STScI. Contenido de NASA, sin derechos de autor en EE. UU. y de uso libre con credito
(https://www.nasa.gov/nasa-brand-center/images-and-media/). No se guarda en el repositorio: se baja de NASA,
se comprueba su sha256, se recorta a 16:9 y se escala a 3840x2160.

  python3 -I tools/fetch-wallpaper.py SALIDA.png
Sale con codigo 1 si no hay red o la descarga no coincide (el instalador usa entonces el fondo generado).
"""
import hashlib, io, sys, urllib.request
from PIL import Image

URL = ("https://assets.science.nasa.gov/dynamicimage/assets/science/missions/webb/science/2022/07/"
       "STScI-01GA6KKWG229B16K4Q38CH3BXS.png?w=5120&h=2880&fit=crop")
SHA256 = "c2b560e6100171216a4b76a3a39213ae0334ac3cd8a98b1593ca49d604ea0069"

out = sys.argv[1]
try:
    data = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "hajime-dotfiles"}), timeout=120).read()
except Exception as e:
    sys.exit(f"no se pudo descargar el fondo: {e}")
if hashlib.sha256(data).hexdigest() != SHA256:
    sys.exit("la imagen descargada no coincide con la esperada (sha256); se descarta")
im = Image.open(io.BytesIO(data)).convert("RGB")
w, h = im.size
nh = round(w * 9 / 16)                                  # recorte 16:9 centrado
top = max(0, (h - nh) // 2)
im = im.crop((0, top, w, top + min(nh, h))).resize((3840, 2160), Image.LANCZOS)
im.save(out, optimize=False)
print(f"{out}: 3840x2160")
