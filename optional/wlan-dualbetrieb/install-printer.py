#!/usr/bin/python3
"""Install support into an existing Debian root; credentials supplied separately."""
import argparse,json,os,pathlib,re,shutil
p=argparse.ArgumentParser()
p.add_argument('--root',required=True)
p.add_argument('--address',required=True,help='Existing printer IPv4/prefix')
p.add_argument('--gateway',required=True)
p.add_argument('--primary-interface',choices=['wlan0','eth1'],default='eth1')
a=p.parse_args()
import ipaddress
addr=ipaddress.IPv4Interface(a.address);gw=ipaddress.IPv4Address(a.gateway)
assert gw in addr.network
root=pathlib.Path(a.root).resolve();src=pathlib.Path(__file__).resolve().parent
boot=root/'usr/local/sbin/s1-boot';service=root/'usr/local/sbin/s1-service';init=root/'etc/inittab'
b=boot.read_text();s=service.read_text();i=init.read_text()
if '# WLAN fallback may boot' not in b:
    # Supports the packaged variable-IP variant and the initially deployed variant.
    pattern=r'\$BB ip addr add [^\n]+ dev eth1\n\$BB ip link set eth1 up\n\$BB ip route add default via [^\n]+'
    m=re.search(pattern,b)
    assert m, 'Unknown boot script; no changes made'
    lines=m.group().splitlines()
    b=b[:m.start()]+'# WLAN fallback may boot without USB LAN.\nif [ -d /sys/class/net/eth1 ]; then\n    '+lines[1]+'\n    '+lines[0]+'\n    '+lines[2]+'\nfi'+b[m.end():]
    b=b.replace('[ "$count" -lt 30 ]','[ "$count" -lt 5 ]')
# WLAN is the only configured IP when installed through Stock WLAN.
# Never assign that DHCP address to eth1 as well.
b=b.replace('while [ ! -d /sys/class/net/eth1 ]', 'while [ "${PRIMARY_INTERFACE:-eth1}" = eth1 ] && [ ! -d /sys/class/net/eth1 ]')
b=b.replace('if [ -d /sys/class/net/eth1 ]; then', 'if [ "${PRIMARY_INTERFACE:-eth1}" = eth1 ] && [ -d /sys/class/net/eth1 ]; then')
if '# Restore RTL8153 hardware MAC before addressing' not in b:
    needle='# WLAN fallback may boot without USB LAN.'
    assert needle in b
    b=b.replace(needle,'# Restore RTL8153 hardware MAC before addressing\n[ ! -x /usr/local/sbin/s1-realtek-init ] || /usr/local/sbin/s1-realtek-init || true\n'+needle)
if '# Load WLAN hardware before the GUI' not in b:
    needle='echo 30 > /run/s1/splash.progress'
    assert b.count(needle)==1
    b=b.replace(needle, '# Load WLAN hardware before the GUI checks for available radios.\n[ -d /sys/module/cfg80211 ] || $BB insmod /opt/s1-wifi/cfg80211.ko || true\n[ -d /sys/module/RTL8723DS ] || $BB insmod /opt/s1-wifi/RTL8723DS.ko || true\n'+needle)
if 's1-dual-network' not in s:
    needle='case "${1:-}" in';assert s.count(needle)==1
    s=s.replace(needle,needle+'\nnetwork)\n    exec /usr/local/sbin/s1-dual-network >>/var/log/s1-network.log 2>&1 ;;')
if 's1-service network' not in i:
    needle='::once:/usr/local/sbin/s1-health';assert i.count(needle)==1
    i=i.replace(needle,'::respawn:/usr/local/sbin/s1-service network\n'+needle)
def put(path,data,mode):
    tmp=path.with_name(path.name+'.wifi-new');tmp.write_bytes(data);tmp.chmod(mode);os.replace(tmp,path)
for path,data in ((boot,b),(service,s),(init,i)):
    backup=path.with_name(path.name+'.before-wifi')
    if not backup.exists():shutil.copy2(path,backup)
    put(path,data.encode(),path.stat().st_mode & 0o777)
network_conf=root/'etc/s1-network.conf'
if network_conf.exists():
    text=re.sub(r'^PRIMARY_INTERFACE=.*\n?','',network_conf.read_text(),flags=re.M)
    put(network_conf,(text.rstrip()+'\nPRIMARY_INTERFACE='+a.primary_interface+'\n').encode(),0o644)
if (src/'s1-realtek-init').is_file():
    put(root/'usr/local/sbin/s1-realtek-init',(src/'s1-realtek-init').read_bytes(),0o755)
if (src/'firmware/rtl_nic/rtl8153b-2.fw').is_file():
    target=root/'lib/firmware/rtl_nic/rtl8153b-2.fw';target.parent.mkdir(parents=True,exist_ok=True)
    put(target,(src/'firmware/rtl_nic/rtl8153b-2.fw').read_bytes(),0o644)
    target=root/'usr/local/share/licenses/realtek-firmware/LICENCE.rtlwifi_firmware.txt';target.parent.mkdir(parents=True,exist_ok=True)
    put(target,(src/'firmware/LICENCE.rtlwifi_firmware.txt').read_bytes(),0o644)
put(root/'usr/local/sbin/s1-dual-network',(src/'s1-dual-network').read_bytes(),0o755)
put(root/'usr/local/sbin/s1-wifi-dhcp',(src/'s1-wifi-dhcp').read_bytes(),0o755)
put(root/'etc/s1-dual-network.json',(json.dumps({'address':str(addr),'gateway':str(gw),'primary_interface':a.primary_interface})+'\n').encode(),0o600)
profile=root/'etc/wpa_supplicant/s1.conf'
if not profile.exists():
    profile.parent.mkdir(parents=True,exist_ok=True)
    put(profile,(src/'s1.conf.example').read_bytes(),0o600)
ping=root/'usr/bin/ping'
if not ping.exists():
    ping.parent.mkdir(parents=True,exist_ok=True)
    put(ping,b'#!/bin/sh\nexec /bin/busybox ping "$@"\n',0o755)
os.sync()
print('Support installed. No service restart. Supply original modules, packages and private WLAN configuration before enabling.')
