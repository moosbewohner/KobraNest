# ACE Pro in KlipperScreen

KobraNest installs the supplied acepro.py panel into /opt/KlipperScreen/panels/acepro.py and adds ACE Pro to both the main menu and the print menu in config/main_menu.conf. Existing menu entries are preserved; replaced files are backed up in /var/backups/kobranest-acepro. Repeated installation does not duplicate menu entries.

The display installer contains a compressed copy of the adjacent acepro.py so the existing assistant staging interface installs the extension without additional downloads. Keep both copies synchronized when updating the panel.

The panel requires the corresponding Kobra-S1 ACEPRO Klipper integration and configured ACE hardware on the Pi; installing this panel alone does not install that integration. Upstream: https://github.com/Kobra-S1/ACEPRO. The provided panel includes optional Kobra X tool-changer detection; this does not configure a Kobra X tool changer on the S1. Third-party licensing remains unchanged.
