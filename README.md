# Custom_Scripts

Repositorio central de herramientas, scripts personalizados y automatizaciones para mi entorno de trabajo en Linux (CachyOS / Niri Wayland).

Diseñado para respaldar configuraciones, facilitar la portabilidad a nuevos dispositivos y mantener un registro claro de utilidades personales.

---

## Índice de Herramientas

| Proyecto / Script | Descripción | Enlace a Documentación |
| :--- | :--- | :--- |
| **`bt-autosuspend`** | Monitor de inactividad multimedia con desconexión selectiva de dispositivos Bluetooth de audio (MPRIS + PipeWire) e interfaz TUI interactiva. | [bt-autosuspend/README.md](bt-autosuspend/README.md) |
| **`frontend_suwayomi`** | Scratchpad flotante agnóstico y configurable para lectores de Suwayomi (**Tsumiru**, **Kaori**, etc.) en Niri (`Mod + M`) con soporte para variables internas o archivo `config.env`. | [frontend_suwayomi/README.md](frontend_suwayomi/README.md) |
| **`Kaori_Suwayomi`** | Scratchpad flotante dinámico original de lectura manga para Kaori en Niri (`Mod + M`). | [Kaori_Suwayomi/README.md](Kaori_Suwayomi/README.md) |

---

## Instalación en un Dispositivo Nuevo

Al clonar este repositorio en una máquina nueva, puedes instalar y activar las herramientas que necesites:

### 1. Clonar el repositorio
```bash
git clone <URL_DEL_REPOSITORIO> ~/Documentos/Custom_Scripts
cd ~/Documentos/Custom_Scripts
```

### 2. Configurar `bt-autosuspend`
```bash
cd bt-autosuspend
./install.sh
# Luego abre la interfaz de configuración:
bt-autosuspend
# O instálalo como servicio automático de usuario:
bt-autosuspend service install
```

### 3. Configurar `frontend_suwayomi` (Tsumiru / Kaori)
1. Instala el lector deseado (por ejemplo, Tsumiru):
   ```bash
   flatpak install app.tsumiru.Tsumiru
   ```
2. Asegúrate de tener instalado `jq`:
   ```bash
   sudo pacman -S jq
   ```
3. Crea el enlace simbólico del script:
   ```bash
   mkdir -p ~/.local/bin
   ln -sf "$(pwd)/frontend_suwayomi/toggle-suwayomi.sh" ~/.local/bin/toggle-suwayomi.sh
   # Compatibilidad con atajo existente si usas toggle-tsumiru.sh:
   ln -sf "$(pwd)/frontend_suwayomi/toggle-suwayomi.sh" ~/.local/bin/toggle-tsumiru.sh
   chmod +x frontend_suwayomi/toggle-suwayomi.sh
   ```
4. Configura tu frontend en `frontend_suwayomi/config.env` (por defecto viene configurado para `tsumiru`).
5. Añade la regla de ventana y el atajo en tu configuración de Niri (`~/.config/niri/cfg/rules.kdl` y `keybinds.kdl`). Consulta la guía detallada en [`frontend_suwayomi/README.md`](frontend_suwayomi/README.md).

---

## Estructura del Repositorio

```text
Custom_Scripts/
├── bt-autosuspend/          # Desconexión automática de Bluetooth por inactividad
│   ├── config.py            # Modelo y persistencia JSON en ~/.config/bt-autosuspend/
│   ├── detector.py          # Detección híbrida (MPRIS + PipeWire) y clasificación BT
│   ├── daemon.py            # Demonio de monitoreo y avisos notify-send
│   ├── tui.py               # Interfaz interactiva de terminal con navegación y checkboxes
│   ├── main.py              # CLI principal
│   ├── install.sh           # Instalador rápido para nuevos equipos
│   └── README.md            # Guía completa de usuario
│
├── frontend_suwayomi/       # Scratchpad flotante configurable para Tsumiru / Kaori
│   ├── toggle-suwayomi.sh   # Script de conmutación IPC configurable
│   ├── config.env           # Archivo de configuración (selección de frontend y comandos)
│   └── README.md            # Guía de configuración y reglas de Niri
│
├── Kaori_Suwayomi/          # Integración original de Kaori (referencia histórica)
│   ├── toggle-kaori.sh      # Script de conmutación IPC original
│   └── README.md            # Guía original de Kaori
│
├── .gitignore               # Exclusión de cachés y temporales
└── README.md                # Índice principal del repositorio
```
