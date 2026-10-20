"""
Interactive Terminal User Interface (TUI) for configuring bt-autosuspend.
Uses curses for interactive navigation and keyboard selection.
"""

from __future__ import annotations
import curses
import sys
from typing import List, Set
from config import Config, DetectionMode, FilterMode
from detector import Detector, BluetoothDevice


DETECTION_MODES: List[Tuple[DetectionMode, str]] = [
    ("hybrid", "Híbrido (MPRIS + Audio PipeWire) [Recomendado]"),
    ("mpris", "Solo MPRIS (Spotify, reproductores, navegadores)"),
    ("pipewire", "Solo PipeWire (Flujo de audio activo)"),
]

FILTER_MODES: List[Tuple[FilterMode, str]] = [
    ("audio_only", "Solo dispositivos de audio (Auriculares, Altavoces, Barras)"),
    ("whitelist", "Lista Blanca (Desconectar todos EXCEPTO los seleccionados)"),
    ("blacklist", "Lista Negra (Solo desconectar los seleccionados)"),
    ("all", "Todos los dispositivos Bluetooth"),
]


class TUI:
    def __init__(self, config: Config):
        self.config = config
        self.devices = Detector.get_paired_devices()

    def run(self) -> bool:
        """Runs the interactive curses TUI. Returns True if saved, False if cancelled."""
        try:
            return curses.wrapper(self._main_menu)
        except curses.error as e:
            print(f"Error iniciando interfaz curses: {e}", file=sys.stderr)
            return self._fallback_menu()

    def _prompt_number(self, stdscr, prompt: str, current_val: int, min_val: int = 5, max_val: int = 3600) -> int:
        """Prompts for an integer value inside curses."""
        curses.echo()
        curses.curs_set(1)
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        y = max(2, h // 2 - 2)
        x = max(2, (w - len(prompt) - 20) // 2)

        stdscr.addstr(y, x, prompt, curses.A_BOLD)
        stdscr.addstr(y + 1, x, f"Valor actual: {current_val} s (Rango: {min_val} - {max_val}s)")
        stdscr.addstr(y + 3, x, "Nuevo valor (ENTER para confirmar): ")
        stdscr.refresh()

        try:
            input_bytes = stdscr.getstr(y + 3, x + 35, 10)
            input_str = input_bytes.decode("utf-8").strip()
            if input_str.isdigit():
                val = int(input_str)
                if min_val <= val <= max_val:
                    return val
        except Exception:
            pass
        finally:
            curses.noecho()
            curses.curs_set(0)

        return current_val

    def _select_devices_screen(self, stdscr) -> None:
        """Sub-screen to select devices for whitelist or blacklist with checkboxes."""
        self.devices = Detector.get_paired_devices()
        current_idx = 0

        # Determine which list we are editing
        is_whitelist = self.config.device_filter_mode == "whitelist"
        target_set: Set[str] = set(
            self.config.whitelist_macs if is_whitelist else self.config.blacklist_macs
        )

        list_name = "Lista Blanca (Excepciones)" if is_whitelist else "Lista Negra (Específicos)"

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            # Header
            title = f"--- Seleccionar Dispositivos :: {list_name} ---"
            stdscr.addstr(1, max(2, (w - len(title)) // 2), title, curses.A_BOLD | curses.A_UNDERLINE)

            desc = "Usa [ESPACIO] para marcar/desmarcar | [ENTER/ESC] para volver"
            stdscr.addstr(2, max(2, (w - len(desc)) // 2), desc, curses.A_DIM)

            if not self.devices:
                stdscr.addstr(4, 4, "No se encontraron dispositivos Bluetooth emparejados.")
            else:
                for i, dev in enumerate(self.devices):
                    y = 4 + i
                    if y >= h - 2:
                        break

                    checked = dev.mac.upper() in target_set
                    box = "[X]" if checked else "[ ]"
                    conn = "[CONECTADO]" if dev.connected else "[DESCONECTADO]"
                    tag = " (Audio)" if dev.is_audio else (" (HID)" if dev.is_hid else "")

                    line = f" {box} {dev.name:<28} {dev.mac}  {conn:<14}{tag}"

                    if i == current_idx:
                        stdscr.addstr(y, 2, line[: w - 4], curses.A_REVERSE | curses.A_BOLD)
                    else:
                        color = curses.A_BOLD if checked else curses.A_NORMAL
                        stdscr.addstr(y, 2, line[: w - 4], color)

            stdscr.refresh()
            key = stdscr.getch()

            if key in (curses.KEY_UP, ord("k")):
                current_idx = max(0, current_idx - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                if self.devices:
                    current_idx = min(len(self.devices) - 1, current_idx + 1)
            elif key == ord(" "):
                if self.devices:
                    dev = self.devices[current_idx]
                    mac = dev.mac.upper()
                    if mac in target_set:
                        target_set.remove(mac)
                    else:
                        target_set.add(mac)
            elif key in (10, 13, 27, ord("q"), ord("Q")):  # ENTER or ESC or Q
                break

        # Save back to config
        new_list = sorted(list(target_set))
        if is_whitelist:
            self.config.whitelist_macs = new_list
        else:
            self.config.blacklist_macs = new_list

    def _main_menu(self, stdscr) -> bool:
        curses.curs_set(0)
        curses.use_default_colors()

        current_idx = 0

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            # Main Title
            title = "bt-autosuspend :: Configuración"
            stdscr.addstr(1, max(2, (w - len(title)) // 2), title, curses.A_BOLD | curses.A_UNDERLINE)

            guide = "Navegación: [↑/↓] o [j/k] | [ENTER/ESPACIO] Cambiar opción | [S] Guardar | [Q] Salir"
            stdscr.addstr(2, max(2, (w - len(guide)) // 2), guide, curses.A_DIM)

            # Read friendly labels
            det_label = dict(DETECTION_MODES).get(self.config.detection_mode, self.config.detection_mode)
            filter_label = dict(FILTER_MODES).get(self.config.device_filter_mode, self.config.device_filter_mode)

            selected_count = (
                len(self.config.whitelist_macs)
                if self.config.device_filter_mode == "whitelist"
                else len(self.config.blacklist_macs)
            )

            # Format items
            menu_items = [
                (
                    "Tiempo de Inactividad",
                    f"{self.config.idle_timeout_seconds} segundos ({self.config.idle_timeout_seconds // 60}m {self.config.idle_timeout_seconds % 60}s)",
                ),
                ("Método de Detección", det_label),
                ("Regla de Dispositivos", filter_label),
                (
                    "Dispositivos seleccionados",
                    f"{selected_count} dispositivo(s) configurado(s) -> [Presiona ENTER para editar]",
                ),
                (
                    "Proteger periféricos (Ratón/Teclado/Mando)",
                    "ACTIVADO (Nunca desconectar HID)" if self.config.auto_ignore_hid else "DESACTIVADO",
                ),
                (
                    "Notificación previa (notify-send)",
                    f"ACTIVADA (Avisar {self.config.notification_grace_seconds}s antes)"
                    if self.config.notify_before_disconnect
                    else "DESACTIVADA",
                ),
                ("Tiempo de aviso de notificación", f"{self.config.notification_grace_seconds} segundos"),
                ("Guardar cambios y Salir", "[ Guardar configuración ]"),
                ("Salir sin guardar", "[ Descartar cambios ]"),
            ]

            start_y = 4
            for i, (label, val) in enumerate(menu_items):
                y = start_y + i
                if y >= h - 2:
                    break

                line = f" {label:<44}: {val}"
                if i == current_idx:
                    stdscr.addstr(y, 2, line[: w - 4], curses.A_REVERSE | curses.A_BOLD)
                else:
                    if i == len(menu_items) - 2:  # Save button
                        stdscr.addstr(y, 2, line[: w - 4], curses.A_BOLD)
                    elif i == len(menu_items) - 1:  # Cancel button
                        stdscr.addstr(y, 2, line[: w - 4], curses.A_DIM)
                    else:
                        stdscr.addstr(y, 2, line[: w - 4])

            # Footer status preview
            status_y = start_y + len(menu_items) + 1
            if status_y < h - 1:
                active, reason = Detector.is_playback_active(self.config)
                connected_devs = Detector.get_connected_devices()
                conn_names = ", ".join(d.name for d in connected_devs) if connected_devs else "Ninguno"
                stdscr.addstr(
                    status_y,
                    2,
                    f"Estado actual: Dispositivos conectados: {conn_names}",
                    curses.A_DIM,
                )
                if status_y + 1 < h:
                    stdscr.addstr(
                        status_y + 1,
                        2,
                        f"Detección en tiempo real: {'[REPRODUCIENDO]' if active else '[INACTIVO]'} - {reason}",
                        curses.A_DIM,
                    )

            stdscr.refresh()
            key = stdscr.getch()

            if key in (curses.KEY_UP, ord("k")):
                current_idx = max(0, current_idx - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                current_idx = min(len(menu_items) - 1, current_idx + 1)

            elif key in (10, 13, ord(" "), curses.KEY_RIGHT):  # ENTER, SPACE, RIGHT
                if current_idx == 0:  # Timeout
                    self.config.idle_timeout_seconds = self._prompt_number(
                        stdscr, "Configurar Tiempo de Inactividad", self.config.idle_timeout_seconds, 10, 7200
                    )

                elif current_idx == 1:  # Detection mode
                    keys = [k for k, _ in DETECTION_MODES]
                    curr_pos = keys.index(self.config.detection_mode) if self.config.detection_mode in keys else 0
                    self.config.detection_mode = keys[(curr_pos + 1) % len(keys)]

                elif current_idx == 2:  # Device filter mode
                    keys = [k for k, _ in FILTER_MODES]
                    curr_pos = keys.index(self.config.device_filter_mode) if self.config.device_filter_mode in keys else 0
                    self.config.device_filter_mode = keys[(curr_pos + 1) % len(keys)]

                elif current_idx == 3:  # Select devices
                    self._select_devices_screen(stdscr)

                elif current_idx == 4:  # Auto ignore HID
                    self.config.auto_ignore_hid = not self.config.auto_ignore_hid

                elif current_idx == 5:  # Notify before disconnect
                    self.config.notify_before_disconnect = not self.config.notify_before_disconnect

                elif current_idx == 6:  # Notification grace seconds
                    self.config.notification_grace_seconds = self._prompt_number(
                        stdscr, "Tiempo de Aviso de Notificación", self.config.notification_grace_seconds, 3, 60
                    )

                elif current_idx == 7:  # Guardar
                    self.config.save()
                    return True

                elif current_idx == 8:  # Salir sin guardar
                    return False

            elif key in (ord("s"), ord("S")):
                self.config.save()
                return True

            elif key in (ord("q"), ord("Q"), 27):
                return False

    def _fallback_menu(self) -> bool:
        """Textual line-by-line fallback when curses is not available."""
        print("\n=== bt-autosuspend :: Configuración Básica ===")
        print(f"1. Tiempo inactividad actual: {self.config.idle_timeout_seconds}s")
        print(f"2. Modo detección actual: {self.config.detection_mode}")
        print(f"3. Modo filtro dispositivos: {self.config.device_filter_mode}")
        print(f"4. Proteger periféricos HID: {self.config.auto_ignore_hid}")
        print(f"5. Notificación previa: {self.config.notify_before_disconnect}")
        print("\nPara modificar interactivamente, ejecuta este comando en una terminal gráfica.")
        return False
