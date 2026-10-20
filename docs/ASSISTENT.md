Eine aktuelle zusammenhängende Anleitung für Windows und Linux steht in [ANLEITUNG-DE.md](ANLEITUNG-DE.md).

## Erforderliche Vorarbeiten: Rinkhals und Klipper-Tunneling

**Vor der KobraNest-Installation müssen Rinkhals und die passende Klipper-Umgebung aus den von Antiriad gepflegten Kobra-S1-Repositories eingerichtet sein. Erfahrung mit Klipper-Tunneling über LAN oder USB wird vorausgesetzt.**

KobraNest ergänzt die lokale Oberfläche und Systemverwaltung auf dem Drucker. Es ersetzt nicht die vorherige Einrichtung von Klipper/Moonraker auf dem externen Host, der passenden MCU-Firmware und des gewählten LAN-/USB-Tunnels. Die ausgewählte Verbindung sollte bereits funktionieren und verstanden sein, bevor das System umgestellt wird. Rinkhals wird unter anderem für den SSH-Zugang im Originalsystem und die Rückkehr-/Start-App benötigt.

Anleitungen und projektspezifische Informationen:

- [Antiriad / Kobra-S1: klipper-kobra-s1](https://github.com/Kobra-S1/klipper-kobra-s1) – angepasste Klipper-Umgebung für den Kobra S1.
- [Antiriad / Kobra-S1: ACEPRO](https://github.com/Kobra-S1/ACEPRO) – ACE-Pro-Anbindung und weitere Einrichtungsinformationen. Für die Verwendung des ACE Pro die dortigen Voraussetzungen beachten.

Die verlinkten Anleitungen und ihre Kompatibilitätshinweise vorab lesen. KobraNest installiert diese Projekte oder Rinkhals nicht automatisch und flasht keine MCU-Firmware.

# Kobrian-Assistent: Sicherung, Vorbereitung und Aktivierung

Windows x64: Das gesamte Paket entpacken und **Kobrian-Assistent.exe** oeffnen.
Python ist im Ordner _internal enthalten; diesen neben der EXE lassen.
Alternativ Start-Kobrian.cmd oder mit eigener Python-Umgebung:
`python -m pip install -r requirements.txt`, danach `python assistant.py`.
Der Standardbrowser oeffnet eine lokale Sitzung auf 127.0.0.1, ohne Cloud.
DE / EN oben schaltet die Sprache um. Die Sprachwahl wird lokal gespeichert;
Passwoerter und technische Bestaetigungswoerter werden nicht uebersetzt.
Englische Kurzanleitung: ASSISTANT-EN.md. Original-Diagnoselogs behalten ihre Sprache.

## Ablauf

1. Drucker und Pi per SSH pruefen. Neue SSH-Fingerabdruecke zuerst unabhaengig
   vergleichen und bestaetigen. Die erste Geraetepruefung liest ausschliesslich.
2. Installationsschritte oeffnen, Gateway und Netzpraefix kontrollieren.
   Passwoerter erneut eingeben; diese werden nicht gespeichert.
3. **YES**: Originalpartitionen auf den PC sichern und gegenpruefen.
   Aus dem eigenen Firmwarebackup wird auf dem Pi per Docker ein Bootstrap
   erstellt. Dieser Schritt schreibt ein neues temporaeres Build-Verzeichnis
   auf dem Pi; er schreibt keine Druckerpartitionen.
4. **YES**: Debian in das neue Datenverzeichnis uebertragen.
   HelixScreen, KlipperScreen, WebUI mit Ersteinrichtung und die deaktivierte Rinkhals-App
   Kobrian starten vorbereiten. Kein Bootwechsel und keine Bootpartitions-
   Schreibvorgaenge. HelixScreen ist Standard; KlipperScreen bleibt ueber die WebUI waehlbar.
5. Den Pi anhand docs/PI.md einrichten bzw. dessen vorhandene Konfiguration
   pruefen. Passende Dienstdateien und die Lichtkonfiguration stehen nach
   SICHERN unter devices/Drucker-IP/pi-config. Der Assistent ueberschreibt
   keine printer.cfg und installiert keine Pi-Tunneldienste automatisch.
6. **YES**: Erst nach Bestaetigung des Druckerleerlaufs und
   der passenden Pi-Konfiguration aktivieren. Der vorhandene Installer prueft
   Firmware, Partitionslayout, Backup und Kandidaten erneut, sichert die
   Originaldaten auch auf dem Drucker, schreibt nur p7/p9, verifiziert durch
   Ruecklesen und startet Slot B. Original-Slot A bleibt erhalten.
7. **Start pruefen**: Nach dem Neustart separat den Debian-SSH-Schluessel
   pruefen/bestaetigen und den lokalen Bootstatus lesen. WebUI auf Port 8080
   oeffnen und einen eigenen Webbenutzer anlegen. Druckerdisplay/Touch und
   Klipper-Verbindung am Geraet praktisch pruefen.

Jeder schreibende Schritt braucht die passende getippte Bestaetigung und die
Leerlaufbestaetigung. Der Pi-Druckstatus wird unmittelbar vor dem Schritt
erneut abgefragt. Bei printing oder paused wird gestoppt; ist der Status nicht
ermittelbar, gilt die ausdrueckliche manuelle Leerlaufbestaetigung. Der
Assistent startet keine Installation von selbst nach einer Geraetepruefung.

## Bestehende Installation und Wiederaufnahme

Ein bereits auf Kobrian laufender Drucker wird nicht neu installiert. Auch im
Originalsystem wird ein vorhandenes Kobrian-Datenverzeichnis nicht blind
ersetzt. Der Assistent ist fuer eine Neuinstallation auf genau dem im CLI
hinterlegten Firmwarestand vorgesehen; andere Firmware wird abgelehnt.

Sicherungen, Einstellungen ohne Passwoerter und Fortschrittsmarker liegen
unter `%LOCALAPPDATA%/Kobrian/Assistant/devices/Drucker-IP/`.
Der Geraete-Manifest bindet Backup und vorbereitete Dateien an die gewaehlten
Einstellungen. Diese zwischen den Schritten nicht aendern. Bei einem neuen
Programmstart zuerst dieselben Geraete pruefen und danach den benoetigten
Schritt waehlen. Keine neue Sicherung ueber ein abgeschlossenes Backup legen.
Nach abgeschlossenem Debian-Staging koennen nur die Zusatzmodule fortgesetzt
werden; unvollstaendige Rootfs-Uebertragungen werden nicht automatisch geloescht.
Ein Fehler beim Flashen darf nicht durch blindes Wiederholen uebergangen werden;
Backup und Fehlerausgabe fuer eine gezielte Wiederherstellung behalten.

## SSH und Zugangsdaten

Unbestaetigte neue Hostschluessel werden vor der Passwortanmeldung abgelehnt.
Geaenderte gespeicherte Schluessel bleiben gesperrt. Stock und Debian verwenden
getrennte Hostschluesseldateien fuer Pruefung/Installation bzw. Startkontrolle.
Kein automatisches Entfernen eines alten Schluessels. Fingerabdruecke mit einem
bekannten SSH-Zugang vergleichen, z.B. auf einem OpenSSH-Pi mit
`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`.

Passwoerter bleiben nur waehrend des Schritts im Arbeitsspeicher bzw. Formular.
Kein localStorage und keine Passwortdatei. Nach dem Schritt ohne offenen
Fingerabdruckdialog werden die Passwortfelder geleert. Sitzungsschluessel im
sessionStorage enthalten keine SSH-Zugangsdaten. Nur bestaetigte oeffentliche
Hostschluessel werden unter `%LOCALAPPDATA%/Kobrian/Assistant/` gespeichert.
Konsole waehrend eines Vorgangs offen lassen; Browser schliessen beendet den
Prozess nicht. Keine Abbruchfunktion waehrend eines Bootpartitions-Schreibens.

## Pruefstand und Grenzen

Formulare, Bestaetigungen, SSH-Vertrauen, Drucksperre, Aufruf des CLI-Installers,
Fehlerbehandlung und Zusatzmodule wurden automatisiert mit wirkungslosen
Geraete-Platzhaltern geprueft. Der Windows-Build und die lesende Pruefung wurden
am Referenzaufbau getestet. Die Grundinstallation wurde inzwischen über den Assistenten am Referenzgerät durchgeführt. Der neueste vollständige Ablauf mit allen WLAN-/USB-Ergänzungen wurde noch nicht erneut durchlaufen. USB-Kommunikation und mehrfaches Umschalten wurden vom Benutzer bestätigt. WLAN-Unterstützung und USB-Brücken werden jetzt beim Staging eingerichtet; die initiale MCU-Verbindung bleibt LAN. Die Pi-Konfiguration wird manuell vorgenommen. Die Installation verwendet HelixScreen als Standard und behaelt KlipperScreen.

## Windows-Build

Python 3.13, PyInstaller 6.22.3, onedir/console. Build aus dem Paketordner:
`pyinstaller --onedir --name Kobrian-Assistent assistant.py`.
EXE und _internal neben assistant.py legen. Die EXE verwendet die Paketdateien
neben sich. Nicht digital signiert. Lizenztexte unter docs/windows-licenses.

## SSH-Schluessel beim A/B-Wechsel

Der Drucker darf auf derselben IP zwei verschiedene bestaetigte Identitaeten
verwenden. Bisherige printer_known_hosts und printer_debian_known_hosts werden
weiter gelesen; jeder neu bestaetigte Druckerschluessel wird in einer eigenen
printer-slot-Fingerabdruck.known_hosts gespeichert. Alte Schluessel werden
nicht ueberschrieben. Vertrauen gilt nur fuer die zugehoerige IP. Ein unbekannter
Schluessel braucht vor der Passwortanmeldung eine ausdrueckliche Bestaetigung.
Beim Pi bleibt ein geaenderter gespeicherter Schluessel weiterhin gesperrt.

## Abgebrochener WLAN-Upload

Ist nur die Uploadphase unterbrochen, Geräte erneut prüfen und denselben Schritt VORBEREITEN starten. Der Assistent akzeptiert ausschließlich bekannte reguläre Upload-Dateien, prüft jeden vorhandenen Teil gegen den Dateianfang des eigenen Pakets und überträgt nur den Rest per SFTP. Die vollständige Prüfsumme wird vor dem Entpacken geprüft. Bereits entpackte Rootfs-Verzeichnisse, fremde Dateien und beschädigte Teilstücke werden weiterhin abgelehnt und nicht gelöscht. Sicherung & Build nicht erneut starten; den bestehenden Geräte-Arbeitsordner erhalten.

## Neustart nach Sicherung

Der Herstellerstart kann den nicht definierten Rest des 512-Byte-Sektors hinter den 32 Byte A/B-Metadaten in misc verändern. Nur Bytes 2080 bis 2559 werden für diesen Vergleich ausgeblendet. Größe, A/B-Signatur, Version und CRC müssen gültig sein; alle A/B-Metadaten und alle anderen misc-Bytes müssen unverändert bleiben. Die ursprüngliche PC-Sicherung bleibt unverändert. Vor Aktivierung werden frische Gerätesicherungen gegen die unmittelbar zuvor gelesenen vollständigen Partitionshashes geprüft. Andere Änderungen bleiben gesperrt.

Current assistant: acknowledge the warning once, reuse passwords for this browser session, and confirm each write step with YES. Optional public SSH keys and Pi light transfer are offered during staging. Reloading the page clears in-memory passwords.
