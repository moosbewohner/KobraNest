# SSH, SFTP und AVNC

## Normales SSH

```sh
ssh root@DRUCKER_IP
```

Port 22, Standardpasswort rockchip, falls stage kein eigenes Passwort gesetzt hat. Dieser Zugang laeuft ueber Dropbear. SFTP wird durch openssh-sftp-server bereitgestellt.

Fuer einen eigenen PC-Schluessel auf dem PC erzeugen, z.B. mit ssh-keygen. Nur die .pub-Datei in /root/.ssh/authorized_keys auf dem Drucker einfuegen. /root/.ssh mit Modus 700 und authorized_keys mit 600 anlegen. Vorhandene Schluessel erhalten. Private Schluessel nie in das weitergegebene Paket aufnehmen.

MobaXterm: SSH, Drucker-IP, Port 22, Benutzer root; unter Advanced SSH settings den eigenen privaten Schluessel auswaehlen. Fuer die bestehende KlipperScreen-Sitzung ist kein X11-Forwarding erforderlich.

## Android / AVNC

AVNC kann SSH-Tunnel und VNC in einer Verbindung verwenden:

| Feld | Wert |
|---|---|
| VNC-Adresse | 127.0.0.1 |
| VNC-Port | 5911 |
| VNC-Benutzer/Passwort | leer |
| Durch SSH tunneln | an |
| SSH-Host | eigene Drucker-IP |
| SSH-Port | 2222 |
| SSH-Benutzer | root |
| SSH-Anmeldung | Passwort oder eigener eingerichteter Schluessel |

Auf dem Referenzgeraet wurde AVNC 3.3.1 auf Android 7 bestaetigt. Dieser SSH-Zugang nutzt ECDH-P256, ECDSA-P256 und AES-CTR; er ist auf lokale TCP-Tunnel nach 127.0.0.1:5911 begrenzt und bietet keine Shell. Der Grund fuer den Abbruch des Android-Clients am Dropbear-Port 22 wurde nicht abschliessend bewiesen.

Die Hostschluessel werden bei der ersten Debian-Initialisierung auf jedem Drucker neu erzeugt. Keine Referenz-Fingerabdruecke eines fremden Druckers uebernehmen. VNC selbst lauscht nur auf Loopback und wird ueber SSH erreicht. Eine zweite KlipperScreen-Instanz wird nicht gestartet.
