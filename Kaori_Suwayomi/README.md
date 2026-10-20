# Integración de Kaori en Niri (Panel Lateral Flotante / Scratchpad Dinámico)

Este documento detalla la integración de **Kaori** (lector de manga/cómics basado en Flatpak) en el compositor Wayland **Niri**, configurado como un panel lateral izquierdo flotante que puede mostrarse y ocultarse al instante mediante un atajo de teclado, sin perder el progreso de lectura ni interferir con la navegación habitual de escritorios.

---

## 1. Resumen del Comportamiento Implementado

1. **Atajo rápido (`Mod + M`):**
   * Si Kaori está cerrado, lo inicia.
   * Si Kaori está abierto y lo estás usando (enfocado), al pulsar `Mod + M` se oculta en segundo plano sin matar el proceso.
   * Si estás en cualquier otro escritorio o ventana, al pulsar `Mod + M` Kaori aparece de inmediato (0 ms de demora) exactamente en la página, capítulo y zoom en los que te quedaste.
2. **Panel flotante fijo (No se cierra al hacer clic fuera):**
   * A diferencia de los paneles emergentes de Noctalia (como `Mod + N`), Kaori es una ventana de Niri: al hacer clic en tu navegador o terminal, Kaori solo pierde el foco, pero **no se quita ni desaparece**.
3. **Dimensiones y posición:**
   * Abre pegado al borde superior izquierdo de la pantalla (respetando los márgenes/gaps de 14px).
   * Ocupa el **33.3%** del ancho de pantalla (~640 px en 1080p), dejando los 2/3 restantes (~1280 px) limpios para trabajar o navegar.
4. **Respeto a los escritorios de Niri (Sin secuestrar el escritorio 2):**
   * Opera de manera 100% dinámica. No declara escritorios estáticos en la configuración, por lo que tus escritorios normales (`Mod + [1-9]` y `Mod + Ctrl + [1-9]`) funcionan sin colisiones.

---

## 2. Archivos Involucrados

| Componente | Ruta en el sistema | Descripción |
| :--- | :--- | :--- |
| **Script Toggle** | `~/.local/bin/toggle-kaori.sh` | Controla la lógica de arranque, ocultación y reaparición vía IPC de Niri. *(El archivo original se encuentra respaldado en esta misma carpeta).* |
| **Reglas de Ventana** | `~/.config/niri/cfg/rules.kdl` | Define que Kaori sea flotante, su ancho (33%), alto completo y posición inicial. |
| **Atajo de Teclado** | `~/.config/niri/cfg/keybinds.kdl` | Vincula la combinación `Mod + M` a la ejecución del script. |

---

## 3. Lógica del Script (`toggle-kaori.sh`)

El script se ejecuta únicamente durante unos milisegundos cuando presionas `Mod + M`. Su flujo de decisión es:

1. **Detección (`niri msg -j windows`):** Consulta por socket IPC a Niri en formato JSON buscando una ventana con `app_id == "io.github.riyaniii.Kaori"`.
2. **Si no existe la ventana:** Ejecuta `flatpak run io.github.riyaniii.Kaori &` y termina.
3. **Si la ventana existe y tiene el foco (`is_focused == true`):**
   * Significa que estás usando Kaori y deseas ocultarlo.
   * Ejecuta: `niri msg action move-window-to-workspace --window-id "$KAORI_ID" --focus false 99`.
   * **¿Por qué índice 99?** Niri no permite huecos en los escritorios; al pasarle `99`, Niri lo envía dinámicamente al fondo absoluto de todos los escritorios que tengas abiertos.
   * Con `--focus false`, tu foco no cambia y la ventana simplemente desaparece de tu vista.
4. **Si la ventana existe pero NO tiene el foco (está oculta al fondo o en otro escritorio):**
   * Detecta tu escritorio activo actual (`CURRENT_WS_IDX`).
   * Si Kaori está en otro escritorio, lo mueve al actual: `niri msg action move-window-to-workspace --window-id "$KAORI_ID" "$CURRENT_WS_IDX"`.
   * Como el escritorio temporal del fondo donde estaba Kaori queda vacío, **Niri lo destruye automáticamente**.
   * Le otorga el foco a Kaori (`niri msg action focus-window --id "$KAORI_ID"`).

---

## 4. Configuraciones Agregadas en Niri

### A. Regla de Ventana en `~/.config/niri/cfg/rules.kdl`
Dentro de la sección de ventanas flotantes (`// Flotantes`), se añadió:

```kdl
window-rule {
    match app-id=r#"^io\.github\.riyaniii\.Kaori$"#
    open-floating true
    default-floating-position x=14 y=14 relative-to="top-left"
    default-column-width { proportion 0.33333; }
    default-window-height { proportion 1.0; }
}
```

* **`open-floating true`**: Hace que la ventana no se divida en columnas en mosaico (*tiling*), sino que flote.
* **`default-floating-position x=14 y=14 relative-to="top-left"`**: La sitúa en la esquina superior izquierda dejando el margen de 14px configurado en los *gaps*.
* **`default-column-width { proportion 0.33333; }`**: Ancho del 33.3% de la pantalla. *(Si en el futuro deseas que ocupe el 40%, cambia este valor a `0.40`).*
* **`default-window-height { proportion 1.0; }`**: Altura completa disponible.

### B. Atajo de Teclado en `~/.config/niri/cfg/keybinds.kdl`
En el bloque de atajos personalizados:

```kdl
    // Kaori - Panel lateral flotante fijo
    Mod+M                               { spawn-sh "toggle-kaori.sh"; }
```

> [!WARNING]
> **No agregues `workspace "scratch"` en `config.kdl`:**
> Si declaras un workspace estático en `config.kdl`, Niri lo forzará como el escritorio número 2, secuestrando tu atajo `Mod + Ctrl + 2`. Deja que Niri administre los espacios de forma dinámica.

---

## 5. Guía de Restauración / Instalación desde Cero

Si cambias de máquina o reinstalas el sistema, sigue estos pasos:

### Paso 1: Instalar Kaori y dependencias
1. Instala Kaori desde Flatpak:
   ```bash
   flatpak install io.github.riyaniii.Kaori
   ```
2. Asegúrate de tener instalado `jq` (usado por el script para procesar el JSON de Niri):
   ```bash
   # En Arch Linux:
   sudo pacman -S jq
   # En Fedora / Debian / Ubuntu:
   sudo dnf install jq  # o sudo apt install jq
   ```

### Paso 2: Instalar el script de toggle
1. Copia el archivo `toggle-kaori.sh` de esta carpeta a tu ruta de binarios de usuario:
   ```bash
   mkdir -p ~/.local/bin
   cp toggle-kaori.sh ~/.local/bin/
   chmod +x ~/.local/bin/toggle-kaori.sh
   ```
2. Asegúrate de que `~/.local/bin` esté en tu `$PATH` (en la mayoría de distros ya viene incluido en `.bashrc`, `.zshrc` o `.config/fish/config.fish`).

### Paso 3: Aplicar las reglas en la configuración de Niri
1. Añade el bloque `window-rule` en `~/.config/niri/cfg/rules.kdl`.
2. Añade la línea del atajo `Mod+M` en `~/.config/niri/cfg/keybinds.kdl`.

### Paso 4: Validar y recargar Niri
Ejecuta en tu terminal:
```bash
niri validate
niri msg action load-config-file
```
Si la validación indica `config is valid`, la recarga será inmediata sin necesidad de reiniciar la sesión.

---

## 6. Atajos de Uso Rápido

* **`Mod + M`:** Alternar entre mostrar Kaori en tu pantalla actual o enviarlo a segundo plano.
* **Clic fuera del panel:** Kaori permanece fijo en pantalla mientras usas otras aplicaciones.
* **`Mod + Q` (con Kaori enfocado):** Cierra definitivamente el proceso de Kaori si deseas liberar memoria RAM por completo.
