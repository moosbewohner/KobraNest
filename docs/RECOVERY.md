# Reparatur & Recovery im Assistenten

Unter **Reparatur & Recovery** im Assistenten werden die bereits eingegebenen Drucker-SSH-Daten verwendet. Ein Pi-Zugang ist nicht erforderlich. Der globale Warnhinweis muss akzeptiert sein. Ein unbekannter SSH-Fingerabdruck wird wie bei der Installation zuerst zur unabhaengigen Pruefung angezeigt.

1. **Recovery-Diagnose starten:** Liest aktiven Slot, Architektur, Partitionslayout, vorhandene Grunddateien und die passende PC-Sicherung unter dem normalen Arbeitsverzeichnis. Keine Dienstneustarts, Bootwechsel oder Schreibzugriffe auf Druckerpartitionen. Eine Diagnose ist keine vollstaendige Integritaetspruefung des entpackten Debian-Dateisystems.
2. **Zu Anycubic zurueckkehren:** Nur bei laufendem KobraNest B mit vorhandenem Rueckkehr-Helfer. Waehlt A und faehrt herunter. 15 Sekunden warten, ausschalten, zehn Sekunden warten und wieder einschalten. Kein automatischer Neustart.
3. **Installation sichern und Neuinstallation vorbereiten:** Nur aus Original A. Prueft, dass die alte Installation weder gemountet noch von Prozessen verwendet wird, und benennt sie in einen einmaligen `.recovery-...`-Ordner um. Der PC-Arbeitsordner mit Sicherungen wird ebenfalls archiviert. Keine Daten werden dabei geloescht. Anschliessend normale Erstinstallation mit neuer Sicherung/Build durchfuehren. Genuegend Platz fuer alte und neue Installation bereithalten.
4. **Slot B aus PC-Sicherung wiederherstellen:** Nur aus Original A. Verwendet `devices/DRUCKER-IP/device.json` und `backup/p7.img`, `p9.img` samt Referenzbildern p1/p6/p8. Alle benoetigten Dateien, Groessen und SHA-256-Werte werden geprueft. Aktuelle p1, p6 und p8 muessen zur Sicherung passen. Das ist eine Bindung an den gesicherten Geraetezustand und bleibt bewusst strenger als die einfache Anfangspruefung. Die aktuelle Version von B wird auf dem Drucker gesichert, die Sicherungen werden kontrolliert, A wird als Startslot gehalten, dann werden ausschliesslich p7/p9 geschrieben und vollstaendig zurueckgelesen. p1/p6/p8 werden abschliessend erneut kontrolliert. Mindestens 512 MiB freier Datenspeicher erforderlich. Es erfolgt kein Neustart.

Fuer jede schreibende Aktion sind eine maximal 15 Minuten alte Diagnose desselben SSH-Geraets, **YES** und die bestaetigte Leerlaufpruefung am Drucker erforderlich. Ein ueber Moonraker bekannter laufender oder pausierter Druck sperrt die Aktion trotzdem. Ein unbekannter Pi-Status ersetzt nicht die Leerlaufpruefung am Geraet.

Die Slot-B-Sicherung enthaelt den Stand **vor der zugehoerigen Installation**. Sie ist kein vollstaendiges Backup aller Debian-Konfigurationen oder Drucker-Datenpartitionen. PC-Sicherungen niemals von einem anderen Drucker uebernehmen. Nach einem IP-Wechsel muss das zugehoerige Arbeitsverzeichnis korrekt zugeordnet werden; es gibt keinen automatischen Import beliebiger Sicherungsordner.

**Pruefstand:** DE/EN-Oberflaeche, API-Zugriffsschutz, Bestaetigungen, Zielbindung, Pruefsummenfehler und der Schreibablauf wurden mit simulierten Transporten getestet. Ein kompletter Recovery-Schreibtest auf Hardware steht aus. Die bereits bestehende Rueckkehr aus KobraNest ist separat am Referenzgeraet erprobt.

## English

Open **Repair & Recovery** in the assistant. Reuse the printer credentials above; no Pi login is needed. Start with read-only diagnosis. Write actions require a recent diagnosis of the same SSH identity, **YES**, and confirmation that no print is running or paused. A known active Moonraker job blocks writes.

- Return to Anycubic selects A and shuts down. Wait 15 seconds, switch off, wait ten seconds, then switch on.
- Archive installation, from stock A only, preserves the old device installation and PC workspace under unique archive names. Then use the normal fresh installation workflow.
- Restore slot B, from stock A only, verifies your own PC backup and the device's p1/p6/p8 references, backs up current B, restores only p7/p9 and checks complete readback. A stays active. It does not restore bootloader, A, raw misc/env images, all Debian settings or user data. At least 512 MiB free storage is required.

The new recovery write flow is simulation-tested, not yet validated by a full hardware restoration. No USB/maskrom recovery is included. Without a booted SSH-capable system, a separate hardware-specific Rockchip procedure is required.

---

# Sicherung und Rueckkehr

## Funktionierendes Debian

Mit dem Debian-Passwort (Standard rockchip, falls nicht geaendert):

```sh
python installer.py rollback --settings settings.json --work device-work
```

Alternativ per SSH zum Drucker:

```sh
/usr/local/sbin/s1-return-to-stock
```

Dies wählt den erhaltenen Original-Slot A und fährt den Drucker herunter. Mindestens 15 Sekunden warten, am Netzschalter ausschalten, zehn Sekunden warten und wieder einschalten. Es erfolgt kein automatischer warmer Neustart. Die neue Debian-Dateistruktur bleibt auf der Datenpartition liegen. Keine persoenlichen Datenpartitionen loeschen.

## Fehlgeschlagener Debian-Start

Der Bootstrap schreibt einen Bootversuchsmarker unter /useremain/s1-klipperscreen-test/boot-attempt. Der Healthcheck entfernt ihn nach bestätigtem lokalem Start: beschreibbares Rootfs, SSH und entweder GUI oder Webdienst. Pi, Moonraker und MCU-Verbindungen sind keine Voraussetzung dieser lokalen Bestätigung. Bleibt der Marker stehen, wechselt der naechste Bootversuch ueber das originale rk_ota-Werkzeug auf den anderen Slot. Diese Rueckfalllogik wurde am Referenzgeraet nach einem fehlgeschlagenen Debian-Start durch Aus-/Einschalten getestet.

Ein Aus-/Einschalten kann daher nach einem fehlgeschlagenen Versuch wieder zum Originalsystem fuehren. Das ist keine Garantie bei Fehlern vor Ausfuehrung des Bootstrap oder bei unterbrochenem Flash-Schreiben. Bei fehlendem Netzwerk zuerst Pi-IP, Moonraker-Zugriff und USB-LAN pruefen. Die Skripte und Daten unter /useremain nicht vorschnell loeschen.

## Gesicherte Partitionen

Auf dem PC: device-work/backup/p1.img, p5.img, p6.img, p7.img, p8.img, p9.img. Pruefsummen: device-work/device.json. Vor dem Flash-Schreiben zusaetzlich auf dem Drucker unter /useremain/s1-klipperscreen-test/sicherung-vor-installation/.

- p1: env
- p5: misc / Slot-Metadaten
- p6: Original boot_a
- p7: vorheriges boot_b
- p8: Original system_a
- p9: vorheriges system_b

Der Installer schreibt nicht nach p1, p6 oder p8. Er aktualisiert p5 ausschliesslich ueber das originale rk_ota. U-Boot, MCU-Firmware und andere Datenpartitionen werden nicht neu geflasht.

Manuelles Zurueckschreiben einzelner Images nur nach Pruefung von Zielgeraet, Partitionsnummer und Hash. Insbesondere misc/env nicht blind von einem anderen Geraet uebernehmen. Fuer einen Fehler ohne gestartetes System ist ein separates, zur eigenen Hardware passendes Rockchip-Recovery-Verfahren erforderlich; dieses Paket installiert oder garantiert keinen USB-Recovery-Modus.

## Abbruch beim Staging

stage kann eine reine Uploadphase mit bekannten Dateien nach erfolgreicher Präfixprüfung fortsetzen. Ein bereits entpacktes Rootfs, fremde Dateien oder beschädigte Teilstücke bleiben gesperrt. Nach einem abgebrochenen Upload zuerst pruefen, dass weiterhin Original-Slot A laeuft und kein Flash-Schritt ausgefuehrt wurde. Dann den unvollstaendigen Staging-Ordner gezielt ausserhalb des Zielpfads umbenennen, genug freien Platz schaffen und stage wiederholen. Keine pauschalen rekursiven Loeschbefehle gegen /useremain verwenden.

## Verzeichnis auf dem Build-Pi

prepare speichert den einmaligen Buildpfad in device-work/device.json. Nach Download und Sicherung der Ergebnisdateien kann genau dieses temporaere Verzeichnis auf dem Pi entfernt werden. Es enthaelt die eigene Original-Systempartition und gehoert nicht in weitergegebene Pakete.
