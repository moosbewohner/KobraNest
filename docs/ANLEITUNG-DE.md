# KobraNest

> USB/ECM 0.1.8: Vor dem PC-Assistenten bei altem USB-Gadget im Komplettpaket auf dem Pi `bash setup.sh --prepare-ecm` ausführen. Danach Pi neu starten, warten bis er erreichbar ist, dann Drucker neu starten. / Before the PC assistant, prepare ECM on older gadgets using that command, restart Pi, wait for SSH, then restart printer. [Pi-Anleitung / Pi guide](PI.md).

[Bebilderte Anleitung / Illustrated guide](BEBILDERT-DE.md)

## Erforderliche Vorarbeiten: Rinkhals und Klipper-Tunneling

**Vor der KobraNest-Installation müssen Rinkhals und die passende Klipper-Umgebung aus den Kobra-S1-Repositories eingerichtet sein. Erfahrung mit Klipper-Tunneling über LAN oder USB wird vorausgesetzt.**

KobraNest ergänzt die lokale Oberfläche und Systemverwaltung auf dem Drucker. Es ersetzt nicht die vorherige Einrichtung von Klipper/Moonraker auf dem externen Host, der passenden MCU-Firmware und des gewählten LAN-/USB-Tunnels. Die ausgewählte Verbindung sollte bereits funktionieren und verstanden sein, bevor das System umgestellt wird. Rinkhals wird unter anderem für den SSH-Zugang im Originalsystem und die Rückkehr-/Start-App benötigt.

Anleitungen und projektspezifische Informationen:

- [Rinkhals – Community-Firmware / Community firmware](https://github.com/rinkhals-community/Rinkhals) – Rinkhals vor der KobraNest-Installation einrichten. / Set up Rinkhals before installing KobraNest.
- [Kobra-S1: klipper-kobra-s1](https://github.com/Kobra-S1/klipper-kobra-s1) – angepasste Klipper-Umgebung für den Kobra S1.
- [Kobra-S1: ACEPRO](https://github.com/Kobra-S1/ACEPRO) – ACE-Pro-Anbindung und weitere Einrichtungsinformationen. Für die Verwendung des ACE Pro die dortigen Voraussetzungen beachten.

Die verlinkten Anleitungen und ihre Kompatibilitätshinweise vorab lesen. KobraNest installiert diese Projekte oder Rinkhals nicht automatisch und flasht keine MCU-Firmware.

Die sichtbare Projektbezeichnung ist KobraNest. Technische Altbezeichnungen in Pfaden, Dateinamen und technischen Dienstbezeichnungen bleiben aus Kompatibilitätsgründen erhalten.

# KobraNest S1 – Installation und Bedienung

Stand: 30. Oktober 2026 · Version 0.1.8

## 1. Was KobraNest macht

KobraNest läuft als Debian-System auf dem Drucker. HelixScreen startet automatisch; KlipperScreen bleibt als Alternative installiert. Klipper und Moonraker laufen auf einem separaten Raspberry Pi. Die beiden Drucker-MCUs werden standardmäßig über USB OTG Serial mit dem Pi verbunden. Ein Netzwerk-Tunnel über kabelgebundenes LAN bleibt als Alternative auswählbar; es gibt keinen WLAN-Fallback für MCU-Verbindungen. WLAN ist der übliche Zugang für Display, WebGUI und SSH.

Enthalten sind Bootlogo mit Ladebalken, Startmelodie, Bauraumlicht, SSH, lokale WebGUI und WLAN für den üblichen Netzwerkzugang. Die Oberfläche gibt es auf Deutsch und Englisch. Original-Slot A bleibt bei der Installation erhalten; KobraNest verwendet Slot B und Dateien auf der Datenpartition.

## 2. Voraussetzungen und Grenzen

- Ausschließlich der unterstützte Anycubic Kobra S1 mit RV1106/ARMv7, passendem Originalkernel und 800×480-Display. Andere Modelle und Firmwarestände sind nicht automatisch geeignet. Der Assistent prüft den unterstützten Stand; siehe [Kompatibilität](KOMPATIBILITAET.md).
- Ausgangspunkt ist normalerweise ein bereits im Anycubic-System eingerichtetes WLAN. Dessen aktuelle Drucker-IP für den ersten SSH-Zugang verwenden. Für die Neuinstallation muss das Originalsystem auf Slot A laufen und Root-SSH erreichbar sein.
- Für den üblichen WLAN-Aufbau das WLAN bereits unter Anycubic einrichten und die aktuelle WLAN-IP im Router für die WLAN-MAC reservieren. Der Installer übernimmt das gespeicherte Profil direkt auf dem Drucker. Ein LAN-Adapter ist hierfür nicht erforderlich. Alternativ ist die bisherige LAN-Installation möglich.
- Mindestens 1,6 GB freier Platz auf der Drucker-Datenpartition. Bei Platzfehlern nicht eigenmächtig vorhandene Systemverzeichnisse löschen.
- Raspberry Pi mit bereits passend eingerichtetem Klipper und Moonraker. Der Installer flasht keine MCU-Firmware und ersetzt keine vollständige printer.cfg.
- Docker auf dem Pi; dessen SSH-Benutzer muss `sudo -n docker info` erfolgreich ausführen können.
- Internetzugang für Python-Abhängigkeiten, Build und gegebenenfalls Debian-WLAN-Pakete.
- Kein laufender oder pausierter Druck während Einrichtung und Umschaltung. Stromversorgung während Übertragung und Aktivierung nicht unterbrechen.

Das Projekt ist am Referenzdrucker erprobt, aber keine breit auf unterschiedlichen Geräten getestete Serienfirmware. Eine saubere Installation sowie USB-/LAN-Betrieb und die Displayfunktionen wurden am Referenzdrucker praktisch getestet. Linux als Installations-PC ist vorgesehen, aber noch nicht vollständig praktisch erprobt.

## 3. Paket auf dem PC öffnen

Das gesamte `KobraNest-S1-v0.1.zip` entpacken. Alle Dateien und Unterordner zusammenlassen. Nicht direkt aus der ZIP starten.

### Windows

`Start-KobraNest.cmd` im entpackten Ordner öffnen. Alle Dateien einschließlich `_internal` zusammenlassen. Python muss nicht separat installiert werden.

### Linux, Beispiel Debian/Ubuntu

Im entpackten Ordner ein Terminal öffnen:

```bash
sudo apt update
sudo apt install python3 python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python assistant.py
```

Bei einem späteren Start genügen:

```bash
source .venv/bin/activate
python assistant.py
```

Der Assistent öffnet eine lokale Browserseite auf `127.0.0.1`. Öffnet sich kein Browser, die vollständig im Terminal angezeigte Adresse einschließlich des Teils hinter `#` aufrufen. Diese Sitzungsadresse nicht weitergeben. Terminal während eines Vorgangs geöffnet lassen; Strg+C erst nach Abschluss verwenden.

Docker wird auf dem Pi benötigt, nicht auf dem Linux-PC.

## 4. Geräte verbinden und prüfen

1. Im Assistenten Deutsch oder English wählen.
2. Die aktuelle IP des Druckers im Anycubic-System verwenden – normalerweise seine WLAN-IP, abzulesen am Display oder im Router. Benutzer `root` und dessen aktuelles SSH-Passwort eintragen. Das Stock-Passwort ist gewöhnlich `rockchip`, sofern nicht geändert.
3. Pi-IP und die eigenen Pi-SSH-Zugangsdaten eintragen. Es gibt kein gemeinsames Pi-Passwort im Paket.
4. Gateway und Netzpräfix kontrollieren. `/24` entspricht beispielsweise `255.255.255.0`; die Werte des eigenen Netzes verwenden.
5. Geräteprüfung starten. Neue SSH-Fingerabdrücke mit einem unabhängig bekannten Zugang vergleichen, bevor sie bestätigt werden. Originalsystem und Debian können an derselben Drucker-IP verschiedene Hostschlüssel besitzen.
6. Alle Fehler klären, bevor die Installation fortgesetzt wird. Die reine Geräteprüfung startet keine Dienste neu und wechselt keinen Bootslot.

Der Assistent erkennt automatisch, ob die eingegebene Adresse zu wlan0 oder eth1 gehört. Diese Verbindung wird für KobraNest vorbereitet. Bei WLAN werden die gespeicherten Netze ausschließlich geräteintern übernommen und HelixScreen mit eingeschaltetem WLAN eingerichtet. Die WLAN-IP bleibt DHCP-basiert: vor der Installation eine DHCP-Reservierung für dieselbe WLAN-MAC und Adresse im Router einrichten. Bei einer geänderten IP muss auch die Pi-Konfiguration angepasst werden; die neue Adresse kann am Display abgelesen werden.

Beispiel des Referenzaufbaus: Drucker-LAN `192.168.1.67`, Pi `192.168.1.151`, Gateway `192.168.1.1`, Präfix `24`. Diese Adressen nicht ungeprüft auf fremde Netze übertragen. Die verwendete Druckeradresse muss frei und dauerhaft reserviert sein. Im WLAN-Fall gilt die Reservierung für die WLAN-MAC, nicht für einen LAN-Adapter.

Wenn bereits KobraNest auf Slot B läuft oder das Zielverzeichnis einer früheren Installation existiert, keine Neuinstallation erzwingen. Erst vorhandene Installation und Sicherungen prüfen.

## 5. Installation mit dem Assistenten

### Sicherung & Build

Den Schritt mit dem angezeigten Wort `YES` und der Leerlaufbestätigung freigeben. Originalpartitionen werden auf dem PC gesichert und geprüft. Auf dem Pi baut Docker die gerätespezifischen Startdateien aus der eigenen Firmware. Noch kein Flashen der Bootpartitionen.

Sicherungsordner aufbewahren:

| PC-System | Standardordner des Assistenten |
| --- | --- |
| Windows | `%LOCALAPPDATA%/Kobrian/Assistant/devices/DRUCKER-IP/` |
| Linux | `~/.local/share/Kobrian/Assistant/devices/DRUCKER-IP/` |

Diese Sicherungen sind gerätespezifisch und gehören nicht in ein öffentlich weitergegebenes Paket.

### Erstellen / Übertragen

Den Vorbereitungsschritt mit `YES` bestätigen. Debian, beide Display-Oberflächen und die Zusatzmodule werden vorbereitet. Im Assistenten ist USB OTG Serial für die MCUs vorausgewählt. Bei Bedarf vor „Sicherung & Build“ auf Netzwerk umstellen. Die gewählte Variante zwischen Sicherung, Vorbereitung und Aktivierung nicht ändern; sie gehört zu den gerätegebundenen Einstellungen.

Der Installer übernimmt die WLAN-Originalmodule vom eigenen Drucker und installiert bei Bedarf die Debian-WLAN-Pakete über das Internet. Bei WLAN-Installation wird das eigene bereits gespeicherte Anycubic-Profil geräteintern übernommen. WLAN-Passwörter werden weder auf den PC exportiert noch im öffentlichen Paket gespeichert. Zertifikatbasierte oder nicht unterstützte Profile werden mit Fehlermeldung abgelehnt. Dieser Schritt schreibt noch keine Bootpartition.

### Pi vorbereiten

Standard USB: Der Pi muss bereits das passende USB-Gadget bereitstellen. Beide MCU-Abschnitte verwenden `/dev/ttyGS0` und `/dev/ttyGS1`; Netzwerk-MCU-Dienste und deren automatische Starts dürfen nicht parallel laufen. Datenkabel verbinden. Die Einzelheiten stehen in Abschnitt 8 und in [PI.md](PI.md). Der Installer konfiguriert den Pi nicht automatisch.


Die erzeugten Dateien liegen im Geräte-Arbeitsordner unter `pi-config`. Die genaue Einrichtung steht in [PI.md](PI.md).

Für Netzwerk-Tunnel über kabelgebundenes LAN:

- `socat` auf dem Pi installieren.
- Die erzeugten `mcu1.service` und `mcu2.service` prüfen, vorhandene Versionen sichern und passend installieren.
- Die vorhandenen MCU-Abschnitte in `printer.cfg` auf `/dev/ttyMCU1` und `/dev/ttyMCU2` einstellen. Andere MCU-Einstellungen und Abschnittsnamen erhalten.
- Den Klipper-Benutzer für die Gruppe `dialout` berechtigen.
- Moonraker auf Port 7125 erreichbar machen und die eigene Drucker-IP gezielt unter `trusted_clients` erlauben.
- `bauraumlicht.cfg` in Moonraker einbinden, falls gewünscht.

Der Assistent ersetzt die Pi-Konfiguration nicht automatisch. Nach Änderungen nur im Leerlauf die betroffenen Pi-Dienste neu starten.

### Aktivieren

Erst bei abgeschlossener Pi-Vorbereitung den Aktivierungsschritt wählen. Die angezeigte Bestätigung lautet `YES` mit der tatsächlichen Adresse.

Der Installer prüft Backup und Firmware erneut, schreibt die vorgesehenen Slot-B-Partitionen p7/p9 und prüft sie durch Rücklesen. Anschließend wird Slot B gewählt und der Drucker neu gestartet. Währenddessen weder Programm noch Stromversorgung unterbrechen.

### Start prüfen

Nach dem Neustart gegebenenfalls den neuen Debian-SSH-Fingerabdruck prüfen und bestätigen. Im Assistenten „Start prüfen“ ausführen. Danach praktisch kontrollieren:

- HelixScreen sichtbar und richtig herum; Touch bedienbar.
- WebGUI erreichbar.
- Klipper meldet `ready`; Düsen- und Betttemperatur werden plausibel angezeigt.
- Bauraumlicht lässt sich schalten.

Die lokale Bootprüfung benötigt keinen erreichbaren Pi. Ein erfolgreicher lokaler Bootstatus bestätigt deshalb noch nicht die MCU-Kommunikation.

## 6. WebGUI und Alltag

Im Browser `http://DRUCKER-IP:8080` öffnen. Beim ersten Aufruf einen eigenen Webbenutzer samt Passwort anlegen. Der Webzugang ist getrennt vom SSH-Zugang; `root / rockchip` ist kein automatisch eingerichteter Webbenutzer.

Die WebGUI zeigt Systemdaten, Netzwerkadressen, Tunnelstatus und Protokolle. Dort lassen sich Bauraumlicht, Display-Auswahl und Wartungsaktionen bedienen. HelixScreen ist Standard; der Wechsel zu KlipperScreen bleibt möglich. Die Sprache oben auf Deutsch oder Englisch einstellen.

Die Anzeige „USB-Brücke läuft“ bestätigt einen laufenden Prozess. Beide MCU-Verbindungen werden durch Klipper `ready` und gültige Temperaturen bestätigt.

## 7. WLAN am Display einrichten

Bei Installation über die Anycubic-WLAN-IP wird das bereits gespeicherte WLAN automatisch übernommen. Eine erneute Passworteingabe ist normalerweise nicht erforderlich. Die folgenden Schritte dienen zum Ändern oder Hinzufügen eines Netzes. Bei Installation über LAN beginnt WLAN weiterhin ohne übernommene Zugangsdaten.

In HelixScreen: **Einstellungen → System → Netzwerkeinstellungen**. WLAN einschalten, ein 2,4-GHz-Netz auswählen und Passwort eingeben.

WLAN erhält eine Adresse per DHCP. Bei WLAN als Hauptzugang dieselbe WLAN-Adresse im Router reservieren. Bei Installation über LAN bleibt dessen feste Adresse separat; WLAN darf diese LAN-Adresse nicht zusätzlich erhalten. Für eine feste WLAN-Adresse im Router eine zusätzliche Reservierung für die WLAN-MAC erstellen. Die angezeigte WLAN-IP kann anschließend für SSH und WebGUI verwendet werden.

LAN und WLAN können parallel bestehen. Auch beim USB-MCU-Tunnel braucht die Display-Oberfläche weiterhin eine Netzwerkverbindung zu Moonraker auf dem Pi. Ein fremdes WLAN ermöglicht diese Verbindung nicht automatisch.

## 8. MCU-Transport: LAN oder USB

Normalerweise einmal eine Variante wählen und beibehalten. Der Web-Umschalter verändert ausschließlich den Drucker; den Pi manuell passend vorbereiten. Es gibt keinen automatischen Wechsel bei Kabelverlust.

| Variante | Druckerseite | Serial-Pfade am Pi |
| --- | --- | --- |
| Netzwerk (nur LAN) | socat auf Ports 7003 und 7005 | `/dev/ttyMCU1`, `/dev/ttyMCU2` |
| USB OTG Serial | USB-ACM zu den beiden MCU-UARTs | `/dev/ttyGS0`, `/dev/ttyGS1` |

### USB erstmals vorbereiten

Der Drucker ist USB-Host, der Pi 4 USB-Gadget über seinen USB-C-Datenanschluss. Geeignete Datenverbindung und Stromversorgung verwenden. Zwei Hostanschlüsse nicht verbinden. Bei selbst angefertigten Kabeln nach Pinbezeichnungen messen: Farben sind keine verlässliche Belegung.

Der Pi braucht das passende DWC2-Overlay und ein Composite-Gadget mit drei ACM-Funktionen. Einen bereits vorhandenen, funktionierenden Gadget-Aufbau nicht zusätzlich durch einen zweiten ersetzen. Die genaue Vorlage und Vorbereitung stehen unter [USB OTG](../optional/usb-otg/README.md). Änderungen am Pi-Overlay können einen Pi-Neustart erfordern.

### Vom Netzwerk auf USB wechseln

1. Klipper auf dem Pi stoppen und die aktuelle `printer.cfg` sowie Dienstkonfiguration sichern.
2. Pi-Dienste `mcu1` und `mcu2` stoppen und deaktivieren. Auch vorhandene automatische LAN-Starts in Klippers `ExecStartPre` entfernen oder gezielt über einen dokumentierten Drop-in aufheben. Andere notwendige Startbefehle erhalten.
3. In den beiden vorhandenen MCU-Abschnitten nur die Serial-Pfade auf `/dev/ttyGS0` und `/dev/ttyGS1` ändern. Der Klipper-Benutzer benötigt Zugriff über `dialout`.
4. USB-Gadget aktivieren und Kabel verbinden. Der Drucker muss beide vorgesehenen USB-Kanäle eindeutig erkennen.
5. In der WebGUI **MCU-Verbindungen → Tunnelvariante → USB OTG Serial** wählen, Pi-Vorbereitung bestätigen und `TUNNEL` eingeben. Der Drucker startet neu.
6. Nach dem Druckerstart Klipper auf dem Pi starten. `ready` und beide Temperaturen prüfen. Bei Bedarf erst jetzt einen Firmware-Neustart ausführen.

### Von USB auf Netzwerk wechseln

1. Klipper am Pi stoppen.
2. Die ursprünglichen MCU-Pfade `/dev/ttyMCU1` und `/dev/ttyMCU2` wiederherstellen; die gesicherte LAN-Dienstkonfiguration passend zurücksetzen. Nur den eigenen USB-Drop-in entfernen, keine fremden Anpassungen löschen.
3. In der WebGUI die Netzwerk-Tunnelvariante auswählen und bestätigen. Der LAN-Adapter muss mit eigener LAN-IP und eingestecktem Netzwerkkabel aktiv sein. Der Pi verwendet diese LAN-IP, nicht die WLAN-Verwaltungsadresse. Der Drucker startet neu.
4. Auf dem Pi `mcu1` und `mcu2` aktivieren und starten, anschließend Klipper starten. `ready` und Temperaturen prüfen.

USB ist auch im Installer Standard. Der mehrfache Wechsel wurde am Referenzaufbau vom Benutzer erfolgreich bestätigt. Das ist kein Nachweis für jede Kabel-, Hub- oder Pi-Variante. GPIO 116 nicht routinemäßig bei Verbindungsproblemen oder USB-Abbrüchen schalten.

## 9. Rückkehr zu Anycubic / Rinkhals

Nur ohne laufenden oder pausierten Druck:

1. In der WebGUI „Wechsel zu Anycubic vorbereiten“ wählen und die Bestätigung befolgen.
2. KobraNest wählt Slot A und fährt sauber herunter. Mindestens 15 Sekunden warten.
3. Drucker am Netzschalter ausschalten, zehn Sekunden warten, wieder einschalten.

Kein bloßer warmer Neustart für diesen Wechsel. Die KobraNest-Dateien bleiben erhalten.

Zurück zu KobraNest: Im Originalsystem die Rinkhals-App **KobraNest starten** verwenden. In den App-Einstellungen beide Bestätigungen (`idle_confirmed` und `boot_confirmation`) auf `True` setzen und die App starten. Sie setzt beide danach zurück. Die App startet einmalig Slot B. Sie ist nicht für automatischen Dauerstart gedacht.

Bei Startproblemen siehe [RECOVERY.md](RECOVERY.md). Keine Boot- oder Datenpartition auf Verdacht formatieren oder fremde Partitionssicherungen zurückschreiben.

## 10. Häufige Meldungen

| Meldung / Verhalten | Vorgehen |
| --- | --- |
| „Start in ORIGINAL slot A before installation“ | Neuinstallation nur aus Original-Slot A beginnen. Eine vorhandene KobraNest-Installation nicht überschreiben. |
| SSH-Schlüssel geändert | Prüfen, ob bewusst zwischen Stock und Debian gewechselt wurde; Schlüssel unabhängig vergleichen. Nicht pauschal alle bekannten Schlüssel löschen. |
| Zielordner existiert | Vorhandene oder unvollständige Installation zuerst sichern und prüfen. Kein blindes Löschen von `/useremain`. |
| „Startprüfung benötigt KobraNest auf Slot B“ | Der Drucker läuft noch im Originalsystem. Bootstatus und vorherige Aktivierung prüfen. |
| USB-Gerät erkannt, aber Klipper nicht bereit | Beide Seiten müssen denselben Transport verwenden. Ein Firmware-Neustart installiert keine fehlende Brücke. |
| WLAN ohne IP | Anmeldung und DHCP prüfen. Eine LAN-MAC-Reservierung gilt nicht automatisch für WLAN. |
| WebGUI zeigt keine neuen Funktionen | Browserseite vollständig neu laden; Installation und Status prüfen. |

## 11. Sicherungen und Prüfnachweise

Gerätesicherungen, SSH-Schlüssel und eigene Konfigurationen privat aufbewahren. Installationspaket und persönliche Sicherung getrennt halten. Vor Änderungen an Pi-Diensten und `printer.cfg` deren funktionsfähigen Stand sichern.

Am Referenzgerät bestätigt: HelixScreen mit Touch, KlipperScreen als Alternative, WebGUI DE/EN, WLAN-Anmeldung nach Wiederherstellung, USB-Kommunikation beider MCUs und mehrfacher manueller Transportwechsel. Die neue WLAN-Erstinstallation mit Übernahme aus Stock ist auf Profilverarbeitung, DHCP-Logik und Installation in Testverzeichnissen geprüft. Der vollständige Wechsel von Stock-WLAN zu KobraNest-WLAN sowie ein Kaltstart dieser neuen Installationsfolge sind noch nicht praktisch geprüft.

RTL8153B: Die benötigte Realtek-Firmware wird mit Lizenz installiert. Da der Kernel den LAN-Adapter bereits vor dem Debian-Start erkennt, prüft KobraNest die vom Adapter gelesene Hardware-MAC und initialisiert bei Abweichung ausschließlich dessen Ethernet-Schnittstelle erneut. Keine feste MAC wird vergeben; EEPROM, USB-Hub und MCU-Gadget bleiben unverändert. Ein vollständiger Kaltstart sollte anschließend mit der Router-Reservierung geprüft werden.

## Anmeldung und Bestätigungen im Assistenten

Vor der Geräteprüfung muss der Warnhinweis zur Nutzung auf eigene Gefahr bestätigt werden. SSH-Passwörter werden einmal eingegeben und nur im Arbeitsspeicher der geöffneten Browserseite wiederverwendet. Schließen oder Neuladen der Seite entfernt diese Sitzungsdaten. Bei geänderten Zugangsdaten können die optionalen SSH-Passwortfelder in den Installationsschritten verwendet werden. Ein neues Debian-root-Passwort ist ebenfalls optional; leer bedeutet weiterhin rockchip. Nach erfolgreicher Aktivierung verwendet der Assistent dieses neue Passwort für KobraNest.

Die drei schreibenden Schritte werden im Assistenten jeweils mit YES bestätigt. Stillstandsbestätigung und Pi-Bereitschaft bleiben erhalten. Die Kommandozeileninstallation behält ihre bisherigen Bestätigungswörter.

Optional kann ein öffentlicher SSH-Schlüssel in das Feld eingefügt oder als .pub-Datei geladen werden. Er wird in Schritt 2 für root in KobraNest unter /root/.ssh/authorized_keys eingetragen. Private Schlüssel werden abgelehnt. Die Passwortanmeldung bleibt möglich. Bereits bestehende öffentliche Schlüssel bleiben erhalten.

Weitere Aktualisierungen / Further updates: [KobraNest Updates](UPDATES.md).
