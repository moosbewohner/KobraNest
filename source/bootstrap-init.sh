#!/bin/sh
# Kandidat fuer /sbin/init im kleinen Hersteller-SquashFS.
# Fehlende Kandidatenwurzel fuehrt zum bisherigen BusyBox-Start zurueck.
BB=/bin/busybox
$BB mount -t devtmpfs devtmpfs /dev || true
$BB mount -t proc proc /proc 2>/dev/null || true
$BB mount -t sysfs sysfs /sys 2>/dev/null || true
fallback() {
    # Vor dem Pivot laeuft noch die originale uClibc-Umgebung.
    $BB mkdir -p /dev/block/by-name
    $BB ln -sf /dev/mmcblk0p5 /dev/block/by-name/misc
    if /usr/bin/rk_ota --misc=other --mode=retry; then
        $BB sync
        $BB reboot -f
    fi
    exec "$BB" init
}
$BB mount -t tmpfs -o mode=1777,size=8m tmpfs /tmp || fallback
STORAGE=/tmp/s1-bootstrap/storage
NEWROOT=/tmp/s1-bootstrap/newroot
$BB mkdir -p "$STORAGE" "$NEWROOT" || fallback
$BB mount -t ext4 /dev/mmcblk0p17 "$STORAGE" || fallback
ROOT=$STORAGE/s1-klipperscreen-test/rootfs
[ -f "$ROOT/etc/s1-boot-ready" ] || fallback
[ -x "$ROOT/bin/busybox" ] || fallback
# Ein fehlgeschlagener Erststart faellt beim naechsten Einschalten auf Stock zurueck.
ATTEMPT=$STORAGE/s1-klipperscreen-test/boot-attempt
[ ! -e "$ATTEMPT" ] || fallback
echo starting > "$ATTEMPT"
$BB sync
$BB mount -o bind "$ROOT" "$NEWROOT" || fallback
$BB mkdir -p "$NEWROOT/.oldroot" || fallback
"$NEWROOT/bin/busybox" mount --make-rprivate / || fallback
for fs in dev proc sys; do
    "$NEWROOT/bin/busybox" mount -o bind "/$fs" "$NEWROOT/$fs" || fallback
done
cd "$NEWROOT" || fallback
"$NEWROOT/bin/busybox" pivot_root . .oldroot || fallback
exec /bin/busybox chroot . /bin/busybox init
