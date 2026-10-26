#!/usr/bin/env python3
import argparse,base64,json,os,re,shutil,signal,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--apply');p.add_argument('--status',action='store_true');p.add_argument('--transport',choices=['ecm'],default='ecm');a=p.parse_args()
assert os.geteuid()==0,'Printer root required'
if a.status:
 sys.path.insert(0,'/usr/local/lib/kobranest-serial-link');import serial_settings
 print(json.dumps(serial_settings.status()));sys.exit(0)
assert Path('/etc/s1-boot-ready').is_file(),'Running KobraNest required'
assert Path('/etc/s1-tunnel-mode').read_text().strip()=='usb','Configure working USB MCU tunneling first'
if a.transport=='serial':
 assert not Path('/etc/s1-usb-ecm.enabled').exists(),'ECM installation found; not switching to serial'
 assert len(list(Path('/sys/class/tty').glob('ttyACM*')))>=3,'Third USB serial channel missing'
else:
 assert any((net/'address').read_text().strip().lower()=='02:4b:53:31:00:02' for net in Path('/sys/class/net').iterdir()),'Printer ECM interface missing; restart printer after Pi, then retry'
for exe in ('ssh','ssh-keygen','python3'):assert shutil.which(exe),'Missing '+exe
key=Path('/root/.ssh/kobranest_serial')
if a.prepare:
 key.parent.mkdir(exist_ok=True);key.parent.chmod(0o700)
 if not key.exists():subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)],check=True)
 result=subprocess.check_output(['ssh-keygen','-y','-f',str(key)],text=True).strip()
 print(' '.join(result.split()[:2]));sys.exit(0)
assert a.apply,'Expected --prepare, --apply or --status'
peer=json.loads(base64.b64decode(a.apply,validate=True));assert re.fullmatch(r'[a-z_][a-z0-9_-]*[$]?',peer['pi_user'])
import ipaddress
peer['pi_ip']=str(ipaddress.IPv4Address(peer['pi_ip']))
parts=peer['host_key'].split();assert len(parts)==2 and parts[0]=='ssh-ed25519' and len(base64.b64decode(parts[1],validate=True))==51
assert key.exists(),'Prepare key first'
source=Path(__file__).resolve().parent;backup=Path('/var/backups/kobranest-usb-ssh-tester')/str(time.time_ns());backup.mkdir(parents=True)
paths=['etc/inittab','etc/s1-web.json','etc/s1-settings.json','etc/KlipperScreen.conf','etc/s1-serial-peer.json','etc/s1-serial-link.enabled','etc/s1-usb-ecm.enabled','usr/local/sbin/s1-usb-ecm','usr/local/sbin/s1-web','usr/local/sbin/s1-gui','usr/local/sbin/s1-helix','usr/local/sbin/s1-light','usr/local/sbin/s1-klipper-autorecover','usr/local/sbin/s1-serial-link','usr/local/lib/kobranest-serial-link','root/.ssh/kobranest_serial_known_hosts']
for name in paths:
 target=Path('/')/name
 if target.exists():
  dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True)
  if target.is_dir():shutil.copytree(target,dest)
  else:shutil.copy2(target,dest)
subprocess.run([sys.executable,str(source/'install-printer.py'),'--root','/'],check=True,stdout=sys.stderr)
for name in ('etc/s1-settings.json','etc/s1-web.json'):
 path=Path('/')/name
 if path.exists():
  value=json.loads(path.read_text());value['pi_ip']=peer['pi_ip'];path.write_text(json.dumps(value)+'\n')
Path('/etc/s1-serial-peer.json').write_text(json.dumps({'pi_user':peer['pi_user'],'transport':a.transport})+'\n');Path('/etc/s1-serial-peer.json').chmod(0o600)
if a.transport=='ecm':
 shutil.copy2(source/'s1-usb-ecm','/usr/local/sbin/s1-usb-ecm');Path('/usr/local/sbin/s1-usb-ecm').chmod(0o755)
 Path('/etc/s1-usb-ecm.enabled').touch()
 table=Path('/etc/inittab');text=table.read_text();line='::respawn:/usr/local/sbin/s1-usb-ecm >>/var/log/s1-usb-ecm.log 2>&1'
 if line not in text:table.write_text(text.rstrip()+'\n'+line+'\n')
web=Path('/usr/local/sbin/s1-web')
if web.exists():
 text=web.read_text();old="'http://' + PI + ':7125'"
 if old in text:text=text.replace(old,"'http://' + ('127.0.0.1' if Path('/etc/s1-serial-link.enabled').exists() and read('/etc/s1-tunnel-mode')=='usb' else PI) + ':7125'");compile(text,str(web),'exec');web.write_text(text)
known=Path('/root/.ssh/kobranest_serial_known_hosts');known.write_text('kobranest-pi-serial '+peer['host_key']+'\n');known.chmod(0o600)
helix=Path('/usr/local/sbin/s1-helix')
if helix.exists():
 text=helix.read_text();line='PI_IP=$(/usr/bin/python3 /usr/local/lib/kobranest-serial-link/serial_settings.py moonraker-host)'
 if line not in text:
  assert 'HP=' in text,'Unrecognized Helix wrapper; restore from backup before retry'
  helix.write_text(text.replace('HP=',line+'\nHP=',1))
Path('/etc/s1-serial-link.enabled').touch();os.sync();os.kill(1,signal.SIGHUP)
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  args=(proc/'cmdline').read_bytes().split(b'\0')
  if len(args)>1 and args[1] in (b'/usr/local/sbin/s1-serial-link',b'/usr/local/sbin/s1-helix',b'/usr/local/sbin/s1-gui',b'/usr/local/sbin/s1-light',b'/usr/local/sbin/s1-web'):os.kill(int(proc.name),signal.SIGTERM)
 except OSError:pass
print('Printer configured. Backup: '+str(backup))
