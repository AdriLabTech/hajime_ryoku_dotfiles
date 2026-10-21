# Hajime

Dotfiles para **Ryoku Arch** y para **Arch puro**. Un solo juego de configuración (`ryoku/`) y un instalador con dos usos:

| Tu sistema | Comando |
|---|---|
| Ya usas Ryoku | `./install.sh` |
| Arch puro (sin Ryoku) | `./install.sh --arch` |

> **Aviso para Arch puro.** `--arch` instala primero **Ryoku** dentro de tu Arch con el convertidor oficial de Ryoku. Eso hace `pacman -Syu`, **cambia el gestor de sesión a SDDM y la red a NetworkManager**, y puede cambiar tu shell de inicio a fish. Guarda una copia para deshacerlo (`~/.local/state/ryoku/shell-install/`). Antes de nada muestra el plan del convertidor (`--dry-run`) y te pide confirmar. **Sudo:** el convertidor usa `sudo` sin preguntar y falla a mitad si pide contraseña, así que Hajime te pide tu contraseña una vez, crea `/etc/sudoers.d/99-hajime-install` (sudo sin contraseña para tu usuario) y **lo borra al terminar**, también si falla o lo cortas con Ctrl+C. Solo x86_64 con systemd. Si no quieres Ryoku, este repo no te sirve.

## Uso
```
./install.sh --dry-run          # ver qué haría, sin cambiar nada
./install.sh [--arch] [--packages] [--yes]
./install.sh --uninstall        # quita lo que puso Hajime (no toca paquetes ni plugins; para volver al
                                # escritorio de antes: Ryoku Hub > Rices > pre-hajime)
```
- `--packages` instala con `pacman` lo de `packages/*.txt` (pide sudo): fish, kitty, starship, fastfetch, python, neovim, git, ripgrep, fd.
- Lo que ya tengas se guarda en `~/.local/state/hajime/backup-<fecha>/`.
- `ryoku/` se enlaza en `$HOME` con enlaces simbólicos. Lo que va a `~/.config/ryoku/user_edits/` se copia (así lo pide Ryoku) y después se ejecuta `ryoku materialize`.
- `ryoku-snippets/` añade un bloque entre marcas (`# >>> hajime >>>`) a ficheros que también son tuyos, como `~/.config/kitty/user.conf`.

## Qué incluye
- **Un rice propio, «Hajime»** (se instala en Ryoku Hub > Rices y se aplica solo):
  - **Fondo:** «Cosmic Cliffs», del telescopio espacial James Webb (NASA, ESA, CSA, STScI), recortado a 3840×2160. Se descarga de NASA al instalar y se comprueba su sha256; no está en el repo. Sin red, se usa un amanecer generado por código. La paleta de la interfaz sale de la imagen (naranja y cobre).
  - **Barra superior** en tres islas flotantes y esmeriladas (lanzador y escritorios, reloj y fecha, estado y ajustes), sin los contadores de CPU, memoria, GPU ni disco.
  - **Ventanas:** disposición *scrolling* (columnas que se desplazan, como Niri), borde azafrán de 2 px, radio 4, huecos de 8, sin sombras ni desenfoque.
  - **Animaciones** `dusky` (fluidas, con un pequeño rebote), cursor Bibata Amber y **dock inferior** que se oculta solo, con lupa (kitty, Firefox, Archivos), y **sin visualizador de sonido**.
  - Antes de aplicarlo guarda tu escritorio como rice `pre-hajime` para poder volver.
- **Iconos pixel art** (los de Adrián, variante «buckshot»): el tema `ryoku-buckshot` (iconos de Nautilus y de las apps GTK y Qt) y una fuente `Ryoku Pixel Icons` para los iconos de `eza` y `yazi` en kitty. Se **generan al instalar** (~30 s, `tools/icons/`) a partir de Papirus-Dark, que ya trae Ryoku; el repo no contiene imágenes.
- **Saludo con el logo de Arch girando sin parar** (`hajime-fetch`): en kitty el logo ASCII de Arch gira **de forma continua** mientras escribes comandos debajo (lo anima kitty, no hay ningún proceso en marcha). Los fotogramas se dibujan en tu equipo al instalar. En otros terminales gira una vuelta y se queda de frente. En ventanas estrechas muestra solo la ficha, para que las líneas no se partan. Una función de fish `ryoku-fastfetch` lo activa en cada terminal sin tocar ficheros de Ryoku (solo fish). `HAJIME_SPIN=0` lo desactiva.
- **starship**: el prompt de Ryoku con una píldora para el entorno virtual de Python.
- **nvim**: aspecto (bordes redondeados, lualine, bufferline…) y ajustes de edición como parches de LazyVim (`hajime-dev.lua`, `hajime-editor.lua`), más subir la fuente de kitty mientras nvim está abierto. Sin extras de lenguajes: añade los tuyos.
- **kitty**: `allow_remote_control yes` (lo necesita lo anterior).
- **Plugin** `claude-companion` (se instala con `ryoku plugin add` y queda **activado** como widget de escritorio). Los demás plugins (apptime, todo-list, obsidian) se instalan desde la Ryostore.

## Qué no incluye (a propósito)
Otros temas, rices o perfiles, iconos y fondos de terceros; la configuración de monitores, GPU y teclado (Ryoku la genera para tu máquina); rutas, claves o cuentas personales.

## Créditos y licencias
- Fondo: NASA, ESA, CSA, STScI ([Cosmic Cliffs](https://science.nasa.gov/)); el contenido de NASA es de uso libre con crédito. No se redistribuye en este repo.
- Iconos: derivados de [Papirus](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) (GPL-3.0), pixelados por `tools/icons/`.

## Logo de Arch
El logo de Arch es marca registrada de sus propietarios. Este repositorio **no distribuye ninguna imagen**: `hajime-fetch` lee el logo ASCII de `fastfetch` al ejecutarse y `tools/logo-spin-preview.py` el SVG que ya trae tu sistema.

## Pruebas
```
tests/check-repo.sh     # sintaxis y que no haya datos personales, secretos ni imágenes
tests/test-install.sh   # el instalador en un HOME falso con un `ryoku` de mentira
```
Verificado (2026-10-21):
- En un contenedor Arch limpio: `test-install.sh`, `hajime-fetch` con animación y la función de fish.
- **En una VM (QEMU/KVM) con Arch instalado desde la ISO oficial 2026.10.01** (`archinstall`, perfil mínimo, BIOS, ext4), **desde una snapshot limpia**: `./install.sh --arch --yes` completó los 15 pasos del convertidor (Ryoku v0.75.3-beta.20, SDDM, NetworkManager, fish), retiró el sudo temporal y, con `./install.sh`, aplicó la capa. Tras reiniciar y entrar en SDDM: fondo, barra en islas, bordes, dock oculto, logo girando de forma continua, iconos pixel art, `claude-companion` activado y sin visualizador. El fondo y los colores los puso el primer terminal de la sesión (el instalador corrió sin sesión gráfica).
- Rarezas del convertidor de Ryoku, tratadas en `install.sh`: su `--dry-run` y su ejecución terminan con código 1 por un fallo de su limpieza final (`work: unbound variable`); necesita una terminal salvo con `--yes`; llama a `sudo -n`; y su fichero de estado solo queda en disco si no terminó.

**No verificado**: UEFI, NVIDIA y btrfs; el `--uninstall` del convertidor; que el instalador pida y acepte la contraseña de sudo en un Arch sin credencial previa más allá de la comprobación manual; los pasos «Una vez» en hardware real.

## English (short)
Dotfiles for Ryoku Arch and plain Arch. `./install.sh` on Ryoku; `./install.sh --arch` on plain Arch first runs Ryoku's **official converter** (switches to SDDM/NetworkManager, runs `pacman -Syu`; it shows its dry-run plan and asks first). Shows an ASCII Arch logo spinning in the fish greeting. No images are shipped. Licence: GPL-3.0-or-later (same as Ryoku).

## Licencia
GPL-3.0-or-later, la misma que Ryoku.
