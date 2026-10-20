"""
Daemon and lifecycle monitoring for bt-autosuspend.
Monitors playback and disconnects idle Bluetooth audio devices.
"""

from __future__ import annotations
import time
import signal
import sys
import subprocess
from dataclasses import dataclass
from typing import Optional, List
from config import Config
from detector import Detector, BluetoothDevice


@dataclass
class DaemonStatus:
    running: bool
    idle_seconds: float
    idle_timeout: int
    playback_active: bool
    playback_reason: str
    connected_managed_devices: List[BluetoothDevice]
    warning_sent: bool


class AutoSuspendDaemon:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self.idle_seconds: float = 0.0
        self.warning_sent: bool = False
        self._running: bool = False

    def send_notification(self, title: str, message: str, urgency: str = "normal") -> None:
        """Sends a desktop notification using notify-send if enabled."""
        if not self.config.notify_before_disconnect:
            return
        try:
            subprocess.run(
                [
                    "notify-send",
                    "-u",
                    urgency,
                    "-i",
                    "audio-headset",
                    "-a",
                    "bt-autosuspend",
                    title,
                    message,
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def disconnect_device(self, device: BluetoothDevice) -> bool:
        """Disconnects a specific Bluetooth device."""
        try:
            print(f"[bt-autosuspend] Desconectando {device.name} ({device.mac}) por inactividad...")
            res = subprocess.run(
                ["bluetoothctl", "disconnect", device.mac],
                check=False,
                text=True,
                capture_output=True,
            )
            success = res.returncode == 0
            if success:
                self.send_notification(
                    "Dispositivo Desconectado",
                    f"{device.name} se ha desconectado por inactividad.",
                    urgency="low",
                )
            return success
        except Exception as e:
            print(f"[bt-autosuspend] Error al desconectar {device.mac}: {e}", file=sys.stderr)
            return False

    def get_current_status(self) -> DaemonStatus:
        """Fetches instantaneous system status."""
        self.config = Config.load()  # hot-reload config
        paired = Detector.get_paired_devices()
        managed_connected = [d for d in paired if d.connected and Detector.should_device_be_managed(d, self.config)]
        active, reason = Detector.is_playback_active(self.config)

        return DaemonStatus(
            running=self._running,
            idle_seconds=self.idle_seconds,
            idle_timeout=self.config.idle_timeout_seconds,
            playback_active=active,
            playback_reason=reason,
            connected_managed_devices=managed_connected,
            warning_sent=self.warning_sent,
        )

    def run(self) -> None:
        """Main daemon loop."""
        self._running = True

        def handle_signal(sig, frame):
            print("\n[bt-autosuspend] Deteniendo demonio...")
            self._running = False
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        print("[bt-autosuspend] Servicio de monitorización iniciado.")
        print(f"[bt-autosuspend] Tiempo de inactividad: {self.config.idle_timeout_seconds}s | Modo detección: {self.config.detection_mode}")

        last_check_time = time.monotonic()

        while self._running:
            time.sleep(self.config.check_interval_seconds)
            now = time.monotonic()
            delta = now - last_check_time
            last_check_time = now

            # Reload config dynamically in case user edited it via TUI
            self.config = Config.load()

            # Find connected devices that match filter criteria
            all_devices = Detector.get_paired_devices()
            managed_devices = [
                d for d in all_devices if d.connected and Detector.should_device_be_managed(d, self.config)
            ]

            if not managed_devices:
                # No managed devices currently connected; stay idle and reset counter
                if self.idle_seconds > 0:
                    self.idle_seconds = 0.0
                    self.warning_sent = False
                continue

            # Check playback status
            is_active, reason = Detector.is_playback_active(self.config)

            if is_active:
                if self.idle_seconds > 0:
                    if self.warning_sent:
                        print(f"[bt-autosuspend] Reproducción reanudada ({reason}). Desconexión cancelada.")
                        self.send_notification(
                            "Reproducción reanudada",
                            "Desconexión automática cancelada.",
                            urgency="low",
                        )
                    self.idle_seconds = 0.0
                    self.warning_sent = False
            else:
                self.idle_seconds += delta
                remaining = self.config.idle_timeout_seconds - self.idle_seconds

                device_names = ", ".join(d.name for d in managed_devices)

                # Check if we should send pre-disconnect warning notification
                if (
                    self.config.notify_before_disconnect
                    and not self.warning_sent
                    and remaining <= self.config.notification_grace_seconds
                    and remaining > 0
                ):
                    print(
                        f"[bt-autosuspend] Inactividad ({self.idle_seconds:.0f}s). Notificando desconexión en {int(remaining)}s para: {device_names}"
                    )
                    self.send_notification(
                        "Bluetooth inactivo",
                        f"Inactividad detectada. Desconectando {device_names} en {int(remaining)} segundos...",
                        urgency="normal",
                    )
                    self.warning_sent = True

                # Check if timeout has expired
                if self.idle_seconds >= self.config.idle_timeout_seconds:
                    print(f"[bt-autosuspend] Tiempo de inactividad alcanzado ({self.config.idle_timeout_seconds}s).")
                    for dev in managed_devices:
                        self.disconnect_device(dev)

                    # Reset timer and warning
                    self.idle_seconds = 0.0
                    self.warning_sent = False
