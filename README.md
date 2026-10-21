# KobraNest

**Dein Drucker. Dein System. / Your printer. Your system.**

Lokales Debian 13 für den **Anycubic Kobra S1**, mit HelixScreen, KlipperScreen als Alternative und einer eigenen Wartungs-Weboberfläche. Klipper und Moonraker laufen auf einem externen Raspberry Pi. Technische Altbezeichnungen in internen Pfaden und Dateinamen bleiben aus Kompatibilitätsgründen erhalten.

Local Debian 13 for the **Anycubic Kobra S1**, with HelixScreen, an optional KlipperScreen interface and a local maintenance dashboard. Klipper and Moonraker run on an external Raspberry Pi. Legacy names in internal paths and filenames are retained for compatibility.

![KobraNest](branding/KobraNest-800x480.png)

## Download

**[Vollständiges Installationspaket mit Windows-EXE herunterladen / Download complete installer](https://github.com/moosbewohner/KobraNest/releases/download/v0.1.0/KobraNest-S1-v0.1.zip)**

[Release-Hinweise / Release notes](https://github.com/moosbewohner/KobraNest/releases/tag/v0.1.0) · [SHA-256](https://github.com/moosbewohner/KobraNest/releases/download/v0.1.0/KobraNest-S1-v0.1.zip.sha256)

ZIP vollständig entpacken, dann **Start-KobraNest.cmd** starten. `_internal` muss daneben bleiben. / Extract the complete ZIP, then run **Start-KobraNest.cmd**. Keep `_internal` beside it.

## Erforderliche Vorarbeiten: Rinkhals und Klipper-Tunneling

**Vor der KobraNest-Installation müssen Rinkhals und die passende Klipper-Umgebung aus den von Antiriad gepflegten Kobra-S1-Repositories eingerichtet sein. Erfahrung mit Klipper-Tunneling über LAN oder USB wird vorausgesetzt.**

KobraNest ergänzt die lokale Oberfläche und Systemverwaltung auf dem Drucker. Es ersetzt nicht die vorherige Einrichtung von Klipper/Moonraker auf dem externen Host, der passenden MCU-Firmware und des gewählten LAN-/USB-Tunnels. Die ausgewählte Verbindung sollte bereits funktionieren und verstanden sein, bevor das System umgestellt wird. Rinkhals wird unter anderem für den SSH-Zugang im Originalsystem und die Rückkehr-/Start-App benötigt.

Anleitungen und projektspezifische Informationen:

- [Rinkhals – Community-Firmware / Community firmware](https://github.com/rinkhals-community/Rinkhals) – Rinkhals vor der KobraNest-Installation einrichten. / Set up Rinkhals before installing KobraNest.
- [Antiriad / Kobra-S1: klipper-kobra-s1](https://github.com/Kobra-S1/klipper-kobra-s1) – angepasste Klipper-Umgebung für den Kobra S1.
- [Antiriad / Kobra-S1: ACEPRO](https://github.com/Kobra-S1/ACEPRO) – ACE-Pro-Anbindung und weitere Einrichtungsinformationen. Für die Verwendung des ACE Pro die dortigen Voraussetzungen beachten.

Die verlinkten Anleitungen und ihre Kompatibilitätshinweise vorab lesen. KobraNest installiert diese Projekte oder Rinkhals nicht automatisch und flasht keine MCU-Firmware.

## Required preparation: Rinkhals and Klipper tunneling

**Before installing KobraNest, set up Rinkhals and the appropriate Klipper environment using Antiriad's Kobra-S1 repositories. Experience with Klipper tunneling over LAN or USB is required.**

KobraNest provides the printer's local interface and system management. It does not replace prior setup of Klipper/Moonraker on the external host, compatible MCU firmware or the selected LAN/USB tunnel. Verify and understand the selected connection before switching systems. Rinkhals is used for access to the original system and the return/start app.

Read the upstream setup and compatibility information first:

- [Rinkhals – Community-Firmware / Community firmware](https://github.com/rinkhals-community/Rinkhals) – Rinkhals vor der KobraNest-Installation einrichten. / Set up Rinkhals before installing KobraNest.
- [Antiriad / Kobra-S1: klipper-kobra-s1](https://github.com/Kobra-S1/klipper-kobra-s1) — Kobra S1 Klipper environment.
- [Antiriad / Kobra-S1: ACEPRO](https://github.com/Kobra-S1/ACEPRO) — ACE Pro integration and related setup information; follow its requirements when using ACE Pro.

KobraNest does not automatically install these projects or Rinkhals, and does not flash MCU firmware.

## Installation

Das vollständige Installationspaket **KobraNest-S1-v0.1.zip** verwenden und vollständig entpacken. GitHub „Source code“ ZIP ist kein vollständiges Installationspaket. Die großen Laufzeitarchive und die Windows-Laufzeit gehören zu den separaten Release-Dateien.

Use the complete **KobraNest-S1-v0.1.zip** installation package and extract it first. GitHub's “Source code” ZIP is not the complete installer. Runtime archives and the Windows runtime are distributed separately as release assets.

- [Deutsche Installationsanleitung](docs/ANLEITUNG-DE.md)
- [Windows / Linux assistant — English](docs/ASSISTANT-EN.md)
- [Assistent — Deutsch](docs/ASSISTENT.md)
- [Pi-Konfiguration / Pi configuration](docs/PI.md)
- [Kompatibilität / Compatibility](docs/KOMPATIBILITAET.md)
- [Wiederherstellung / Recovery](docs/RECOVERY.md)
- [Build und Fremdsoftware / Build and third-party components](docs/BUILD.md)

## Funktionen / Features

- HelixScreen als Standard; KlipperScreen bleibt als Alternative erhalten.
- MCU-Verbindung per USB OTG Serial (Standard) oder Netzwerk; Pi-Konfiguration separat.
- WLAN als üblicher Installations- und Verwaltungszugang; zusätzliches LAN per DHCP bei WLAN-Installation.
- Weboberfläche und Assistent auf Deutsch und Englisch.
- Bootlogo, Ladebalken, Startmelodie und Bauraumlicht an GPIO 117.
- Optionaler öffentlicher SSH-Schlüssel, eigenes root-Passwort und bestätigte Übertragung der Lichtkonfiguration zum Pi.
- Slot A bleibt erhalten; Anycubic-Rückkehr und Rinkhals-Starter vorhanden.
- Realtek RTL8153B: Firmware und geprüfte Wiederherstellung der aus dem Adapter gelesenen MAC, ohne fest vorgegebene Adresse.

## Teststand / Test status

Die Erstinstallation und der laufende Betrieb wurden auf **einem Referenz-S1** getestet. Kein allgemeiner Nachweis für andere Geräte oder Firmwarestände. Der Einstieg prüft die RV1106/ARMv7-Plattform, Linux 5.10, Slot A, das dokumentierte Partitionslayout, Image-Formate und benötigte Geräte; eine bytegenaue Firmware-Whitelist ist nicht erforderlich. Keine automatische Freigabe für S1 Max oder andere Drucker.

Installation and operation have been tested on **one reference S1**. Other devices and firmware revisions are not validated. The initial check validates the RV1106/ARMv7 platform, Linux 5.10, slot A, documented partition layout, image formats and required devices, without a byte-exact firmware whitelist. Backups, transfer integrity and flash readback remain checksum-verified. S1 Max and other printer models are not supported automatically.

Bekannte offene Punkte: vollständige Kaltstartbestätigung der letzten Logo-/LAN-Änderungen; Signaturkompatibilität der WLAN-Länderdatenbank. Der zusätzliche zweite LAN-Adapter war ein temporärer Hardwaretest und wird nicht automatisch dauerhaft eingerichtet.

Known pending checks: a full cold-start confirmation after the latest logo/LAN changes; compatibility of the wireless regulatory database signature. The second simultaneous Ethernet adapter was a temporary hardware test and is not configured persistently.

## Warnhinweis / Warning

Nutzung auf eigene Gefahr. Unsachgemäße oder fehlerhafte Nutzung sowie Softwarefehler können das Druckersystem beschädigen oder unbrauchbar machen und Datenverlust verursachen. Der Projektanbieter übernimmt, soweit gesetzlich zulässig, keine Haftung für daraus entstehende Schäden. Vorher persönliche Sicherungen anlegen. Niemals während eines Drucks installieren oder das System umschalten.

Use at your own risk. Improper use, incorrect operation and software defects may damage or render the printer unusable and cause data loss. To the extent permitted by law, the project provider accepts no liability for resulting damage. Create personal backups first. Never install or switch systems during a print.

## Lizenz / License

Eigener KobraNest-Code: **GPL-3.0-only**, siehe [LICENSE](LICENSE). Fremdsoftware behält ihre jeweiligen Lizenzen; siehe [THIRD_PARTY.md](THIRD_PARTY.md). Enthaltene Marken gehören ihren jeweiligen Inhabern. Keine Herstellerfreigabe oder Verbindung zu Anycubic, Debian oder Rinkhals wird behauptet.

Original KobraNest code: **GPL-3.0-only**, see [LICENSE](LICENSE). Third-party components retain their own licenses. Trademarks belong to their respective owners; no vendor endorsement is claimed.
