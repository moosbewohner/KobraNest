# Additional USB Ethernet modules / Zusätzliche USB-LAN-Module

ASIX and CDC-NCM modules passed an actual load test on the reference S1. Adapter-specific connection, DHCP, throughput and restart tests are still pending. No claim of hardware validation for every supported USB ID is made.

The startup loader runs before network addressing, verifies each module checksum and only loads on the exact tested ARMv7 kernel build (5.10.160, Jan 26 2026). Other builds are skipped. Failures are logged to /var/log/s1-usb-lan.log and do not block startup. No interface addresses or MACs are changed, and no existing driver is unloaded. Realtek remains the built-in driver. usbnet/cdc_ether are already built in and are not duplicated.

Die beiden zusätzlichen Treiber werden beim Start geladen. Die Freigabe gilt nur für den exakt getesteten Kernel-Build. Hardwaretests mit passenden ASIX-/CDC-NCM-Adaptern stehen noch aus. Realtek, MAC-Adressen und die vorhandene Netzwerkkonfiguration bleiben erhalten. Kernel-Build-Abweichungen und Ladefehler werden protokolliert; der Start läuft weiter.

Provenance: user-provided usb ethernet kernel modules.zip. ASIX declares GPL and CDC-NCM declares Dual BSD/GPL. The original build recipe, exact source revision and any vendor patches were not provided. Upstream reference: https://github.com/torvalds/linux/tree/v5.10/drivers/net/usb . This reference is not a claim that unmodified upstream source reproduces these binaries. The source-provisioning limitations documented in THIRD_PARTY.md remain applicable.

Runtime: /opt/s1-usb-lan/{asix,cdc_ncm}.ko and modules.json; /usr/local/sbin/s1-usb-lan-init. The binaries are embedded with compression and checksums in install-printer.py so existing assistant uploads also install the extension without changing the frozen executable.
