# bt-autosuspend :: Guía de Usuario e Instalación

**bt-autosuspend** es una herramienta ligera para Linux que detecta de forma automática cuándo dejas de reproducir contenido multimedia y desconecta selectivamente tus dispositivos Bluetooth (auriculares, altavoces, barras de sonido) tras un periodo de inactividad configurable.

A diferencia de los scripts tradicionales que apagan el controlador Bluetooth por completo, **bt-autosuspend solo desconecta el dispositivo de audio específico**, protegiendo tus periféricos (ratones, teclados o mandos) para que nunca pierdas el control de tu sistema.

---

## Tabla de Contenidos
1. [Requisitos del Sistema](#1-requisitos-del-sistema)
2. [Instalación en un Dispositivo Nuevo](#2-instalación-en-un-dispositivo-nuevo)
   - [Opción A: Instalación Automática (Recomendada)](#opción-a-instalación-automática-recomendada)
   - [Opción B: Instalación Manual](#opción-b-instalación-manual)
3. [Guía de Configuración (Explicación de cada opción)](#3-guía-de-configuración-explicación-de-cada-opción)
   - [Tiempo de Inactividad](#tiempo-de-inactividad)
   - [Método de Detección](#método-de-detección)
   - [Regla de Dispositivos](#regla-de-dispositivos)
   - [Selección de Dispositivos (Lista Blanca / Negra)](#selección-de-dispositivos-lista-blanca--negra)
   - [Proteger Periféricos (Ratón / Teclado / Mandos)](#proteger-periféricos-ratón--teclado--mandos)
   - [Notificación Previa de Desconexión](#notificación-previa-de-desconexión)
   - [Tiempo de Aviso de Notificación](#tiempo-de-aviso-de-notificación)
4. [Uso de la Interfaz Interactiva (TUI)](#4-uso-de-la-interfaz-interactiva-tui)
5. [Referencia de Comandos CLI](#5-referencia-de-comandos-cli)
6. [Cómo iniciarlo automáticamente con el sistema](#6-cómo-iniciarlo-automáticamente-con-el-sistema)
   - [Opción 1: Servicio Systemd de Usuario](#opción-1-servicio-systemd-de-usuario-recomendado)
   - [Opción 2: Compositor Niri (Wayland)](#opción-2-compositor-niri-wayland)
   - [Opción 3: Hyprland / Sway](#opción-3-hyprland--sway)
7. [Preguntas Frecuentes y Solución de Problemas](#7-preguntas-frecuentes-y-solución-de-problemas)

---

## 1. Requisitos del Sistema

Para funcionar en cualquier distribución Linux (Arch, CachyOS, Fedora, Ubuntu, Debian, etc.), `bt-autosuspend` requiere las siguientes herramientas estándar:

* **Python 3** (versión 3.9 o superior).
* **bluetoothctl** (incluido en el paquete `bluez` o `bluez-utils`).
* **playerctl** (para consultar el estado de reproductores MPRIS como Spotify o navegadores).
* **pactl** (cliente de PulseAudio/PipeWire para inspeccionar el estado de los canales de sonido).
* **notify-send** (incluido en `libnotify`, para enviar notificaciones de aviso al escritorio).

### Comandos de instalación de dependencias según tu distribución:

* **Arch Linux / CachyOS / Manjaro / EndeavourOS:**
  ```bash
  sudo pacman -S python bluez bluez-utils playerctl libpulse libnotify
  ```
* **Debian / Ubuntu / Linux Mint / Pop!_OS:**
  ```bash
  sudo apt update
  sudo apt install python3 bluez playerctl pulseaudio-utils libnotify-bin
  ```
* **Fedora / RHEL:**
  ```bash
  sudo dnf install python3 bluez playerctl pulseaudio-utils libnotify
  ```

---

## 2. Instalación en un Dispositivo Nuevo

Si estás configurando este script en un equipo nuevo, sigue estos pasos:

### Opción A: Instalación Automática (Recomendada)
1. Copia o clona la carpeta `bt-autosuspend` en el lugar que prefieras (por ejemplo, `~/Documentos/Cambios_Niri/bt-autosuspend` o `~/.local/share/bt-autosuspend`).
2. Abre una terminal dentro de la carpeta y ejecuta:
   ```bash
   ./install.sh
   ```
   El instalador verificará automáticamente que tengas todas las dependencias instaladas, otorgará permisos de ejecución y creará el enlace en `~/.local/bin/bt-autosuspend`.

### Opción B: Instalación Manual
Si prefieres hacerlo manualmente paso a paso:
1. Dale permisos de ejecución al script principal:
   ```bash
   chmod +x main.py
   ```
2. Asegúrate de que la carpeta de binarios locales exista:
   ```bash
   mkdir -p ~/.local/bin
   ```
3. Crea un enlace simbólico para poder invocar `bt-autosuspend` desde cualquier terminal:
   ```bash
   ln -sf "$(pwd)/main.py" ~/.local/bin/bt-autosuspend
   ```
4. Verifica que `~/.local/bin` esté en tu variable `$PATH` (en la gran mayoría de distribuciones modernas ya viene incluido por defecto; si no, agrega `export PATH="$HOME/.local/bin:$PATH"` a tu `~/.bashrc` o `~/.zshrc`).

---

## 3. Guía de Configuración (Explicación de cada opción)

Al abrir la interfaz (`bt-autosuspend` o `bt-autosuspend config`), verás una serie de opciones. A continuación se explica para qué sirve cada una y cómo elegir el valor adecuado:

### Tiempo de Inactividad
* **Qué hace:** Es el tiempo continuo (en segundos) que debe transcurrir sin que se reproduzca sonido alguno antes de que el script proceda a desconectar el dispositivo Bluetooth.
* **Valores sugeridos:**
  * `120` (2 minutos): Ideal para pausas cortas.
  * `300` (5 minutos): Recomendado si sueles pausar para atender llamadas o contestar mensajes sin que se apaguen tus auriculares de inmediato.
  * `600` (10 minutos): Para un margen amplio de espera.

### Método de Detección
Define cómo sabe el script si estás escuchando algo o no:
* **Híbrido (MPRIS + Audio PipeWire) [Recomendado]:**
  * *Cómo funciona:* Monitorea tanto reproductores multimedia con soporte MPRIS (`playerctl`, como Spotify, Zen Browser, Firefox, Chrome, VLC) **y simultáneamente** revisa a nivel de PipeWire (`pactl`) si hay un flujo de audio activo dirigiéndose a tus auriculares.
  * *Ventaja:* Es la opción más completa. Si estás jugando a un videojuego, en una llamada de Discord, o viendo un reproductor web que no expone controles multimedia al sistema, el audio de PipeWire mantendrá la conexión viva y **no** te desconectará por error.
* **Solo MPRIS:**
  * *Cómo funciona:* Solo consulta si algún reproductor multimedia registrado en el sistema está en estado `Playing`.
  * *Cuándo usarlo:* Si solo quieres basarte en reproductores de música formales y quieres que llamadas o sonidos del sistema no retrasen el apagado.
* **Solo PipeWire:**
  * *Cómo funciona:* Solo se fija en si hay flujo de sonido activo saliendo por el canal del dispositivo Bluetooth.
  * *Cuándo usarlo:* En entornos donde no uses clientes MPRIS o si prefieres una detección puramente acústica a nivel del servidor de audio.

### Regla de Dispositivos
Determina qué dispositivos Bluetooth están sujetos a la desconexión automática:
* **Solo dispositivos de audio (Auriculares, Altavoces, Barras):**
  * *Por defecto.* El script inspecciona el perfil de cada dispositivo (`Audio Sink`, `Headset`, etc.). Desconectará cualquier auricular o altavoz inactivo, ignorando cualquier otro tipo de periférico.
* **Lista Blanca (Desconectar todos EXCEPTO los seleccionados):**
  * Desconecta cualquier auricular inactivo, **salvo** aquellos que marques en la subpantalla de selección. Útil si tienes un dispositivo fijo (como una barra de sonido en tu escritorio) que quieres que permanezca siempre conectado, pero quieres que tus auriculares portátiles sí se desconecten.
* **Lista Negra (Solo desconectar los seleccionados):**
  * El script **únicamente** desconectará los dispositivos que tú elijas explícitamente en la lista. El resto de dispositivos Bluetooth conectados no serán tocados nunca.
* **Todos los dispositivos Bluetooth:**
  * Aplica la regla a cualquier dispositivo conectado (a menos que esté protegido por la opción de periféricos HID).

### Selección de Dispositivos (Lista Blanca / Negra)
* **Qué hace:** Abre una pantalla que lista todos los dispositivos Bluetooth emparejados en tu ordenador.
* **Cómo usarla:**
  * Con las flechas `↑` y `↓` te posicionas sobre un dispositivo.
  * Al pulsar `ESPACIO`, marcas o desmarcas la casilla (`[X]` o `[ ]`).
  * Cada dispositivo muestra si está `[CONECTADO]` o `[DESCONECTADO]`, y si es de tipo `(Audio)` o `(HID)`.
  * Al pulsar `ENTER` o `ESC`, vuelves al menú principal con tu selección guardada.

### Proteger Periféricos (Ratón / Teclado / Mandos)
* **Qué hace:** Inspecciona los identificadores HID (*Human Interface Device*) de cada dispositivo Bluetooth.
* **Por qué es vital:** Si tienes un ratón o teclado inalámbrico Bluetooth, esta opción garantiza que **bajo ninguna circunstancia** el script desconecte tu ratón o teclado, incluso si se activa la regla de desconexión. Se recomienda mantenerla siempre en **ACTIVADO**.

### Notificación Previa de Desconexión
* **Qué hace:** Muestra una notificación visual en tu entorno de escritorio (`notify-send`) advirtiéndote antes de realizar la desconexión.
* **Comportamiento inteligente:** Si te sale la notificación de *"Inactividad detectada. Desconectando auriculares en 15s..."* y simplemente reanudas la música o pones un vídeo, el script detecta el sonido inmediatamente, cancela la desconexión y te avisa: *"Reproducción reanudada. Desconexión cancelada"*.

### Tiempo de Aviso de Notificación
* **Qué hace:** Define cuántos segundos antes del tiempo límite de inactividad se lanza la notificación previa (por defecto: `15` segundos).

---

## 4. Uso de la Interfaz Interactiva (TUI)

Para abrir la interfaz de terminal, simplemente escribe:
```bash
bt-autosuspend
```
o:
```bash
bt-autosuspend config
```

### Controles del teclado:
* `↑` / `↓` o teclas `k` / `j`: Desplazarte por las opciones.
* `ENTER` o `ESPACIO`: Cambiar el valor de la opción seleccionada o entrar a editar.
* `S`: Guardar la configuración y salir.
* `Q` o `ESC`: Salir sin guardar los cambios.

En la parte inferior de la ventana, la interfaz te mostrará en todo momento un **resumen en tiempo real** de qué dispositivos Bluetooth tienes conectados y si el motor detecta reproducción activa en ese instante.

---

## 5. Referencia de Comandos CLI

El ejecutable `bt-autosuspend` ofrece varios comandos útiles:

| Comando | Descripción |
| :--- | :--- |
| `bt-autosuspend` o `bt-autosuspend config` | Abre la interfaz gráfica de terminal (TUI) para configurar tiempos y reglas. |
| `bt-autosuspend status` | Muestra un resumen rápido en texto con la configuración actual, si hay música sonando y la lista de dispositivos detectados. |
| `bt-autosuspend run` | Inicia el monitor en primer plano (útil para pruebas o scripts de inicio de tu gestor de ventanas). |
| `bt-autosuspend service install` | Instala y activa el servicio automático de **Systemd** para tu usuario. |
| `bt-autosuspend service status` | Consulta el estado y los registros del servicio de Systemd. |
| `bt-autosuspend service uninstall` | Detiene y elimina el servicio de Systemd del sistema. |

---

## 6. Cómo iniciarlo automáticamente con el sistema

Para no tener que preocuparte de iniciarlo a mano, elige cualquiera de estas opciones:

### Opción 1: Servicio Systemd de Usuario (Recomendado)
Es la forma más robusta y limpia en cualquier distribución con Systemd:
```bash
bt-autosuspend service install
```
A partir de ese momento, el servicio se ejecutará silenciosamente en segundo plano cada vez que inicies sesión y se reiniciará automáticamente si llega a cerrarse.

Si deseas ver qué está haciendo el servicio en tiempo real:
```bash
bt-autosuspend service status
# o también:
journalctl --user -u bt-autosuspend.service -f
```

### Opción 2: Compositor Niri (Wayland)
Si utilizas el compositor **Niri**, puedes pedirle directamente a Niri que lo lance al arrancar tu sesión gráfica.
Edita tu archivo `~/.config/niri/config.kdl` y añade la siguiente línea:

```kdl
spawn-at-startup "bt-autosuspend" "run"
```

### Opción 3: Hyprland / Sway
Si usas **Hyprland**, añade a tu `~/.config/hypr/hyprland.conf`:
```ini
exec-once = bt-autosuspend run
```
Si usas **Sway**, añade a tu `~/.config/sway/config`:
```ini
exec bt-autosuspend run
```

---

## 7. Preguntas Frecuentes y Solución de Problemas

#### ¿Dónde se almacena la configuración?
En el archivo estándar JSON:
`~/.config/bt-autosuspend/config.json`
Puedes editarlo con la interfaz `bt-autosuspend config` o directamente con un editor de texto si lo prefieres.

#### La terminal dice "bt-autosuspend: comando no encontrado"
Asegúrate de que la ruta `~/.local/bin` esté en tu variable `$PATH`. Puedes verificarlo ejecutando:
```bash
echo $PATH
```
Si no aparece, agrega esta línea al final de tu archivo `~/.bashrc` (o `~/.zshrc` si usas Zsh):
```bash
export PATH="$HOME/.local/bin:$PATH"
```
Luego cierra la terminal y ábrela nuevamente.

#### No aparecen las notificaciones de aviso antes de desconectar
`bt-autosuspend` utiliza la herramienta estándar `notify-send`. Asegúrate de tener un daemon de notificaciones activo en tu sesión gráfica (como `mako`, `dunst`, `swaync` o el centro de notificaciones de tu entorno). Puedes hacer una prueba manual escribiendo:
```bash
notify-send "Prueba" "Esto es una notificación"
```
Si ves la notificación, `bt-autosuspend` funcionará a la perfección.

#### ¿Consume batería o procesador en segundo plano?
Prácticamente nada. El script despierta una vez cada varios segundos (configurable con `check_interval_seconds`, por defecto 3 segundos), hace una comprobación ultraligera de estados y vuelve a dormir.
