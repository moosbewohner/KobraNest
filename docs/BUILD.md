# Build und Komponenten

## Debian-Laufzeit nachbauen

Linux-Rechner mit Docker; fuer ARMv7-Container einen ARM-kompatiblen Host oder passend eingerichtete Emulation verwenden. Die ausgelieferte rootfs ist bereits gebaut; dieser Schritt ist fuer eine normale Installation nicht erforderlich.

Aus dem Paket-Hauptverzeichnis:

```sh
docker build --platform linux/arm/v7 -f source/Dockerfile.test-rootfs -t s1-klipperscreen-test:local source
docker build --platform linux/arm/v7 -f source/Dockerfile.release -t kobrian-s1:v0.1 .
container=$(docker create kobrian-s1:v0.1)
docker export "$container" | gzip -1 >payload/rootfs-armhf.tar.gz
docker rm "$container"
```

Nach eigenen Aenderungen Paketpruefsummen neu erzeugen und Tests wiederholen. Ein eigener Build ist nicht automatisch bytegleich: Debian-Pakete werden aus den konfigurierten Paketquellen aufgeloest. Der Debian-Basisdigest und KlipperScreen-Commit sind in der ersten Dockerdatei festgehalten. Rootfs nie aus dem laufenden persoenlichen Drucker kopieren und als saubere Distribution deklarieren.

## Bootstrap und Rockchip-Werkzeuge

source/build-device.sh wird ausschliesslich von prepare in einem einmaligen Docker-Verzeichnis mit der eigenen system_a-Sicherung ausgefuehrt. Es ersetzt /sbin/init im entpackten Original-SquashFS, baut es neu und extrahiert rk_ota mit seiner eigenen uClibc-Laufzeit. Diese herstellerspezifischen Binaerdateien sowie Original-Boot-/Systempartitionen sind nicht im weitergegebenen Paket enthalten.

Der neue Bootstrap ist weiterhin auf die Datenpartition und den festen Pfad /useremain/s1-klipperscreen-test/rootfs angewiesen. Er ist kein eigenstaendiges Installationsimage fuer ein anderes Board.

## Framebuffer-Viewer

payload/fb-vnc-viewer ist das unveraenderte statische ARM-Binaerprogramm aus der KlipperScreen-Viewer-App des Referenzgeraets. Quellcode derselben dort installierten App liegt in source/viewer/src/fb-vnc-viewer.c; README und app.json dokumentieren die Herkunft. GPL-2.0-or-later ist im Quellkopf angegeben; GPL-2 liegt als source/viewer/COPYING bei.

Upstream: https://github.com/Kobra-S1/vanilla-klipper-swu/tree/main/klipperscreen-viewer-app

Der Code nutzt LibVNCClient aus LibVNCServer. Zum Neubau sind ein passender ARMv7-Compiler, Linux-Framebuffer-/Input-Header und LibVNCClient samt dessen Link-Abhaengigkeiten erforderlich. Ein dynamischer Ersatz muss zusammen mit seinen Bibliotheken in die rootfs integriert werden; das mitgelieferte statische Binaerprogramm wurde auf dem Referenz-S1 getestet. Das Paket behauptet keine bitidentische Reproduktion des urspruenglichen statischen Builds.

## Weitere Herkunft

- Debian und BusyBox: Copyright-/Lizenzdateien der installierten Pakete unter /usr/share/doc in der rootfs, Debian-Quellen ueber https://sources.debian.org/ und die Paketquellen.
- KlipperScreen: https://github.com/KlipperScreen/KlipperScreen, Commit 911c75bfc7658c0f5db39b39ee35910082e807f4, Lizenz im eingebetteten Repository.
- TigerVNC: https://github.com/TigerVNC/tigervnc
- Dropbear: https://github.com/mkj/dropbear
- OpenSSH: https://www.openssh.com/
- LibVNCServer/LibVNCClient: https://github.com/LibVNC/libvncserver
- FIT/RSCE-Formatreferenz: https://github.com/rockchip-linux/u-boot/blob/next-dev/tools/rockchip/resource_tool.c
- Bootgrafik: aus der vom Projektinhaber bereitgestellten Kobrian-Vorlage mit ImageGen als flache Grafik aufbereitet. Enthaltene Fremdmarken bleiben ihren jeweiligen Inhabern zugeordnet; keine Herstellerfreigabe wird behauptet.

Bestehende Fremdlizenzen werden durch dieses Paket nicht ersetzt. Die Debian-Binaerdistribution enthaelt viele Komponenten mit eigenen Lizenzen. Fuer eine oeffentliche Weiterverteilung deren Quellcode- und Lizenzpflichten beachten; Paket und Viewer-Quellcode sind keine vollstaendige Quellcode-Sammlung aller Debian-Abhaengigkeiten.

## Verified reset variant

System A also accepts the exact full-partition SHA-256 `dc6b2a43642bb7f7221a43aa0aa5d14ad7b781b55c88aebaf2e84a6bae1471d2`. Compared with the initial reference, all 5660094 bytes of the SquashFS filesystem are identical (SHA-256 `c8de64c981f72b1407ad677727528552bc2112f02195026349e2122e119c9e3f`). Differences begin after the filesystem ends. Checks still require one of the two exact partition hashes during inspection and activation; this is not a blanket allowance for arbitrary partition tails or firmware.
