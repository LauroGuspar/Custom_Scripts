#!/usr/bin/env bash
# ==============================================================================
# Script Toggle Dinámico para Frontends de Suwayomi (Tsumiru / Kaori) en Niri
# ==============================================================================
# Comportamiento:
#   - Si la aplicación no está abierta: la inicia en segundo plano.
#   - Si la aplicación está enfocada: la oculta enviándola al workspace de fondo.
#   - Si está oculta o en otro workspace: la trae al actual y le otorga el foco.
#
# Configuración:
#   Permite definir APP_ID y LAUNCH_CMD en este mismo archivo, en config.env,
#   o mediante variables de entorno.
# ==============================================================================

set -eo pipefail

# 1. Configuración por defecto dentro del script
# (Puedes editar directamente aquí si prefieres no usar un archivo externo)
FRONTEND="${FRONTEND:-tsumiru}"
APP_ID="${APP_ID:-}"
LAUNCH_CMD="${LAUNCH_CMD:-}"
HIDE_WORKSPACE="${HIDE_WORKSPACE:-99}"
NOTIFY_ON_ERROR="${NOTIFY_ON_ERROR:-true}"

# 2. Cargar archivo de configuración externo si existe
# Busca en la carpeta del script (resolviendo symlinks) o en ~/.config/
RESOLVED_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd -- "$(dirname -- "$RESOLVED_PATH")" &>/dev/null && pwd)"

CONFIG_LOCATIONS=(
    "$SCRIPT_DIR/config.env"
    "${XDG_CONFIG_HOME:-$HOME/.config}/frontend-suwayomi/config.env"
    "${XDG_CONFIG_HOME:-$HOME/.config}/suwayomi-frontend/config.env"
)

for cfg in "${CONFIG_LOCATIONS[@]}"; do
    if [ -f "$cfg" ]; then
        # shellcheck disable=SC1090
        source "$cfg"
        break
    fi
done

# Función de notificación de errores
notify_error() {
    local msg="$1"
    echo "[toggle-suwayomi] ERROR: $msg" >&2
    if [ "$NOTIFY_ON_ERROR" = "true" ] && command -v notify-send >/dev/null 2>&1; then
        notify-send -u critical -a "Frontend Suwayomi" "Error de Scratchpad" "$msg"
    fi
}

# 3. Comprobar dependencias requeridas
if ! command -v niri >/dev/null 2>&1; then
    notify_error "Niri no está instalado o no se encuentra en el PATH."
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    notify_error "El paquete 'jq' es necesario para procesar el JSON de Niri."
    exit 1
fi

# 4. Resolver automáticamente APP_ID y LAUNCH_CMD según el frontend elegido
# Esto evita el error de incompatibilidad entre el app_id de Wayland y el nombre Flatpak
case "${FRONTEND,,}" in
    tsumiru)
        APP_ID="${APP_ID:-tsumiru}"
        LAUNCH_CMD="${LAUNCH_CMD:-flatpak run app.tsumiru.Tsumiru}"
        ;;
    kaori)
        APP_ID="${APP_ID:-io.github.riyaniii.Kaori}"
        LAUNCH_CMD="${LAUNCH_CMD:-flatpak run io.github.riyaniii.Kaori}"
        ;;
esac

# Si APP_ID fue establecido directamente (sin FRONTEND):
if [ -z "$APP_ID" ]; then
    APP_ID="tsumiru"
fi

if [ -z "$LAUNCH_CMD" ]; then
    case "$APP_ID" in
        tsumiru|app.tsumiru.Tsumiru)
            APP_ID="tsumiru"
            LAUNCH_CMD="flatpak run app.tsumiru.Tsumiru"
            ;;
        kaori|io.github.riyaniii.Kaori)
            APP_ID="io.github.riyaniii.Kaori"
            LAUNCH_CMD="flatpak run io.github.riyaniii.Kaori"
            ;;
        *)
            # Si el usuario puso un APP_ID personalizado:
            if command -v flatpak >/dev/null 2>&1 && flatpak info "$APP_ID" >/dev/null 2>&1; then
                LAUNCH_CMD="flatpak run $APP_ID"
            elif command -v "$APP_ID" >/dev/null 2>&1; then
                LAUNCH_CMD="$APP_ID"
            elif command -v flatpak >/dev/null 2>&1; then
                # Buscar si existe algún Flatpak instalado cuyo ID contenga el nombre
                MATCHED_FLATPAK=$(flatpak list --app --columns=application 2>/dev/null | grep -i "\b${APP_ID}\b" | head -n 1 || true)
                if [ -n "$MATCHED_FLATPAK" ]; then
                    LAUNCH_CMD="flatpak run $MATCHED_FLATPAK"
                else
                    LAUNCH_CMD="$APP_ID"
                fi
            else
                LAUNCH_CMD="$APP_ID"
            fi
            ;;
    esac
fi

# 5. Consultar ventanas abiertas en Niri
WINDOWS=$(niri msg -j windows 2>/dev/null || echo "[]")
TARGET_WIN=$(echo "$WINDOWS" | jq -c --arg app "$APP_ID" '.[] | select(.app_id == $app)' | head -n 1)

# Si no está en ejecución: iniciarla con el comando resuelto
if [ -z "$TARGET_WIN" ]; then
    nohup $LAUNCH_CMD >/dev/null 2>&1 &
    exit 0
fi

# 6. Extraer información de la ventana y foco
TARGET_ID=$(echo "$TARGET_WIN" | jq -r '.id')
IS_FOCUSED=$(echo "$TARGET_WIN" | jq -r 'select(.is_focused == true) | .id')

# 7. Obtener workspaces actuales
WORKSPACES=$(niri msg -j workspaces 2>/dev/null || echo "[]")
CURRENT_WS_ID=$(echo "$WORKSPACES" | jq -r '.[] | select(.is_focused == true) | .id')
CURRENT_WS_IDX=$(echo "$WORKSPACES" | jq -r '.[] | select(.is_focused == true) | .idx')
TARGET_WS_ID=$(echo "$TARGET_WIN" | jq -r '.workspace_id')

# 8. Lógica Toggle
if [ -n "$IS_FOCUSED" ]; then
    # Está enfocada: ocultarla enviándola al fondo dinámico sin mover el foco
    niri msg action move-window-to-workspace --window-id "$TARGET_ID" --focus false "$HIDE_WORKSPACE"
else
    # Traerla al workspace actual si está en otro escritorio
    if [ "$TARGET_WS_ID" != "$CURRENT_WS_ID" ] && [ -n "$CURRENT_WS_IDX" ]; then
        niri msg action move-window-to-workspace --window-id "$TARGET_ID" "$CURRENT_WS_IDX"
    fi
    # Enfocar la ventana
    niri msg action focus-window --id "$TARGET_ID"
fi
