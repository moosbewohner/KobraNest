#!/usr/bin/env python3
"""One-time updater setup for Pi and printer; run on the Pi using setup.sh."""
import argparse,base64,io,ipaddress,json,os,re,shlex,shutil,subprocess,sys,tarfile,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
FILES=('RELEASE_VERSION','bootstrap.sh','install.py','repair.py','patch_web.py','s1-update','s1-time-sync','updater.py','release.pub')

def printer_public_key(output):
 # OpenSSH may retain a trailing comment when deriving a public key with -y.
 lines=output.decode('utf-8').strip().splitlines()
 if len(lines)!=1:raise ValueError('Invalid printer public key: expected one OpenSSH key line')
 parts=lines[0].split()
 if len(parts)<2 or parts[0]!='ssh-ed25519':raise ValueError('Invalid printer public key: expected Ed25519')
 try:raw=base64.b64decode(parts[1],validate=True)
 except ValueError as error:raise ValueError('Invalid printer public key encoding') from error
 if len(raw)!=51 or raw[:19]!=b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20':raise ValueError('Invalid printer public key structure')
 return ' '.join(parts[:2])
def package():
 result=io.BytesIO()
 with tarfile.open(fileobj=result,mode='w:gz') as tar:
  for name in FILES:tar.add(HERE/name,arcname=name)
  for path in sorted((HERE/'connection').iterdir()):
   if path.is_file() and path.suffix!='.pyc' and path.name!='transport.py':tar.add(path,arcname='connection/'+path.name)
 return result.getvalue()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--printer');parser.add_argument('--pi-user');parser.add_argument('--pi-address');parser.add_argument('--check',action='store_true');parser.add_argument('--prepare-ecm',action='store_true');parser.add_argument('--complete',action='store_true',help='Install bundled signed release updates AND configure both devices');a=parser.parse_args()
 if sys.platform!='linux':raise ValueError('Run on the Pi, not Windows.')
 if os.geteuid()!=0:raise ValueError('Run using sudo.')
 if Path('/etc/s1-boot-ready').exists():raise ValueError('Run setup.sh on the Pi. For printer-only setup use bootstrap.sh.')
 for name in ('ssh','runuser','openssl','python3','systemctl'):
  if not shutil.which(name):raise ValueError('Missing prerequisite: '+name)
 if not Path('/usr/sbin/sshd').is_file():raise ValueError('Pi OpenSSH server missing; install openssh-server first')
 for name in FILES:
  if not (HERE/name).is_file():raise ValueError('Incomplete setup package: '+name)
 if sum((a.check,a.prepare_ecm,a.complete))>1:raise ValueError('Choose only one of --check, --prepare-ecm, --complete')
 if a.complete:
  import complete
  complete.validate_bundle(HERE)
 for name in ('install-pi.py','configure-printer.py','install-printer.py','serial_settings.py','s1-serial-link','s1-usb-ecm','install-pi-light.py','bauraumlicht.cfg.template','prepare-ecm.py','ports-ecm.sh','ports-ecm.service'):
  if not (HERE/'connection'/name).is_file():raise ValueError('Incomplete connection setup: '+name)
 transport='ecm'
 if a.prepare_ecm:
  if input('Neue ECM ports.sh fuer naechsten Pi-Start vorbereiten? / Prepare new ECM ports.sh for next Pi boot? [YES]: ').strip().upper()!='YES':return
  subprocess.run([sys.executable,str(HERE/'connection/prepare-ecm.py')],check=True)
  return
 if not all(Path('/dev/ttyGS'+n).is_char_device() for n in ('0','1')):raise ValueError('Working USB MCU tunneling is required first; ports.sh is not replaced.')
 if a.complete and not Path('/sys/kernel/config/usb_gadget/klipper/configs/c.1/ecm.usb0').exists():
  if input('ECM fehlt. Fuer naechsten Start vorbereiten? / Prepare ECM for next boot? [YES]: ').strip().upper()!='YES':return
  subprocess.run([sys.executable,str(HERE/'connection/prepare-ecm.py')],check=True)
  print('STOP: Restart Pi, wait for SSH, then restart printer. Run bash setup.sh --complete again. Configuration is NOT complete yet.')
  return
 if transport=='ecm':
  if not Path('/sys/kernel/config/usb_gadget/klipper/configs/c.1/ecm.usb0').exists():raise ValueError('ECM is not prepared. Run bash setup.sh --prepare-ecm, then restart Pi and printer before rerunning setup.sh.')
  interfaces=json.loads(subprocess.check_output(['ip','-j','-4','address','show','dev','usb0'],text=True))
  if not any(x.get('local')=='10.55.0.1' for d in interfaces for x in d['addr_info']):raise ValueError('New ECM link missing. Run bash setup.sh --prepare-ecm, restart Pi then printer, then rerun setup.sh.')
 if a.check:print('Pi prerequisites OK; detected '+transport+'; no changes made.');return
 import pwd,urllib.request
 user=a.pi_user or os.environ.get('SUDO_USER') or input('Pi-Benutzer / Pi user: ').strip()
 if user=='root' or not re.fullmatch(r'[a-z_][a-z0-9_-]*[$]?',user):raise ValueError('Use the normal Pi user, not root.')
 account=pwd.getpwnam(user)
 host=str(ipaddress.IPv4Address(a.printer or input('Drucker-IP / Printer IP: ').strip()))
 route=json.loads(subprocess.check_output(['ip','-j','route','get',host],text=True));suggested=route[0].get('prefsrc','')
 address=str(ipaddress.IPv4Address(a.pi_address or input('Pi-IP fuer Links / Pi IP for access links ['+suggested+']: ').strip() or suggested))
 if input('Pi-Verbindung, Licht und Updater einrichten? / Set up Pi connection, light and updaters? [YES]: ').strip().upper()!='YES':return
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://127.0.0.1:7125/printer/objects/query?print_stats&extruder&heater_bed',timeout=5) as response:state=json.load(response)['result']['status']
 if state['print_stats']['state'] not in ('standby','complete','cancelled') or any(state[h]['target']!=0 for h in ('extruder','heater_bed')):raise ValueError('Printer must be idle with heaters off.')
 if a.complete:
  subprocess.run([sys.executable,str(HERE/'install.py'),'--root','/','--platform','pi','--if-missing'],check=True)
  complete.update_local(HERE,'pi')
 prefix=['runuser','-u',user,'--']
 with tempfile.TemporaryDirectory(prefix='kobranest-update-setup-') as tmp:
  os.chown(tmp,account.pw_uid,account.pw_gid);os.chmod(tmp,0o700)
  socket=tmp+'/ssh';target='root@'+host
  ssh=prefix+['ssh','-S',socket,'-o','StrictHostKeyChecking=ask','-o','ConnectTimeout=15']
  print('SSH-Fingerabdruck pruefen; OpenSSH fragt die Drucker-Anmeldung einmal ab. / Verify fingerprint; OpenSSH requests printer login once.')
  subprocess.run(ssh+['-M','-N','-f','-o','ControlPersist=120',target],check=True)
  remote_dir=None
  def remote(command,data=None):return subprocess.run(ssh+[target,command],input=data,stdout=subprocess.PIPE,check=True).stdout
  try:
   remote('test -f /etc/s1-boot-ready && command -v python3 && command -v openssl')
   remote_dir=remote('mktemp -d /tmp/kobranest-update-setup.XXXXXXXX').decode().strip()
   if not re.fullmatch(r'/tmp/kobranest-update-setup\.[A-Za-z0-9]+',remote_dir):raise ValueError('Unexpected temporary path')
   remote('tar xzf - -C '+shlex.quote(remote_dir),package())
   helper='python3 '+shlex.quote(remote_dir+'/connection/configure-printer.py')+' --transport '+transport
   public=printer_public_key(remote(helper+' --prepare'))
   key=Path(tmp)/'printer.pub';key.write_text(public+'\n');key.chmod(0o600)
   subprocess.run([sys.executable,str(HERE/'connection/install-pi.py'),'--pi-user',user,'--key',str(key),'--transport',transport],check=True)
   pi_key=Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
   peer=base64.b64encode(json.dumps({'pi_user':user,'pi_ip':address,'host_key':' '.join(pi_key[:2])}).encode()).decode()
   print(remote(helper+' --apply '+shlex.quote(peer)).decode())
   subprocess.run([sys.executable,str(HERE/'install.py'),'--root','/','--platform','pi','--if-missing'],check=True)
   for _ in range(25):
    status=json.loads(remote(helper+' --status'))
    if status['connected']:break
    time.sleep(2)
   else:raise ValueError('USB forwarding did not connect. Inspect the Pi service and printer serial-link log; no reboot was triggered.')
   if a.complete:
    complete.repair_remote(remote,remote_dir)
    complete.update_remote(HERE,remote,remote_dir)
   else:print(remote('sh '+shlex.quote(remote_dir+'/bootstrap.sh')).decode())
   before={};light_dir=Path(account.pw_dir)/'printer_data/config'
   for name in ('moonraker.conf','bauraumlicht.cfg'):
    path=light_dir/name
    if path.exists():before[name]=(path.stat().st_uid,path.stat().st_gid)
   template=base64.b64encode((HERE/'connection/bauraumlicht.cfg.template').read_bytes()).decode()
   try:subprocess.run([sys.executable,str(HERE/'connection/install-pi-light.py'),host,template,'--usb'],check=True,env=dict(os.environ,HOME=account.pw_dir))
   finally:
    for name in ('moonraker.conf','bauraumlicht.cfg'):
     path=light_dir/name
     if path.exists():os.chown(path,*before.get(name,(account.pw_uid,account.pw_gid)))
   values=status['settings']
   if a.complete:
    for attempt in range(12):
     try:complete.verify(remote,helper,HERE);break
     except (OSError,ValueError,subprocess.CalledProcessError):
      if attempt==11:raise
      time.sleep(2)
   print('Connection, forwarding, light and both updaters configured. WebUI: http://'+address+':'+str(values['web_port'])+' | Helix: http://'+address+':'+str(values['helix_port'])+' | printer SSH port '+str(values['ssh_port']))
  finally:
   if remote_dir:
    try:remote('rm -rf -- '+shlex.quote(remote_dir))
    except subprocess.CalledProcessError:pass
   subprocess.run(prefix+['ssh','-S',socket,'-O','exit',target],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,subprocess.CalledProcessError) as error:print('Setup stopped:',error,file=sys.stderr);sys.exit(1)
