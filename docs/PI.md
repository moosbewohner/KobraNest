# Raspberry Pi vorbereiten

Ein bereits funktionierendes Rinkhals-Klipper/Moonraker-System und passendes MCU-Tunneling werden vorausgesetzt. KobraNest flasht keine MCU-Firmware und ersetzt keine `printer.cfg`.

## Zwei Varianten

- **USB (Standard):** zwei serielle MCU-Kanäle (`ttyGS0`, `ttyGS1`) und zusätzlich USB-Ethernet (ECM) für Moonraker, Licht und Fernzugänge. [USB-Anleitung / English](USB.md).
- **LAN:** MCU-Verbindung ausschließlich über kabelgebundenes LAN zur LAN-IP des Druckers, Ports 7003/7005 (7007 für eine entsprechend vorbereitete dritte MCU). Kein WLAN-Fallback für MCU-Daten. Das Druckerdisplay benötigt bei dieser Variante Netzwerk zum Pi.

`klipper.service` und MCU-Konfiguration bleiben erhalten. Ein älteres Gadget mit drei seriellen Kanälen muss einmalig auf zwei serielle Kanäle plus ECM vorbereitet werden. Der Assistent installiert bei USB nur den zusätzlichen `kobranest-serial-link.service`; er überschreibt die MCU-Dienste nicht. Bei fehlendem ECM vor der Installation im Komplettpaket auf dem Pi `bash setup.sh --prepare-ecm` ausführen. Dabei werden `ports.sh` und `ports.service` gesichert und für den nächsten Start angepasst. Pi neu starten, Erreichbarkeit abwarten, danach Drucker neu starten. Keine laufende USB-Verbindung neu binden. Der Pi-SSH-Benutzer benötigt passwortloses sudo und darf nicht root sein. Bei ausschließlich LAN wird der serielle Zusatzdienst nicht eingerichtet.

Für den vorgelagerten USB-/LAN-/Alle-MCU-Installer: [Kobra-S1-Lan-Tunnel](https://github.com/moosbewohner/Kobra-S1-Lan-Tunnel). Das USB-Projekt liegt unter [Kobra-S1/vanilla-klipper-swu](https://github.com/Kobra-S1/vanilla-klipper-swu). Die passende SWU muss vorher unter Rinkhals auf dem Drucker installiert sein.

## Bootstrap-Build

Der Pi wird beim Vorbereitungsschritt außerdem als Build-Rechner verwendet. Sein SSH-Benutzer muss `sudo -n docker info` ausführen können. Der Assistent richtet Docker nicht automatisch ein und verändert keine vorhandenen Container.

## Moonraker und Bauraumlicht

Die Übertragung der Lichtkonfiguration bleibt eine ausdrückliche Auswahl im Assistenten. Bei USB werden die URLs auf Pi-intern `127.0.0.1:17126` gesetzt, bei LAN auf die gewählte Drucker-IP:7126. Vorhandene Dateien werden gesichert; Moonraker wird nur im Leerlauf neu gestartet. Ohne Auswahl erfolgt keine automatische Änderung. Erwarteter Pi-Konfigurationsordner ist `~/printer_data/config`.

Die Datei wird einmal in `moonraker.conf` eingebunden:

```ini
[include bauraumlicht.cfg]
```

Über USB kommen die Moonraker-Verbindungen vom Loopback-Interface. Bei LAN muss `trusted_clients` den Drucker passend zulassen. Vorhandene Zugriffsregeln erhalten. Druckaufträge oder MCU-Verbindungen werden durch den zusätzlichen SSH-Dienst nicht neu konfiguriert.

## Neustart und Kamera

Wird nur der Pi neu gestartet, kann anschließend ein Druckerneustart nötig sein, damit USB wieder erkannt wird. Diese Einschränkung betrifft bereits den bisherigen Rinkhals-USB-Aufbau.

Die Kamera kann direkt am Pi bleiben; ihre Konfiguration wird nicht verändert. Ohne eigenes Druckernetzwerk steht die Druckerkamera nicht zur Verfügung. [Alle USB-Weiterleitungen](USB.md).

Die alten generierten `pi-config/mcu1.service` und `mcu2.service` bleiben als manuelle Vorlagen für bestehende LAN-Aufbauten enthalten; sie werden nicht automatisch installiert. Für neue MCU-Tunnel den oben verlinkten gemeinsamen Installer verwenden.
