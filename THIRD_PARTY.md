# Third-party components

GPL-3.0-only applies to original KobraNest code, not to third-party components or third-party branding.

- Debian packages: individual licenses and copyright notices under `/usr/share/doc` inside the runtime. See `docs/BUILD.md` for upstream and source information.
- HelixScreen 1.1.0-beta.10: binary and matching upstream source archives accompany the installation package. Preserve their notices and licenses.
- KlipperScreen: pinned upstream revision and license information are documented in `docs/BUILD.md`.
- Framebuffer VNC viewer: GPL-2.0-or-later; source and license in `source/viewer/`.
- Realtek RTL8153B firmware: distributed unchanged under `optional/wlan-dualbetrieb/firmware/LICENCE.rtlwifi_firmware.txt`; origin and SHA-256 in the adjacent README.
- Python, Paramiko and Windows runtime dependencies: notices in the full installation package under `docs/windows-licenses/` and the included component distributions.
- Manufacturer boot/system partitions, Wi-Fi modules and Rockchip utilities are obtained from the user's own device; manufacturer partition backups must never be uploaded to this repository.

The current binary package is not a complete corresponding-source collection for every Debian package and statically linked dependency. Before public binary distribution, complete the applicable source redistribution/provision requirements. This source repository is prepared separately from the binary release candidate for that reason.

- uStreamer: GPL-3.0, https://github.com/pikvm/ustreamer; installed from Debian repositories during runtime preparation. Debian provides copyright notices and the source package.

### Optional USB Ethernet modules

The ASIX (GPL) and CDC-NCM (Dual BSD/GPL) modules were supplied by the user and load-tested on the reference S1. Exact build sources, vendor patches and build recipe were not supplied; the upstream Linux reference does not establish reproducibility of these particular binaries. Their hashes and kernel restriction are embedded in optional/wlan-dualbetrieb/install-printer.py. See optional/wlan-dualbetrieb/USB-LAN.md. This is an additional corresponding-source provisioning limitation.
