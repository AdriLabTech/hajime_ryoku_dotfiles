#!/usr/bin/env bash
# Antes de cada commit: sintaxis, y nada personal ni secreto en lo que se publica.
#   tests/check-repo.sh
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail=0
bad() { printf 'FALLO %s\n' "$1"; fail=1; }

bash -n install.sh tests/*.sh || bad "sintaxis de bash"
for f in ryoku/.local/bin/hajime-fetch tools/*.py; do python3 -I -c "import sys; compile(open(sys.argv[1]).read(), sys.argv[1], 'exec')" "$f" || bad "sintaxis de python: $f"; done
command -v fish >/dev/null && { fish -n ryoku/.config/fish/functions/*.fish || bad "sintaxis de fish"; }

files="$(git ls-files -co --exclude-standard)"
# rutas y datos personales
if grep -nE "/home/[a-z]|labs\.lownoise|@gmail\.com|adrian|Adrián" $files 2>/dev/null \
     | grep -v "^tests/check-repo.sh" | grep -v "^README.md.*Adrián"; then bad "datos personales en el repo"; fi
# secretos tipicos
if grep -nEi "(api[_-]?key|secret|token|passwd|password)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}" $files 2>/dev/null \
     | grep -v "^tests/check-repo.sh"; then bad "posible secreto"; fi
# imagenes: el logo de Arch no se distribuye
if printf '%s\n' $files | grep -Ei '\.(png|gif|svg|jpe?g|webp|raw)$'; then bad "hay imagenes en el repo"; fi

[ "$fail" = 0 ] && echo "repo limpio"
exit "$fail"
