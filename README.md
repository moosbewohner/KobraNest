# KobraNest

**Dein Drucker. Dein System. / Your printer. Your system.**

Lokales Debian 13 für den **Anycubic Kobra S1**, mit HelixScreen, KlipperScreen als Alternative und einer eigenen Wartungs-Weboberfläche. Klipper und Moonraker laufen auf einem externen Raspberry Pi. Bisheriger Projektname: Kobrian; technische Pfade bleiben aus Kompatibilitätsgründen erhalten.

Local Debian 13 for the **Anycubic Kobra S1**, with HelixScreen, an optional KlipperScreen interface and a local maintenance dashboard. Klipper and Moonraker run on an external Raspberry Pi. Previously named Kobrian; existing technical paths are retained for compatibility.

![KobraNest](branding/KobraNest-800x480.png)

## Download

**[Vollständiges Installationspaket mit Windows-EXE herunterladen / Download complete installer](https://github.com/moosbewohner/KobraNest/releases/download/v0.1.0/KobraNest-S1-v0.1.zip)**

[Release-Hinweise / Release notes](https://github.com/moosbewohner/KobraNest/releases/tag/v0.1.0) · [SHA-256](https://github.com/moosbewohner/KobraNest/releases/download/v0.1.0/KobraNest-S1-v0.1.zip.sha256)

ZIP vollständig entpacken, dann **Start-KobraNest.cmd** oder **Kobrian-Assistent.exe** starten. `_internal` muss daneben bleiben. / Extract the complete ZIP, then run **Start-KobraNest.cmd** or **Kobrian-Assistent.exe**. Keep `_internal` beside it.

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

Die Erstinstallation und der laufende Betrieb wurden auf **einem Referenz-S1** getestet. Kein allgemeiner Nachweis für andere Geräte oder Firmwarestände. Der Installer akzeptiert nur das dokumentierte Partitionslayout und die bekannten Firmware-Prüfsummen. Keine automatische Freigabe für S1 Max oder andere Drucker.

Installation and operation have been tested on **one reference S1**. Other devices and firmware revisions are not validated. The installer checks the documented partition layout and firmware hashes. S1 Max and other printer models are not supported automatically.

Bekannte offene Punkte: vollständige Kaltstartbestätigung der letzten Logo-/LAN-Änderungen; Signaturkompatibilität der WLAN-Länderdatenbank. Der zusätzliche zweite LAN-Adapter war ein temporärer Hardwaretest und wird nicht automatisch dauerhaft eingerichtet.

Known pending checks: a full cold-start confirmation after the latest logo/LAN changes; compatibility of the wireless regulatory database signature. The second simultaneous Ethernet adapter was a temporary hardware test and is not configured persistently.

## Warnhinweis / Warning

Nutzung auf eigene Gefahr. Unsachgemäße oder fehlerhafte Nutzung sowie Softwarefehler können das Druckersystem beschädigen oder unbrauchbar machen und Datenverlust verursachen. Der Projektanbieter übernimmt, soweit gesetzlich zulässig, keine Haftung für daraus entstehende Schäden. Vorher persönliche Sicherungen anlegen. Niemals während eines Drucks installieren oder das System umschalten.

Use at your own risk. Improper use, incorrect operation and software defects may damage or render the printer unusable and cause data loss. To the extent permitted by law, the project provider accepts no liability for resulting damage. Create personal backups first. Never install or switch systems during a print.

## Lizenz / License

Eigener KobraNest-Code: **GPL-3.0-only**, siehe [LICENSE](LICENSE). Fremdsoftware behält ihre jeweiligen Lizenzen; siehe [THIRD_PARTY.md](THIRD_PARTY.md). Enthaltene Marken gehören ihren jeweiligen Inhabern. Keine Herstellerfreigabe oder Verbindung zu Anycubic, Debian oder Rinkhals wird behauptet.

Original KobraNest code: **GPL-3.0-only**, see [LICENSE](LICENSE). Third-party components retain their own licenses. Trademarks belong to their respective owners; no vendor endorsement is claimed.
