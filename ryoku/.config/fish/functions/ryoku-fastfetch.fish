# Hajime: el saludo de Ryoku (config.fish llama a `ryoku-fastfetch`) muestra el logo
# ASCII de Arch girando. En fish una funcion gana a un binario del PATH, asi que no
# se toca ningun fichero de Ryoku. Sin hajime-fetch se usa el original.
function ryoku-fastfetch --description 'fastfetch con el logo de Arch girando (Hajime)'
    if command -q hajime-fetch
        hajime-fetch $argv
    else
        command ryoku-fastfetch $argv
    end
end
