# Rinkhals-App: Kobrian starten

Einmaliger Rueckweg vom originalen Anycubic/Rinkhals-System zu der bereits installierten Kobrian-Installation auf Slot B. Grundlage fuer Metadaten, Eigenschaften und Start/Stop/Status ist die bereitgestellte lan-tunneled-klipper-App und das tatsaechlich installierte Rinkhals-Framework.

## Installation

Den vollstaendigen Ordner **kobrian-start** nach **/useremain/home/rinkhals/apps/kobrian-start** kopieren. app.sh muss ausfuehrbar sein (`chmod 755 app.sh`). Die App bleibt standardmaessig deaktiviert; keine .enabled-Datei anlegen. Sie darf manuell ueber **Start app** gestartet werden. Ein Rinkhals-Neuladen bzw. erneutes Oeffnen der App-Liste kann erforderlich sein.

## Bedienung auf dem Stock-Display

1. **Sicherstellen, dass kein Druck laeuft**, auch kein pausierter Druck. Der Starter kann den proprietaeren Stock-Druckstatus nicht verlaesslich automatisch ermitteln.
2. Im Rinkhals-App-Menue **Kobrian starten** oeffnen.
3. In den Eigenschaften **boot_confirmation** auf **KOBRIAN** und **idle_confirmed** auf **True** setzen und speichern.
4. **Start app** waehlen. Nach etwa acht Sekunden wird Slot B gewaehlt und der S1 neu gestartet. Innerhalb der Wartezeit kann **Stop app** abbrechen.

Die bestaetigenden Eigenschaften werden vorab sowohl dauerhaft als auch temporaer zurueckgesetzt. Die App deaktiviert ihren Autostart vor der Umschaltung. Ein spaeterer Stock-Fallback startet deshalb keine automatische Rueckkehrschleife. Fuer jeden neuen Wechsel muss erneut bestaetigt werden.

**Stop app** bricht nur einen noch wartenden Auftrag ab. Wenn die Bootauswahl bereits geschrieben wurde, wird sie dadurch nicht zurueckgesetzt.

## Was geprueft wird

- Original-Slot A (`root=/dev/mmcblk0p8`) vor jeder wirksamen Umschaltung.
- Kobra S1 (KS1), nicht pauschal andere Anycubic-Modelle.
- Vorhandene Kobrian-Kennung, Debian-Laufzeit, Bootskript und korrigierte lokale Startpruefung.
- Erwartete Groessen von boot_b und system_b.
- Einmalige Freigabe fuer den getrennten Neustartauftrag.

Es werden keine Kernel-, Rootfs- oder MCU-Images geflasht und keine Netzwerk-/Tunnel-Einstellungen geaendert. Nur der A/B-Bootdatensatz wird mit dem vorhandenen Herstellerwerkzeug umgestellt. Ein alter Fehlstartmarker wird vorher nach **/useremain/s1-klipperscreen-test/return-history/** gesichert und entfernt; dort wird auch der vorherige misc-Inhalt gesichert. Ein tatsaechlich fehlerhafter lokaler Kobrian-Start kann weiterhin auf Stock zurueckfallen.

Das Vorhandensein der Installation ist keine vollstaendige Integritaets- oder Dateisystempruefung. Die separat empfohlene Offline-Dateisystempruefung wird nicht durch diese App ersetzt.

## Status und Diagnose

- `./app.sh check`: nur Installations-/Layoutpruefung, keine Umschaltung.
- `./app.sh status`: Rinkhals-Status des laufenden Neustartauftrags.
- Log: **/tmp/kobrian-start/app.log** (auf dem Stock-System).
- Nach erfolgreichem Start von Kobrian: **/var/log/s1-boot-health.log** und fehlender boot-attempt-Marker bestaetigen den lokalen Start.

## Pruefstand

Auf dem Referenzdrucker wird die App nur deaktiviert installiert. Syntax, Metadaten, die reine Installationspruefung und die Verweigerung eines Starts aus dem bereits laufenden Kobrian werden geprueft. Dabei wird kein Slot gewechselt und kein Neustart ausgeloest. Sichtbarkeit und tatsaechliche Rueckkehr aus dem Stock-Menue sind anschliessend noch praktisch abzunehmen.

## Korrektur 0.1.1

Fehlende temporaere Rinkhals-Konfigurationen brechen den Start nicht mehr vorzeitig ab. Bei einem fehlgeschlagenen Start werden Sperre und Freigabedateien aufgeraeumt. Die Bestaetigungsruecksetzung wurde auf dem Stock-System mit den echten Rinkhals-Hilfsfunktionen und einem wirkungslosen Neustart-Platzhalter geprueft. Der vollstaendige Slotwechsel bleibt separat praktisch zu testen.

## Korrektur 0.1.2

Das Stock-System enthaelt weder rmdir noch das entsprechende BusyBox-Applet. Leere Sperrverzeichnisse werden jetzt mit dem vorhandenen Python 3 ausschliesslich per os.rmdir entfernt. Entfernen der vorhandenen Sperre und Stoppen mit einer neu angelegten Testsperre wurden auf dem Drucker erfolgreich geprueft.
