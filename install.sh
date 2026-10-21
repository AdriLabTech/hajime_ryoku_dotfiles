#!/usr/bin/env bash
# Hajime: dotfiles para Ryoku Arch (y, con --arch, para Arch puro).
#
#   ./install.sh [--arch] [--packages] [--dry-run] [--yes] [--uninstall]
#
#   --arch       si Ryoku no esta instalado, ejecuta antes el convertidor OFICIAL de Ryoku
#                (cambia el gestor de sesion a SDDM, hace pacman -Syu, etc.; ver README)
#   --packages   instala con pacman lo de packages/*.txt (pide sudo)
#   --dry-run    no cambia nada: muestra lo que haria (con --arch, el plan del convertidor)
#   --yes        no pregunta (el convertidor tambien va sin preguntas)
#   --uninstall  quita lo que puso Hajime (enlaces, copias, bloques); no toca paquetes ni plugins
#
# ryoku/           se refleja en $HOME con enlaces simbolicos (copias bajo .config/ryoku/user_edits)
# ryoku-snippets/  bloques que se anaden entre marcas a ficheros que tambien son del usuario
# Lo que ya exista se guarda en ~/.local/state/hajime/backup-<fecha>/.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
backup="$HOME/.local/state/hajime/backup-$(date +%Y%m%d-%H%M%S)"
CONVERTER="https://raw.githubusercontent.com/neur0map/ryoku-arch/main/ryoku-shell-installer/install.sh"
BEGIN="# >>> hajime >>>" END="# <<< hajime <<<"
dry=0 undo=0 arch=0 pkgs=0 yes=0 overlay_changed=0

same() { [ "$(<"$1")" = "$(<"$2")" ]; }   # sin depender de cmp/diffutils
say() { printf '%s\n' "$*"; }
die() { printf 'hajime: %s\n' "$*" >&2; exit 1; }
run() { if [ "$dry" = 1 ]; then say "[dry-run] $*"; else "$@"; fi; }
confirm() {
  [ "$yes" = 1 ] && return 0
  local a; read -r -p "$1 [s/N] " a </dev/tty || return 1
  [[ "$a" =~ ^[sSyY]$ ]]
}

for a in "$@"; do
  case "$a" in
    --dry-run) dry=1 ;;
    --uninstall) undo=1 ;;
    --arch) arch=1 ;;
    --packages) pkgs=1 ;;
    --yes) yes=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) die "opcion desconocida: $a" ;;
  esac
done
[ "$(id -u)" != 0 ] || die "ejecutalo como tu usuario, no como root"

# --- Ryoku sobre Arch puro: convertidor oficial -------------------------------------------
install_ryoku() {
  if command -v ryoku >/dev/null 2>&1; then say "Ryoku ya esta instalado."; return; fi
  [ "$arch" = 1 ] || die "Ryoku no esta instalado. Usa --arch para instalarlo (o instala Ryoku por su ISO)."
  command -v curl >/dev/null 2>&1 || die "falta curl"
  tmp="$(mktemp -d)"; CONV_TMP="$tmp"; trap 'rm -rf "$CONV_TMP"' EXIT
  curl -fsSL "$CONVERTER" -o "$tmp/ryoku-convert.sh" || die "no se pudo descargar el convertidor de Ryoku"
  say "Convertidor oficial descargado: sha256 $(sha256sum "$tmp/ryoku-convert.sh" | cut -d' ' -f1)"
  say "--- plan del convertidor (--dry-run, no cambia nada) ---"
  # el dry-run del convertidor es sin interfaz (--yes) y acaba con error aunque el plan sea correcto
  # (no compila yay-bin); solo se considera rechazo si dice que no admite este sistema.
  local plan; plan="$(bash "$tmp/ryoku-convert.sh" --dry-run --yes 2>&1)" || true
  printf '%s\n' "$plan"
  if printf '%s' "$plan" | grep -qiE 'needs systemd|not supported|refus'; then die "el convertidor rechazo este sistema (ver arriba)"; fi
  [ "$dry" = 1 ] && return
  say "El convertidor hara pacman -Syu, cambiara a SDDM + NetworkManager y guardara una copia"
  say "para deshacerlo (~/.local/state/ryoku/shell-install/). Se deshace con --uninstall del convertidor."
  confirm "¿Instalar Ryoku en este Arch?" || die "cancelado"
  # El convertidor llama a `sudo -n` (sin preguntar) y falla a mitad si sudo pide contrasena (la credencial
  # en cache no le llega). Se concede sudo sin contrasena a este usuario SOLO mientras dura la instalacion,
  # con una contrasena ahora, y el fichero se borra al terminar (tambien si falla o se corta con Ctrl+C).
  DROP=/etc/sudoers.d/99-hajime-install
  say "El convertidor usa sudo sin preguntar. Se creara ${DROP} (sudo sin contrasena para $USER) y se"
  say "BORRARA al terminar, tambien si falla o lo cortas. Escribe tu contrasena si te la pide:"
  sudo -v || die "sin sudo no se puede instalar Ryoku"
  cleanup_sudo() { [ -e "$DROP" ] && sudo -n rm -f "$DROP" 2>/dev/null; return 0; }
  trap 'cleanup_sudo; rm -rf "$CONV_TMP"' EXIT INT TERM
  printf '%s ALL=(ALL:ALL) NOPASSWD: ALL\n' "$USER" | sudo tee "$DROP" >/dev/null && sudo chmod 0440 "$DROP" \
    && sudo visudo -cf "$DROP" >/dev/null || { cleanup_sudo; die "no se pudo preparar sudo para el convertidor"; }
  # El convertidor devuelve codigo 1 por un fallo de su limpieza final ("work: unbound variable") aunque
  # termine bien, y tambien puede fallar a medias con el mismo codigo. Se mira su estado: el ultimo paso
  # es `verify`.
  local rc=0; bash "$tmp/ryoku-convert.sh" ${yes:+--yes} || rc=$?
  cleanup_sudo; say "sudo sin contrasena retirado (${DROP})."
  hash -r
  # El estado del convertidor (`shell-install-state.json`) solo queda en disco si NO termino: al acabar lo
  # borra. Si queda y le falta `verify`, la conversion esta a medias.
  local st="$HOME/.local/state/ryoku/shell-install-state.json" ok=1
  if [ -f "$st" ]; then
    if command -v jq >/dev/null 2>&1; then jq -e '.completed | index("verify")' "$st" >/dev/null 2>&1 || ok=0
    else [ "$rc" = 0 ] || ok=0; fi
  fi
  if [ "$ok" = 1 ] && command -v ryoku >/dev/null 2>&1; then
    [ "$rc" = 0 ] || say "aviso: el convertidor termino con codigo $rc, pero completo todos sus pasos; se sigue."
    say "Ryoku instalado. Reinicia para usar su escritorio (SDDM)."
  else
    die "la conversion no termino (codigo $rc). Vuelve a ejecutar ./install.sh --arch: el convertidor reanuda donde lo dejo. Registro: ~/.local/state/ryoku/shell-install.log"
  fi
}

# --- paquetes ------------------------------------------------------------------------------
install_packages() {
  local list; list="$(grep -hv '^\s*#' "$repo"/packages/*.txt | grep -v '^\s*$' | sort -u | tr '\n' ' ')"
  say "Paquetes: $list"
  run sudo pacman -S --needed --noconfirm $list
}

# --- ficheros ------------------------------------------------------------------------------
is_copy() { case "$1" in .config/ryoku/user_edits/*|.config/ryoku/anim-preset) return 0 ;; *) return 1 ;; esac; }

place() {  # $1 = ruta en el repo, $2 = ruta relativa a $HOME
  local f="$1" rel="$2" dst="$HOME/$2"
  if is_copy "$rel"; then
    if [ -f "$dst" ] && [ ! -L "$dst" ] && same "$f" "$dst"; then say "ya instalado ~/$rel"; return; fi
  elif [ -L "$dst" ] && [ "$(readlink "$dst")" = "$f" ]; then say "ya enlazado ~/$rel"; return
  fi
  run mkdir -p "$(dirname "$dst")"
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    run mkdir -p "$backup/$(dirname "$rel")"; run mv "$dst" "$backup/$rel"; say "copia de seguridad de ~/$rel"
  fi
  if is_copy "$rel"; then run cp "$f" "$dst"; overlay_changed=1; say "copiado ~/$rel"
  else run ln -s "$f" "$dst"; say "enlazado ~/$rel"; fi
}

unplace() {
  local f="$1" rel="$2" dst="$HOME/$2"
  if is_copy "$rel"; then
    [ -f "$dst" ] && same "$f" "$dst" && { run rm "$dst"; overlay_changed=1; say "quitado ~/$rel"; }
  elif [ -L "$dst" ] && [ "$(readlink "$dst")" = "$f" ]; then run rm "$dst"; say "quitado ~/$rel"
  fi
  return 0
}

strip_block() {  # imprime $1 sin el bloque de Hajime
  awk -v b="$BEGIN" -v e="$END" '$0==b{skip=1} !skip{print} $0==e{skip=0}' "$1"
}

snippet() {  # $1 = ruta en el repo, $2 = ruta relativa a $HOME
  local f="$1" rel="$2" dst="$HOME/$2" tmp
  run mkdir -p "$(dirname "$dst")"
  [ -f "$dst" ] || run touch "$dst"
  [ "$dry" = 1 ] && { say "[dry-run] bloque de Hajime en ~/$rel"; return; }
  tmp="$(mktemp)"
  { strip_block "$dst"; printf '%s\n' "$BEGIN"; cat "$f"; printf '%s\n' "$END"; } > "$tmp"
  if same "$tmp" "$dst"; then rm "$tmp"; say "bloque ya presente en ~/$rel"
  else cat "$tmp" > "$dst"; rm "$tmp"; say "bloque anadido a ~/$rel"; fi
}

unsnippet() {
  local dst="$HOME/$2" tmp
  [ -f "$dst" ] && grep -qxF "$BEGIN" "$dst" || return 0
  [ "$dry" = 1 ] && { say "[dry-run] quitar bloque de ~/$2"; return; }
  tmp="$(mktemp)"; strip_block "$dst" > "$tmp"; cat "$tmp" > "$dst"; rm "$tmp"; say "bloque quitado de ~/$2"
}

each() {  # $1 = directorio base, $2 = funcion
  [ -d "$1" ] || return 0
  while IFS= read -r -d '' f; do "$2" "$f" "${f#"$1"/}"; done < <(find "$1" -type f -not -path '*/__pycache__/*' -print0 | sort -z)
}

# --- plugins de Ryoku ------------------------------------------------------------------------
install_plugins() {
  command -v ryoku >/dev/null 2>&1 || { say "sin ryoku: plugins omitidos"; return; }
  local url id
  while IFS= read -r url; do
    id="$(basename "$url" .git)"
    if ryoku plugin list 2>/dev/null | awk '{print $1}' | grep -qx "$id"; then say "plugin $id ya instalado"; continue; fi
    run ryoku plugin add "$url" --yes || say "aviso: no se pudo instalar el plugin $id"
  done < <(grep -hv '^\s*#' "$repo/plugins.txt" | grep -v '^\s*$')
  enable_plugins
}

# activa (widget de escritorio) los plugins de plugins.txt; Ryoku guarda el estado en plugins.json
enable_plugins() {
  local cfg="$HOME/.config/ryoku/plugins.json" url id tmp
  [ "$dry" = 1 ] && { say "[dry-run] activar los plugins de plugins.txt"; return; }
  [ -f "$cfg" ] && command -v jq >/dev/null 2>&1 || { say "aviso: no se pudieron activar los plugins (falta plugins.json o jq)"; return; }
  while IFS= read -r url; do
    id="$(basename "$url" .git)"
    jq -e --arg id "$id" 'has($id)' "$cfg" >/dev/null 2>&1 || continue
    tmp="$(mktemp)"
    jq --arg id "$id" '.[$id].enabled = true | .[$id].host //= "desktopWidget" | .[$id].desktopWidget //= {"x": 32, "y": 256, "scale": 1.5, "locked": false}' "$cfg" > "$tmp" \
      && cat "$tmp" > "$cfg" && say "plugin $id activado"
    rm -f "$tmp"
  done < <(grep -hv '^\s*#' "$repo/plugins.txt" | grep -v '^\s*$')
}

# --- fotogramas del logo para kitty (se dibujan aqui, con tu fuente; no se distribuyen) ---------------
build_spin() {
  [ "$dry" = 1 ] && { say "[dry-run] hajime-fetch build"; return; }
  python3 -c 'import PIL' 2>/dev/null || { say "aviso: falta python-pillow; el logo girara solo una vuelta"; return; }
  "$HOME/.local/bin/hajime-fetch" build >/dev/null 2>&1 && say "fotogramas del logo generados" \
    || say "aviso: no se pudieron generar los fotogramas; el logo girara solo una vuelta"
}

# --- iconos pixel art (los de Adrian): el tema y la fuente de terminal se generan aqui ----------------
ICONS="$HOME/.local/share/icons/ryoku-buckshot"
FONTS="$HOME/.local/share/fonts/RyokuPixelIcons"
build_icons() {
  if [ "$dry" = 1 ]; then say "[dry-run] generar iconos pixel art (tema ryoku-buckshot y fuente de terminal)"; return; fi
  python3 -c 'import PIL, fontTools' 2>/dev/null || { say "aviso: faltan python-pillow/python-fonttools; sin iconos pixel art"; return; }
  [ -d /usr/share/icons/Papirus-Dark ] || { say "aviso: falta papirus-icon-theme; sin iconos pixel art"; return; }
  say "generando iconos pixel art (unos 30 s)..."
  python3 "$repo/tools/icons/build_theme.py" --variant=buckshot "$ICONS" >/dev/null 2>&1 \
    || { say "aviso: no se pudo generar el tema de iconos"; return; }
  local tmp; tmp="$(mktemp -d)"
  if python3 "$repo/tools/icons/build_font.py" "$tmp" >/dev/null 2>&1; then
    mkdir -p "$FONTS" "$HOME/.config/kitty"
    cp "$tmp/RyokuPixelIcons.ttf" "$FONTS/" && cp "$tmp/pixel-icons.conf" "$HOME/.config/kitty/pixel-icons.conf"
    fc-cache -f "$FONTS" >/dev/null 2>&1 || true
  else say "aviso: no se pudo generar la fuente de iconos de terminal"; fi
  rm -rf "$tmp"
  # tema activo: GTK (ficheros y gsettings) y Qt
  for f in gtk-3.0/settings.ini gtk-4.0/settings.ini; do
    [ -f "$HOME/.config/$f" ] && sed -i 's/^gtk-icon-theme-name=.*/gtk-icon-theme-name=ryoku-buckshot/' "$HOME/.config/$f"
  done
  [ -f "$HOME/.config/qt6ct/qt6ct.conf" ] && sed -i 's/^icon_theme=.*/icon_theme=ryoku-buckshot/' "$HOME/.config/qt6ct/qt6ct.conf"
  command -v gsettings >/dev/null 2>&1 && gsettings set org.gnome.desktop.interface icon-theme ryoku-buckshot 2>/dev/null || true
  say "iconos pixel art instalados (tema ryoku-buckshot)"
}

# --- rice Hajime: el fondo se genera aqui (original, sin imagenes en el repo) y se aplica -----------------
RICE="$HOME/.config/ryoku/rices/hajime"
build_rice() {
  [ -f "$RICE/rice.json" ] || [ "$dry" = 1 ] || return 0
  if [ "$dry" = 1 ]; then say "[dry-run] generar el fondo de Hajime y aplicar el rice"; return; fi
  python3 -c 'import numpy, PIL' 2>/dev/null || { say "aviso: faltan python-numpy/python-pillow; sin fondo ni rice"; return; }
  # fondo: Cosmic Cliffs (Webb, NASA) si hay red; si no, el amanecer generado por codigo
  if python3 -I "$repo/tools/fetch-wallpaper.py" "$RICE/wall.png" >/dev/null 2>&1; then say "fondo descargado: Cosmic Cliffs (NASA, ESA, CSA, STScI)"
  elif python3 -I "$repo/tools/gen-wallpaper.py" "$RICE/wall.png" >/dev/null 2>&1; then say "aviso: sin red; fondo generado de reserva"
  else say "aviso: no se pudo crear el fondo"; return; fi
  python3 -I -c 'import sys; from PIL import Image; Image.open(sys.argv[1]).convert("RGB").resize((1280, 720)).save(sys.argv[2])' \
    "$RICE/wall.png" "$RICE/preview.png" 2>/dev/null || true
  command -v ryoku-hub >/dev/null 2>&1 || { say "aviso: sin ryoku-hub; aplica el rice en Ryoku Hub > Rices > Hajime"; return; }
  # copia del escritorio actual para poder volver (Ryoku Hub > Rices > pre-hajime)
  ryoku-hub rice list 2>/dev/null | grep -q '"slug":"pre-hajime"' || ryoku-hub rice capture pre-hajime >/dev/null 2>&1 || true
  ryoku-hub rice apply hajime >/dev/null 2>&1 || { say "aviso: no se pudo aplicar el rice; hazlo en Ryoku Hub > Rices > Hajime"; return; }
  if [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ] && command -v ryogami >/dev/null 2>&1; then
    ryogami wallpaper set "$RICE/wall.png" >/dev/null 2>&1 && ryogami wallpaper repaint >/dev/null 2>&1 \
      && say "rice Hajime aplicado (fondo y colores)" || say "aviso: rice aplicado; falta poner el fondo (Ryoku Hub > Fondos)"
  else
    # sin sesion grafica (p. ej. recien convertido): el primer terminal de la sesion termina el trabajo
    mkdir -p "$HOME/.local/state/hajime"; : > "$HOME/.local/state/hajime/pending-rice"
    say "rice Hajime aplicado; el fondo y los colores se ponen en tu primer terminal dentro del escritorio"
  fi
}

# --- main ---------------------------------------------------------------------------------------
if [ "$undo" = 1 ]; then
  each "$repo/ryoku" unplace
  each "$repo/ryoku-snippets" unsnippet
  # lo generado al instalar
  run rm -rf "$HOME/.local/share/hajime" "$RICE/wall.png" "$RICE/preview.png" "$ICONS" "$FONTS" "$HOME/.config/kitty/pixel-icons.conf"
  for f in gtk-3.0/settings.ini gtk-4.0/settings.ini; do
    [ -f "$HOME/.config/$f" ] && sed -i 's/^gtk-icon-theme-name=ryoku-buckshot$/gtk-icon-theme-name=ryoku-folders/' "$HOME/.config/$f"
  done
  [ -f "$HOME/.config/qt6ct/qt6ct.conf" ] && sed -i 's/^icon_theme=ryoku-buckshot$/icon_theme=Papirus-Dark/' "$HOME/.config/qt6ct/qt6ct.conf"
  command -v gsettings >/dev/null 2>&1 && gsettings set org.gnome.desktop.interface icon-theme ryoku-folders 2>/dev/null || true
  rmdir "$RICE" 2>/dev/null || true
  [ "$overlay_changed" = 1 ] && command -v ryoku >/dev/null 2>&1 && run ryoku materialize
  exit 0
fi

install_ryoku
[ "$dry" = 1 ] && [ "$arch" = 1 ] && ! command -v ryoku >/dev/null 2>&1 && { say "(dry-run: el resto se aplica tras instalar Ryoku)"; exit 0; }
[ "$pkgs" = 1 ] && install_packages
each "$repo/ryoku" place
each "$repo/ryoku-snippets" snippet
[ "$overlay_changed" = 1 ] && command -v ryoku >/dev/null 2>&1 && run ryoku materialize
install_plugins
build_spin
build_icons
build_rice
say "Hecho. Abre una terminal nueva (fish) para ver el saludo."
