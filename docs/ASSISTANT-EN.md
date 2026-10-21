# KobraNest setup assistant

## Required preparation: Rinkhals and Klipper tunneling

**Before installing KobraNest, set up Rinkhals and the appropriate Klipper environment using Antiriad's Kobra-S1 repositories. Experience with Klipper tunneling over LAN or USB is required.**

KobraNest provides the printer's local interface and system management. It does not replace prior setup of Klipper/Moonraker on the external host, compatible MCU firmware or the selected LAN/USB tunnel. Verify and understand the selected connection before switching systems. Rinkhals is used for access to the original system and the return/start app.

Read the upstream setup and compatibility information first:

- [Rinkhals – Community-Firmware / Community firmware](https://github.com/rinkhals-community/Rinkhals) – Rinkhals vor der KobraNest-Installation einrichten. / Set up Rinkhals before installing KobraNest.
- [Kobra-S1: klipper-kobra-s1](https://github.com/Kobra-S1/klipper-kobra-s1) — Kobra S1 Klipper environment.
- [Kobra-S1: ACEPRO](https://github.com/Kobra-S1/ACEPRO) — ACE Pro integration and related setup information; follow its requirements when using ACE Pro.

KobraNest does not automatically install these projects or Rinkhals, and does not flash MCU firmware.

Extract the complete package on Windows x64 and run **Start-KobraNest.cmd**.
Keep the `_internal` folder beside the executable. Python is included.
The assistant opens a local browser session, accessible only on this PC.
Use **DE / EN** in the header to change language. Only the language preference
is saved in localStorage; SSH credentials are not stored there.

1. Enter the printer and Pi IP addresses and SSH credentials. Verify unfamiliar
   SSH fingerprints independently before confirming them. Device checks only
   read data. An existing KobraNest installation is not overwritten.
2. Open the installation steps and check the gateway and subnet prefix.
3. Type **YES** to back up and verify the original partitions on this PC
   and build device-specific boot files on the Pi using existing Docker.
   This creates a temporary build directory on the Pi, without writing printer
   partitions. Backups remain in `%LOCALAPPDATA%/Kobrian/Assistant/devices/IP/`.
4. Type **YES** to stage Debian, HelixScreen, KlipperScreen, the local Web UI and the
   disabled Rinkhals return app. Boot partitions are unchanged at this stage.
5. Check the Pi setup using PI.md. Matching service files and chamber-light
   configuration are generated in the backup workspace's `pi-config` folder.
   Existing printer.cfg and Pi services are not automatically overwritten.
6. Confirm the Pi setup, printer idle state and **INSTALL B printer-IP** to
   activate slot B. The CLI verifies backups and firmware, writes only p7/p9,
   verifies by reading back and requests a reboot. Original slot A is preserved.
7. Select **Check startup** afterwards. Debian uses a separate SSH host key;
   independently verify and approve it. Create your own Web UI account on
   printer port 8080, and check display, touch and Klipper on the printer.

The technical confirmation words are identical in both languages. Passwords
are kept only in memory and the current form; fields are cleared after a step
unless a host-key confirmation is pending. Keep the assistant and console open
until the operation completes. Do not interrupt partition writes.

Each writing step checks the Pi print state again and rejects running or paused
prints. When the state is unavailable, the explicit manual idle confirmation
is required. Known changed SSH keys are rejected, not automatically replaced.
Do not delete backups or blindly rerun a failed flash. A completed Debian stage
can resume add-on setup; partial rootfs uploads are not automatically removed.

This release connects the existing CLI installer to the GUI. Writing paths were
tested with fake devices, not through a new live installation on the configured
reference printer. The package uses HelixScreen by default and retains KlipperScreen, selectable
in the Web UI. Wi-Fi and USB remain separate modules. USB has not yet been tested with a cable.
Diagnostic logs may retain their original language. See ASSISTENT.md for the
full technical scope and recovery notes.

## Printer SSH keys when switching systems

The same printer IP may have separately approved Stock and Debian identities.
Each approved printer key is retained in its own fingerprint-named file; old
keys are never overwritten. Trust is scoped to that IP. Unrecognized keys still
require explicit confirmation before password authentication. A changed known
Pi key remains blocked.

Current assistant: acknowledge the warning once, reuse passwords for this browser session, and confirm each write step with YES. Optional public SSH keys and Pi light transfer are offered during staging. Reloading the page clears in-memory passwords.

## Legacy technical names

The product name is KobraNest. The bundled executable `Kobrian-Assistent.exe`, internal paths such as `%LOCALAPPDATA%/Kobrian/Assistant/`, service/directory names containing `kobrian`, and the Rinkhals confirmation word `KOBRIAN` keep their existing technical names. Use `Start-KobraNest.cmd` to launch the assistant. Do not rename paths or commands from the instructions.
