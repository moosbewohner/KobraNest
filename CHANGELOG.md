# Changelog

## 0.1.8 — 2026-10-30: native HelixScreen layout compatibility

- Merge PR #2: canonical `bin/helix-screen` is recognized by WebUI and runtime validation; older fbdev deployments remain supported.
- Preserve the official file tree and stop injecting the fbdev compatibility link into newly packaged upstream archives.
- Remove the artificial test-home from the S1 launcher; keep S1 integration outside the upstream program directory.
- Preserve self-updated canonical installations during repair instead of downgrading to the bundled baseline. Move recognized legacy bookkeeping outside the upstream tree, with backups.
- Printer-only bootstrap records 0.0.0 until the actual signed runtime is installed; fresh installer records its release only after staging the native display runtime.
- Signed compatibility update 0.1.7 enables the 0.1.8 native launcher/helper update on existing clients. WebUI offers both in order; printer-only ZIP automates the sequence. No Pi reconfiguration needed.
- Offline regression tests, real signed-chain validation and byte-for-byte archive comparison; no new on-device beta.14 validation is claimed.

## 0.1.6 — 2026-10-26

- Unified public installer, signed platform updates and complete Pi/printer setup.
- USB now uses two MCU serial channels plus ECM; explicit preparation for next boot, no live gadget rebind.
- Complete setup configures restricted Pi SSH, per-device key, host-key pinning, internal Moonraker, chamber light and enabled forwards.
- Accept valid Ed25519 public-key comments; retain structural key validation.
- Guard incomplete updater APIs and missing optional USB helpers so the maintenance WebUI remains accessible.
- Missing version metadata uses a marked repair bootstrap, then the signed target version; no fabricated installed release.
- Preserve original klipper.service, MCU services, user settings, accounts and camera configuration.
- Rebuilt Windows executable and DE/EN instructions; normal and illustrated guides remain separate.
- Official HelixScreen v1.1.0-beta.11 with S1 defaults, native PWM sound support and ACE Pro panel for KlipperScreen.
- Known limitation retained: a Pi-only reboot may require restarting the printer for ECM enumeration.

## 2026-10-26: Signed KobraNest updates

- Manual update checks, signed package download/upload, version and release-note display in DE/EN.
- Idle/heater checks, file backups, health verification, rollback and interrupted-transaction recovery.
- Separate manual Pi updates; no changes to personal settings, boot partitions or MCU firmware.
- One-time bootstrap for existing installations and staging integration in installer source.


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

## 2026-10-23 — optional USB Ethernet drivers

- Add load-tested ASIX and CDC-NCM modules, gated by exact kernel build and file checksums.
- Load before network setup; fail without blocking boot and preserve built-in Realtek.
- Adapter-specific hardware validation remains pending.

## 2026-10-23 — bundled custom printer image

- Add rinkhals_s1.png to HelixScreen Custom Images during installation without selecting it automatically.
- Preserve existing custom images during recognized upgrades and retain user replacements with the same filename.
