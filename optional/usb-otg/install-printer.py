#!/usr/bin/python3
"""Install optional support only; preserve selected mode, never restart anything."""
import argparse, os, pathlib, shutil
p=argparse.ArgumentParser()
p.add_argument('--root', required=True, help='Debian root directory, / only when installing on printer')
args=p.parse_args()
root=pathlib.Path(args.root).resolve()
source=pathlib.Path(__file__).resolve().parent
service=root/'usr/local/sbin/s1-service'
health=root/'usr/local/sbin/s1-health'
marker='# Optional USB OTG transport'
text=service.read_text()
h=health.read_text()
if marker not in text:
    needle='case "${1:-}" in'
    assert text.count(needle)==1, 'Unknown s1-service layout; no changes made'
    text=text.replace(needle, marker+'''
MODE=$(cat /etc/s1-tunnel-mode 2>/dev/null || echo network)
case "$MODE" in network|usb) ;; *) echo 'Invalid tunnel mode' >&2; exit 1 ;; esac
case "${1:-}:$MODE" in
    mcu1:usb|mcu2:usb)
        exec /usr/local/sbin/s1-usb-bridge "$1" >>"/var/log/$1-usb.log" 2>&1 ;;
esac
'''+needle)
if marker not in h and '# Local-only Kobrian boot health' not in h:
    needle='    for port in 0016 1B5B 1B5D; do'
    assert h.count(needle)==1, 'Unknown s1-health layout; no changes made'
    h=h.replace(needle, '''    # Optional USB OTG transport
    MODE=$(cat /etc/s1-tunnel-mode 2>/dev/null || echo network)
    PORTS="0016 1B5B 1B5D"
    case "$MODE" in
        usb)
            PORTS="0016"
            for name in mcu1 mcu2; do
                file=/run/s1/$name-usb.pid
                [ -r "$file" ] && kill -0 "$(cat "$file" 2>/dev/null)" 2>/dev/null || ok=0
            done ;;
        network) ;;
        *) ok=0 ;;
    esac
    for port in $PORTS; do''')
    h=h.replace('beide MCU-Listener', 'beide MCU-Tunnel')
def atomic(path, data, mode):
    tmp=path.with_name(path.name+'.usb-new')
    tmp.write_bytes(data);tmp.chmod(mode);os.replace(tmp,path)
for path,data in ((service,text),(health,h)):
    backup=path.with_name(path.name+'.before-usb')
    if not backup.exists(): shutil.copy2(path,backup)
    atomic(path,data.encode(),path.stat().st_mode & 0o777)
atomic(root/'usr/local/sbin/s1-usb-bridge', (source/'printer/s1-usb-bridge').read_bytes(),0o755)
mode=root/'etc/s1-tunnel-mode'
if not mode.exists(): atomic(mode,b'network\n',0o644)
os.sync()
print('Optional support installed. Mode preserved; no service started or restarted.')
