"""
Detection module for Bluetooth devices and audio playback status.
Supports MPRIS (via playerctl) and PipeWire/PulseAudio sink states (via pactl).
"""

from __future__ import annotations
import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from config import Config


@dataclass
class BluetoothDevice:
    mac: str
    name: str
    connected: bool
    is_audio: bool
    is_hid: bool


class Detector:
    @staticmethod
    def get_paired_devices() -> List[BluetoothDevice]:
        """Returns all paired bluetooth devices with classification."""
        try:
            out = subprocess.check_output(["bluetoothctl", "devices"], text=True, stderr=subprocess.DEVNULL)
        except Exception:
            return []

        try:
            conn_out = subprocess.check_output(
                ["bluetoothctl", "devices", "Connected"], text=True, stderr=subprocess.DEVNULL
            )
            connected_macs = set(re.findall(r"Device ([0-9A-Fa-f:]{17})", conn_out))
        except Exception:
            connected_macs = set()

        devices: List[BluetoothDevice] = []
        for line in out.strip().splitlines():
            m = re.match(r"Device ([0-9A-Fa-f:]{17})\s+(.*)", line)
            if not m:
                continue
            mac = m.group(1).upper()
            name = m.group(2).strip()

            is_audio = False
            is_hid = False

            try:
                info_out = subprocess.check_output(
                    ["bluetoothctl", "info", mac], text=True, stderr=subprocess.DEVNULL
                )
                # Check for audio profile UUIDs or icons
                audio_indicators = [
                    "Audio Sink",
                    "Audio Source",
                    "Headset",
                    "A/V Remote Control",
                    "audio-headset",
                    "audio-card",
                ]
                is_audio = any(ind in info_out for ind in audio_indicators)

                # Check for HID indicators (mice, keyboards, gamepads)
                hid_indicators = ["Human Interface Device", "input-keyboard", "input-mouse", "input-gaming"]
                is_hid = any(ind in info_out for ind in hid_indicators)
            except Exception:
                pass

            devices.append(
                BluetoothDevice(
                    mac=mac,
                    name=name,
                    connected=mac in connected_macs,
                    is_audio=is_audio,
                    is_hid=is_hid,
                )
            )

        return devices

    @staticmethod
    def get_connected_devices() -> List[BluetoothDevice]:
        """Returns only currently connected bluetooth devices."""
        return [dev for dev in Detector.get_paired_devices() if dev.connected]

    @staticmethod
    def is_mpris_playing() -> Tuple[bool, List[str]]:
        """
        Checks if any media player is actively Playing via playerctl.
        Returns (is_playing, list_of_active_players).
        """
        try:
            # Check players status
            out = subprocess.check_output(
                ["playerctl", "-a", "status"], text=True, stderr=subprocess.DEVNULL
            )
            statuses = [s.strip() for s in out.strip().splitlines() if s.strip()]
            is_playing = any(s.lower() == "playing" for s in statuses)

            players_playing: List[str] = []
            if is_playing:
                try:
                    players_out = subprocess.check_output(
                        ["playerctl", "-l"], text=True, stderr=subprocess.DEVNULL
                    )
                    for player in players_out.strip().splitlines():
                        player = player.strip()
                        if not player:
                            continue
                        st = subprocess.check_output(
                            ["playerctl", "-p", player, "status"],
                            text=True,
                            stderr=subprocess.DEVNULL,
                        ).strip()
                        if st.lower() == "playing":
                            players_playing.append(player)
                except Exception:
                    pass

            return is_playing, players_playing
        except subprocess.CalledProcessError:
            # playerctl returns non-zero when no players exist
            return False, []
        except Exception:
            return False, []

    @staticmethod
    def get_bluez_sink_states() -> Dict[str, str]:
        """
        Inspects PipeWire/PulseAudio sinks via pactl and maps Bluetooth MACs to their sink state
        (RUNNING, IDLE, SUSPENDED).
        """
        try:
            out = subprocess.check_output(["pactl", "list", "sinks"], text=True, stderr=subprocess.DEVNULL)
        except Exception:
            return {}

        sinks: Dict[str, str] = {}
        current_state: Optional[str] = None

        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Sink #"):
                current_state = None
            elif line.startswith("State:"):
                current_state = line.split(":", 1)[1].strip()
            elif line.startswith("Name:") and "bluez_output." in line:
                m = re.search(
                    r"([0-9A-Fa-f]{2}[_:][0-9A-Fa-f]{2}[_:][0-9A-Fa-f]{2}[_:][0-9A-Fa-f]{2}[_:][0-9A-Fa-f]{2}[_:][0-9A-Fa-f]{2})",
                    line,
                )
                if m and current_state:
                    mac = m.group(1).replace("_", ":").upper()
                    sinks[mac] = current_state

        return sinks

    @classmethod
    def is_playback_active(cls, config: Config, target_mac: Optional[str] = None) -> Tuple[bool, str]:
        """
        Determines whether multimedia playback is active according to the configured detection mode.
        Returns (is_active, reason_description).
        """
        mpris_playing, active_players = cls.is_mpris_playing()
        sink_states = cls.get_bluez_sink_states()

        # Check if the specific sink or any BT sink is actively streaming audio
        pipewire_running = False
        running_sinks = [mac for mac, state in sink_states.items() if state.upper() == "RUNNING"]
        if target_mac:
            pipewire_running = sink_states.get(target_mac.upper(), "").upper() == "RUNNING"
        else:
            pipewire_running = len(running_sinks) > 0

        mode = config.detection_mode

        if mode == "mpris":
            if mpris_playing:
                players_str = ", ".join(active_players) if active_players else "reproductor"
                return True, f"MPRIS activo ({players_str})"
            return False, "Sin reproductores MPRIS activos"

        elif mode == "pipewire":
            if pipewire_running:
                return True, f"PipeWire activo ({len(running_sinks)} sink(s) emitiendo sonido)"
            return False, "Audio PipeWire en silencio / IDLE"

        else:  # hybrid
            reasons = []
            if mpris_playing:
                players_str = ", ".join(active_players) if active_players else "MPRIS"
                reasons.append(f"MPRIS ({players_str})")
            if pipewire_running:
                reasons.append(f"PipeWire ({', '.join(running_sinks)})")

            if reasons:
                return True, f"Reproduciendo: {' + '.join(reasons)}"
            return False, "Sin audio (MPRIS pausado y salida PipeWire inactiva)"

    @classmethod
    def should_device_be_managed(cls, device: BluetoothDevice, config: Config) -> bool:
        """Determines if a connected device is subject to auto-disconnection under the config rules."""
        if not device.connected:
            return False

        # Protect HID devices (mouse, keyboard, etc.)
        if config.auto_ignore_hid and device.is_hid:
            return False

        mode = config.device_filter_mode
        mac_upper = device.mac.upper()

        if mode == "all":
            return True

        elif mode == "audio_only":
            return device.is_audio

        elif mode == "whitelist":
            # Disconnect if it's NOT in the whitelist (and is audio)
            whitelisted = {m.upper() for m in config.whitelist_macs}
            return device.is_audio and (mac_upper not in whitelisted)

        elif mode == "blacklist":
            # Disconnect ONLY if it's in the blacklist
            blacklisted = {m.upper() for m in config.blacklist_macs}
            return mac_upper in blacklisted

        return False
