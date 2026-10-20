"""
Configuration management for bt-autosuspend.
Stores and loads configuration from ~/.config/bt-autosuspend/config.json.
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Literal

CONFIG_DIR = Path.home() / ".config" / "bt-autosuspend"
CONFIG_FILE = CONFIG_DIR / "config.json"

DetectionMode = Literal["hybrid", "mpris", "pipewire"]
FilterMode = Literal["audio_only", "all", "whitelist", "blacklist"]


@dataclass
class Config:
    # Inactivity timeout in seconds before disconnecting
    idle_timeout_seconds: int = 120

    # Detection method: "hybrid" (MPRIS + PipeWire audio stream), "mpris", or "pipewire"
    detection_mode: DetectionMode = "hybrid"

    # Device filtering mode:
    # - "audio_only": Disconnect any audio devices (headphones, speakers, soundbars)
    # - "all": Disconnect all BT devices (except HID if auto_ignore_hid is True)
    # - "whitelist": Disconnect all audio devices EXCEPT those in whitelist_macs
    # - "blacklist": Disconnect ONLY devices in blacklist_macs
    device_filter_mode: FilterMode = "audio_only"

    # Lists of MAC addresses for filter modes
    whitelist_macs: List[str] = field(default_factory=list)
    blacklist_macs: List[str] = field(default_factory=list)

    # Protect HID devices (keyboards, mice, gamepads) from disconnection
    auto_ignore_hid: bool = True

    # Show a desktop notification warning before disconnecting
    notify_before_disconnect: bool = True

    # Seconds between pre-disconnect warning notification and actual disconnect
    notification_grace_seconds: int = 15

    # Interval in seconds to poll for status
    check_interval_seconds: int = 3

    @classmethod
    def load(cls) -> Config:
        """Loads configuration from ~/.config/bt-autosuspend/config.json or returns defaults."""
        if not CONFIG_FILE.exists():
            cfg = cls()
            cfg.save()
            return cfg

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Filter unknown keys to prevent crashes on schema evolution
            valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
            clean_data = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**clean_data)
        except Exception:
            return cls()

    def save(self) -> None:
        """Saves current configuration to disk safely."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp_file = CONFIG_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4)
        tmp_file.replace(CONFIG_FILE)
