# Feature: Auto Bluetooth Disconnect on Media Idle (`bt-autosuspend`)

## Objective
Detect when multimedia playback stops (MPRIS / PipeWire audio streams) and automatically disconnect designated Bluetooth devices after a configurable inactivity timeout, avoiding global Bluetooth power off (protecting mice/keyboards) and providing a friendly Terminal User Interface (TUI) for configuration.

## Scope & Constraints
- **Target OS / Desktop**: Linux CachyOS, Niri (Wayland), PipeWire + WirePlumber.
- **Audio Detection**: Hybrid (MPRIS via `playerctl` + PipeWire audio stream/sink state via `pactl`/`wpctl`), with configuration to toggle MPRIS-only or Hybrid.
- **Device Management**: Specific device disconnect (`bluetoothctl disconnect <MAC>`) rather than disabling the whole controller.
- **Filtering Options**: All audio devices, Whitelist (disconnect all except specified), Blacklist (only disconnect specified), auto-ignore HID peripherals (mouse, keyboard, gamepad).
- **Grace Period / Notifications**: Optional desktop notification (`notify-send`) warning before disconnecting.
- **TUI Interface**: Interactive terminal interface with arrow keys and checkboxes to adjust settings without editing files manually.
- **Persistence**: Configuration saved in `~/.config/bt-autosuspend/config.json`.
- **System Integration**: Ready for Niri `spawn-at-startup` and systemd user service.

---

## Tasks

- [x] **TASK-1**: Configuration engine & data model
  - Path: `bt-autosuspend/config.py`
  - Route: Direct inline
  - Checks: Load default configuration, serialize/deserialize JSON in `~/.config/bt-autosuspend/config.json`, schema validation.
  - Evidence: Commit `858f758`

- [x] **TASK-2**: Bluetooth & Audio detection core
  - Path: `bt-autosuspend/detector.py`
  - Route: Direct inline
  - Checks: Enumerate paired & connected BT devices, distinguish audio vs HID, detect MPRIS playback (`playerctl`), detect PipeWire active audio sinks/streams (`pactl`).
  - Evidence: Commit `fb0d4cb`

- [x] **TASK-3**: Daemon & Disconnection lifecycle
  - Path: `bt-autosuspend/daemon.py`
  - Route: Direct inline
  - Checks: Track idle elapsed time, trigger pre-disconnect notification via `notify-send`, disconnect target devices on timeout, cancel countdown if playback resumes.
  - Evidence: Commit `0cecba3`

- [x] **TASK-4**: Interactive Terminal User Interface (TUI)
  - Path: `bt-autosuspend/tui.py`
  - Route: Direct inline
  - Checks: Interactive curses/rich menu for idle time, detection mode selection, device list with toggle checkboxes, preview status.
  - Evidence: Commit `f8ce55a`

- [x] **TASK-5**: CLI entry point & system integration
  - Path: `bt-autosuspend/main.py`, symlink `~/.local/bin/bt-autosuspend`, systemd unit generator
  - Route: Direct inline
  - Checks: Commands `config`, `run`, `status`, `service install/uninstall`, executable permissions and symlink.
  - Evidence: Commit `a909ed6`

- [x] **TASK-6**: End-to-end testing & verification
  - Route: Direct inline
  - Checks: Automated test suite `test_all.py` passed (4 tests in 0.002s), status verified against live Spotify stream & Samsung Soundbar.
  - Evidence: Commit `e7cb4b2`

- [x] **TASK-7**: Complete User Guide & 1-Command Installer
  - Path: `bt-autosuspend/README.md`, `bt-autosuspend/install.sh`
  - Route: Direct inline
  - Checks: Automated installer verifies dependencies across distros, complete documentation for each setting and scenario.
  - Evidence: Commit `9833101`
