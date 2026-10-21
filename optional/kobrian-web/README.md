# KobraNest Web – lokale Wartung auf dem S1

Kleine, eigenstaendige Webseite auf dem Drucker, ohne Cloud, CDN oder zusaetzliche Python-Pakete. Sie bleibt ueber WLAN erreichbar, wenn LAN-Adapter, MCU-Tunnel oder Pi fehlen. Solange Debian bzw. das Netzwerk selbst nicht startet, ist auch diese Seite nicht erreichbar.

## Aufrufen

Im Referenzsystem: http://192.168.10.67:8080 ueber LAN oder die am Display angezeigte WLAN-IP mit Port 8080. Die WLAN-IP kommt per DHCP und kann sich aendern.

Bei einer frischen Installation erscheint zuerst **Webzugang erstellen**. Der Benutzer legt selbst einen Namen (3–32 Zeichen: Buchstaben, Ziffern, Punkt, _ oder -) und ein Passwort mit mindestens acht Zeichen fest und wiederholt das Passwort. Es gibt kein voreingestelltes Webkonto. Nach erfolgreicher Einrichtung ist die offene Registrierung gesperrt.

Bestehende Installationen behalten ihre Zugangsdaten. Angemeldete Nutzer koennen ueber **Webzugang** Name und Passwort aendern; dafuer ist das bisherige Webpasswort erforderlich. Danach werden alle Websitzungen beendet und eine neue Anmeldung ist noetig. Im Referenzsystem wurden die vorhandenen Zugangsdaten nicht zurueckgesetzt.

Webkonto und SSH-Konto sind getrennt. Es wird nur ein gesalzener PBKDF2-Hash in /etc/s1-web.json gespeichert, Rechte 600. Sitzungscookie, CSRF-Pruefung und Begrenzung der Anmeldeversuche sind vorhanden.

## Funktionen

- Lokale LAN-/WLAN-Adressen, MACs, RAM, Speicherplatz, Betriebszeit und aktive Oberflaeche.
- MCU-TCP-Listener und bestehende Verbindungen werden aus /proc gelesen. Der Statuscheck oeffnet keine MCU-Verbindung und blockiert keine serielle Schnittstelle.
- Pi/Moonraker-Status, Druckdatei, Laufzeit und Temperaturen, soweit erreichbar. Ohne Pi stehen diese Werte explizit nicht zur Verfuegung.
- Licht ueber den bereits initialisierten GPIO 117; keine Pin-Neukonfiguration. Der vorhandene Lichtdienst liest denselben Zustand.
- HelixScreen/KlipperScreen waehlen, Oberflaeche neu starten. Die Auswahl bleibt fuer den naechsten Start erhalten; MCU-Dienste werden dabei nicht beendet.
- Einzelne Netzwerk-MCU-Tunnel kontrolliert beenden; BusyBox init startet sie neu. Keine Bewegung, kein MCU-Reset und kein automatisches FIRMWARE_RESTART.
- Ausgewaehlte lokale Logs ansehen und maximal 24 KB pro Log herunterladen. Keine beliebigen Pfade oder Konfigurationsdateien auslesen.
- S1 neu starten oder den bestehenden s1-return-to-stock-Helfer fuer Anycubic aufrufen.

MCU-Neustart, Druckerneustart und Anycubic-Boot werden bei erkanntem laufendem/pausiertem Druck gesperrt. Ist der Druckstatus unbekannt, muss dies ausdruecklich bestaetigt werden. Der Druckstatus wird vor diesen Aktionen erneut abgefragt. Zusaetzlich muss NEUSTART bzw. ANYCUBIC eingegeben werden.

**Anycubic-Boot:** Danach ist die KobraNest-Weboberflaeche weg. Der Rueckweg erfolgt ueber die separat installierte Rinkhals-App "KobraNest starten" (Version 0.1.2, auf dem Referenzdrucker erfolgreich getestet): boot_confirmation=KOBRIAN und idle_confirmed=True speichern und Start app waehlen. Kein aktiver oder pausierter Druck. Der Knopf verwendet den vorhandenen Boot-Helfer; die Installation der Webseite selbst aendert keine Bootpartition und fuehrt keinen Bootwechsel aus.

## Installation fuer das bestehende KobraNest-Debian

Den Ordner auf den Drucker kopieren, dann dort:

```sh
python3 install.py --root / --pi-ip IP_DES_PI --start
```

Port optional mit --port angeben (Standard 8080). Das Erstkonto wird beim ersten Aufruf im Browser erstellt. Eine vorhandene /etc/s1-web.json mit eingerichteten Zugangsdaten wird erhalten. Bereits vorhandene Portbelegung vorher pruefen.

Der Installer kopiert Server und Seite, sichert s1-service/inittab als .before-web, ergaenzt den eigenen Respawn-Dienst und liest mit --start BusyBox init neu ein. Kein Drucker- oder Pi-Neustart. Auf einem Offline-Rootfs --start weglassen. Nach Updates eines schon laufenden Webdienstes diesen gezielt neu starten, damit neuer Python-Code geladen wird.

## Betrieb

Konfiguration: /etc/s1-web.json; Server: /usr/local/sbin/s1-web; Seite: /opt/kobrian-web/index.html; Log: /var/log/s1-web.log. Statusabfrage alle fuenf Sekunden. Es werden hoechstens zwoelf HTTP-Anfragen gleichzeitig bearbeitet.

Deinstallation nur im Leerlauf: die Web-Respawn-Zeile aus /etc/inittab entfernen, init neu einlesen und den passenden s1-web-Prozess beenden. Andere seit .before-web vorgenommene Aenderungen erhalten; nicht blind komplette Sicherungen zurueckkopieren.

## Abnahme

Anmeldung, abgewiesene unberechtigte/ungueltige Anfragen, Status, Logs, JavaScript-Syntax und der automatische Dienst-Neustart werden bei der Referenzinstallation geprueft. Die responsive Mobilansicht ist vorbereitet; die visuelle Browserabnahme steht noch aus. Wirksame Boot-, Reboot- und MCU-Neustart-Aktionen werden dabei nicht ausgeloest. Ohne Pi-Verbindung werden weiterhin lokale Daten angezeigt; nur Druckdaten werden unbekannt.

Der Display-Umschalter setzt den bereits eingerichteten s1-ui-select-Helfer voraus. Ohne ihn sind die entsprechenden Schalter deaktiviert. Die Installation aktiviert niemals automatisch HelixScreen oder KlipperScreen.

## Tunnelvariante im Dashboard

Im Feld MCU-Verbindungen stehen Netzwerk und USB-OTG Serial zur Auswahl. Das Auswaehlen allein aendert keine Datei und keinen Dienst. Erst Uebernehmen & S1 neu starten speichert die Variante, nach Eingabe von TUNNEL und Bestaetigung der vorbereiteten Pi-Konfiguration. Bei erkanntem laufendem/pausiertem Druck ist der Wechsel gesperrt; bei unbekanntem Status ist eine weitere Bestaetigung erforderlich.

USB ist nur aktivierbar, wenn die optionale USB-Erweiterung auf dem Drucker installiert ist und beide eindeutigen Pi-Gadget-Kanaele (VID 1d6b / PID 0104, Interfaces 00 und 02) erkannt werden. Netzwerk setzt einen aktiven LAN-Link voraus. Der Pi wird niemals automatisch geaendert. Er muss vorher im Leerlauf vorbereitet werden: Netzwerk mit mcu1/mcu2-Diensten und ttyMCU1/2, USB mit Gadget und ttyGS0/1. Klipper auf dem Pi vor dem Wechsel stoppen. Ein erkannter Serial-Kanal ist noch kein bestaetigter MCU-Protokolltest.

Im Referenzsystem ist die Drucker-Erweiterung nun vorbereitet, aber weiterhin Netzwerk aktiv. Der Pi blieb unveraendert. Kein USB-Kabeltest und keine Umschaltung/kein Neustart wurden durch die Installation ausgefuehrt. Die separate USB-Anleitung im Gesamtpaket beschreibt Vorbereitung und Rueckweg.

Ersteinrichtung und Kontoaenderung wurden mit einer isolierten Testkonfiguration geprueft. Das echte Druckerkonto wurde dabei nicht geaendert.

## Sprachen

Deutsch und Englisch stehen ueber den Sprachumschalter im Kopfbereich bereit, auch bei Ersteinrichtung und Anmeldung. Die Auswahl wird nur im jeweiligen Browser unter kobrian.language gespeichert; ohne Auswahl orientiert sie sich an der Browsersprache (Deutsch, sonst Englisch). Dynamische Statuswerte, Meldungen und Bestaetigungsdialoge sind uebersetzt. Benutzerinhalte, Dateinamen und Original-Logs bleiben unveraendert. Die Bestaetigungswoerter NEUSTART, ANYCUBIC und TUNNEL bleiben in beiden Sprachen gleich.

Die Texte stehen in translations.json und werden mit python3 build-translations.py in index.html eingebettet. Es werden keine Sprachdateien oder Fonts extern geladen. Ein Sprachwechsel betrifft nur die Weboberflaeche, nicht HelixScreen oder die SSH-Konfiguration. Sprachwechsel, Einrichtung, Dialoge und unveraenderte Benutzereingaben wurden in einem lokalen DOM-Test geprueft.

## Wechsel zu Anycubic mit manuellem Kaltstart

Die Webaktion waehlt Original-Slot A synchron aus und synchronisiert die Daten. Erst bei Erfolg wird nach fuenf Sekunden ein geordnetes poweroff ausgefuehrt, kein reboot. Die WebUI zeigt dauerhaft: mindestens 15 Sekunden warten, am Netzschalter ausschalten, zehn Sekunden warten und wieder einschalten. Die Rueckkehr-App fuer Stock nach KobraNest bleibt unveraendert. Die Aktion wurde bei dieser Aktualisierung nicht auf dem Drucker ausgeloest. Auswahl-/Shutdown-Reihenfolge und Fehlersperren wurden mit Platzhaltern geprueft.

s1-return-to-stock --prepare waehlt nur Slot A und synchronisiert. Ohne Argument wird anschliessend poweroff angefordert. Alte Aufrufer duerfen keinen automatischen Neustart mehr erwarten.

## Integrierte Kamera / Integrated camera

Die WebUI bietet Kamera Ein/Aus, 640x480 / 960x720 / 1280x720, 1–30 FPS sowie eine reduzierte Bildrate ohne Zuschauer. Werte werden sofort und dauerhaft in /etc/s1-camera.json gespeichert. Ausschalten beendet den Aufnahmeprozess; der kleine Verwaltungsprozess wartet weiter. Neuinstallationen aktivieren die Kamera standardmaessig. Ohne angeschlossene integrierte Kamera wartet der Dienst; nach dem Anschliessen startet die Aufnahme automatisch. Manuelles Deaktivieren bleibt gespeichert. Vorhandene Einstellungen bleiben erhalten. Die Einstellungen veraendern keine Kamera-Konfiguration am Pi.

Der Installer installiert Debians ustreamer. /usr/local/sbin/s1-camera waehlt die integrierte UVC-Kamera 13d3:784b anhand ihrer USB-Kennung und ignoriert Metadaten- und Fremdkameraknoten. MJPEG wird direkt aus der Kamera weitergereicht (HW encoder), ohne Software-Neukodierung. Der Stream ist im lokalen Netz auf Port 8081 verfuegbar: /stream, /snapshot und /state. Eine erreichbare Bildrate ist nicht garantiert; Belichtung, USB und Hardware begrenzen sie. Log: /var/log/s1-camera.log.

The web dashboard provides camera on/off, resolution, 1–30 FPS and reduced capture rate without viewers. Settings persist in /etc/s1-camera.json and apply without a printer reboot. Disabling stops the capture process. Fresh installations enable the camera by default. Capture starts when the integrated camera is connected; otherwise the supervisor waits. Explicitly disabling it is persistent. Existing settings are preserved. Pi webcam settings are never modified. Debian ustreamer forwards the integrated camera's MJPEG frames without software re-encoding. Local network stream: http://PRINTER-IP:8081/stream; snapshot: /snapshot. Requested frame rate is a target, not a guarantee.

Upstream: https://github.com/pikvm/ustreamer (GPL-3.0, installed from Debian repositories).
