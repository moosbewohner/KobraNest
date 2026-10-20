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
