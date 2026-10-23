# Gepruefte Plattform

Referenz: Anycubic Kobra S1, RV1106 ARMv7 Cortex-A7, 256 MB RAM, Rockchip-Kernel 5.10.160, 800x480-Display, 32-Bit-Framebuffer /dev/fb0 mit 3200 Byte Stride. Bild und Touch werden um 180 Grad gedreht. Touchgeraet /dev/input/event0. USB-A-Port GPIO 41, MCU-Reset GPIO 116, Licht GPIO 117. UARTs /dev/ttyS3 und /dev/ttyS5, je 576000 Baud.

Historische Referenz-Pruefsummen (Dokumentation, keine Start-Whitelist):

```text
boot_a p6 SHA256:
352ee437ecb6c4b8c7c5f4de1b36a89e345cd511e6a3bc065ab5c556c3a59241

system_a p8 SHA256:
e104cc77d3c9d8b5ed5ff63ec55cda6433d09071db1a62f759435e48bc88de01
```

Die Anfangspruefung vergleicht keine vollstaendigen Firmware-Hashes. Geprueft werden ARMv7/RV1106, Linux 5.10, Original-Slot A, Partitionsgroessen, FIT-/SquashFS-Header, benoetigte UARTs und Display sowie Root-Zugang und Daten-Mount. Abweichende Firmware-Bytes allein fuehren nicht zum Abbruch. Sicherungen und Transfers bleiben SHA-256-geprueft; vor dem Schreiben werden die aktuellen Partitionen mit der Sicherung dieses Druckers verglichen. Nach dem Schreiben werden Slot B und der unveraenderte Slot A kontrolliert.

Partitionen: p1 env 32 KiB, p5 misc 256 KiB, p6/p7 boot je 16 MiB, p8/p9 system je 48 MiB, p17 ext4-Datenpartition. Die uebrige Originalpartitionierung wird nicht neu angelegt. Der Installationsstart muss aus p8 erfolgen; p7 und p9 duerfen nicht gemountet sein.

BusyBox-init wird verwendet, weil der Referenzkernel keine passende systemd/cgroup-Umgebung bietet. Der originale Kernel und die U-Boot-Installation werden beibehalten. In boot_b werden nur beide BMP-Ressourcen und ihre Ressourcen-/FIT-Pruefsummen ersetzt. Kernel und DTB bleiben bytegleich.

Die integrierte UVC-Kamera wird ueber uStreamer unterstuetzt und ist in der WebGUI konfigurierbar. Herstellerspezifische Zusatzdienste wurden nicht allgemein portiert. Ein Firmware- oder KlipperScreen-Update kann die geprueften Annahmen oder lokalen Anpassungen aendern. S1 Max und andere Kobra-Modelle sind mit diesem Paket nicht freigegeben.

## Zusätzliche USB-Ethernet-Module / Additional modules

ASIX and CDC-NCM: successful module-load test on the reference S1 kernel build 5.10.160 (2026-01-26). Actual adapter testing is pending. Loaded at boot only on the exact tested kernel build. Existing Realtek and built-in USB networking are preserved. No claim of universal USB-LAN compatibility. See [driver details](../optional/wlan-dualbetrieb/USB-LAN.md).
