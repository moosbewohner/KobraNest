# HelixScreen + KlipperScreen on the Kobra S1

The package includes the tested Kobra-S1/helixscreen kobrian branch build,
version 1.1.0-beta.10, commit 67ecd2597f63d29b727a74d679ffcb3dbc848fd3.
This is a pinned beta branch build. Later ACE changes are not included.
Binary SHA-256: 6cb694d4b5935e027de5fa08598ea42445087b9dc13e4ad799064243e6556f32.
Upstream: https://github.com/Kobra-S1/helixscreen/tree/kobrian
Binary and corresponding sources are in payload/. Reproduction instructions
and Dockerfile are in source/helixscreen-build/. No upstream C++ changes;
compatibility symlink and provenance added for the S1 supervisor.

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
Debian root with --root, or use --root / --start on a running KobraNest system.

VNC mirrors KlipperScreen only; HelixScreen uses the framebuffer directly.
Wi-Fi and USB OTG are separate options. This module installs no Pi macros,
changes no printer.cfg and sends no heating or motion commands.

## Bundled custom image

rinkhals_s1.png is installed into /opt/helixscreen/config/custom_images/ and can be selected in HelixScreen under Custom Images. It is not selected automatically. Existing custom images, selection settings and any existing file with the same name are preserved. Artwork supplied by the project owner.
