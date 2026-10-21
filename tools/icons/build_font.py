#!/usr/bin/env python3
"""Genera la fuente «Ryoku Pixel Icons» (iconos de terminal en pixel art 16x16).

Sustituye, vía `symbol_map` de kitty, los glifos Nerd Font que usan eza y yazi
para carpetas y ficheros. Monocromo: el color lo pone la terminal.

Uso: build_font.py [dir_trabajo]   -> escribe RyokuPixelIcons.ttf y pixel-icons.conf
"""
import re, sys
from pathlib import Path
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

import pixelart as px

HERE = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out"
NERD = "/usr/share/fonts/TTF/HackNerdFontMono-Regular.ttf"
G = 16

# ---------------------------------------------------------------- bitmaps
def blank():
    return [[0] * G for _ in range(G)]

def put_text(bm, s, cx, y):
    x = cx - px.text_w(s) // 2
    for ch in s.upper():
        bits = px._F.get(ch)
        if bits:
            for j in range(5):
                for i in range(3):
                    if bits[j * 3 + i] == "1" and 0 <= x + i < G:
                        bm[y + j][x + i] = 1
        x += 4

def small_glyph(name, size=8):
    """Reduce un glifo 11x11 a size x size por área."""
    rows = px.GLYPHS[name]
    out = [[0] * size for _ in range(size)]
    f = 11 / size
    for j in range(size):
        for i in range(size):
            tot = on = 0
            for y in range(int(j * f), min(11, int((j + 1) * f + .999))):
                for x in range(int(i * f), min(11, int((i + 1) * f + .999))):
                    tot += 1
                    on += rows[y][x] == "#"
            out[j][i] = 1 if tot and on / tot >= .4 else 0
    return out

def stamp(bm, mask, ox, oy, v=1):
    for j, row in enumerate(mask):
        for i, c in enumerate(row):
            if c and 0 <= oy + j < G and 0 <= ox + i < G:
                bm[oy + j][ox + i] = v

def file_frame():
    bm = blank()
    for y in range(16):
        for x in range(2, 14):
            bm[y][x] = 1 if (y in (0, 15) or x in (2, 13)) else 0
    for y in range(5):                       # esquina doblada de 4 px
        for x in range(9, 14):
            d = x - 9
            bm[y][x] = 0 if d > y else 1 if (d == y or x == 9 or y == 4) else 0
    return bm

def file_sprite(label=None, glyph=None):
    bm = file_frame()
    if label:
        put_text(bm, label[:2], 8, 8)
    elif glyph in px.GLYPHS:
        stamp(bm, small_glyph(glyph), 4, 6)
    return bm

def folder_sprite(opened=False, glyph=None):
    bm = blank()
    for x in range(0, 7):
        for y in (3, 4):
            bm[y][x] = 1
    bm[3][6] = 0
    if not opened:
        for y in range(5, 15):
            for x in range(0, 16):
                bm[y][x] = 1
        for x in range(0, 16):
            bm[5][x] = 0 if x > 7 else 1
        for x in range(8, 16):
            bm[5][x] = 1
        bm[5][7] = 0
        bm[6][0:16] = [1] * 16
        if glyph in px.GLYPHS:
            stamp(bm, small_glyph(glyph), 4, 6, 0)
    else:
        for y in range(5, 8):                 # trasera
            for x in range(0, 16):
                bm[y][x] = 1 if (y == 5 or x in (0, 15)) else 0
        for y in range(8, 15):                # frontal inclinada
            sh = (y - 8) // 3
            for x in range(3 - sh, 16 - sh):
                bm[y][x] = 1
        for x in range(1, 4):
            bm[7][x] = 1
    return bm

def free_sprite(glyph):
    bm = blank()
    stamp(bm, small_glyph(glyph, 12), 2, 2)
    return bm

def logo_sprite(label):
    bm = blank()
    for y in range(2, 14):
        for x in range(1, 15):
            bm[y][x] = 1
    for x, y in ((1, 2), (14, 2), (1, 13), (14, 13)):
        bm[y][x] = 0
    tmp = blank()
    put_text(tmp, label[:2], 8, 5)
    for y in range(G):
        for x in range(G):
            if tmp[y][x]:
                bm[y][x] = 0
    return bm

# ---------------------------------------------------------------- clasificación
SKIP_PREFIX = {"ple", "pl", "pom", "weather", "indent", "iec", "power", "extra", "indentation"}

LABELS = {
    "python": "PY", "javascript": "JS", "js": "JS", "typescript": "TS", "ts": "TS", "rust": "RS", "java": "JV",
    "kotlin": "KT", "go": "GO", "golang": "GO", "c": "C", "cpp": "C+", "csharp": "C#", "php": "PH", "ruby": "RB",
    "lua": "LU", "swift": "SW", "dart": "DT", "html": "HT", "css": "CS", "sass": "SA", "scss": "SA", "json": "JN",
    "markdown": "MD", "yaml": "YM", "toml": "TM", "xml": "XM", "sql": "SQ", "shell": "SH", "bash": "SH", "vim": "VM",
    "docker": "DK", "git": "GT", "haskell": "HS", "scala": "SC", "perl": "PL", "r": "R", "julia": "JL",
    "elixir": "EX", "erlang": "ER", "clojure": "CJ", "nix": "NX", "react": "RE", "vue": "VU", "svelte": "SV",
    "angular": "NG", "node": "ND", "npm": "NP", "tex": "TX", "txt": "TX", "csv": "CV", "log": "LG", "lock": "LK",
    "config": "CF", "makefile": "MK", "cmake": "CM", "gradle": "GR", "maven": "MV", "zig": "ZG", "nim": "NM",
    "ocaml": "ML", "fsharp": "F#", "coffee": "CO", "less": "LS", "pug": "PG", "ejs": "EJ", "svg": "SV",
    "terraform": "TF", "license": "LC", "readme": "RM", "ansible": "AN", "godot": "GD", "unity": "UN",
    "arduino": "AR", "android": "AN", "apple": "AP", "windows": "WN", "linux": "LX", "arch": "AR",
    "debian": "DB", "ubuntu": "UB", "fedora": "FD", "manjaro": "MJ", "nixos": "NX", "gentoo": "GE",
}
GLYPH_RULES = [
    (r"pdf", ("label", "PD")), (r"word|\bdoc", ("label", "DC")), (r"excel|spreadsheet|sheet|table|csv", ("glyph", "table")),
    (r"powerpoint|presentation|slide", ("glyph", "slides")), (r"image|photo|picture|camera|png|jpg|gif", ("glyph", "image")),
    (r"audio|music|sound|headphone|note\b|midi|mp3", ("glyph", "audio")), (r"video|film|movie|play", ("glyph", "video")),
    (r"archive|zip|tar|package|pkg|box|gift", ("glyph", "archive")), (r"database|\bdb\b|sql", ("glyph", "db")),
    (r"font|typography", ("glyph", "font")), (r"lock|shield|secret", ("glyph", "lock")), (r"key|cert|pgp", ("glyph", "key")),
    (r"cog|gear|settings|config|wrench|tools?", ("glyph", "gear")), (r"disc|cd\b|iso|dvd|floppy|save", ("glyph", "disc")),
    (r"terminal|console|shell|bash|prompt|command", ("glyph", "term")), (r"globe|web|html|browser|world", ("glyph", "globe")),
    (r"book|epub|read|library|journal|bookmark", ("glyph", "book")), (r"calendar|clock|time", ("glyph", "cal")),
    (r"mail|envelope|email", ("glyph", "mail")), (r"star|favou?rite|heart", ("glyph", "star")),
    (r"download", ("glyph", "down")), (r"upload", ("glyph", "up")), (r"home", ("glyph", "home")),
    (r"cloud", ("glyph", "cloud")), (r"user|person|people|account", ("glyph", "person")),
    (r"trash|delete|bin\b", ("glyph", "trash")), (r"print", ("glyph", "print")),
    (r"git|branch|source_branch|merge|commit", ("glyph", "git")), (r"code|script|json|xml|yaml|toml", ("glyph", "code")),
    (r"text|document|file_document|align|list|note", ("glyph", "text")),
]
GLYPH_RULES = [(re.compile(rx), v) for rx, v in GLYPH_RULES]
FOLDER_GLYPH = [(re.compile(rx), g) for rx, g in (
    (r"git|github|gitlab", "git"), (r"config|cog|settings|vscode|idea|\.", "gear"), (r"node|npm|package|docker", "pkg"),
    (r"download", "down"), (r"music|audio", "audio"), (r"image|photo|picture", "image"), (r"video|movie", "video"),
    (r"doc|text|book", "text"), (r"home", "home"), (r"star|favou?rite", "star"), (r"lock|private|ssh", "lock"),
    (r"cloud|drive", "cloud"), (r"code|dev|src|source|project", "code"), (r"key", "key"),
)]

def classify(name):
    """name de glifo Nerd (p. ej. 'seti-python', 'fa-file_pdf_o') -> sprite o None (se deja el glifo original)."""
    prefix, _, rest = name.partition("-")
    if prefix in SKIP_PREFIX:
        return None
    r = rest.lower()
    if re.search(r"folder|directory|\bdir\b", r) and "file_" not in r.replace("file_directory", ""):
        g = next((g for rx, g in FOLDER_GLYPH if rx.search(r)), None)
        return ("folder", "open" in r, g)
    if prefix == "linux":
        return ("logo", LABELS.get(r.split("_")[0], r[:2].upper()))
    if re.search(r"symlink|\blink\b|shortcut", r):
        return ("free", "link")
    token = re.sub(r"^(file_|language_|logo_|language-)", "", r)
    for t in re.split(r"[_\-]", token):
        if t in LABELS and prefix in ("seti", "dev", "custom", "md", "fa", "fae", "oct", "cod"):
            return ("file", LABELS[t], None)
    for rx, spec in GLYPH_RULES:
        if rx.search(r):
            return ("file", spec[1], None) if spec[0] == "label" else ("file", None, spec[1])
    if "file" in r:
        return ("file", None, "text")
    if prefix in ("seti", "dev", "custom"):
        return ("file", token[:2].upper() if token else None, None)
    return None

# ---------------------------------------------------------------- fuente
UNIT = 62.5

def bitmap_to_glyph(bm):
    pen = TTGlyphPen(None)
    for y in range(G):
        x = 0
        while x < G:
            if bm[y][x]:
                x0 = x
                while x < G and bm[y][x]:
                    x += 1
                top = int(round((G - y) * UNIT - 110))
                bot = int(round((G - y - 1) * UNIT - 110))
                l, r = int(round(x0 * UNIT)), int(round(x * UNIT))
                pen.moveTo((l, bot)); pen.lineTo((l, top)); pen.lineTo((r, top)); pen.lineTo((r, bot)); pen.closePath()
            else:
                x += 1
    return pen.glyph()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cps = set()
    for fn in ("eza.cp", "yazi.cp"):
        p = HERE / "data" / fn
        cps |= {int(x) for x in p.read_text().split()}
    nerd = TTFont(NERD).getBestCmap()
    cps = sorted(c for c in cps if c in nerd)

    glyphs, cmap, order, used = {".notdef": TTGlyphPen(None).glyph()}, {}, [".notdef"], 0
    cache = {}
    for cp in cps:
        spec = classify(nerd[cp])
        if not spec:
            continue
        key = spec
        if key not in cache:
            kind = spec[0]
            bm = (folder_sprite(spec[1], spec[2]) if kind == "folder" else
                  file_sprite(spec[1], spec[2]) if kind == "file" else
                  free_sprite(spec[1]) if kind == "free" else logo_sprite(spec[1]))
            gname = f"px{len(cache):04d}"
            cache[key] = gname
            glyphs[gname] = bitmap_to_glyph(bm)
            order.append(gname)
        cmap[cp] = cache[key]
        used += 1

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({g: (1000, 0) for g in order})
    fb.setupHorizontalHeader(ascent=900, descent=-200)
    fb.setupNameTable({"familyName": "Ryoku Pixel Icons", "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=900, sTypoDescender=-200, usWinAscent=900, usWinDescent=200)
    fb.setupPost()
    ttf = OUT / "RyokuPixelIcons.ttf"
    fb.save(str(ttf))

    cp_list = ",".join(f"U+{c:X}" for c in sorted(cmap))
    (OUT / "pixel-icons.conf").write_text(
        "# Iconos pixel art de eza/yazi (generado por ryoku-pixel-icons/build_font.py)\n"
        f"symbol_map {cp_list} Ryoku Pixel Icons\n")
    print(f"{used} codepoints -> {len(cache)} glifos distintos: {ttf}")

if __name__ == "__main__":
    main()
