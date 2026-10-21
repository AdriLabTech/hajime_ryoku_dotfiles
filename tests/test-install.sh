#!/usr/bin/env bash
# Prueba install.sh en un HOME falso con un `ryoku` de mentira. No toca el sistema real.
#   tests/test-install.sh
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export HOME="$T/home"; mkdir -p "$HOME" "$T/bin"
LOG="$T/ryoku.log"
cat > "$T/bin/ryoku" <<STUB
#!/usr/bin/env bash
echo "\$*" >> "$LOG"
[ "\${1:-}" = plugin ] && [ "\${2:-}" = list ] && exit 0
exit 0
STUB
chmod +x "$T/bin/ryoku"
cat > "$T/bin/ryoku-hub" <<STUB
#!/usr/bin/env bash
echo "\$*" >> "$LOG.hub"
STUB
chmod +x "$T/bin/ryoku-hub"
export PATH="$T/bin:$PATH"
ok() { printf 'ok   %s\n' "$1"; }
bad() { printf 'FALLO %s\n' "$1"; exit 1; }
check() { local d="$1"; shift; if "$@"; then ok "$d"; else bad "$d"; fi; }

# estado previo del usuario: un fichero que hay que respaldar y un user.conf propio
mkdir -p "$HOME/.config/fish/functions" "$HOME/.config/kitty"
echo viejo > "$HOME/.config/fish/functions/ryoku-fastfetch.fish"
printf 'font_size 12\n' > "$HOME/.config/kitty/user.conf"
mkdir -p "$HOME/.config/ryoku" && echo '{"claude-companion":{"enabled":false}}' > "$HOME/.config/ryoku/plugins.json"

"$repo/install.sh" --dry-run >/dev/null
check "dry-run no crea nada" test ! -e "$HOME/.local/bin/hajime-fetch"

"$repo/install.sh" >/dev/null
check "hajime-fetch enlazado" test -L "$HOME/.local/bin/hajime-fetch"
check "funcion de fish enlazada" test -L "$HOME/.config/fish/functions/ryoku-fastfetch.fish"
check "copia de seguridad del fichero previo" grep -rqx viejo "$HOME/.local/state/hajime"
check "nvim hajime-editor enlazado" test -L "$HOME/.config/nvim/lua/plugins/hajime-editor.lua"
check "starship copiado a user_edits (no enlace)" test -f "$HOME/.config/ryoku/user_edits/starship.toml" -a ! -L "$HOME/.config/ryoku/user_edits/starship.toml"
check "kitty user.conf conserva lo del usuario" grep -qx 'font_size 12' "$HOME/.config/kitty/user.conf"
check "kitty user.conf lleva el bloque" grep -qx 'allow_remote_control yes' "$HOME/.config/kitty/user.conf"
check "ryoku materialize invocado" grep -qx materialize "$LOG"
check "plugin add invocado" grep -q 'plugin add https://github.com/AdriLabTech/claude-companion' "$LOG"

check "fondo del rice generado" test -s "$HOME/.config/ryoku/rices/hajime/wall.png"
check "tema de iconos pixel art generado" test -f "$HOME/.local/share/icons/ryoku-buckshot/index.theme"
check "fuente de iconos de terminal" test -f "$HOME/.local/share/fonts/RyokuPixelIcons/RyokuPixelIcons.ttf" -a -f "$HOME/.config/kitty/pixel-icons.conf"
check "claude-companion activado" test "$(jq -r '.["claude-companion"].enabled' "$HOME/.config/ryoku/plugins.json")" = true
check "copia previa del escritorio" grep -qx "rice capture pre-hajime" "$LOG.hub"
check "rice aplicado con ryoku-hub" grep -qx 'rice apply hajime' "$LOG.hub"
check "anim-preset copiado (no enlace)" test -f "$HOME/.config/ryoku/anim-preset" -a ! -L "$HOME/.config/ryoku/anim-preset"
check "fotogramas del logo para kitty" test -s "$HOME/.local/share/hajime/spin/spin.raw"

before="$(cat "$HOME/.config/kitty/user.conf")"
"$repo/install.sh" >/dev/null
check "idempotente (user.conf igual)" test "$before" = "$(cat "$HOME/.config/kitty/user.conf")"
check "un solo bloque" test "$(grep -c '>>> hajime >>>' "$HOME/.config/kitty/user.conf")" = 1

"$repo/install.sh" --uninstall >/dev/null
check "desinstalado: sin enlace" test ! -e "$HOME/.local/bin/hajime-fetch"
check "desinstalado: sin iconos generados" test ! -e "$HOME/.local/share/icons/ryoku-buckshot"
check "desinstalado: sin fondo ni fotogramas" test ! -e "$HOME/.config/ryoku/rices/hajime" -a ! -e "$HOME/.local/share/hajime"
check "desinstalado: sin copia de starship" test ! -e "$HOME/.config/ryoku/user_edits/starship.toml"
check "desinstalado: user.conf vuelve a lo del usuario" test "$(cat "$HOME/.config/kitty/user.conf")" = 'font_size 12'

echo "todo correcto"
