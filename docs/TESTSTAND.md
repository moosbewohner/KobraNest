# Teststand v0.1, 19.10.2026

## Am Referenzdrucker bestaetigt

- Debian-Start aus Slot B; Original-Kernel/-System A unveraendert.
- Rueckfall nach fehlgeschlagenem Debian-Start durch naechsten Einschaltvorgang.
- Lokales KlipperScreen mit Bild und Touch.
- Netzwerk-UART-Tunnel zu beiden MCUs; Klipper/Moonraker auf dem Pi erreichbar.
- KobraNest-Bootlogo, Ladebalken, anschliessender Wechsel zu KlipperScreen.
- GPIO117-Licht: EIN/AUS/EIN elektrisch ausgelesen, Licht und Schalter vom Benutzer bestaetigt.
- AVNC 3.3.1 auf Android 7 ueber SSH2222 zu VNC127.0.0.1:5911 vom Benutzer bestaetigt.
- SSH-PC-Schluesselanmeldung auf Port 22; persoenlicher Schluessel nicht im Paket.
- Lokaler Druckerneustart aus dem korrigierten KlipperScreen-Dialog vom Benutzer bestaetigt.
- Kurze Startmelodie am PWM-Summer: manuell abgespielt, vom Benutzer gehoert; danach enable=0 und duty_cycle=0 geprueft. Autostart in s1-boot eingetragen, noch kein erneuter kompletter Boot-Test fuer diese Ergaenzung.

## Am verallgemeinerten Paket geprueft

- Vollstaendiger sauberer Debian-Containerbuild und Rootfs-Export mit neuen generischen Startdateien.
- SHA256 beim Download des Runtime-Archivs verglichen.
- Runtime: Root vor Staging gesperrt; keine aktiven SSH-Privat-/Hostschluessel und keine PC-authorized_keys im Export.
- BusyBox-reboot/poweroff-Symlinks, notwendige Dienstprogramme, Python-Syntax und Shell-Syntax geprueft.
- Isolierter Container: ECDSA-Schluesselerzeugung, Umwandlung fuer OpenSSH, sshd-Konfigurationspruefung und chpasswd erfolgreich. Keine Testschluessel oder Testpasswoerter werden in das Exportimage zurueckgespeichert.
- build-device.sh auf dem Build-Pi mit der Referenz-System-A-Sicherung erfolgreich: Bootstrap und getrennte Bootcontrol-Laufzeit erzeugt, eingebettete Init-Datei mit der Vorlage verglichen.
- Logo-Rebuild ergibt exakt den Hash des auf dem Drucker getesteten Images.
- Installer-Vorabpruefung mit simuliertem passenden Geraet erfolgreich; falsche Architektur, aktiver Slot B, falscher A-Hash, falsche Partitionsgroesse und gemountetes B werden abgewiesen.
- IP-/Gateway-Validierung und Ablehnung von ungueltigen Eingaben geprueft.
- Paketmanifest und ZIP-Integritaet werden vor Auslieferung geprueft.

## Noch nicht bestaetigt

Der neue generische Ablauf prepare -> stage -> activate wurde nicht auf einem zweiten Drucker vollstaendig ausgefuehrt. Die genauen Erststartschritte fuer einen fremden Drucker und dessen Hardware-/Netzwerkvariante sind daher noch nicht praktisch bestaetigt. Kein automatisiertes Hardware-in-the-loop-Verfahren und keine Modellfreigabe fuer andere Kobra-Drucker.

Keine Achsbewegungen, Heiztests oder Druckjobs durch die Pakettests ausgefuehrt. Kein Live-Neuflash des persoenlichen Referenzdruckers fuer den Pakettest. Die Kamera und originalen Herstellerdienste wurden nicht in Debian portiert.
