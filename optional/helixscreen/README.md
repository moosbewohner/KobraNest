# HelixScreen + KlipperScreen on the Kobra S1

The package includes the unmodified HelixScreen pi32 v1.0.5 release, pinned to
SHA-256 c6655f4fca7b004d26595a808db3da89e02207dc0c2aa6a87d384aa819235b66.
Upstream: https://github.com/prestonbrown/helixscreen/tree/v1.0.5
The matching source archive and binary release are in payload/. LICENSE is
included here. Sources and build instructions are upstream in that archive.

The native stage action installs both display interfaces before activation.
The assistant also checks/installs the display module when resuming add-ons.
HelixScreen is the default on a fresh installation. KlipperScreen and its
Python environment remain installed. The Web UI enables both selection buttons.
Switching only restarts the init-owned GUI supervisor, not MCU or Pi services.

The installer uses the release's clean settings template. No personal API keys,
Wi-Fi settings or copied printer credentials are distributed. Moonraker uses
the configured Pi IP; display and touch are rotated 180 degrees for the S1.
The chamber-light widget uses the existing Moonraker device Bauraumlicht.
Animations and the clock screensaver are disabled to avoid unnecessary CPU load.
The startup melody remains independent of HelixScreen sound settings.

Runtime scripts: /usr/local/sbin/s1-ui, s1-ui-select, s1-helix.
Persistent selection: /etc/s1-ui. Runtime selection: /run/s1/ui.current.
HelixScreen settings: /opt/helixscreen/config/settings.json.
Reinstalling a known release preserves settings; an unknown existing HelixScreen
directory is not overwritten. The original service script is backed up under
/var/backups/kobrian-display. The optional install.py can target an inactive
Debian root with --root, or use --root / --start on a running Kobrian system.

VNC mirrors KlipperScreen only; HelixScreen uses the framebuffer directly.
Wi-Fi and USB OTG are separate options. This module installs no Pi macros,
changes no printer.cfg and sends no heating or motion commands.
