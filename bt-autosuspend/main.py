#!/usr/bin/env python3
"""
bt-autosuspend: Automatic Bluetooth Disconnect on Media Inactivity.
CLI entrypoint and manager.
"""

from __future__ import annotations
import sys
import os
import argparse
import subprocess
from pathlib import Path
from config import Config
from detector import Detector
from daemon import AutoSuspendDaemon
from tui import TUI

SERVICE_DIR = Path.home() / ".config" / "systemd" / "user"
SERVICE_FILE = SERVICE_DIR / "bt-autosuspend.service"


def cmd_config(args):
    """Opens interactive TUI configuration."""
    cfg = Config.load()
    tui = TUI(cfg)
    saved = tui.run()
    if saved:
        print("\n✔ Configuración guardada correctamente en ~/.config/bt-autosuspend/config.json\n")
    else:
        print("\nSaliendo sin guardar cambios.\n")


def cmd_run(args):
    """Runs the monitor daemon."""
    cfg = Config.load()
    daemon = AutoSuspendDaemon(cfg)
    daemon.run()


def cmd_status(args):
    """Displays current system status, playback detection and devices."""
    cfg = Config.load()
    daemon = AutoSuspendDaemon(cfg)
    st = daemon.get_current_status()

    paired = Detector.get_paired_devices()
    connected = [d for d in paired if d.connected]

    print("\n" + "=" * 56)
    print("        bt-autosuspend :: Estado del Sistema")
    print("=" * 56)

    print("\n[Configuración]")
    print(f"  • Tiempo de inactividad : {cfg.idle_timeout_seconds} segundos")
    print(f"  • Modo de detección     : {cfg.detection_mode}")
    print(f"  • Regla de dispositivos : {cfg.device_filter_mode}")
    print(f"  • Proteger HID (ratón)  : {'Sí' if cfg.auto_ignore_hid else 'No'}")
    print(f"  • Notificación previa   : {'Sí (' + str(cfg.notification_grace_seconds) + 's antes)' if cfg.notify_before_disconnect else 'No'}")

    print("\n[Detección de Reproducción]")
    print(f"  • Estado actual         : {'▶ REPRODUCIENDO' if st.playback_active else '⏸ INACTIVO'}")
    print(f"  • Detalle               : {st.playback_reason}")

    print("\n[Dispositivos Bluetooth]")
    if not paired:
        print("  • No hay dispositivos emparejados.")
    else:
        for d in paired:
            managed = Detector.should_device_be_managed(d, cfg)
            status_tag = "[CONECTADO]" if d.connected else "[DESCONECTADO]"
            type_tag = "Audio" if d.is_audio else ("Periférico (HID)" if d.is_hid else "Otro")
            manage_tag = "✔ Gestionado" if managed else "Ignorado"

            print(f"  • {status_tag:<14} {d.name} ({d.mac})")
            print(f"      Tipo: {type_tag} | {manage_tag}")

    print("\n" + "=" * 56 + "\n")


def cmd_service(args):
    """Manages the systemd user service."""
    action = args.action

    current_script = Path(__file__).resolve()
    # If symlinked in ~/.local/bin, prefer that path
    local_bin = Path.home() / ".local" / "bin" / "bt-autosuspend"
    exec_path = str(local_bin) if local_bin.exists() else f"{sys.executable} {current_script}"

    service_content = f"""[Unit]
Description=bt-autosuspend: Automatic Bluetooth Disconnect on Media Inactivity
After=pipewire.service wireplumber.service bluetooth.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart={exec_path} run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""

    if action == "install":
        SERVICE_DIR.mkdir(parents=True, exist_ok=True)
        with open(SERVICE_FILE, "w", encoding="utf-8") as f:
            f.write(service_content)

        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        res = subprocess.run(["systemctl", "--user", "enable", "--now", "bt-autosuspend.service"], check=False)

        if res.returncode == 0:
            print(f"✔ Servicio instalado y activado en {SERVICE_FILE}")
            print("  El demonio se iniciará automáticamente con tu sesión de usuario.")
        else:
            print("⚠ Se guardó el archivo de servicio, pero hubo un error al activarlo.")

    elif action == "uninstall":
        subprocess.run(["systemctl", "--user", "disable", "--now", "bt-autosuspend.service"], check=False)
        if SERVICE_FILE.exists():
            SERVICE_FILE.unlink()
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
            print("✔ Servicio desinstalado y detenido correctamente.")
        else:
            print("El servicio no estaba instalado.")

    elif action == "status":
        subprocess.run(["systemctl", "--user", "status", "bt-autosuspend.service"])


def main():
    parser = argparse.ArgumentParser(
        prog="bt-autosuspend",
        description="Desconecta automáticamente dispositivos Bluetooth tras inactividad multimedia.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # config command
    subparsers.add_parser("config", help="Abre la interfaz interactiva de configuración (TUI)")

    # run command
    subparsers.add_parser("run", help="Inicia el monitor en segundo plano (daemon)")

    # status command
    subparsers.add_parser("status", help="Muestra el estado actual y los dispositivos detectados")

    # service command
    srv_parser = subparsers.add_parser("service", help="Gestiona el servicio systemd de usuario")
    srv_parser.add_argument(
        "action",
        choices=["install", "uninstall", "status"],
        help="install: instala e inicia el servicio | uninstall: elimina el servicio | status: ver estado",
    )

    args = parser.parse_args()

    # Default to config TUI if no command is given
    if not args.command:
        cmd_config(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "service":
        cmd_service(args)


if __name__ == "__main__":
    main()
