# Feature: Suwayomi Frontend Dynamic Scratchpad (`frontend_suwayomi`)

## Objective
Provide an agnostic, highly configurable scratchpad toggle script for Niri Wayland supporting any Suwayomi frontend (such as Tsumiru or Kaori). Allow configuration of `APP_ID` and `LAUNCH_CMD` either directly in the script or via external configuration files (`config.env`), fixing the Flatpak naming mismatch error encountered with Tsumiru.

## Scope & Constraints
- **Platform**: Linux CachyOS, Niri Wayland compositor, `jq`, `flatpak`.
- **Target Applications**: Tsumiru (`app_id: tsumiru`, flatpak `app.tsumiru.Tsumiru`), Kaori (`app_id: io.github.riyaniii.Kaori`), and arbitrary custom frontends.
- **Root Cause of Original Error**: `toggle-kaori.sh` hardcoded `flatpak run "$APP_ID" &`. For Tsumiru, the Wayland window `app_id` in Niri is `tsumiru`, but Flatpak requires reverse-DNS format (`app.tsumiru.Tsumiru`), causing `error: Id tsumiru no válido: Los nombres deben contener al menos 2 puntos`.
- **Configuration Flexibility**: Support variables in script header, external file `config.env` alongside script, or user config `~/.config/frontend-suwayomi/config.env`, plus automatic smart preset resolution when only `APP_ID` is defined.
- **Engram Mirror**: Pending (Engram MCP unavailable in session).

---

## Tasks

- [x] **TASK-1**: Implement configurable `toggle-suwayomi.sh` and `config.env` in `frontend_suwayomi/`
  - Path: `frontend_suwayomi/toggle-suwayomi.sh`, `frontend_suwayomi/config.env`
  - Route: Direct inline
  - Checks: Support loading from external config file or script variables; smart fallback resolving `tsumiru` -> `app.tsumiru.Tsumiru` and `kaori` -> `io.github.riyaniii.Kaori`; launch without flatpak naming errors.
  - Evidence: Commit `ea07342`

- [x] **TASK-2**: Integrate with user system paths and verify Niri keybinding compatibility
  - Path: `~/.local/bin/toggle-suwayomi.sh`, `~/.local/bin/toggle-tsumiru.sh`
  - Route: Direct inline
  - Checks: Make executable, verify symlinks/binaries exist in user PATH, ensure `Mod+M` works with current Niri keybind.
  - Evidence: Symlinks created and tested with `niri msg -j windows` showing window toggle.

- [ ] **TASK-3**: Documentation & Repository Guide
  - Path: `frontend_suwayomi/README.md`, `README.md`
  - Route: Direct inline
  - Checks: Document setup, configuration parameters, Niri window rules for Tsumiru and Kaori, explanation of the Flatpak ID vs Wayland app_id distinction.

- [ ] **TASK-4**: End-to-end verification
  - Route: Direct inline
  - Checks: Test launch when closed, test toggle hide to workspace 99, test restore & focus, verify exit codes.
