## Standard: USB OTG Serial für die MCUs

Der Installationsassistent wählt standardmäßig USB. Auf dem Pi 4 muss das passende USB-Gadget bereits eingerichtet sein; siehe optional/usb-otg/README.md. Haupt-MCU: /dev/ttyGS0, zweite MCU: /dev/ttyGS1. Klipper-Benutzer braucht dialout-Zugriff. Die Netzwerkdienste mcu1/mcu2 und etwaige automatische Starts in Klippers ExecStartPre müssen für USB deaktiviert sein. Vor Änderungen sichern und nur im Leerlauf arbeiten. Einen vorhandenen funktionierenden Gadget-Aufbau erhalten.

Im Assistenten kann vor der Sicherung alternativ „Netzwerk über WLAN oder LAN“ ausgewählt werden. Nur für diese Variante die nachfolgend beschriebenen socat-Netzwerkdienste einrichten. Das Erzeugen von pi-config installiert oder aktiviert sie nicht automatisch.

WLAN ist unabhängig von der gewählten MCU-Variante für HelixScreen, WebGUI und SSH erforderlich, sofern kein LAN verwendet wird.

## Netzwerkadresse bei WLAN

Für die übliche WLAN-Installation die bestehende Anycubic-WLAN-IP für dieselbe WLAN-MAC im Router reservieren. Dieselbe Adresse wird nach der Übernahme in Kobrian für die Pi-Tunnel und Moonraker-Lichtkonfiguration verwendet. LAN ist optional; beide Netzwerkvarianten verwenden dieselben Ports 7003/7005. Der Pi muss diese IP erreichen können; WLAN-Client-Isolation darf den Zugriff nicht verhindern.

# Raspberry Pi vorbereiten

Das Paket setzt einen bereits funktionierenden Klipper/Moonraker-Aufbau fuer genau diesen Drucker voraus. Es installiert keine universelle printer.cfg und flasht keine MCUs. Die Haupt-MCU muss zum Klipper auf dem Pi passen.

## Bootstrap-Build

`prepare` verwendet den Pi nur als Build-Rechner. Dessen SSH-Benutzer muss `sudo -n docker info` ausfuehren koennen. Eine bestehende Docker-Installation verwenden oder gemaess der Dokumentation der eigenen Pi-Distribution installieren. Der Installer installiert Docker nicht heimlich und veraendert keine vorhandenen Container.

## MCU-Tunnel

`python render_pi.py --settings settings.json --output pi-config` erzeugt mcu1.service, mcu2.service und bauraumlicht.cfg fuer die eigene IP-Adresse. Diese Dateien auf den Pi uebertragen.

Vorhandene gleichnamige Dienste zuerst sichern und die bisherigen Serial-Pfade pruefen. In den Dateien steht Haupt-MCU = /dev/ttyMCU1 und zweite MCU = /dev/ttyMCU2. Die PTYs werden mit dialout-Gruppe angelegt; der Klipper-Benutzer muss diese Gruppe verwenden duerfen.

```sh
sudo apt-get install socat
sudo install -m 644 mcu1.service /etc/systemd/system/mcu1.service
sudo install -m 644 mcu2.service /etc/systemd/system/mcu2.service
sudo systemctl daemon-reload
sudo systemctl enable --now mcu1.service mcu2.service
```

Die vorhandenen, passenden MCU-Sektionen der printer.cfg muessen auf diese Serial-Pfade zeigen. Keine anderen MCU-Optionen blind ersetzen:

```ini
[mcu]
serial: /dev/ttyMCU1

# Im bereits vorhandenen Abschnitt der zweiten MCU:
# serial: /dev/ttyMCU2
```

Ein bereits vorhandener Netzwerk-/USB-Tunneldienst darf nicht parallel dieselben PTYs oder MCU-Verbindungen beanspruchen. Dienste vor einem Wechsel sichern und gezielt abloesen. Die Druckerports 7003 und 7005 akzeptieren nur die konfigurierte Pi-IP.

## Moonraker und Licht

Im Assistenten kann bei Schritt 2 optional „Bauraumlicht-Konfiguration auf den Pi übertragen?“ aktiviert werden (standardmäßig aus). Die gewählte Drucker-IP wird übernommen, vorhandene geänderte Dateien werden mit `.kobrian-backup-…` gesichert und Moonraker wird nur im Leerlauf neu gestartet. Erwarteter Pi-Konfigurationsordner: `~/printer_data/config`. Abweichende oder mehrdeutige Lichtdefinitionen werden nicht automatisch ersetzt. Die Tunnelkonfiguration wird nicht geändert. Ohne Zustimmung erfolgt keine Übertragung.

Für die manuelle Einrichtung: bauraumlicht.cfg in den eigenen Moonraker-Konfigurationsordner legen und in moonraker.conf einmal einbinden:

```ini
[include bauraumlicht.cfg]
```

Der Abschnitt [authorization] muss den Drucker in trusted_clients erlauben, falls noch kein passender Bereich eingetragen ist. Vorhandene Einstellungen erhalten; nur die eigene Drucker-IP hinzufuegen. Der Installer erzeugt keine allgemeinen Freigaben und verteilt keine API-Schluessel.

Moonraker auf Port 7125 starten bzw. nach Konfigurationsaenderung im Leerlauf neu starten:

```sh
sudo systemctl restart moonraker
```

Fuer den Druckbetrieb muss der Moonraker-Port vom Druckernetz erreichbar sein. Die lokale Boot-Bestaetigung prueft ein beschreibbares Debian-Rootfs, SSH und entweder die lokale Display-Oberflaeche oder den lokalen Webdienst. Ein fehlender Pi, Tunnel oder LAN-Adapter allein loest keinen Stock-Fallback aus. Ein fehlendes Lichtgeraet vor dem ersten Debian-Start ist erwartbar, weil dessen HTTP-Endpunkt erst dann startet.

Nach dem S1-Neustart gegebenenfalls in KlipperScreen/Mainsail/Fluidd FIRMWARE_RESTART ausfuehren. Es ist kein automatischer Neustart von Klipper waehrend laufender Druckauftraege vorgesehen.

Bei Installation über WLAN erhält ein zusätzlicher USB-LAN-Adapter (eth1) eine eigene Adresse per DHCP. Die WLAN-Adresse bleibt erhalten; LAN und WLAN dürfen nicht dieselbe IP bekommen. Die LAN-Adresse kann im Router separat reserviert werden.
