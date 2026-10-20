#!/usr/bin/python3
"""Discover Stock access and copy its WLAN profile only inside the printer."""
import argparse,ipaddress,json,os,re,socket,struct
from pathlib import Path

PROFILE_PATHS=('/userdata/wifi_cfg/wpa_supplicant.conf','/useremain/home/wpa_supplicant.conf')

def sanitize_profile(text):
    # Keep complete network blocks; discard Stock socket paths and global includes.
    blocks=[];start=None;depth=0;quoted=False;escaped=False;comment=False
    for i,ch in enumerate(text):
        if comment:
            if ch=='\n':comment=False
            else:continue
        if escaped:escaped=False;continue
        if ch=='\\' and quoted:escaped=True;continue
        if ch=='"':quoted=not quoted;continue
        if not quoted and ch=='#':comment=True;continue
        if quoted:continue
        if ch=='{':
            if depth==0:
                if not re.search(r'network\s*=\s*$',text[:i]):raise ValueError('Unsupported WLAN profile')
                start=i
            depth+=1
        elif ch=='}':
            depth-=1
            if depth<0:raise ValueError('Unsupported WLAN profile')
            if depth==0:blocks.append('network='+text[start:i+1])
    if quoted or depth or not blocks:raise ValueError('No usable saved WLAN profile')
    for block in blocks:
        if not re.search(r'^\s*ssid\s*=\s*\S',block,re.M):raise ValueError('Unsupported WLAN profile')
        if re.search(r'^\s*(?:ca_cert|ca_path|client_cert|private_key|pac_file|include)\s*=',block,re.M):raise ValueError('Certificate-based WLAN needs manual setup')
        km=re.search(r'^\s*key_mgmt\s*=\s*([^\n#]+)',block,re.M)
        if km and not set(km[1].split()) <= {'WPA-PSK','WPA-PSK-SHA256','SAE','NONE'}:raise ValueError('Unsupported WLAN authentication')
    country=re.search(r'^\s*country\s*=\s*([A-Z]{2})\s*$',text,re.M)
    return 'ctrl_interface=/run/wpa_supplicant\nupdate_config=1\n'+('country='+country[1]+'\n' if country else '')+'\n'.join(blocks)+'\n'

def discover(host):
    import fcntl
    address=str(ipaddress.IPv4Address(host));matches=[]
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        for name in ('wlan0','eth1'):
            try:raw=fcntl.ioctl(sock.fileno(),0x8915,struct.pack('256s',name.encode()));ip=socket.inet_ntoa(raw[20:24])
            except OSError:continue
            if ip==address:matches.append(name)
    if len(matches)!=1:raise ValueError('Installation IP must belong to exactly one WLAN or LAN interface')
    profile=None
    if matches[0]=='wlan0':
        for name in PROFILE_PATHS:
            path=Path(name)
            if path.is_file():profile=sanitize_profile(path.read_text(encoding='utf-8'));break
        if profile is None:raise ValueError('Saved Anycubic WLAN profile not found')
    return matches[0],profile

def main():
    p=argparse.ArgumentParser();p.add_argument('--host',required=True);p.add_argument('--root');a=p.parse_args()
    interface,profile=discover(a.host)
    if a.root:
        root=Path(a.root).resolve()
        assert root!=Path('/') and (root/'etc/s1-settings.json').is_file(),'Expected inactive Kobrian root'
        if profile is not None:
            target=root/'etc/wpa_supplicant/s1.conf';target.parent.mkdir(parents=True,exist_ok=True)
            pending=target.with_suffix('.stock-new');pending.write_text(profile,encoding='utf-8');pending.chmod(0o600);os.replace(pending,target)
        conf=root/'etc/s1-network.conf';text=conf.read_text(encoding='utf-8');text=re.sub(r'^PRIMARY_INTERFACE=.*\n?','',text,flags=re.M);conf.write_text(text.rstrip()+'\nPRIMARY_INTERFACE='+interface+'\n',encoding='utf-8')
        (root/'etc/s1-primary-interface').write_text(interface+'\n',encoding='utf-8')
        helix=root/'opt/helixscreen/config/settings.json'
        if profile is not None and helix.is_file():
            data=json.loads(helix.read_text(encoding='utf-8'));data.update(wifi_enabled=True,wifi_expected=True)
            pending=helix.with_suffix('.wifi-new');pending.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');pending.chmod(0o600);os.replace(pending,helix)
        os.sync()
    print(json.dumps({'interface':interface,'saved_wifi':profile is not None,'address_mode':'dhcp' if profile is not None else 'static'}))

if __name__=='__main__':
    try:main()
    except Exception:
        raise SystemExit('Stock network preparation failed. Check interface and saved WLAN profile; credentials were not logged.')
