# Changelog

## Guided recovery

- DE/EN read-only diagnosis, return to stock, archive for reinstall and own-backup slot-B restore.
- Fresh diagnosis/SSH identity, explicit YES/idle gates, protected A/env and before-write B backups.
- Recovery write path simulation-tested; full hardware restoration test pending.


## Compatibility preflight

- Replace the initial byte-exact firmware whitelist with platform, layout, image format and device checks.
- Retain backup, transfer, device-consistency and flash-readback verification.


## Camera controls

- Persistent camera on/off, resolution, frame rate and idle slowdown in the DE/EN web dashboard.
- Integrated UVC selection and hardware MJPEG passthrough; enabled when connected by default, with persistent manual off.

## 0.1 — initial preview

- KobraNest branding, retaining compatible internal paths.
- Tested first installation on one Anycubic Kobra S1 reference device.
- DE/EN assistant with warning acknowledgement, YES confirmations and session-only SSH credential reuse.
- Optional public SSH key and optional Pi chamber-light configuration transfer.
- HelixScreen, KlipperScreen alternative, local Web UI and return tools.
- USB/network MCU transports; WLAN installation and secondary LAN DHCP.
- Resumable uploads, validated base checkpoint and bounded package preparation.
- RTL8153B firmware and factory-MAC reinitialization.

See README for current validation limits.

## 2026-10-22 — tested HelixScreen branch update

- Default display runtime: HelixScreen 1.1.0-beta.10 from Kobra-S1/helixscreen, kobrian branch, pinned at 67ecd2597f63d29b727a74d679ffcb3dbc848fd3.
- Display, touch and a print test confirmed on the reference S1. Further unfinished ACE changes are excluded.
- Fresh installations and recognized upgrades use the new runtime; existing settings are preserved and the previous runtime is backed up.
- Matching source archive, ARM32 Debian trixie toolchain, asset dependencies and static OpenSSL/Zstandard link instructions included.
