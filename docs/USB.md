# USB-Verbindung / USB connection

## Deutsch

KobraNest bietet weiterhin genau zwei Varianten: **LAN-Tunnel** oder **USB-Tunnel**. Die USB-Variante verwendet zwei serielle MCU-Kanäle und zusätzlich USB-Ethernet (ECM) über dasselbe Kabel:

| Kanal | Aufgabe |
|---|---|
| `/dev/ttyGS0` ↔ Drucker ACM-Kanal 0 | Haupt-MCU |
| `/dev/ttyGS1` ↔ Drucker ACM-Kanal 1 | Zweite MCU |
| ECM: Pi `10.55.0.1/30` ↔ Drucker `10.55.0.2/30` | SSH an Pi-Port 2223 für Moonraker und Rückleitungen |

Die MCU-Firmware und das funktionierende Rinkhals-USB-Tunneling müssen vorher vorhanden sein. Der Assistent verändert weder `klipper.service` noch die MCU-Abschnitte. Ein älteres Gadget wird vorher einmalig mit `bash setup.sh --prepare-ecm` aus dem Komplettpaket vorbereitet; dabei werden `ports.sh` und `ports.service` gesichert. Danach Pi neu starten, warten bis er erreichbar ist, danach Drucker neu starten. Die laufende USB-Verbindung wird nicht neu gebunden. Er benötigt einen normalen Pi-SSH-Benutzer mit passwortlosem sudo, OpenSSH und ein Gadget mit zwei seriellen MCU-Kanälen plus ECM. `ports.service` oder `kobrian-usb-gadget.service` muss den vorhandenen Gadget-Start verwalten.

Bei USB-Auswahl erzeugt die Vorbereitung einen **eigenen Schlüssel auf dem Drucker** und installiert auf dem Pi `kobranest-serial-link.service`. Der Schlüssel erlaubt nur Portweiterleitungen; Shellbefehle und Passwortanmeldung an diesem Zusatzdienst sind gesperrt. Der Pi-Hostschlüssel wird aus der bereits geprüften SSH-Verbindung übernommen. Private Schlüssel und WLAN-Daten werden nicht veröffentlicht oder vom laufenden Drucker in das Installationspaket kopiert.

### Zugänge über den Pi

`PI-IP` durch die eigene Pi-Adresse ersetzen:

| Funktion | Adresse / Port |
|---|---|
| KobraNest-WebUI | `http://PI-IP:18080` |
| Helix-Fernbedienung | `http://PI-IP:7130` |
| SSH zum Drucker | `ssh -p 2222 root@PI-IP` |
| Moonraker für das Druckerdisplay | Drucker-intern `127.0.0.1:7125` |
| Bauraumlicht-Rückleitung | Pi-intern `127.0.0.1:17126` |

Im Assistenten **„Bauraumlicht-Konfiguration auf den Pi übertragen?“** auswählen, wenn das Licht ohne Druckernetzwerk funktionieren soll. Die Übertragung bleibt ausdrücklich optional. Für manuelle Konfiguration zeigen `on_url`, `off_url` und `status_url` in der Pi-Datei `bauraumlicht.cfg` auf `http://127.0.0.1:17126/light/on`, `/light/off` beziehungsweise `/light/status`; der Include in Moonraker bleibt bestehen.

Die WebUI verwendet weiterhin dein eigenes Webkonto. SSH verwendet weiterhin die Anmeldung des Druckers. Bei der ersten Verbindung über `PI-IP:2222` den Fingerabdruck mit dem bekannten Druckerschlüssel vergleichen: Das Ziel ist der Drucker, nicht der Pi.

### Einstellungen in der WebUI

**USB-Weiterleitungen** erscheint nur bei ausgewähltem USB-Tunnel. Moonraker, Licht, KobraNest-WebUI, Helix-Fernbedienung und SSH sind einzeln schaltbar. Für die drei externen Zugänge lassen sich die Pi-Ports ändern. Interne Ports bleiben fest. Nach Übernehmen innerhalb von **90 Sekunden „Verbindung bestätigen“** wählen; andernfalls stellt der Drucker die vorherige Einstellung wieder her. Das gilt auch nach einem Neustart mit unbestätigter Änderung. Nicht während eines Drucks ändern.

Neue Ports werden vor dem Entfernen alter Weiterleitungen angelegt. Bei Portkonflikten bleibt die bestehende Verbindung erhalten. Wer den gerade benutzten Webzugang deaktiviert, benötigt zur Bestätigung einen anderen Zugang, etwa die direkte Drucker-IP; sonst erfolgt die Rückkehr automatisch.

HelixScreen und KlipperScreen verwenden bei aktivierter USB-Moonraker-Weiterleitung `127.0.0.1:7125`. Bei LAN oder ausgeschalteter USB-Moonraker-Weiterleitung verwenden sie die konfigurierte Pi-Netzwerkadresse.

### Betrieb ohne Druckernetzwerk

Nach Einrichtung funktionieren Display, Bauraumlicht, beide Webzugänge und Drucker-SSH über USB. LAN/WLAN am Drucker können zur Administration erhalten bleiben. Der Pi benötigt für Zugriffe vom PC weiterhin eine Netzwerkverbindung. Internetfunktionen des Druckers, etwa Update-Downloads, benötigen weiterhin einen separaten Netzwerkzugang; der SSH-Tunnel ist kein allgemeiner Internetzugang.

**Ohne Druckernetzwerk ist die am Drucker angeschlossene Kamera nicht verfügbar. Eine direkt am Pi angeschlossene Kamera funktioniert weiterhin.** Der Kamerastream wird nicht durch den ECM-SSH-Tunnel geleitet.

Bei beiden USB-Aufbauten kann ein alleiniger Pi-Neustart eine erneute USB-Erkennung verhindern. Dann anschließend auch den Drucker neu starten. Das wurde bereits beim ursprünglichen Rinkhals-USB-Aufbau beobachtet. Normale Druckerneustarts und der automatische Wiederaufbau des SSH-Zusatzdienstes wurden geprüft.

## English

There are still two choices: **wired LAN tunnel** or **USB tunnel**. USB uses two serial channels (`ttyGS0` and `ttyGS1`) for the MCUs and an additional USB Ethernet ECM link for SSH carrying Moonraker and reverse forwards. The internal link uses Pi 10.55.0.1/30, printer 10.55.0.2/30, SSH port 2223. Working Rinkhals USB tunneling and matching MCU firmware are prerequisites. Klipper and MCU configuration are preserved. An older gadget requires explicit one-time preparation: run `bash setup.sh --prepare-ecm` from the complete bundle on the Pi. It backs up ports.sh and ports.service and stages ECM for next boot. Restart Pi first, wait for SSH, then restart printer. No live USB rebind is performed.

USB preparation requires a non-root Pi account with passwordless sudo, OpenSSH, two serial MCU channels plus ECM, and the existing `ports.service` or `kobrian-usb-gadget.service`. It creates a device-local key and installs `kobranest-serial-link.service` on the Pi. The key only permits forwarding, with shell commands and password login to this additional service disabled. The host key comes from the already verified Pi SSH connection.

Default addresses: KobraNest at `http://PI-IP:18080`, Helix remote at `http://PI-IP:7130`, printer SSH with `ssh -p 2222 root@PI-IP`. Moonraker is forwarded to printer-local `127.0.0.1:7125`; the light endpoint is Pi-local `127.0.0.1:17126`.

Select the optional **transfer chamber light configuration** checkbox in the assistant for light operation without a printer network. Otherwise configure the Pi's existing `bauraumlicht.cfg` URLs manually as `http://127.0.0.1:17126/light/on`, `/light/off`, `/light/status`. Existing Web UI and printer SSH credentials remain in use.

**USB forwarding** appears in the dashboard only in USB mode. Toggle each connection separately and change the external Web UI, Helix and SSH ports. Internal ports stay fixed. Confirm changes within **90 seconds**, or previous settings return automatically, including after an unconfirmed reboot. New forwards are added before old ones are removed. Disabling the web access currently in use requires another connection to confirm. Changes are blocked during printing or a paused print.

HelixScreen and KlipperScreen use local Moonraker when USB forwarding is enabled; wired LAN or disabled Moonraker forwarding uses the configured Pi network address. After setup, printer LAN/Wi-Fi is optional for the listed connections. The Pi still needs networking for PC access. The SSH tunnel does not provide general Internet access for printer updates.

**Without a printer network, the camera attached to the printer is unavailable. A camera connected directly to the Pi continues to work.** The camera stream is not forwarded over ECM SSH.

As with the original Rinkhals USB setup, rebooting only the Pi can require a subsequent printer restart to restore USB enumeration. Printer autostart and automatic SSH reconnection have been tested on the reference S1.
