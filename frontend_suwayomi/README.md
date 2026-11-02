# Integración de Frontends de Suwayomi en Niri (Panel Lateral Flotante / Scratchpad Dinámico)

Este proyecto proporciona un scratchpad dinámico y conmutable para el compositor Wayland **Niri** (`Mod + M`), diseñado específicamente para aplicaciones lectoras de manga/cómics que actúan como clientes frontend de **Suwayomi** (como **Tsumiru** o **Kaori**).

Permite abrir, ocultar y traer al instante el lector de manga en pantalla sin perder la página ni interferir con la navegación entre escritorios.

---

## 1. ¿Por qué ocurrió el error con Tsumiru?

Cuando cambiaste `APP_ID="tsumiru"` en el script original de Kaori (`toggle-kaori.sh`), apareció el error:
```text
error: Id tsumiru no válido: Los nombres deben contener al menos 2 puntos
```

### La causa raíz:
* **En Kaori:** Por coincidencia, el `app_id` de la ventana en Wayland (`io.github.riyaniii.Kaori`) y el ID del paquete Flatpak (`io.github.riyaniii.Kaori`) eran **idénticos**. Por ende, `flatpak run "$APP_ID"` funcionaba.
* **En Tsumiru:**
  * El `app_id` que Wayland y Niri asignan a la ventana es simplemente: `tsumiru`.
  * El ID de la aplicación en Flatpak es: `app.tsumiru.Tsumiru`.
  * Los IDs de Flatpak exigen nomenclatura de dominio inverso (al menos dos puntos, e.g. `app.tsumiru.Tsumiru`). Al ejecutar `flatpak run tsumiru`, Flatpak rechaza el comando.

### La solución implementada:
Este nuevo script separa conceptualmente:
1. **`APP_ID`**: El identificador de ventana en Niri para consultar y mover la ventana (`niri msg -j windows`).
2. **`LAUNCH_CMD`**: El comando real del sistema para iniciar la app si está cerrada.
3. **Presets inteligentes**: Si solo defines `APP_ID="tsumiru"` o `FRONTEND="tsumiru"`, el script mapea automáticamente el comando correcto `flatpak run app.tsumiru.Tsumiru` sin que tengas que lidiar con errores de Flatpak.

---

## 2. Archivos del Módulo

| Archivo | Descripción |
| :--- | :--- |
| **`toggle-suwayomi.sh`** | Script principal con lógica IPC para Niri, resolución de presets y manejo de foco/espacios de trabajo. |
| **`config.env`** | Archivo de configuración desacoplado para seleccionar la aplicación o definir variables personalizadas. |
| **`README.md`** | Esta documentación. |

---

## 3. Opciones de Configuración

Puedes configurar la aplicación de 4 formas distintas según tu preferencia:

### Opción A: Mediante `config.env` (Recomendada)
Edita el archivo [config.env](file:///home/rogervz/Documentos/Custom_Scripts/frontend_suwayomi/config.env):

```bash
# Cambiar entre "tsumiru" y "kaori" en un solo paso:
FRONTEND="tsumiru"
```

O si utilizas una aplicación con binario nativo u otro nombre:
```bash
APP_ID="tsumiru"
LAUNCH_CMD="flatpak run app.tsumiru.Tsumiru"
```

### Opción B: Directamente dentro de `toggle-suwayomi.sh`
Al inicio del script puedes ajustar los valores por defecto:
```bash
FRONTEND="${FRONTEND:-tsumiru}"
APP_ID="${APP_ID:-}"
LAUNCH_CMD="${LAUNCH_CMD:-}"
```

### Opción C: Archivo global en `~/.config/`
El script busca automáticamente en:
* `~/.config/frontend-suwayomi/config.env`
* `~/.config/suwayomi-frontend/config.env`

### Opción D: Variables de entorno en línea
```bash
FRONTEND=kaori toggle-suwayomi.sh
```

---

## 4. Configuración en Niri

### A. Reglas de Ventana (`~/.config/niri/cfg/rules.kdl`)
Para que la ventana flote como panel lateral (ancho del 33%, altura completa y sin bordes molestos), asegúrate de tener la regla correspondiente:

#### Para Tsumiru:
```kdl
window-rule {
    match app-id=r"^tsumiru$"
    open-floating true
    default-floating-position x=14 y=14 relative-to="top-right"
    default-column-width { proportion 0.33333; }
    default-window-height { proportion 0.97; }
}
```

#### Para Kaori (si deseas alternar con Kaori):
```kdl
window-rule {
    match app-id=r"^io\.github\.riyaniii\.Kaori$"
    open-floating true
    default-floating-position x=14 y=14 relative-to="top-right"
    default-column-width { proportion 0.33333; }
    default-window-height { proportion 0.97; }
}
```

> [!TIP]
> Si prefieres que el panel aparezca en el lado izquierdo en lugar del derecho, cambia `relative-to="top-right"` por `relative-to="top-left"`.

### B. Atajo de Teclado (`~/.config/niri/cfg/keybinds.kdl`)
Vincula tu combinación deseada (por ejemplo `Mod + M`):

```kdl
    // Suwayomi Frontend - Panel lateral flotante fijo
    Mod+M                               { spawn-sh "toggle-suwayomi.sh"; }
```

---

## 5. Instalación y Enlaces Simbólicos

Para instalar o actualizar los enlaces en `~/.local/bin`:

```bash
mkdir -p ~/.local/bin
ln -sf ~/Documentos/Custom_Scripts/frontend_suwayomi/toggle-suwayomi.sh ~/.local/bin/toggle-suwayomi.sh

# Para mantener compatibilidad con atajos existentes:
ln -sf ~/Documentos/Custom_Scripts/frontend_suwayomi/toggle-suwayomi.sh ~/.local/bin/toggle-tsumiru.sh
```

Aplica cualquier cambio en la configuración de Niri ejecutando:
```bash
niri msg action load-config-file
```

---

## 6. Comportamiento en Uso

* **`Mod + M` cuando la app está cerrada:** Inicia el lector en segundo plano.
* **`Mod + M` cuando estás leyendo (ventana enfocada):** Oculta la ventana enviándola al escritorio dinámico de fondo (índice 99).
* **`Mod + M` desde cualquier otro escritorio:** Trae la ventana de inmediato a tu escritorio activo actual y le otorga el foco.
* **Clic fuera del panel:** La ventana solo pierde el foco, permaneciendo visible mientras consultas notas o terminal.
