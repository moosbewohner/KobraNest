#!/usr/bin/python3
"""Install a restricted serial-only SSH service on an already configured USB Pi."""
import argparse,base64,json,os,re,shutil,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pi-user',required=True);p.add_argument('--key',type=Path,required=True);p.add_argument('--root',type=Path,default=Path('/'));p.add_argument('--transport',choices=['ecm'],default='ecm');a=p.parse_args()
root=a.root.resolve();source=Path(__file__).resolve().parent
assert re.fullmatch(r'[a-z_][a-z0-9_-]*[$]?',a.pi_user),'Invalid Pi user'
parts=a.key.read_text().strip().split();assert len(parts)>=2 and parts[0]=='ssh-ed25519' and len(base64.b64decode(parts[1],validate=True))==51,'Expected Ed25519 public key'
public=' '.join(parts[:2]);live=root==Path('/')
if live:
 assert os.geteuid()==0,'Run using sudo'
 import pwd
 pwd.getpwnam(a.pi_user)
 assert all(Path('/dev/ttyGS'+n).is_char_device() for n in ('0','1')),'USB MCU gadget missing; configure working USB MCU tunneling first'
 if a.transport=='serial':assert Path('/dev/ttyGS2').is_char_device(),'Third USB serial channel missing'
 else:
  assert Path('/sys/kernel/config/usb_gadget/klipper/configs/c.1/ecm.usb0').exists(),'New ECM gadget configuration is required'
  interfaces=json.loads(subprocess.check_output(['ip','-j','-4','address','show','dev','usb0'],text=True))
  assert any(x.get('local')=='10.55.0.1' for d in interfaces for x in d['addr_info']),'ECM ports.sh must already provide 10.55.0.1 on usb0'
 import urllib.request
 status=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?print_stats',timeout=5))['result']['status']['print_stats']['state']
 assert status in ('standby','complete','cancelled'),'Printer must be idle for setup'
 for name in ('ports.service','kobrian-usb-gadget.service'):
  if subprocess.run(['systemctl','cat',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
   gadget=name;break
 else:raise RuntimeError('No recognized USB startup service; configure ports.service first. Gadget unchanged.')
else:gadget='ports.service'
sshd='''# Managed by KobraNest serial link
Port 22
HostKey /etc/ssh/ssh_host_ed25519_key
UsePAM no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile /etc/kobranest-serial-link/authorized_keys
AllowUsers @USER@
AllowTcpForwarding yes
GatewayPorts clientspecified
PermitOpen 127.0.0.1:7125
PermitListen 127.0.0.1:17126 0.0.0.0:*
PermitTTY no
X11Forwarding no
AllowAgentForwarding no
PermitTunnel no
LoginGraceTime 20
ClientAliveInterval 10
ClientAliveCountMax 3
LogLevel ERROR
'''.replace('@USER@',a.pi_user)
if a.transport=='ecm':sshd=sshd.replace('Port 22\n','Port 2223\nListenAddress 10.55.0.1\n',1)
unit='''[Unit]
Description=KobraNest Moonraker and reverse web services over USB ECM
Requires=@GADGET@
Wants=network-online.target
After=@GADGET@ network-online.target
StartLimitIntervalSec=0
[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/lib/kobranest-serial-link/transport.py server
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
'''.replace('@GADGET@',gadget)
if a.transport=='ecm':unit=unit.replace('ExecStart=/usr/bin/python3 /usr/local/lib/kobranest-serial-link/transport.py server','ExecStartPre=/usr/bin/mkdir -p /run/sshd\nExecStart=/usr/sbin/sshd -D -e -f /etc/kobranest-serial-link/sshd_ecm_config')
paths={'etc/kobranest-serial-link/sshd_config':(sshd.encode(),0o600),'etc/kobranest-serial-link/authorized_keys':(('command="/bin/false",restrict,port-forwarding,permitopen="127.0.0.1:7125" '+public+'\n').encode(),0o644),'etc/systemd/system/kobranest-serial-link.service':(unit.encode(),0o644)}
existing=root/'etc/systemd/system/kobranest-serial-link.service'
if a.transport=='ecm':paths['etc/kobranest-serial-link/sshd_ecm_config']=paths.pop('etc/kobranest-serial-link/sshd_config')
drop=root/'etc/systemd/system/kobranest-serial-link.service.d/ecm.conf'
if a.transport=='serial':assert not drop.exists(),'Existing ECM override found; not switching transport automatically'
if existing.exists():assert any(marker in existing.read_text() for marker in ('KobraNest Moonraker and reverse web services over USB serial','KobraNest Moonraker and reverse web services over USB ECM')),'Unrecognized service; not overwritten'
changed=[];backup=root/'var/backups/kobranest-serial-link'/str(time.time_ns())
for name,(data,mode) in paths.items():
 target=root/name
 if target.exists() and target.read_bytes()==data:continue
 if target.exists():backup.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup/target.name)
 target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name(target.name+'.new');tmp.write_bytes(data);tmp.chmod(mode);os.replace(tmp,target);changed.append(name)
if live:
 subprocess.run(['/usr/sbin/sshd','-t','-f','/etc/kobranest-serial-link/'+('sshd_ecm_config' if a.transport=='ecm' else 'sshd_config')],check=True)
 subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['systemctl','enable','kobranest-serial-link.service'],check=True)
 if changed:subprocess.run(['systemctl','restart','kobranest-serial-link.service'],check=True)
 else:subprocess.run(['systemctl','start','kobranest-serial-link.service'],check=True)
print('Restricted ECM SSH service installed; original ports.sh, klipper.service and MCU tunnels preserved.')
