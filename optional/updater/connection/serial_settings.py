"""Private, transactional configuration for the serial SSH forwards."""
from pathlib import Path
import json,os,secrets,time,ipaddress,re
CONFIG=Path('/etc/s1-serial-link.json')
PENDING=Path('/etc/s1-serial-link.pending.json')
LAST=Path('/run/s1/serial-link-last.json')
PEER=Path('/etc/s1-serial-peer.json')
def pi_host():
 return str(ipaddress.IPv4Address(json.loads(Path('/etc/s1-settings.json').read_text())['pi_ip']))
def peer():
 value=json.loads(PEER.read_text())
 if not re.fullmatch(r'[a-z_][a-z0-9_-]*[$]?',value.get('pi_user','')):raise ValueError('Invalid Pi account')
 if value.get('transport','ecm')!='ecm':raise ValueError('This setup requires ECM')
 return value
DEFAULTS={'moonraker_enabled':True,'light_enabled':True,'web_enabled':True,'web_port':18080,'helix_enabled':True,'helix_port':7130,'ssh_enabled':True,'ssh_port':2222}

def atomic(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.new')
 with tmp.open('w') as f:
  os.chmod(tmp,0o600);json.dump(value,f);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
 if os.name!='nt':
  directory=os.open(str(path.parent),os.O_RDONLY)
  try:os.fsync(directory)
  finally:os.close(directory)
def validate(value):
 if not isinstance(value,dict) or set(value)!=set(DEFAULTS):raise ValueError('Unvollständige USB-Einstellungen.')
 for key,default in DEFAULTS.items():
  if isinstance(default,bool):
   if type(value[key]) is not bool:raise ValueError('Ungültiger Schalterwert.')
  elif type(value[key]) is not int or not 1024<=value[key]<=65535:raise ValueError('Ports müssen zwischen 1024 und 65535 liegen.')
 ports=[value[k+'_port'] for k in ('web','helix','ssh') if value[k+'_enabled']]
 if len(ports)!=len(set(ports)):raise ValueError('Jede aktivierte Weiterleitung benötigt einen eigenen Port.')
 if any(x in (7125,8088,17126,2223) for x in ports):raise ValueError('Dieser Port ist für Moonraker, Kamera oder Licht reserviert.')
 return dict(value)
def load():
 if not CONFIG.exists():return dict(DEFAULTS)
 return validate(json.loads(CONFIG.read_text()))
def bootid():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def pending():
 try:return json.loads(PENDING.read_text())
 except FileNotFoundError:return None

def expire():
 p=pending()
 if p and (p['boot_id']!=bootid() or time.monotonic()>=p['deadline']):
  atomic(CONFIG,validate(p['previous']));PENDING.unlink(missing_ok=True)
  atomic(LAST,{'result':'rolled_back','time':time.time()});return True
 return False

def begin(value):
 expire()
 if pending():raise ValueError('Bitte die ausstehende Verbindung zuerst bestätigen oder zurücksetzen.')
 value=validate(value);old=load()
 if old==value:raise ValueError('Die Einstellungen sind unverändert.')
 p={'previous':old,'boot_id':bootid(),'deadline':time.monotonic()+90,'token':secrets.token_urlsafe(24)}
 atomic(PENDING,p)
 try:atomic(CONFIG,value)
 except Exception:PENDING.unlink(missing_ok=True);raise
 return status()
def confirm(token):
 expire();p=pending()
 if not p:raise ValueError('Keine ausstehende Änderung.')
 if not isinstance(token,str) or not secrets.compare_digest(token,p['token']):raise ValueError('Ungültige Bestätigung. Seite neu laden.')
 if not status()['connected']:raise ValueError('USB-Verbindung wird noch aufgebaut.')
 PENDING.unlink();atomic(LAST,{'result':'confirmed','time':time.time()})
 return status()
def rollback():
 p=pending()
 if not p:raise ValueError('Keine ausstehende Änderung.')
 atomic(CONFIG,validate(p['previous']));PENDING.unlink();atomic(LAST,{'result':'rolled_back','time':time.time()})
 return status()
def status():
 p=pending()
 try:
  active=json.loads(Path('/run/s1/serial-link-active.json').read_text());connected=active['settings']==load() and Path('/proc/'+str(active['pid'])).exists()
 except (OSError,ValueError,KeyError):connected=False
 try:last=json.loads(LAST.read_text())
 except (OSError,ValueError):last={}
 return {'installed':PEER.exists(),'connected':connected,'settings':load(),'pi_host':pi_host(),'pending':bool(p),'remaining':max(0,int(p['deadline']-time.monotonic())) if p else 0,'token':p['token'] if p else None,'last_result':last.get('result')}
def moonraker_host(fallback):
 mode=Path('/etc/s1-tunnel-mode')
 return '127.0.0.1' if mode.exists() and mode.read_text().strip()=='usb' and Path('/etc/s1-serial-link.enabled').exists() and load()['moonraker_enabled'] else fallback

def command(settings):
 v=validate(settings);p=peer()
 cmd=['ssh','-o','ControlMaster=yes','-o','ControlPath=/run/s1/serial-link-control','-N','-T','-i','/root/.ssh/kobranest_serial','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile=/root/.ssh/kobranest_serial_known_hosts','-o','HostKeyAlias=kobranest-pi-serial','-o','ConnectTimeout=20','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=3']
 if v['moonraker_enabled']:cmd+=['-L','127.0.0.1:7125:127.0.0.1:7125']
 if v['light_enabled']:cmd+=['-R','127.0.0.1:17126:127.0.0.1:7126']
 for name,target in (('web',8080),('helix',7130),('ssh',22)):
  if v[name+'_enabled']:cmd+=['-R',f"0.0.0.0:{v[name+'_port']}:127.0.0.1:{target}"]
 return cmd+['-p','2223',p['pi_user']+'@10.55.0.1']
if __name__=='__main__':
 import sys
 if len(sys.argv)>1 and sys.argv[1]=='moonraker-host':
  p=Path('/etc/s1-web.json');p=p if p.exists() else Path('/etc/s1-settings.json')
  print(moonraker_host(json.loads(p.read_text())['pi_ip']))
