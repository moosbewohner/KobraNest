Realtek RTL8153B firmware, unchanged from upstream linux-firmware.

Source: https://kernel.googlesource.com/pub/scm/linux/kernel/git/firmware/linux-firmware/+/refs/heads/main/rtl_nic/rtl8153b-2.fw
SHA-256: 137c9c752e8648ecfcf3b74ffc7d675c098145c222e2969721e6257af31716bc
License: LICENCE.rtlwifi_firmware.txt (included unchanged).

The S1 kernel probes USB Ethernet before the Debian root is available. The startup helper reads PLA_BACKUP with an IN-only USB request, matching upstream r8152. If the factory address differs from the active address, it rebinds only the Ethernet interface once per USB attachment with the firmware now available. It never writes an EEPROM or a configured MAC, and never resets the USB hub or MCU gadget. Unsupported devices are left unchanged.
