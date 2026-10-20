# USB als Standard für Neuinstallationen

Der Assistent und CLI-Einstellungen verwenden jetzt USB für die MCUs (tunnel_mode=usb). Netzwerk bleibt vor „Sicherung & Build“ ausdrücklich auswählbar. Der Drucker wird entsprechend vorbereitet; der Pi muss manuell mit funktionierendem Gadget und /dev/ttyGS0 sowie /dev/ttyGS1 eingerichtet sein. Keine automatische Veränderung der Pi-Dienste.

Die nachfolgenden historischen Hinweise dokumentieren außerdem den ursprünglichen optionalen Aufbau. Aussagen über LAN als Standard gelten für den früheren Stand.

# USB OTG Serial: bestätigter Funktionstest

Am Referenzdrucker wurden beide USB-MCU-Verbindungen getestet: Klipper ready und Düsen-/Betttemperatur vom Benutzer bestätigt. Neustart, längerer Betrieb und Kabelverlust bleiben ungeprüft.

Der Installer installiert jetzt die Drucker-Erweiterung ohne Transportwechsel; LAN bleibt Standard. Die WebGUI schaltet ausschließlich den Drucker um. Der Pi wird manuell vorbereitet; keine Pi-Zugangsdaten werden auf dem Drucker hinterlegt.

Die folgenden ursprünglichen Vorbereitungshinweise dokumentieren Aufbau und Rückweg; frühere Angaben „ungetestet“ beziehen sich auf den damaligen Stand.

# Zweite Tunnelvariante: USB OTG Serial (optional, ungetestet)

Im Referenzsystem ist die Drucker-Erweiterung fuer den Web-Umschalter vorbereitet, ohne die laufenden Netzwerk-Tunnel neu zu starten. Auf dem Pi wurde nichts installiert oder umgestellt. USB ist nicht aktiviert und nicht mit Hardware getestet. Netzwerk bleibt Standard. Der normale Grundinstaller aktiviert diese Option nicht.

Grundlage sind die bereitgestellten socat.sh / setup_tunnel_klipper.sh. Die Debian-Anpassung verwendet keine Rinkhals-tools.sh und installiert kein KIAUH; vorhandene Klipper-Quellen werden nicht geaendert. Kein MCU-Reset bei einzelnen USB-Abbruechen. Beide MCU-UARTs bleiben bei 576000 Baud.

## Aufbau

Drucker = USB-Host, Pi 4 = USB-Gadget am USB-C-Datenport. Ein geeignetes Datenkabel und passende Stromversorgung sind erforderlich. Nicht zwei Host-Ports verbinden. Die USB-Verbindung uebertraegt nur MCU-Serial; HelixScreen/KlipperScreen und Bauraumlicht brauchen weiterhin das Netzwerk zu Moonraker. Ein USB-LAN-Adapter muss gegebenenfalls ueber einen Hub angeschlossen bleiben.

| Drucker | ACM-Interface | Pi | MCU |
| --- | --- | --- | --- |
| ttyS3 | 00 | ttyGS0 | Haupt-MCU |
| ttyS5 | 02 | ttyGS1 | zweite MCU |
| unbelegt | 04 | ttyGS2 | Reserve |

Die Erkennung nutzt VID 1d6b / PID 0104 und bInterfaceNumber, nicht die wechselnde ttyACM-Nummer. Mehrere passende Gadgets werden abgelehnt. CDC ACM im Druckerkernel und der UDC des Pi muessen spaeter mit Hardware geprueft werden. Andere Pi-Modelle sind in dieser Anpassung nicht freigegeben.

## Spaeter vorbereiten (jetzt nicht ausgefuehrt)

Den ganzen optional/usb-otg-Ordner uebertragen. Auf dem Debian-Drucker:

```sh
python3 install-printer.py --root /
```

Das ergaenzt s1-service und s1-health mit Sicherung .before-usb und kopiert s1-usb-bridge. Fehlende /etc/s1-tunnel-mode wird mit network angelegt. Keine Umschaltung, kein Neustart. Funktioniert fuer die mitgelieferte KlipperScreen- und die separate HelixScreen-Servicevariante.

Auf dem Pi 4 zuerst config.txt und printer.cfg sichern. In /boot/firmware/config.txt (aeltere Systeme: /boot/config.txt) im passenden [pi4]-Abschnitt nach Pruefung vorhandener USB-Overlays dtoverlay=dwc2,dr_mode=peripheral setzen. dwc2 und libcomposite in /etc/modules-load.d/kobrian-usb.conf eintragen. Vorhandene fremde USB-Gadgets nicht ersetzen.

```sh
sudo install -m 755 pi/kobrian-usb-gadget /usr/local/sbin/kobrian-usb-gadget
sudo install -m 644 pi/kobrian-usb-gadget.service /etc/systemd/system/
sudo systemctl daemon-reload
```

Der Dienst wird dadurch noch nicht aktiviert. Pi-Neustart fuer den Overlay-Wechsel spaeter bewusst planen.

## Spaeter auf USB wechseln: nur im Drucker-Leerlauf

1. Klipper auf dem Pi stoppen. mcu1.service und mcu2.service stoppen und deaktivieren; deren Dateien als Netzwerk-Rueckweg behalten.
2. Auf dem Pi den Gadget-Dienst aktivieren: sudo systemctl enable --now kobrian-usb-gadget.service. Nach Overlay-Aenderungen gegebenenfalls vorher neu starten.
3. In den vorhandenen MCU-Abschnitten der gesicherten printer.cfg nur serial aendern: /dev/ttyMCU1 -> /dev/ttyGS0 und /dev/ttyMCU2 -> /dev/ttyGS1. Klipper-Benutzer braucht dialout-Zugriff auf ttyGS0/1.
4. Kabel verbinden. Auf dem Drucker printf 'usb\n' > /etc/s1-tunnel-mode; sync setzen und geplant neu starten. s1-service startet je UART ausschliesslich USB oder Netzwerk, niemals beide.
5. USB-Erkennung und /var/log/mcu1-usb.log sowie mcu2-usb.log pruefen, dann Klipper starten. Gegebenenfalls FIRMWARE_RESTART im Leerlauf.

Die lokale Bootpruefung setzt kein USB-Kabel voraus; fehlende MCU-Verbindungen allein fuehren nicht zum Stock-Fallback. USB kann im Web-Umschalter dennoch erst mit eindeutig erkannten Kanaelen aktiviert werden. Kein automatischer Transportwechsel bei Kabelverlust.

## Zurueck zum Netzwerk

Im Leerlauf Klipper stoppen, auf dem Drucker printf 'network\n' > /etc/s1-tunnel-mode; sync und geplant neu starten. Auf dem Pi die urspruenglichen Serial-Pfade wiederherstellen und mcu1.service/mcu2.service mit sudo systemctl enable --now mcu1.service mcu2.service starten, dann Klipper starten. Optional den Gadget-Dienst deaktivieren. config.txt-Overlay bei Bedarf aus der eigenen Sicherung wiederherstellen; dafuer ist ein Pi-Neustart erforderlich.

## Pruefstand

Nur Python-Syntax und dateibasierte Installation auf Kopien beider Servicevarianten geprueft. Kein USB-Hardwaretest, keine Aenderung an laufenden Systemen. USB-Gadget-Reihenfolge, Treiber, Versorgung und Wiederverbindung bleiben spaeter zu bestaetigen.
