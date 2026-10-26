"""One explicit, resumable setup for signed runtime updates and ECM configuration."""
import hashlib,json,os,shlex,subprocess,sys,tarfile,time
from pathlib import Path
NUMBER=(Path(__file__).resolve().parent/'RELEASE_VERSION').read_text().strip()

def package_path(here,kind):return here/'packages'/('KobraNest-'+kind+'-update-'+NUMBER+'.tar.gz')

def validate_bundle(here):
 for kind in ('pi','printer'):
  path=package_path(here,kind)
  if not path.is_file():raise ValueError('Use the COMPLETE release ZIP; missing '+str(path))
  with tarfile.open(path,'r:gz') as tar:
   raw=tar.extractfile('manifest.json').read();signature=tar.extractfile('manifest.sig').read();manifest=json.loads(raw)
   if manifest.get('version')!=NUMBER or manifest.get('platform')!=kind:raise ValueError('Wrong bundled update version/platform')
  import tempfile
  with tempfile.TemporaryDirectory() as tmp:
   data=Path(tmp)/'manifest';sig=Path(tmp)/'signature';data.write_bytes(raw);sig.write_bytes(signature)
   subprocess.run(['openssl','pkeyutl','-verify','-pubin','-inkey',str(here/'release.pub'),'-rawin','-in',str(data),'-sigfile',str(sig)],check=True,stdout=subprocess.DEVNULL)

def needs_update(info,kind):
 if info.get('platform')!=kind:raise ValueError('Installed updater platform does not match '+kind)
 v=tuple(map(int,info['version'].split('.')));target=tuple(map(int,NUMBER.split('.')))
 if v>target:raise ValueError('Newer '+kind+' version installed; use a newer complete setup')
 return v<target

def update_local(here,kind):
 info=json.loads(Path('/usr/share/kobranest-update/version.json').read_text())
 if not needs_update(info,kind):print(kind+' already at '+NUMBER+'; checking configuration next.');return
 for action,args in [('stage',['--package',str(package_path(here,kind))]),('apply',['--confirmation','YES'])]:
  subprocess.run(['/usr/local/sbin/s1-update',action,*args],check=True)

def repair_remote(remote,directory):
 # Repair legacy/mixed modules before using their CLI; preserve all existing versions.
 script="""import ast,json,subprocess,sys
from pathlib import Path
p=Path('/usr/share/kobranest-update/version.json')
v=json.loads(p.read_text()) if p.exists() else None
if v and v.get('platform')!='printer':raise ValueError('Wrong printer version platform')
release=(Path(sys.argv[1])/'RELEASE_VERSION').read_text().strip()
if not v or tuple(map(int,v['version'].split('.'))) < tuple(map(int,release.split('.'))):
 subprocess.run([sys.executable,sys.argv[1]+'/repair.py','--restart-web'],check=True)
else:
 p=Path('/usr/local/lib/kobranest-update/updater.py')
 names={n.name for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
 if not {'boot_recover','status','launch','recover'}<=names:raise ValueError('Newer but incomplete updater; matching repair needed')
"""
 remote('python3 -c '+shlex.quote(script)+' '+shlex.quote(directory))

def update_remote(here,remote,directory):
 info=json.loads(remote('cat /usr/share/kobranest-update/version.json'))
 if not needs_update(info,'printer'):print('Printer runtime already at '+NUMBER);return
 dest=directory+'/printer-update.tar.gz'
 remote('cat > '+shlex.quote(dest),package_path(here,'printer').read_bytes())
 print(remote('/usr/local/sbin/s1-update stage --package '+shlex.quote(dest)).decode())
 print(remote('/usr/local/sbin/s1-update apply --confirmation YES').decode())

def verify(remote,helper,here):
 import urllib.request
 subprocess.run(['systemctl','is-active','--quiet','kobranest-serial-link.service'],check=True)
 printer=json.loads(remote('cat /usr/share/kobranest-update/version.json'))
 pi=json.loads(Path('/usr/share/kobranest-update/version.json').read_text())
 for info,kind in ((printer,'printer'),(pi,'pi')):
  if needs_update(info,kind):raise ValueError(kind+' runtime update is incomplete')
 status=json.loads(remote(helper+' --status'))
 if not status['connected']:raise ValueError('ECM SSH connection is not active')
 # Query Moonraker through the printer's INTERNAL USB forward, not WLAN/LAN.
 command="python3 -c "+shlex.quote("import json,urllib.request; print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:7125/server/info',timeout=8))))")
 moonraker=json.loads(remote(command))
 if not isinstance(moonraker.get('result'),dict):raise ValueError('Moonraker over ECM did not respond')
 settings=status['settings'];links={}
 for enabled,port,path in [('web_enabled','web_port','/api/setup'),('helix_enabled','helix_port','/')]:
  if settings[enabled]:
   with urllib.request.urlopen('http://127.0.0.1:'+str(settings[port])+path,timeout=8) as response:
    if response.status!=200:raise ValueError('Forward check failed: '+port)
   links[port]=settings[port]
 if settings['light_enabled']:
  with urllib.request.urlopen('http://127.0.0.1:17126/light/status',timeout=8) as response:json.load(response)
 if settings['ssh_enabled']:
  import socket
  with socket.create_connection(('127.0.0.1',settings['ssh_port']),timeout=5) as conn:
   if not conn.recv(256).startswith(b'SSH-'):raise ValueError('Printer SSH forwarding is not responding')
 receipt={'version':NUMBER,'time':time.time(),'transport':'ecm','configuration_complete':True,'forward_settings':settings,'runtime_platforms':['printer','pi'],'checks':['restricted-sshd','ecm-link','moonraker-through-usb','enabled-forwards']}
 dest=Path('/var/lib/kobranest-updates/complete-setup.json');dest.parent.mkdir(parents=True,exist_ok=True)
 tmp=dest.with_suffix('.new');tmp.write_text(json.dumps(receipt,indent=2)+'\n');tmp.chmod(0o600);os.replace(tmp,dest)
 print('COMPLETE '+NUMBER+': both runtimes, ECM SSH service, settings and enabled forwards verified. Receipt: '+str(dest))
