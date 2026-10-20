# WLAN als üblicher Installationszugang

Der Installer erkennt die aktuelle Drucker-IP auf wlan0 oder eth1. Ein LAN-Adapter ist nicht mehr Voraussetzung. Bei WLAN werden die gespeicherten Netzwerkblöcke aus /userdata/wifi_cfg/wpa_supplicant.conf ausschließlich auf dem Drucker in die neue Konfiguration übernommen. Keine WLAN-Passwörter werden auf dem PC oder im Paket gespeichert. WPA-PSK, SAE und offene Profile sind vorgesehen; zertifikatbasierte Netze werden abgelehnt.

WLAN bleibt bei DHCP. Die aktuelle WLAN-IP vor der Installation anhand der WLAN-MAC im Router reservieren, damit der Pi den Drucker nach dem Start wiederfindet. Die WLAN-Adresse wird nicht zusätzlich eth1 zugewiesen. Bei Installation über eth1 bleibt die bisherige statische LAN-Konfiguration mit separatem WLAN-DHCP erhalten.

stock-network.py prüft die Zugangsadresse und überträgt das Profil im inaktiven Root. install-printer.py unterstützt --primary-interface wlan0 oder eth1 (Standard für einzelne manuelle Aufrufe: eth1). HelixScreen erhält bei Profilübernahme wifi_enabled=true und wifi_expected=true.

Prüfstand: Profilverarbeitung, sichere geräteinterne Übernahme, DHCP-Adresskonflikte und wiederholte Dateiinstallation automatisiert geprüft; tatsächliche LAN-Erkennung lesend am Gerät bestätigt. Eine komplette Erstinstallation aus Stock über WLAN mit anschließendem WLAN-Boot wurde noch nicht praktisch ausgeführt.

## Vorherige Aufbauhinweise und manuelle Einrichtung

# WLAN im Installer

Der Grundinstaller richtet jetzt LAN und WLAN gemeinsam ein. Er kopiert die beiden Originalmodule aus /oem/usr/ko oder /usr/ko des eigenen Stock-Systems; Herstellerdateien werden nicht öffentlich mitgeliefert. Fehlen die Module, stoppt die Vorbereitung mit einer Fehlermeldung. Debian-WLAN-Pakete werden bei Bedarf während der Vorbereitung heruntergeladen: Internetzugang erforderlich. Dabei werden keine Dienste im inaktiven Root gestartet.

WLAN-Zugangsdaten werden nicht verteilt oder vom alten System übernommen. Am HelixScreen-Display das gewünschte WLAN auswählen. LAN bleibt statisch, WLAN erhält seine eigene DHCP-Adresse. USB-MCU-Verbindungen sind davon unabhängig.

Auf der frischen Referenzinstallation wurden Treiber und Dienst wiederhergestellt; wpa_cli PONG und Scan OK bestätigt. Anmeldung, DHCP und Kaltstart dieser Installation stehen noch aus. Der vollständige neue Installationsablauf wurde noch nicht erneut durchlaufen.

# LAN fuer Druckerbetrieb, WLAN fuer SSH

LAN (eth1) behaelt die konfigurierte statische Drucker-IP. WLAN (wlan0) bekommt eine eigene IPv4-Adresse per DHCP vom Router. Die LAN-Adresse wird nicht mehr auf WLAN verschoben. MCU-Tunnel und Bauraumlicht bleiben an die LAN-Adresse gebunden; WLAN ist fuer die Verwaltung per SSH vorgesehen. Der SSH-Dienst lauscht auf beiden Adressen.

WLAN am HelixScreen-Display einrichten: Einstellungen -> System -> Netzwerkeinstellungen -> WLAN einschalten, 2,4-GHz-Netz auswaehlen, Passwort eingeben. Die Netzkonfiguration wird dauerhaft gespeichert. Es liegen keine Zugangsdaten im Projektpaket.

Die WLAN-IP kann sich durch DHCP aendern. Fuer eine feste WLAN-IP eine eigene DHCP-Reservierung anhand der WLAN-MAC im Router anlegen. Die bestehende LAN-Reservierung erhalten. Die beiden Adressen muessen verschieden sein. Die Verwaltungs-IP wird in /run/s1/wifi.lease.json gespeichert und am Display vom WLAN-Dienst gemeldet.

## Komponenten

- /opt/s1-wifi/cfg80211.ko und RTL8723DS.ko: Originalmodule aus dem eigenen OEM-Backup, passend zum Kernel 5.10.160.
- /etc/wpa_supplicant/s1.conf: ctrl_interface=/run/wpa_supplicant, update_config=1, gespeicherte WLAN-Netze; Rechte 600.
- /etc/s1-dual-network.json: statische LAN-Adresse/Prefix und LAN-Gateway.
- /usr/local/sbin/s1-dual-network: WLAN-Anmeldung und DHCP-Client; richtet einen nachtraeglich angeschlossenen LAN-Adapter ein.
- /usr/local/sbin/s1-wifi-dhcp: verwaltet ausschliesslich die WLAN-DHCP-Adresse und WLAN-Routen mit Metrik 600.
- /etc/inittab: ::respawn:/usr/local/sbin/s1-service network; Log /var/log/s1-network.log.

LAN-Routen sind bevorzugt. ignore_routes_with_linkdown wird aktiviert, damit ein vorhandener LAN-Adapter ohne Kabel WLAN-Verwaltungszugriff nicht blockiert. Der Drucker-Kernel unterstuetzt hier keine IPv4-Policy-Routing-Regeln; es werden keine solchen Regeln benoetigt. Ein fremdes WLAN kann SSH ermoeglichen, ersetzt aber weder die LAN-MCU-Verbindung noch die Erreichbarkeit des Pi durch HelixScreen.

## Optionale Installation

Nur auf dem Debian-S1 bzw. dessen Rootfs, nicht auf dem Pi:

1. Originalmodule aus dem eigenen OEM-Backup nach /opt/s1-wifi uebernehmen.
2. apt-get install --no-install-recommends wpasupplicant iproute2 wireless-regdb
3. python3 install-printer.py --root / --address LAN_IP/PREFIX --gateway LAN_GATEWAY
4. Im Leerlauf kill -HUP 1 ausfuehren oder geplant neu starten. Anfangs LAN angeschlossen lassen. HelixScreen bei nachtraeglichem Treiberstart einmal neu starten, damit es die WLAN-Hardware erkennt.

Der Helfer sichert und ergaenzt s1-boot, s1-service und inittab, kopiert beide Netzwerkprogramme und legt nur bei fehlender Datei eine leere WLAN-Konfiguration an. Er startet keine Dienste und ueberschreibt keine vorhandenen WLAN-Zugangsdaten. Die Module werden im Bootablauf vor dem GUI-Start geladen. Es darf kein weiterer DHCP-Client auf wlan0 laufen.

## Pruefung und Rueckweg

ip -4 addr; ip route; cat /run/s1/wifi.lease.json; wpa_cli -p /run/wpa_supplicant -i wlan0 status. WLAN-Schluessel nicht in oeffentliche Berichte kopieren.

Am Referenzdrucker wurden eine eigene DHCP-Adresse und SSH darueber mit geprueftem Hostschluessel bestaetigt. Der normale Pi-Verkehr bleibt bei angeschlossenem LAN auf eth1. Ein Kaltstart und ein erneuter Test ohne LAN-Adapter stehen fuer diese geaenderte Variante noch aus.

Rueckweg nur mit angeschlossenem LAN: Netzwerk-Zusatzzeile aus inittab entfernen, init neu einlesen und den Netzwerkdienst kontrolliert beenden; bei Bedarf .before-wifi-Sicherungen wiederherstellen und geplant neu starten. Originale Bootpartitionen und Stock-System sind unberuehrt.

HelixScreen-Netzwerktest: ping muss im Prozess-Suchpfad liegen. /usr/bin/ping kann als Wrapper `exec /bin/busybox ping "$@"` bereitgestellt werden. Der optionale WLAN-Installer und das Staging des Grundpakets ergaenzen diesen Befehl.
