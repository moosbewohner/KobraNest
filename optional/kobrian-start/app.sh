#!/bin/sh
# Rinkhals one-shot launcher. No partition flashing, MCU reset or network changes.
set -e
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_ID=$(basename "$APP_DIR")
BASE=/useremain/s1-klipperscreen-test
ROOT=$BASE/rootfs
STATE=/tmp/kobrian-start
LOG=$STATE/app.log
TOOLS=/useremain/rinkhals/.current/tools.sh

remove_lock() {
    # Stock BusyBox may not provide the rmdir applet.
    # Use Python to remove only the empty lock directory.
    /usr/bin/python3 -c 'import os,sys
try: os.rmdir(sys.argv[1])
except FileNotFoundError: pass' "$STATE/lock"
}

message() {
    printf '%s\n' "$*"
}

check_installation() {
    [ -f "$ROOT/etc/s1-boot-ready" ] || { message 'Kobrian marker missing.'; return 1; }
    [ -x "$ROOT/bin/busybox" ] || { message 'Debian runtime missing.'; return 1; }
    [ -x "$ROOT/usr/local/sbin/s1-boot" ] || { message 'Kobrian boot script missing.'; return 1; }
    [ -x "$ROOT/usr/local/sbin/s1-health" ] || { message 'Boot health check missing.'; return 1; }
    grep -q 'Local-only Kobrian boot health' "$ROOT/usr/local/sbin/s1-health" || {
        message 'Please install the corrected local boot health check first.'; return 1;
    }
    [ "$(cat /sys/class/block/mmcblk0p7/size 2>/dev/null)" = 32768 ] || return 1
    [ "$(cat /sys/class/block/mmcblk0p9/size 2>/dev/null)" = 98304 ] || return 1
    message 'Kobrian installation and Slot B layout present. No filesystem or image integrity check performed.'
}

require_stock() {
    grep -q 'root=/dev/mmcblk0p8\([[:space:]]\|$\)' /proc/cmdline || {
        message 'Start only from Anycubic/Stock Slot A. No switch performed.'; return 1;
    }
    [ -x /usr/bin/rk_ota ] || { message 'Original boot tool (rk_ota) missing.'; return 1; }
}

worker_pid() {
    [ -r "$STATE/worker.pid" ] || return 1
    read -r pid started < "$STATE/worker.pid"
    case "$pid:$started" in *[!0-9:]*|:) return 1 ;; esac
    [ -r "/proc/$pid/stat" ] || return 1
    [ "$(awk '{print $22}' "/proc/$pid/stat")" = "$started" ] || return 1
    tr '\000' '\n' < "/proc/$pid/cmdline" | grep -Fqx -- "$APP_DIR/app.sh" || return 1
    tr '\000' '\n' < "/proc/$pid/cmdline" | grep -Fqx -- 'boot-once' || return 1
    printf '%s\n' "$pid"
}

status_app() {
    pid=$(worker_pid) || pid=
    if [ -n "$pid" ]; then message 'Status: started'; else message 'Status: stopped'; fi
    message "PIDs: $pid"
    message "Log: $LOG"
}

start_app_once() {
    require_stock || return 1
    check_installation || return 1
    [ -r "$TOOLS" ] || { message 'Rinkhals framework missing.'; return 1; }
    . "$TOOLS"
    [ "${KOBRA_MODEL_CODE:-}" = KS1 ] || { message 'This app is only for a verified Kobra S1.'; return 1; }
    confirmation=$(get_app_property "$APP_ID" boot_confirmation)
    idle=$(get_app_property "$APP_ID" idle_confirmed)
    if [ "$confirmation" != True ] || [ "$idle" != True ]; then
        message 'In app settings, set both options to True; then tap Start app.'
        return 0
    fi
    mkdir -p "$STATE"
    if worker_pid >/dev/null; then message 'Kobrian reboot already prepared.'; return 0; fi
    mkdir "$STATE/lock" 2>/dev/null || { message 'Launcher locked; stop app and try again.'; return 1; }
    launch_pid=
    start_cleanup() {
        if [ -n "$launch_pid" ]; then kill -TERM "$launch_pid" 2>/dev/null || true; fi
        rm -f "$STATE/armed" "$STATE/worker.pid"
        remove_lock
    }
    trap start_cleanup EXIT
    trap 'exit 1' TERM INT
    # Reset both persistent and temporary confirmation properties before
    # changing the boot configuration. This prevents reusing the confirmation.
    # Keep the helper calls in a conditional so set -e does not abort before
    # the failure handler can report an error.
    if set_app_property "$APP_ID" boot_confirmation False &&
       set_app_property "$APP_ID" idle_confirmed False &&
       set_temporary_app_property "$APP_ID" boot_confirmation False &&
       set_temporary_app_property "$APP_ID" idle_confirmed False &&
       disable_app "$APP_ID"; then
        :
    else
        message 'Failed to reset one-time confirmation. No switch performed.'
        return 1
    fi
    [ "$(get_app_property "$APP_ID" boot_confirmation)" = False ] &&
        [ "$(get_app_property "$APP_ID" idle_confirmed)" = False ] || {
        message 'One-time confirmation still active. No switch performed.'; return 1;
    }
    token=$(cat /proc/sys/kernel/random/uuid)
    printf '%s\n' "$token" > "$STATE/armed"
    chmod 600 "$STATE/armed"
    sync
    # The Rinkhals UI may time out while waiting for start() to finish.
    # Run the countdown in a separate session so it can continue independently.
    setsid "$APP_DIR/app.sh" boot-once "$token" </dev/null >"$LOG" 2>&1 &
    pid=$!
    launch_pid=$pid
    started=$(awk '{print $22}' "/proc/$pid/stat" 2>/dev/null) || started=
    [ -n "$started" ] || { message 'Failed to monitor reboot process.'; return 1; }
    printf '%s %s\n' "$pid" "$started" > "$STATE/worker.pid"
    trap - EXIT TERM INT
    message 'Confirmed. S1 will reboot into Kobrian in about 8 seconds. Stop app cancels the countdown.'
}

stop_app_once() {
    pid=$(worker_pid) || pid=
    if [ -n "$pid" ]; then kill -TERM "$pid" 2>/dev/null || true; fi
    rm -f "$STATE/armed" "$STATE/worker.pid"
    remove_lock
    message 'Pending start aborted. An already selected boot slot will not be reverted.'
}

boot_once() {
    [ -r "$STATE/armed" ] && [ -n "${1:-}" ] && [ "$(cat "$STATE/armed")" = "$1" ] || {
        message 'No valid one-time confirmation.'; return 1;
    }
    rm -f "$STATE/armed"
    trap 'rm -f "$STATE/worker.pid"; remove_lock' EXIT
    trap 'exit 0' TERM INT
    message 'Kobrian reboot scheduled. You have 8 seconds to cancel.'
    sleep 8
    require_stock || return 1
    check_installation || return 1
    history=$BASE/return-history
    mkdir -p "$history"
    tag=$(date +%s)-$$
    # Save a device-local copy of the misc partition before changing the boot slot.
    # Keep this diagnostic data outside the distributable application files.
    dd if=/dev/mmcblk0p5 of="$history/misc-before-$tag.img" bs=4096 count=64
    [ "$(wc -c < "$history/misc-before-$tag.img" | tr -d ' ')" = 262144 ] || return 1
    if [ -e "$BASE/boot-attempt" ]; then
        cp "$BASE/boot-attempt" "$history/boot-attempt-$tag.txt"
        rm "$BASE/boot-attempt"
    fi
    sync
    /usr/bin/rk_ota --misc=other --mode=retry
    sync
    message 'Slot B selected. Rebooting.'
    /sbin/reboot
}

case "${1:-}" in
    status) status_app ;;
    check) check_installation ;;
    start) start_app_once ;;
    stop) stop_app_once ;;
    boot-once) boot_once "${2:-}" ;;
    *) message "Usage: $0 {status|check|start|stop}"; exit 1 ;;
esac
