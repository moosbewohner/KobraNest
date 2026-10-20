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
    # Stock BusyBox has no rmdir applet. Remove only this empty directory.
    /usr/bin/python3 -c 'import os,sys
try: os.rmdir(sys.argv[1])
except FileNotFoundError: pass' "$STATE/lock"
}

message() {
    printf '%s\n' "$*"
}

check_installation() {
    [ -f "$ROOT/etc/s1-boot-ready" ] || { message 'Kobrian-Kennung fehlt.'; return 1; }
    [ -x "$ROOT/bin/busybox" ] || { message 'Debian-Laufzeit fehlt.'; return 1; }
    [ -x "$ROOT/usr/local/sbin/s1-boot" ] || { message 'Kobrian-Startskript fehlt.'; return 1; }
    [ -x "$ROOT/usr/local/sbin/s1-health" ] || { message 'Startpruefung fehlt.'; return 1; }
    grep -q 'Local-only Kobrian boot health' "$ROOT/usr/local/sbin/s1-health" || {
        message 'Bitte zuerst die korrigierte lokale Startpruefung installieren.'; return 1;
    }
    [ "$(cat /sys/class/block/mmcblk0p7/size 2>/dev/null)" = 32768 ] || return 1
    [ "$(cat /sys/class/block/mmcblk0p9/size 2>/dev/null)" = 98304 ] || return 1
    message 'Kobrian-Installation und Slot-B-Layout vorhanden. Keine Dateisystem- oder Image-Integritaetspruefung ausgefuehrt.'
}

require_stock() {
    grep -q 'root=/dev/mmcblk0p8\([[:space:]]\|$\)' /proc/cmdline || {
        message 'Nur aus Anycubic/Stock-Slot A starten. Keine Umschaltung ausgefuehrt.'; return 1;
    }
    [ -x /usr/bin/rk_ota ] || { message 'Originales Boot-Werkzeug fehlt.'; return 1; }
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
    [ -r "$TOOLS" ] || { message 'Rinkhals-Framework fehlt.'; return 1; }
    . "$TOOLS"
    [ "${KOBRA_MODEL_CODE:-}" = KS1 ] || { message 'Nur fuer den geprueften Kobra S1.'; return 1; }
    confirmation=$(get_app_property "$APP_ID" boot_confirmation)
    idle=$(get_app_property "$APP_ID" idle_confirmed)
    if [ "$confirmation" != KOBRIAN ] || [ "$idle" != True ]; then
        message 'In den App-Einstellungen KOBRIAN eingeben und Kein Druck aktiv auf True setzen; danach Start app.'
        return 0
    fi
    mkdir -p "$STATE"
    if worker_pid >/dev/null; then message 'Kobrian-Neustart bereits vorbereitet.'; return 0; fi
    mkdir "$STATE/lock" 2>/dev/null || { message 'Starter gesperrt; App stoppen und erneut versuchen.'; return 1; }
    launch_pid=
    start_cleanup() {
        if [ -n "$launch_pid" ]; then kill -TERM "$launch_pid" 2>/dev/null || true; fi
        rm -f "$STATE/armed" "$STATE/worker.pid"
        remove_lock
    }
    trap start_cleanup EXIT
    trap 'exit 1' TERM INT
    # Consume both persistent and temporary properties BEFORE changing boot control.
    # Rinkhals helpers intentionally tolerate a missing config file. Calling
    # them in a conditional preserves that behaviour with our own set -e.
    if set_app_property "$APP_ID" boot_confirmation '' &&
       set_app_property "$APP_ID" idle_confirmed False &&
       set_temporary_app_property "$APP_ID" boot_confirmation '' &&
       set_temporary_app_property "$APP_ID" idle_confirmed False &&
       disable_app "$APP_ID"; then
        :
    else
        message 'Einmal-Freigabe konnte nicht zurueckgesetzt werden. Keine Umschaltung.'
        return 1
    fi
    [ -z "$(get_app_property "$APP_ID" boot_confirmation)" ] &&
        [ "$(get_app_property "$APP_ID" idle_confirmed)" = False ] || {
        message 'Einmal-Freigabe ist noch aktiv. Keine Umschaltung.'; return 1;
    }
    token=$(cat /proc/sys/kernel/random/uuid)
    printf '%s\n' "$token" > "$STATE/armed"
    chmod 600 "$STATE/armed"
    sync
    # Rinkhals UI gives start() five seconds; the worker must outlive that call.
    setsid "$APP_DIR/app.sh" boot-once "$token" </dev/null >"$LOG" 2>&1 &
    pid=$!
    launch_pid=$pid
    started=$(awk '{print $22}' "/proc/$pid/stat" 2>/dev/null) || started=
    [ -n "$started" ] || { message 'Neustartauftrag konnte nicht ueberwacht werden.'; return 1; }
    printf '%s %s\n' "$pid" "$started" > "$STATE/worker.pid"
    trap - EXIT TERM INT
    message 'Bestaetigt. S1 startet in etwa acht Sekunden mit Kobrian. Stop app bricht die Wartezeit ab.'
}

stop_app_once() {
    pid=$(worker_pid) || pid=
    if [ -n "$pid" ]; then kill -TERM "$pid" 2>/dev/null || true; fi
    rm -f "$STATE/armed" "$STATE/worker.pid"
    remove_lock
    message 'Ausstehender Start abgebrochen. Ein bereits gesetzter Boot-Slot wird nicht rueckgaengig gemacht.'
}

boot_once() {
    [ -r "$STATE/armed" ] && [ -n "${1:-}" ] && [ "$(cat "$STATE/armed")" = "$1" ] || {
        message 'Keine gueltige Einmal-Freigabe.'; return 1;
    }
    rm -f "$STATE/armed"
    trap 'rm -f "$STATE/worker.pid"; remove_lock' EXIT
    trap 'exit 0' TERM INT
    message 'Kobrian-Neustart vorgemerkt; acht Sekunden Abbruchzeit.'
    sleep 8
    require_stock || return 1
    check_installation || return 1
    history=$BASE/return-history
    mkdir -p "$history"
    tag=$(date +%s)-$$
    # Device-specific diagnostics stay on this device, not in the distributable app.
    dd if=/dev/mmcblk0p5 of="$history/misc-before-$tag.img" bs=4096 count=64
    [ "$(wc -c < "$history/misc-before-$tag.img" | tr -d ' ')" = 262144 ] || return 1
    if [ -e "$BASE/boot-attempt" ]; then
        cp "$BASE/boot-attempt" "$history/boot-attempt-$tag.txt"
        rm "$BASE/boot-attempt"
    fi
    sync
    /usr/bin/rk_ota --misc=other --mode=retry
    sync
    message 'Slot B ausgewaehlt. Neustart.'
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
