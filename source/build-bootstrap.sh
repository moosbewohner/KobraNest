#!/bin/sh
# Ausfuehrung nur in einem Build-Container mit /build als Arbeitsverzeichnis.
set -eu
cd /build
[ ! -e bootstrap-root-v6 ] || { echo "bootstrap-root-v6 existiert bereits" >&2; exit 1; }
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends squashfs-tools
unsquashfs -no-xattrs -d bootstrap-root-v6 system_a.original.img
# Nur die Init-Verknuepfung in der entpackten Kopie ersetzen.
[ -L bootstrap-root-v6/sbin/init ] || { echo "Unerwartete Original-init" >&2; exit 1; }
rm bootstrap-root-v6/sbin/init
cp bootstrap-init.sh bootstrap-root-v6/sbin/init
chmod 755 bootstrap-root-v6/sbin/init
mksquashfs bootstrap-root-v6 system_b.debian-bootstrap.img -comp xz -b 131072 -noappend -all-root -processors 1
size=$(stat -c %s system_b.debian-bootstrap.img)
[ "$size" -le 50331648 ]
unsquashfs -cat system_b.debian-bootstrap.img sbin/init > bootstrap-init.verified.sh
cmp bootstrap-init.sh bootstrap-init.verified.sh
sha256sum system_a.original.img system_b.debian-bootstrap.img > bootstrap-sha256.txt
