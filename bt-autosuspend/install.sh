#!/usr/bin/env bash
# Script de instalación rápida de bt-autosuspend para nuevos dispositivos

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
TARGET_BIN="$BIN_DIR/bt-autosuspend"

echo "========================================================"
echo "      Instalador de bt-autosuspend"
echo "========================================================"

# 1. Comprobar dependencias requeridas
echo -n "[1/4] Verificando dependencias del sistema... "
MISSING_DEPS=()

for cmd in python3 bluetoothctl playerctl pactl notify-send; do
    if ! command -v "$cmd" &> /dev/null; then
        MISSING_DEPS+=("$cmd")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "FALTAN DEPENDENCIAS!"
    echo "  Por favor instala las siguientes herramientas antes de continuar:"
    echo "  -> ${MISSING_DEPS[*]}"
    echo ""
    echo "  En Arch / CachyOS / Manjaro:"
    echo "    sudo pacman -S python bluez bluez-utils playerctl libpulse libnotify"
    echo "  En Debian / Ubuntu / Mint:"
    echo "    sudo apt install python3 bluez playerctl pulseaudio-utils libnotify-bin"
    echo "  En Fedora:"
    echo "    sudo dnf install python3 bluez playerctl pulseaudio-utils libnotify"
    exit 1
fi
echo "OK"

# 2. Dar permisos de ejecución
echo -n "[2/4] Asignando permisos de ejecución a main.py... "
chmod +x "$SCRIPT_DIR/main.py"
echo "OK"

# 3. Crear enlace en ~/.local/bin
echo -n "[3/4] Creando enlace simbólico en $BIN_DIR... "
mkdir -p "$BIN_DIR"
ln -sf "$SCRIPT_DIR/main.py" "$TARGET_BIN"
echo "OK"

# 4. Verificar si ~/.local/bin está en el PATH
echo -n "[4/4] Verificando variable PATH... "
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "ADVERTENCIA"
    echo "  '$BIN_DIR' no parece estar en tu variable PATH actual."
    echo "  Asegúrate de tener en tu ~/.bashrc o ~/.zshrc:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
else
    echo "OK"
fi

echo "========================================================"
echo "✔ ¡Instalación completada con éxito!"
echo ""
echo "Ahora puedes usar los siguientes comandos desde cualquier terminal:"
echo "  • Configurar (TUI interactivo):  bt-autosuspend"
echo "  • Ver estado actual:             bt-autosuspend status"
echo "  • Instalar como servicio auto:   bt-autosuspend service install"
echo "========================================================"
