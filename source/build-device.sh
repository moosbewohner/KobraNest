#!/bin/sh
# Runs in an isolated Docker build directory with the device's own system_a image.
set -eu
cd /build
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends squashfs-tools
unsquashfs -no-xattrs -d original system_a.img
[ -L original/sbin/init ]
mkdir -p runtime/opt/rockchip-bootcontrol runtime/usr/lib
cp -L original/usr/bin/rk_ota runtime/opt/rockchip-bootcontrol/rk_ota
for name in ld-uClibc.so.0 libc.so.0 libgcc_s.so.1; do
    cp -L "original/lib/$name" "runtime/opt/rockchip-bootcontrol/$name"
done
cp runtime/opt/rockchip-bootcontrol/ld-uClibc.so.0 runtime/usr/lib/ld-uClibc.so.0
cp runtime/opt/rockchip-bootcontrol/ld-uClibc.so.0 runtime/usr/lib/ld-uClibc.so.1
chmod 755 runtime/opt/rockchip-bootcontrol/* runtime/usr/lib/*
tar czf bootcontrol.tar.gz -C runtime .
rm original/sbin/init
cp bootstrap-init.sh original/sbin/init
chmod 755 original/sbin/init
mksquashfs original bootstrap.img -comp xz -b 131072 -noappend -all-root -processors 1
[ "$(stat -c %s bootstrap.img)" -le 50331648 ]
unsquashfs -cat bootstrap.img sbin/init >init.verified
cmp bootstrap-init.sh init.verified
sha256sum bootstrap.img bootcontrol.tar.gz
