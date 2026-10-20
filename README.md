# Custom_Scripts

Repositorio central de herramientas, scripts personalizados y automatizaciones para mi entorno de trabajo en Linux (CachyOS / Niri Wayland).

Diseñado para respaldar configuraciones, facilitar la portabilidad a nuevos dispositivos y mantener un registro claro de utilidades personales.

---

## Índice de Herramientas

| Proyecto / Script | Descripción | Enlace a Documentación |
| :--- | :--- | :--- |
| **`bt-autosuspend`** | Monitor de inactividad multimedia con desconexión selectiva de dispositivos Bluetooth de audio (MPRIS + PipeWire) e interfaz TUI interactiva. | [bt-autosuspend/README.md](bt-autosuspend/README.md) |
| **`Kaori_Suwayomi`** | Scratchpad flotante dinámico de lectura manga para el compositor Niri (`Mod + M`), con reubicación instantánea de ventana y preservación de workspaces. | [Kaori_Suwayomi/README.md](Kaori_Suwayomi/README.md) |

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

### 3. Configurar `Kaori_Suwayomi`
1. Asegúrate de tener instalado `jq` y Flatpak:
   ```bash
   sudo pacman -S jq
   flatpak install io.github.riyaniii.Kaori
   ```
2. Crea el enlace simbólico del script:
   ```bash
   ln -sf "$(pwd)/Kaori_Suwayomi/toggle-kaori.sh" ~/.local/bin/toggle-kaori.sh
   chmod +x ~/.local/bin/toggle-kaori.sh
   ```
3. Añade la regla de ventana y el atajo en tu configuración de Niri (`~/.config/niri/cfg/rules.kdl` y `keybinds.kdl`). Consulta la guía detallada en [`Kaori_Suwayomi/README.md`](Kaori_Suwayomi/README.md).

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
├── Kaori_Suwayomi/          # Integración de lector Kaori con atajo flotante en Niri
│   ├── toggle-kaori.sh      # Script de conmutación IPC
│   └── README.md            # Guía de integración de reglas y atajos en Niri
│
├── .gitignore               # Exclusión de cachés y temporales
└── README.md                # Índice principal del repositorio
```
