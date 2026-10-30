# Updates und Pi-Einrichtung / Updates and Pi setup

## Helix-Korrektur 0.1.8 / Helix fix

**Bestehende Installation, ohne neue Pi-Einrichtung:** In der Drucker-WebUI zuerst 0.1.7 installieren, anschließend erneut **Updates prüfen** und 0.1.8 installieren. 0.1.7 erweitert ausschließlich die Updatefähigkeit; 0.1.8 installiert die native Helix-Einbindung. Pro Schritt Leerlauf, Heizungen aus und `YES` bestätigen.

Alternativ **KobraNest-Drucker-Update-0.1.8.zip** auf dem **Drucker** entpacken und dort als root `python3 update_printer.py --confirmation YES` ausführen. Dieses Paket erledigt beide Schritte, überspringt bereits installierte Versionen und benötigt keine Pi-Einrichtung. Es ist kein WebUI-Uploadpaket; dafür die zwei jeweiligen TAR-Dateien verwenden.

Helix selbst wird nicht durch die gebündelte ältere Basis ersetzt. Einstellungen, eigene Bilder und eine bereits selbst aktualisierte Version bleiben erhalten. Nur ein ausgewähltes Helix wird kurz neu gestartet. Veraltete eigene KobraNest-Marker/Verknüpfungen werden gesichert; originale Helix-Dateien bleiben unverändert. Nach Rücknahme des Hauptupdates bleibt die Vorbereitung 0.1.7 installiert. Die archivierten Verwaltungsdateien haben separate Sicherungen.

**Existing installations:** install 0.1.7 in the printer WebUI, check again, then install 0.1.8. Alternatively unpack **KobraNest-Drucker-Update-0.1.8.zip on the printer** and run `python3 update_printer.py --confirmation YES` as root. No Pi setup is needed for this fix. Your Helix version, settings and custom images are preserved. The selected Helix UI restarts; MCU services do not. File rollback returns to preparation version 0.1.7; archived legacy bookkeeping has separate backups.

## Deutsch

### Welche Datei gehört wohin?

| Datei | Ziel und Zweck |
| --- | --- |
| `KobraNest-S1-v0.1.8.zip` | Erstinstallation am Windows-/Linux-PC; vorhandenes KobraNest nicht überschreiben. |
| `KobraNest-Komplett-0.1.8.zip` | Bestehendes USB-System aktualisieren **und** ECM-/SSH auf beiden Geräten einrichten. **Auf dem Pi** ausführen. |
| `KobraNest-printer-update-0.1.8.tar.gz` | Nur Drucker-Dateiupdate, in der Drucker-WebUI hochladen. |
| `KobraNest-pi-update-0.1.8.tar.gz` | Nur Pi-Dateiupdate, direkt am Pi mit `s1-update` installieren. |

Die WebUI läuft auf dem Drucker, auch bei Zugriff über die Pi-IP. Sie akzeptiert kein Pi-Paket. Einzelne TARs ersetzen keine erstmalige ECM-/SSH-Einrichtung. Helix behält seinen eigenen Updater; Debian und MCU-Firmware werden nicht ersetzt.

### Bestehendes USB-System: gemeinsamer Weg

1. [Komplettpaket aus Release 0.1.8](https://github.com/moosbewohner/KobraNest/releases/tag/v0.1.8) auf den Pi übertragen und vollständig entpacken.
2. Kein Druck oder pausierter Druck, Heizungsziele 0. Funktionierender USB-MCU-Tunnel. Der Pi muss vorübergehend per SSH die **aktuelle** Drucker-LAN-/WLAN-IP erreichen können.
3. Als normaler Pi-Benutzer im entpackten Ordner starten:

```bash
bash setup.sh --complete
```

4. Eigene IPs und Pi-Benutzer angeben, `YES` bestätigen und SSH-Fingerabdruck unabhängig prüfen. Das Passwort wird einmal für die Sitzung abgefragt und nicht gespeichert.
5. Fehlt ECM, wird Vorbereitung angeboten. Sie sichert `ports.sh`/`ports.service` und bereitet den nächsten Start vor. **Pi neu starten, auf SSH warten, danach Drucker neu starten.** Anschließend denselben Befehl erneut ausführen. Kein Hot-Rebind, kein automatischer Neustart.
6. Erst **`COMPLETE 0.1.8`** bestätigt Updates und Einrichtung. Die Versionsanzeige allein reicht nicht. Protokoll auf dem Pi: `/var/lib/kobranest-updates/complete-setup.json`.

Der Ablauf installiert beide signierten Updates, den beschränkten Pi-SSH-Dienst, Druckerschlüssel, Hostkey-Pinning, ECM-Adresse, internen Moonraker-Zugriff, Licht und aktivierte Weiterleitungen. Bereits installierte Zielversionen werden beim Fortsetzen übersprungen. Benutzerkonten, eigene Weiterleitungsports, `klipper.service`, MCU-Dienste und Kamera bleiben erhalten. Konfigurationsänderungen werden gesichert; Moonraker startet nur bei geänderter Lichtkonfiguration neu.

Nach erfolgreichem `COMPLETE` die zusätzliche Pi-Einrichtung aus der WebUI **nicht erneut** ausführen. Bei Fehlern Ausgabe aufheben, keine Version herabsetzen und keine Sperre umgehen. Fremde Signaturschlüssel und manuell geänderte verwaltete Dateien werden nicht stillschweigend überschrieben.

### Erstinstallation und LAN

Bei USB ECM zuerst wie in [PI.md](PI.md) vorbereiten. `bash setup.sh --prepare-ecm` aus dem Komplettpaket kann auf dem Pi laufen, während der Drucker noch Anycubic/Rinkhals verwendet. Danach die Erstinstallation im aktuellen PC-Assistenten starten; er verwendet die bereits eingegebenen Pi-Zugangsdaten. Funktionierendes Rinkhals-Tunneling bleibt Voraussetzung. Kein automatischer Klipper-Grundaufbau oder MCU-Flash.

LAN benötigt kein ECM. MCU-Daten dürfen ausschließlich über kabelgebundenes LAN zur LAN-IP laufen. Vorhandene LAN-Dienste und manuelle MCU-Zuordnung bleiben bestehen. Bei bereits vollständiger LAN-Einrichtung die plattformspezifischen Dateiupdates verwenden.

### Spätere Dateiupdates

Im Drucker-Webbereich **KobraNest Updates** prüfen, Hinweise lesen, herunterladen/prüfen und mit `YES` installieren. Alternativ die **Drucker-TAR** hochladen. Signaturen, SHA-256, Plattform, Version, Platz, bekannter Leerlauf und Heizungsziele 0 werden geprüft. Die WebUI startet kurz neu; bei Bedarf erneut anmelden.

Das **Pi-TAR** direkt per SSH auf dem Pi installieren:

```bash
sudo s1-update stage --package ./KobraNest-pi-update-0.1.8.tar.gz
sudo s1-update apply --confirmation YES
sudo s1-update status
```

Den zweiten Befehl nur nach erfolgreicher Prüfung ausführen. „Wrong package platform“: Zielgerät und Dateityp prüfen. „Downgrade/reinstall refused“: gleiche oder ältere Version wird absichtlich abgelehnt.

### Reparatur und Rücksetzung

Der gemeinsame Ablauf repariert gemischte Updater mit fehlendem `boot_recover()`. Fehlt die Versionsdatei, entsteht vorübergehend ein ausdrücklich markierter **0.0.0-Reparatur-Bootstrap**, anschließend wird die echte signierte Zielversion installiert. Es wird keine frühere Systemversion erfunden. `repair.py --restart-web` allein repariert nur WebUI/Updater, keine Pi-Verbindung.

Bei fehlgeschlagener Update-Startprüfung werden ersetzte Dateien zurückgesetzt. Unterbrochene Dateiaustausche werden beim nächsten WebUI-Start aus dem Journal wiederhergestellt. Die drei neuesten eigenen Update-Sicherungen bleiben erhalten; persönliche Sicherungen werden nicht gelöscht. Dateiupdate-Rollback entfernt nicht die separat eingerichtete ECM-/SSH-Konfiguration. Diese hat eigene Sicherungen unter `/var/backups` bzw. neben geänderten Moonraker-Dateien.

Kein Bootloader-/Partitions-Recovery: siehe [RECOVERY.md](RECOVERY.md). Nach einem alleinigen Pi-Neustart kann ein Druckerneustart nötig bleiben; die ECM-/Kernel-Startschwierigkeit ist nicht allgemein behoben. Ohne Druckernetzwerk ist dessen Kamera nicht erreichbar. Pi-Kameras bleiben unverändert.

## English

Use the **complete installer ZIP on the PC for a fresh installation**. Existing USB users should unpack **KobraNest-Komplett-0.1.8.zip on the Pi** and run:

```bash
bash setup.sh --complete
```

This updates both devices and configures ECM, the restricted SSH service, device key, pinned host key, internal Moonraker, chamber light and enabled reverse forwards. Enter your own current printer IP and Pi account. The printer must be idle, heater targets zero; working Rinkhals USB MCU tunneling and temporary network SSH to the printer are required. Verify its fingerprint independently. No password is stored and the printer gets no persistent Pi administrator access.

If ECM is absent, preparation is offered for next boot. ports.sh/ports.service are backed up. Restart Pi, wait for SSH, restart printer, then rerun the command. No live USB rebind is performed. Only **COMPLETE 0.1.8** confirms success. Receipt: `/var/lib/kobranest-updates/complete-setup.json` on the Pi. Installed target updates are skipped on resume. After success, do not repeat WebUI Pi setup.

For fresh USB installations, `bash setup.sh --prepare-ecm` can run on the Pi before KobraNest installation while the printer still runs Anycubic/Rinkhals. Use the current PC assistant afterwards. LAN users do not need ECM; MCU LAN transport requires wired Ethernet, never Wi-Fi. Existing complete LAN setups may use separate platform updates. See [PI.md](PI.md) and [USB.md](USB.md).

For later file updates, the **printer TAR belongs in the printer WebUI**, even when accessed through a Pi forwarding port. The **Pi TAR belongs on the Pi**: run `sudo s1-update stage --package ./KobraNest-pi-update-0.1.8.tar.gz`, then `sudo s1-update apply --confirmation YES` only after staging succeeds. TARs do not provision first-time configuration.

Signatures, platform, version, hashes, disk space, idle state and heater targets are checked. Downgrade/reinstallation is refused. User settings, accounts, camera configuration, klipper.service and MCU services are preserved. Moonraker restarts only if light configuration changes. Helix keeps its own updater; Debian and MCU firmware are not replaced.

Mixed updater installations and missing metadata are repaired. A temporary marked **0.0.0 repair bootstrap** is followed by the signed target version; an earlier system version is not invented. File-update rollback/startup recovery does not undo separately provisioned ECM/SSH configuration, which has its own backups. Personal backups are not deleted. This is not bootloader recovery. Restarting only Pi can still require a printer restart due to the known ECM/kernel issue. Printer-camera streaming requires printer networking; Pi cameras remain unchanged.
