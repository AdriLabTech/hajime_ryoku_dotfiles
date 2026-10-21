#!/usr/bin/env python3
"""Genera el tema de iconos GTK «ryoku-pixel» (pixel art) y lo instala.

Uso: build_theme.py [destino]   (por defecto ~/.local/share/icons/ryoku-pixel)

- places: carpetas dibujadas a mano por color/glifo; el resto se pixeliza de Papirus-Dark.
- mimetypes: hoja con etiqueta (PDF, ISO, DOC…) por reglas sobre el nombre MIME.
- devices y apps instaladas: se pixelizan desde Papirus-Dark.
Lo no cubierto cae a Papirus-Dark (Inherits).
"""
import io, os, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image
import pixelart as px
import detail as sp

PAPIRUS = Path("/usr/share/icons/Papirus-Dark/64x64")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
VARIANT = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--variant=")), "")
DEST = Path(args[0] if args else f"~/.local/share/icons/ryoku-{VARIANT or 'pixel'}").expanduser()
THEME_NAME = {"buckshot": "Ryoku Buckshot"}.get(VARIANT, "Ryoku Pixel")


def grade(im):
    """Variante Buckshot: menos saturación, sombras granates de la sala, luces hueso, más contraste."""
    if VARIANT != "buckshot":
        return im
    im = im.convert("RGBA")
    px_ = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b_, a = px_[x, y]
            if a == 0:
                continue
            lum = (0.3 * r + 0.59 * g + 0.11 * b_) / 255
            r, g, b_ = [lum * 255 + (c - lum * 255) * .58 for c in (r, g, b_)]       # desatura
            k = max(0.0, 1 - lum * 1.6) * .45                                          # sombras -> verde sucio
            r, g, b_ = r * (1 - k) + 46 * k, g * (1 - k) + 20 * k, b_ * (1 - k) + 24 * k
            k2 = max(0.0, lum - .62) * .55                                             # luces -> ámbar
            r, g, b_ = r * (1 - k2) + 255 * k2, g * (1 - k2) + 232 * k2, b_ * (1 - k2) + 190 * k2
            r, g, b_ = [(c - 128) * 1.2 + 128 - 12 for c in (r, g, b_)]                 # contraste
            px_[x, y] = tuple(max(0, min(255, round(c))) for c in (r, g, b_)) + (a,)
    return im



# ---------------------------------------------------------------- PNG por tamaño entero
SIZES = (16, 24, 32, 48, 64, 96, 144, 192, 256)     # 48, 96, 144 y 192 son múltiplos enteros de la rejilla 48

class Writer:
    """Un PNG por icono y tamaño (vecino más cercano); los alias son symlinks."""
    def __init__(self, ctx):
        self.ctx, self.seen, self.n = ctx, {}, 0
        for s in SIZES:
            (DEST / f"{s}x{s}" / ctx).mkdir(parents=True, exist_ok=True)

    def put(self, name, key, make):
        first = key not in self.seen
        if first:
            im = grade(make().convert("RGBA"))
            self.seen[key] = name
        for s in SIZES:
            d = DEST / f"{s}x{s}" / self.ctx
            target = d / f"{name}.png"
            if first:
                if s < sp.N:      # tamaños pequeños: reducción suave, el detalle no cabe a píxel
                    small = im.resize((s, s), Image.Resampling.LANCZOS)
                    small.save(target, optimize=True)
                else:
                    im.resize((s, s), Image.Resampling.NEAREST).save(target, optimize=True)
            else:
                if target.is_symlink() or target.exists():
                    target.unlink()
                target.symlink_to(f"{self.seen[key]}.png")
        self.n += 1

# ---------------------------------------------------------------- carpetas
COLOR_ALIAS = {"paleorange": "orange", "deeporange": "orange", "palebrown": "brown",
               "bluegrey": "navy", "darkcyan": "teal", "carmine": "red", "magenta": "pink",
               "indigo": "navy", "violet": "purple", "grey": "gray", "nordic": "gray",
               "adwaita": "gray", "breeze": "cyan", "yaru": "orange"}
GLYPH_KW = [
    (r"document|^notes?$", "text"), (r"download|torrent", "down"), (r"music", "audio"),
    (r"picture|photo|image", "image"), (r"video", "video"), (r"templates", "table"),
    (r"public", "person"), (r"people|visiting", "person"), (r"remote|link", "link"),
    (r"mail", "mail"), (r"cloud|mega|dropbox|drive|yandex|onedrive|cloud|pcloud|meocloud|syncthing|sync", "cloud"),
    (r"git", "git"), (r"code|development|projects|java|script", "code"), (r"games|steam", "play"),
    (r"favorites|important|activities", "star"), (r"unlocked", "key"), (r"locked|private", "lock"),
    (r"network|wifi", "wifi"), (r"print", "print"), (r"books|obsidian", "book"),
    (r"backup|tar|snap", "archive"), (r"docker|vbox|vmware|wine|applications|android|apple", "pkg"),
    (r"recent", "cal"), (r"cd", "disc"), (r"systemd|linux|kde|gnome|arduino", "gear"),
    (r"desktop", "star"), (r"home", "home"), (r"drag-accept", "down"),
]
KNOWN_COLORS = set(px.COLORS) | set(COLOR_ALIAS) | {"black", "white"}
# cada carpeta especial, su cartulina
GLYPH_COLOR = {"down": "green", "audio": "purple", "image": "teal", "video": "red", "text": "blue", "table": "gray",
               "person": "cyan", "code": "navy", "star": "orange", "git": "orange", "lock": "gray", "key": "yellow",
               "cloud": "cyan", "pkg": "brown", "book": "brown", "mail": "teal", "wifi": "cyan", "print": "gray",
               "archive": "brown", "gear": "gray", "cal": "red", "disc": "orange", "play": "green", "link": "cyan"}

def folder_spec(name):
    """folder-[color-]kw[-open] / user-[color-]home|desktop[-open] -> (color, glyph, open)."""
    toks = name.split("-")
    if toks[0] in ("folder", "user"):
        toks = toks[1:]
    opened = "open" in toks
    toks = [t for t in toks if t != "open"]
    color = "gold"
    if toks and toks[0] in KNOWN_COLORS:
        color = COLOR_ALIAS.get(toks[0], toks[0])
        toks = toks[1:]
    explicit = color != "gold"
    kw = "-".join(toks)
    glyph = None
    for rx, g in GLYPH_KW:
        if re.search(rx, kw):
            glyph = g
            break
    if not explicit and glyph in GLYPH_COLOR:
        color = GLYPH_COLOR[glyph]
    return color, glyph, opened

def is_folder_name(n):
    return n.startswith("folder") or re.fullmatch(r"user-([a-z]+-)?(home|desktop)(-open)?", n) or n in (
        "inode-directory", "gtk-directory", "stock_folder", "stock_open", "gnome-home", "insync-folder")

# ---------------------------------------------------------------- mimetypes
# (regex sobre el nombre en minúsculas, etiqueta, color, glifo); gana la primera
R = [
    (r"pdf|postscript|acrobat|nappdf", "PDF", "red", "text"),
    (r"msword|wordprocessing|opendocument\.text|ms-word|x-office-document|abiword|\bdoc|wps-office\.doc|libreoffice.*writer", "DOC", "blue", "text"),
    (r"rtf", "RTF", "blue", "text"),
    (r"excel|msexcel|lotus123|spreadsheet|ms-excel|x-office-spreadsheet|libreoffice.*calc|wps-office\.xls", "XLS", "green", "table"),
    (r"csv|tab-separated", "CSV", "green", "table"),
    (r"powerpoint|mspowerpoint|presentation|slideshow|x-office-presentation|libreoffice.*impress|wps-office\.ppt|keynote", "PPT", "orange", "slides"),
    (r"opendocument\.graphics|libreoffice.*draw|drawing", "ODG", "orange", "image"),
    (r"opendocument\.database|libreoffice.*base|ms-access|msaccess|mdb|dbase|dbf", "DB", "purple", "db"),
    (r"epub|mobi|ebook|kindle", "EPUB", "brown", "book"),
    (r"djvu", "DJVU", "brown", "book"),
    (r"comicbook|cbz|cbr", "CBZ", "brown", "image"),
    (r"markdown|x-md|\bmd\b", "MD", "gray", "text"),
    (r"json", "JSON", "yellow", "code"),
    (r"yaml|yml", "YML", "yellow", "code"),
    (r"toml", "TOML", "yellow", "code"),
    (r"xml|rss|atom|gml|kml|xsl|rdf", "XML", "orange", "code"),
    (r"html|xhtml|htm", "HTML", "orange", "globe"),
    (r"css", "CSS", "blue", "code"),
    (r"typescript", "TS", "navy", "code"),
    (r"javascript|ecmascript|nodejs", "JS", "yellow", "code"),
    (r"python", "PY", "navy", "code"),
    (r"java|jar", "JAVA", "red", "code"),
    (r"rust", "RS", "orange", "code"),
    (r"cpp|hpp|cpp-src|cppsrc|cpphdr", "CPP", "navy", "code"),
    (r"csharp|c-sharp", "CS", "purple", "code"),
    (r"csrc|chdr|c", "C", "navy", "code"),
    (r"golang|text-x-go", "GO", "cyan", "code"),
    (r"php", "PHP", "purple", "code"),
    (r"ruby", "RB", "red", "code"),
    (r"perl", "PL", "navy", "code"),
    (r"lua", "LUA", "navy", "code"),
    (r"kotlin", "KT", "purple", "code"),
    (r"swift", "SWFT", "orange", "code"),
    (r"dart", "DART", "cyan", "code"),
    (r"coffeescript", "COFE", "brown", "code"),
    (r"sql|sqlite", "SQL", "purple", "db"),
    (r"x-sh|shellscript|shell|bash|zsh|fish|x-script|text-x-script", "SH", "green", "term"),
    (r"makefile|cmake|meson|gradle|maven", "MAKE", "gray", "gear"),
    (r"tex|latex|bibtex", "TEX", "green", "text"),
    (r"x-log|text-x-log", "LOG", "gray", "text"),
    (r"ini|conf|desktop|properties|cfg|settings", "CFG", "gray", "gear"),
    (r"x-subrip|subtitle|vtt|srt", "SRT", "gray", "text"),
    (r"calendar|ics|vcalendar", "ICS", "red", "cal"),
    (r"vcard|address-book", "VCF", "teal", "mail"),
    (r"x-iso|iso9660|\biso\b|efi\.iso|cd-image|cdimage|disc-image|-iso|toc|cue|nrg|mds|bin-cue", "ISO", "orange", "disc"),
    (r"disk-image|\bimg\b|raw-disk|msa-disk|fastcopy|efi\.img|vhd|vmdk|qcow|vdi|\bvm\b", "IMG", "orange", "disc"),
    (r"appimage", "APP", "green", "pkg"),
    (r"android.package|apk", "APK", "green", "pkg"),
    (r"flatpak", "FPK", "navy", "pkg"),
    (r"debian|\bdeb\b", "DEB", "red", "pkg"),
    (r"rpm", "RPM", "red", "pkg"),
    (r"x-snap|snap", "SNAP", "orange", "pkg"),
    (r"msi|installer", "MSI", "navy", "pkg"),
    (r"package|x-pak|archlinux|pacman|pkg\.tar|libreoffice\.extension|openofficeorg\.extension", "PKG", "brown", "pkg"),
    (r"7zip|x-7z", "7Z", "teal", "archive"),
    (r"zip", "ZIP", "teal", "archive"),
    (r"rar", "RAR", "teal", "archive"),
    (r"x-tar|tar", "TAR", "teal", "archive"),
    (r"gzip|x-gz|gz\b|bzip3|bzip2|x-bz|xz|zstd|lzma|lzip|lzop|compress|cab-compressed|ms-cab|squashfs|archive|cpio|arj|ace|lha|lzh|stuffit|ar\b|x-ar|jar", "ARC", "teal", "archive"),
    (r"x-ms-dos-executable|msdownload|x-dosexec|x-msdos|\bexe\b|ms-executable", "EXE", "navy", "gear"),
    (r"x-sharedlib|sharedlib|\.so|x-object|x-core|x-coredump", "SO", "gray", "gear"),
    (r"x-executable|executable|x-binary|octet-stream|x-pie", "BIN", "gray", "gear"),
    (r"google-apps-document|google-apps\.document", "DOC", "blue", "text"),
    (r"font|truetype|opentype|woff|x-font|ttf|otf", "FONT", "pink", "font"),
    (r"pgp-keys|pgp-signature|pgp|pkcs\d+|pkcs\d+-[a-z]+|pkix|certificate|x509|x-pem|x-cert|ssl|gnupg|\bkey\b|x-ssh", "KEY", "yellow", "key"),
    (r"ics|todo", "TODO", "red", "cal"),
    (r"x-torrent|bittorrent", "TOR", "green", "down"),
    (r"sqlite|database|mysql|mongodb|dbf|x-db", "DB", "purple", "db"),
    (r"svg", "SVG", "orange", "image"),
    (r"png", "PNG", "purple", "image"),
    (r"jpeg|jpg|jpe\b", "JPG", "purple", "image"),
    (r"gif", "GIF", "purple", "image"),
    (r"webp", "WEBP", "purple", "image"),
    (r"bmp|x-ms-bmp", "BMP", "purple", "image"),
    (r"tiff|tif", "TIFF", "purple", "image"),
    (r"x-icon|vnd\.microsoft\.icon|ico\b|icns", "ICO", "purple", "image"),
    (r"photoshop|psd|xcf|gimp|krita|kra\b|ora\b|illustrator|inkscape|affinity|afdesigner|aseprite|pixel", "ART", "pink", "image"),
    (r"x-raw|raw-image|dng|cr2|nef|arw|heic|heif|avif|jxl|jp2|exr|hdr|dds|tga|pcx|pnm|ppm|pgm|xpm|xbm|qoi|fits", "IMG", "purple", "image"),
    (r"^image-|image\b", "IMG", "purple", "image"),
    (r"mpeg|mp3|mpga", "MP3", "pink", "audio"),
    (r"flac", "FLAC", "pink", "audio"),
    (r"ogg|vorbis|opus", "OGG", "pink", "audio"),
    (r"wav|x-wav|riff", "WAV", "pink", "audio"),
    (r"midi|x-midi|mid\b", "MIDI", "pink", "audio"),
    (r"aac|m4a|mp4-audio|wma|aiff|ape\b|mka|ac3|dts|amr|musepack|mpc|tta|wv\b|caf", "AUD", "pink", "audio"),
    (r"^audio-|audio", "AUD", "pink", "audio"),
    (r"mp4|m4v", "MP4", "brown", "video"),
    (r"matroska|mkv|x-matroska", "MKV", "brown", "video"),
    (r"webm", "WEBM", "brown", "video"),
    (r"avi|msvideo", "AVI", "brown", "video"),
    (r"quicktime|mov\b", "MOV", "brown", "video"),
    (r"flash|swf|flv", "FLV", "red", "video"),
    (r"^video-|video|x-ms-asf|asf|wmv|ogv|3gp|mpg|mpeg-video|rmvb|realmedia|rn-real|mxf|vob|m2ts|mts|ts-video|apple\.mpegurl|m3u|pls|playlist", "VID", "brown", "video"),
    (r"x-nes-rom|nintendo|snes|rom|gba|nds|n64|sega|genesis|gameboy|atari|ps1|playstation|chess|pgn|sgf|game", "ROM", "green", "play"),
    (r"3d|blend|stl|obj\b|fbx|collada|dae\b|gltf|glb|dxf|dwg|acad|autocad|openscad|sweethome|scad", "3D", "cyan", "pkg"),
    (r"gpx|tcx|geo\+json|gpkg|shapefile|map|geo|osm|plt|rte|wpt|nmea|igc|fit\b", "GEO", "teal", "globe"),
    (r"dicom|mathematica|mathml|matlab|octave|latex-math|formula|math", "MATH", "navy", "table"),
    (r"x-theme|theme|css|qss", "THEM", "pink", "image"),
    (r"url|link|x-desktop|shortcut|webloc|\.lnk|ms-shortcut|internet-shortcut|symlink", "LINK", "cyan", "link"),
    (r"directory|inode|folder", "DIR", "gold", "none"),
    (r"diff|patch", "DIFF", "green", "code"),
    (r"x-cue|x-ruby|x-pascal|x-java|x-lisp|x-scheme|x-haskell|x-elixir|x-erlang|x-scala|x-objc|x-vala|x-zig|x-nim|x-fortran|x-asm|x-r\b|x-julia|text-x-.*src|-src$", "SRC", "navy", "code"),
    (r"x-ms-reg|registry|reg\b", "REG", "gray", "gear"),
    (r"x-ms-dos|batch|x-msdos-batch|powershell|bat\b|cmd\b", "BAT", "navy", "term"),
    (r"text-plain|text-x-generic|plain", "TXT", "gray", "text"),
    (r"^text-|text\b", "TXT", "gray", "text"),
    (r"x-office", "DOC", "blue", "text"),
    (r"packages?-|x-package", "PKG", "brown", "pkg"),
    (r"unknown|x-content|x-generic", "", "gray", "text"),
]
# cada regla casa con tokens completos (texto-x-... no debe activar «tex»)
RULES = [(re.compile(r"(?<![a-z0-9])(?:%s)(?![a-z0-9])" % rx.replace(r"\b", "")), lab, col, gl)
         for rx, lab, col, gl in R]

GENERIC = {  # icono genérico de shared-mime-info -> (etiqueta, color, glifo)
    "x-office-document": ("DOC", "blue", "text"), "x-office-spreadsheet": ("XLS", "green", "table"),
    "x-office-presentation": ("PPT", "orange", "slides"), "x-office-calendar": ("ICS", "red", "cal"),
    "x-office-address-book": ("VCF", "teal", "mail"), "package-x-generic": ("ARC", "teal", "archive"),
    "application-x-executable": ("BIN", "gray", "gear"), "font-x-generic": ("FONT", "pink", "font"),
    "image-x-generic": ("IMG", "purple", "image"), "audio-x-generic": ("AUD", "pink", "audio"),
    "video-x-generic": ("VID", "brown", "video"), "text-x-script": ("SRC", "navy", "code"),
    "text-html": ("HTML", "orange", "globe"), "media-optical": ("ISO", "orange", "disc"),
    "media-floppy": ("IMG", "orange", "disc"), "emblem-mail": ("MAIL", "teal", "mail"),
    "emblem-symbolic-link": ("LINK", "cyan", "link"), "security-high": ("KEY", "yellow", "key"),
    "application-x-addon": ("ADD", "green", "pkg"), "text-x-generic-template": ("TPL", "gray", "text"),
}

def norm(name):
    return re.sub(r"[^a-z0-9]+", "-", "-" + name.lower().replace("c++", "cpp") + "-")

def classify(name, generic=None):
    n = norm(name)
    for rx, lab, col, gl in RULES:
        if rx.search(n):
            return lab, col, gl
    if generic in GENERIC:
        return GENERIC[generic]
    return "", "gray", "text"

def mime_names():
    """Todos los nombres de icono MIME: Papirus + base shared-mime-info + genéricos."""
    names, generic = {}, {}
    for f in (PAPIRUS / "mimetypes").glob("*.svg"):
        names[f.stem] = None
    mime = Path("/usr/share/mime")
    for line in (mime / "types").read_text().split():
        names.setdefault(line.replace("/", "-"), None)
    for fn in ("aliases", "generic-icons"):
        p = mime / fn
        if p.exists():
            for line in p.read_text().splitlines():
                a, _, b = line.partition(" " if fn == "aliases" else ":")
                if a:
                    names.setdefault(a.replace("/", "-"), None)
                if fn == "generic-icons" and b:
                    generic[a.replace("/", "-")] = b.strip()
                    names.setdefault(b.strip(), None)
    for g in GENERIC:
        names.setdefault(g, None)
    names.update({k: None for k in ("unknown", "application-x-generic", "text-x-generic", "folder", "inode-directory")})
    return sorted(names), generic

# ---------------------------------------------------------------- pixelizar Papirus
def rasterize(svg: Path):
    r = subprocess.run(["rsvg-convert", "-w", "64", "-h", "64", str(svg)], capture_output=True)
    if r.returncode or not r.stdout:
        return None
    im = Image.open(io.BytesIO(r.stdout)).convert("RGBA").resize((sp.N, sp.N), Image.Resampling.BOX)
    return px.pixelize(im, size=sp.N, colors=24)

def installed_icon_names():
    names = set()
    for d in ("/usr/share/applications", os.path.expanduser("~/.local/share/applications")):
        if os.path.isdir(d):
            for f in Path(d).glob("*.desktop"):
                for line in f.read_text(errors="ignore").splitlines():
                    if line.startswith("Icon=") and "/" not in line:
                        names.add(line[5:].strip())
    return names

# ---------------------------------------------------------------- main
def main():
    if DEST.exists() and DEST.name.startswith("ryoku-"):
        shutil.rmtree(DEST)
    stats = {}

    # places
    w = Writer("places")
    for f in sorted((PAPIRUS / "places").glob("*.svg")):
        name = f.stem
        if is_folder_name(name):
            col, gl, op = folder_spec(name) if name not in ("inode-directory", "gtk-directory", "stock_folder", "insync-folder") else ("gold", None, False)
            if name in ("stock_open", "gnome-home"):
                col, gl, op = ("gold", "home" if "home" in name else None, name == "stock_open")
            w.put(name, ("f", col, gl, op), lambda c=col, g=gl, o=op: sp.folder(c, g, o))
        else:
            im = rasterize(f)
            if im:
                w.put(name, ("p", name), lambda im=im: im)
    stats["places"] = w.n

    # mimetypes
    w = Writer("mimetypes")
    names, generic = mime_names()
    for name in names:
        lab, col, gl = classify(name, generic.get(name))
        if name in ("text-x-generic", "application-x-generic", "unknown"):
            lab, col, gl = "", "gray", "text"
        if lab == "DIR":
            w.put(name, ("f", "gold", None, False), lambda: sp.folder("gold"))
        else:
            w.put(name, ("m", lab, col, gl), lambda l=lab, c=col, g=gl: sp.page(c, l, g))
    stats["mimetypes"] = w.n

    # devices + apps instaladas
    for ctx, wanted in (("devices", None), ("apps", installed_icon_names())):
        w = Writer(ctx)
        files = sorted((PAPIRUS / ctx).glob("*.svg"))
        files = [f for f in files if wanted is None or f.stem in wanted]
        with ThreadPoolExecutor(os.cpu_count() or 4) as ex:
            for f, im in zip(files, ex.map(rasterize, files)):
                if im:
                    w.put(f.stem, ("p", ctx, f.stem), lambda im=im: im)
        stats[ctx] = w.n

    ctxs = (("places", "Places"), ("mimetypes", "MimeTypes"), ("devices", "Devices"), ("apps", "Applications"))
    dirs = [f"{s}x{s}/{c}" for s in SIZES for c, _ in ctxs]
    (DEST / "index.theme").write_text(
        f"[Icon Theme]\nName={THEME_NAME}\nComment=Iconos pixel art detallados 48x48 para el escritorio Ryoku\n"
        "Inherits=Papirus-Dark,Adwaita,hicolor\n"
        f"Directories={','.join(dirs)}\n\n"
        + "".join(f"[{s}x{s}/{c}]\nContext={t}\nSize={s}\nType=Fixed\n\n" for s in SIZES for c, t in ctxs))
    subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(DEST)], capture_output=True)
    print(stats, "->", DEST)

if __name__ == "__main__":
    main()
