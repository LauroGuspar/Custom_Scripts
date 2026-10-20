#!/usr/bin/env bash

APP_ID="io.github.riyaniii.Kaori"

# Buscar ventana de Kaori
WINDOWS=$(niri msg -j windows)
KAORI_WIN=$(echo "$WINDOWS" | jq -c --arg app "$APP_ID" '.[] | select(.app_id == $app)' | head -n 1)

if [ -z "$KAORI_WIN" ]; then
    # No está en ejecución: iniciarla
    flatpak run "$APP_ID" &
    exit 0
fi

KAORI_ID=$(echo "$KAORI_WIN" | jq -r '.id')
IS_FOCUSED=$(echo "$KAORI_WIN" | jq -r 'select(.is_focused == true) | .id')

# Obtener workspaces actuales
WORKSPACES=$(niri msg -j workspaces)
CURRENT_WS_ID=$(echo "$WORKSPACES" | jq -r '.[] | select(.is_focused == true) | .id')
CURRENT_WS_IDX=$(echo "$WORKSPACES" | jq -r '.[] | select(.is_focused == true) | .idx')
KAORI_WS_ID=$(echo "$KAORI_WIN" | jq -r '.workspace_id')

if [ -n "$IS_FOCUSED" ]; then
    # Está enfocada: ocultarla enviándola al fondo dinámico (índice 99 que Niri ajusta al final) sin mover el foco
    niri msg action move-window-to-workspace --window-id "$KAORI_ID" --focus false 99
else
    # Traerla al workspace actual si está oculta o en otro escritorio
    if [ "$KAORI_WS_ID" != "$CURRENT_WS_ID" ]; then
        niri msg action move-window-to-workspace --window-id "$KAORI_ID" "$CURRENT_WS_IDX"
    fi
    # Enfocar Kaori
    niri msg action focus-window --id "$KAORI_ID"
fi
