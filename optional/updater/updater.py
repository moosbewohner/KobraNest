#!/usr/bin/python3
"""Signed, file-only KobraNest updates. No boot, MCU, apt or user-config writes."""
import argparse,hashlib,io,json,os,platform,re,shutil,signal,subprocess,sys,tarfile,tempfile,time,uuid
from pathlib import Path,PurePosixPath
from urllib.request import Request,build_opener,ProxyHandler,HTTPRedirectHandler
ROOT=Path(os.environ.get('KOBRANEST_UPDATE_ROOT','/')).resolve()
def at(name):return ROOT/name.lstrip('/')
STATE=at('/var/lib/kobranest-updates')
KEY=at('/usr/share/kobranest-update/release.pub')
VERSION=at('/usr/share/kobranest-update/version.json')
CONFIG=at('/etc/kobranest-update.json')
ALLOW={
 'printer':{'usr/local/sbin/s1-web','opt/kobrian-web/index.html','usr/local/sbin/s1-update','usr/local/lib/kobranest-update/updater.py'},
 'pi':{'usr/local/sbin/s1-update','usr/local/lib/kobranest-update/updater.py','usr/local/lib/kobranest-serial-link/transport.py','etc/systemd/system/kobranest-serial-link.service'},
}
MAX_PACKAGE=16*1024*1024
def atomic(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.new');data=json.dumps(value,ensure_ascii=False,indent=2).encode()+b'\n'
 with tmp.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.chmod(tmp,0o600);os.replace(tmp,path)
 if os.name!='nt':
  fd=os.open(str(path.parent),os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
def read(path,default=None):
 try:return json.loads(path.read_text(encoding='utf-8'))
 except FileNotFoundError:return default
def digest(data):return hashlib.sha256(data).hexdigest()
def version(v):
 if not isinstance(v,str) or not re.fullmatch(r'\d+\.\d+\.\d+',v):raise ValueError('Invalid release version')
 return tuple(map(int,v.split('.')))
def installed():
 info=read(VERSION)
 if not isinstance(info,dict) or info.get('platform') not in ALLOW:
  raise ValueError('Version metadata missing or invalid. Run the complete setup; no installed release was assumed.')
 version(info.get('version'))
 return info
def status():
 job=read(STATE/'job.json',{})
 busy=job.get('busy',False)
 if busy:
  pid=job.get('pid',0)
  if pid:
   try:os.kill(pid,0)
   except OSError:busy=False
  elif time.time()-job.get('time',0)>20:busy=False
 offer=read(STATE/'offer.json');staged=read(STATE/'staged.json')
 transaction=read(STATE/'transaction.json',{})
 return {'installed':True,'current':installed()['version'],'platform':installed()['platform'],'busy':busy,
         'job':job,'offer':offer,'staged':staged,'rollback_available':transaction.get('phase')=='committed',
         'pi_separate':True,'automatic':False}
def progress(phase,**extra):atomic(STATE/'job.json',dict(phase=phase,time=time.time(),pid=os.getpid(),busy=True,**extra))
def safe_target(name,kind):
 if name not in ALLOW.get(kind,set()) or str(PurePosixPath(name))!=name:raise ValueError('Update target is not allowed: '+str(name))
 target=at(name)
 for p in (target,*target.parents):
  if p==ROOT:break
  if p.is_symlink():raise ValueError('Symlink update target refused: '+name)
 if target.exists() and not target.is_file():raise ValueError('Non-file target refused')
 return target
def verify_signature(data,signature):
 if len(signature)!=64 or not KEY.is_file():raise ValueError('Missing update signature or trusted release key')
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);(p/'data').write_bytes(data);(p/'sig').write_bytes(signature)
  r=subprocess.run(['openssl','pkeyutl','-verify','-pubin','-inkey',str(KEY),'-rawin','-in',str(p/'data'),'-sigfile',str(p/'sig')],capture_output=True,timeout=15)
  if r.returncode:raise ValueError('Release signature verification failed')
class HTTPSOnly(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if not newurl.startswith('https://'):raise ValueError('Non-HTTPS redirect refused')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def download(url,limit):
 if not isinstance(url,str) or not url.startswith('https://'):raise ValueError('HTTPS release URL required')
 opener=build_opener(ProxyHandler({}),HTTPSOnly())
 with opener.open(Request(url,headers={'User-Agent':'KobraNest-Updater/1'}),timeout=25) as r:
  result=bytearray();deadline=time.monotonic()+90
  while True:
   block=r.read(min(65536,limit+1-len(result)))
   if not block:return bytes(result)
   result.extend(block)
   if len(result)>limit or time.monotonic()>deadline:raise ValueError('Update download exceeded limits')
def validate_offer(o):
 if o.get('format')!=1 or o.get('platform')!=installed()['platform']:raise ValueError('Wrong update platform/format')
 version(o['version']);version(o['minimum_version'])
 if not re.fullmatch('[0-9a-f]{64}',o.get('sha256','')):raise ValueError('Invalid package hash')
 if not isinstance(o.get('size'),int) or not 0<o['size']<=MAX_PACKAGE:raise ValueError('Invalid package size')
 if version(installed()['version'])<version(o['minimum_version']):raise ValueError('An intermediate update is required')
 if version(o['version'])<=version(installed()['version']):return False
 return True
def check():
 sync_clock()
 cfg=read(CONFIG,{});url=cfg.get('catalog_url','https://github.com/moosbewohner/KobraNest/releases/latest/download/kobranest-update.json')
 from urllib.error import HTTPError
 try:raw=download(url,128*1024)
 except HTTPError as error:
  if error.code==404:atomic(STATE/'offer.json',None);return 'not_published'
  raise
 sig=download(url+'.sig',64);verify_signature(raw,sig)
 catalog=json.loads(raw);offer=catalog.get(installed()['platform'])
 if not offer:raise ValueError('No release for this system in catalog')
 available=validate_offer(offer)
 atomic(STATE/'catalog.json',{'raw':raw.decode(),'signature':sig.hex()})
 atomic(STATE/'offer.json',offer if available else None)
 return 'available' if available else 'up_to_date'
def verified_offer():
 catalog=read(STATE/'catalog.json')
 if not catalog:raise ValueError('Check for updates first')
 raw=catalog['raw'].encode();verify_signature(raw,bytes.fromhex(catalog['signature']))
 offer=json.loads(raw)[installed()['platform']]
 if not validate_offer(offer):raise ValueError('No newer compatible release')
 return offer
def inspect_package(data):
 if len(data)>MAX_PACKAGE:raise ValueError('Package too large')
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
  members=[];expanded=0
  for m in tar:
   expanded+=m.size
   if len(members)>=20 or not m.isfile() or m.size<0 or m.size>8*1024*1024 or expanded>24*1024*1024:raise ValueError('Invalid package entries')
   members.append(m)
  names=[m.name for m in members]
  if len(names)!=len(set(names)) or 'manifest.json' not in names or 'manifest.sig' not in names:raise ValueError('Invalid package manifest')
  def get(name):return tar.extractfile(name).read()
  if tar.getmember('manifest.json').size>128*1024 or tar.getmember('manifest.sig').size!=64:raise ValueError('Invalid manifest size')
  raw=get('manifest.json');verify_signature(raw,get('manifest.sig'));manifest=json.loads(raw)
  if manifest.get('format')!=1 or manifest.get('platform')!=installed()['platform']:raise ValueError('Wrong package platform')
  version(manifest['version']);version(manifest['minimum_version'])
  if version(installed()['version'])<version(manifest['minimum_version']):raise ValueError('Incompatible installed version')
  if version(manifest['version'])<=version(installed()['version']):raise ValueError('Downgrade/reinstall refused')
  files=manifest.get('files',[])
  if not files or len({f['path'] for f in files})!=len(files):raise ValueError('Invalid file list')
  expected={'manifest.json','manifest.sig'};payload={};total=0
  for f in files:
   safe_target(f['path'],manifest['platform'])
   if f.get('mode') not in (0o644,0o755):raise ValueError('Invalid file permissions')
   name='files/'+f['path'];expected.add(name);blob=get(name);total+=len(blob)
   if len(blob)!=f['size'] or digest(blob)!=f['sha256']:raise ValueError('File checksum failed: '+f['path'])
   if f['path'].endswith('.py') or f['path'].endswith('/s1-web'):compile(blob,f['path'],'exec')
   payload[f['path']]=blob
   if f['path']=='usr/local/sbin/s1-web':
    current=safe_target(f['path'],manifest['platform'])
    if current.exists() and b'import serial_settings' in current.read_bytes() and b'import serial_settings' not in blob:
     raise ValueError('This package would remove USB forwarding integration; use a matching runtime release')
  if set(names)!=expected or total>24*1024*1024:raise ValueError('Unexpected package contents')
  return manifest,payload
def stage(package=None):
 if package is None:
  offer=verified_offer();data=download(offer['url'],MAX_PACKAGE)
  if len(data)!=offer['size'] or digest(data)!=offer['sha256']:raise ValueError('Package checksum failed')
 else:offer=None;data=Path(package).read_bytes()
 manifest,payload=inspect_package(data)
 if offer and manifest['version']!=offer['version']:raise ValueError('Catalog/package version mismatch')
 needed=sum(map(len,payload.values()))*4+8*1024*1024
 if shutil.disk_usage(STATE).free<needed:raise ValueError('Insufficient free space for download, backup and rollback')
 with (STATE/'package.new').open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(STATE/'package.new',STATE/'package.tar.gz')
 atomic(STATE/'staged.json',{'version':manifest['version'],'sha256':digest(data),'notes':manifest.get('notes',{}),'files':[f['path'] for f in manifest['files']],'pi_required':manifest.get('pi_required',False)})
 return 'staged'
def moonraker_address():
 cfg=read(at('/etc/s1-web.json'),read(at('/etc/s1-settings.json'),{}));host=cfg.get('pi_ip','127.0.0.1')
 if at('/etc/s1-tunnel-mode').exists() and at('/etc/s1-tunnel-mode').read_text().strip()=='usb' and at('/etc/s1-serial-link.enabled').exists():host='127.0.0.1'
 if installed()['platform']=='pi':host='127.0.0.1'
 import ipaddress
 return str(ipaddress.IPv4Address(host))
def sync_clock():
 if ROOT!=Path('/') or installed()['platform']=='pi':return
 if 1704067200<=time.time()<4102444800:return
 import email.utils
 try:
  with build_opener(ProxyHandler({})).open('http://'+moonraker_address()+':7125/server/info',timeout=5) as r:
   stamp=email.utils.parsedate_to_datetime(r.headers['Date']).timestamp()
  if not 1704067200<=stamp<4102444800:raise ValueError('Invalid Pi clock')
  time.clock_settime(time.CLOCK_REALTIME,stamp)
 except Exception as error:raise ValueError('Printer clock is invalid. Connect Moonraker or set the system time before HTTPS updates.') from error
def require_idle():
 if ROOT!=Path('/'):raise ValueError('Live idle check cannot run against a fixture root')
 host=moonraker_address()
 with build_opener(ProxyHandler({})).open('http://'+host+':7125/printer/objects/query?print_stats&extruder&heater_bed',timeout=5) as r:state=json.load(r)['result']['status']
 if state['print_stats']['state'] not in ('standby','complete','cancelled'):raise ValueError('Printer must be idle')
 if any(state[x]['target']!=0 for x in ('extruder','heater_bed')):raise ValueError('Turn heaters off before updating')
def replace_file(target,data,mode):
 target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name(target.name+'.update-new')
 with tmp.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.chmod(tmp,mode);os.replace(tmp,target)
def restart_web():
 if ROOT!=Path('/'):return
 stopped=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit() or int(p.name)==os.getpid():continue
  try:
   args=(p/'cmdline').read_bytes().split(b'\0')
   if b'/usr/local/sbin/s1-web' in args[:2]:os.kill(int(p.name),signal.SIGTERM);stopped.append(int(p.name))
  except OSError:pass
 for _ in range(30):
  if not any(Path('/proc/'+str(pid)).exists() for pid in stopped):return
  time.sleep(0.1)
 raise ValueError('Previous WebUI process did not stop')
def prune_backups(keep):
 base=STATE/'backups'
 entries=[p for p in base.iterdir() if re.fullmatch('[0-9a-f]{32}',p.name) and p.is_dir() and not p.is_symlink()]
 entries.sort(key=lambda p:p.stat().st_mtime,reverse=True)
 retained={keep}
 for p in entries:
  if p.name in retained:continue
  if len(retained)<3:retained.add(p.name);continue
  if p.resolve().parent==base.resolve():shutil.rmtree(p)
def health():
 if ROOT!=Path('/'):raise ValueError('Fixture health must be explicitly injected by tests')
 if installed()['platform']=='pi':
  changed={f['path'] for f in read(STATE/'transaction.json',{}).get('files',[])}
  if changed&{'usr/local/lib/kobranest-serial-link/transport.py','etc/systemd/system/kobranest-serial-link.service'}:
   subprocess.run(['systemctl','daemon-reload'],check=True,timeout=15)
   subprocess.run(['systemctl','restart','kobranest-serial-link'],check=True,timeout=20)
   subprocess.run(['systemctl','is-active','kobranest-serial-link'],check=True,timeout=5)
  return
 cfg=read(at('/etc/s1-web.json'),{});url='http://127.0.0.1:'+str(int(cfg.get('port',8080)))+'/api/setup'
 for _ in range(30):
  try:
   with build_opener(ProxyHandler({})).open(url,timeout=2) as r:
    if r.status==200 and isinstance(json.load(r).get('required'),bool):return
  except (OSError,ValueError):pass
  time.sleep(1)
 raise ValueError('Updated WebUI did not become healthy')
def restore(tx,check_changes=False):
 backup=STATE/'backups'/tx['id']
 for f in tx['files']:
  target=safe_target(f['path'],tx['platform'])
  if check_changes and (not target.exists() or digest(target.read_bytes())!=f['new_hash']):raise ValueError('A managed file was changed after update; manual recovery required')
 for f in reversed(tx['files']):
  target=safe_target(f['path'],tx['platform']);saved=backup/'files'/f['path']
  if f['existed']:replace_file(target,saved.read_bytes(),f['mode'])
  else:target.unlink(missing_ok=True)
 atomic(VERSION,tx['previous']);tx['phase']='rolled_back';atomic(STATE/'transaction.json',tx)
 if hasattr(os,'sync'):os.sync()
def apply(idle=require_idle,probe=health,restart=restart_web):
 idle();staged=read(STATE/'staged.json')
 if not staged:raise ValueError('Download an update first')
 data=(STATE/'package.tar.gz').read_bytes()
 if digest(data)!=staged['sha256']:raise ValueError('Staged package changed')
 manifest,payload=inspect_package(data);current=installed()
 if shutil.disk_usage(STATE).free<sum(map(len,payload.values()))*3+8*1024*1024:raise ValueError('Insufficient free space for backup and rollback')
 tx={'id':uuid.uuid4().hex,'phase':'preparing','platform':current['platform'],'previous':current,'version':manifest['version'],'files':[]}
 backup=STATE/'backups'/tx['id'];backup.mkdir(parents=True)
 for f in manifest['files']:
  target=safe_target(f['path'],current['platform']);exists=target.exists()
  if exists and current.get('files',{}).get(f['path']) not in (None,digest(target.read_bytes())):raise ValueError('Locally modified file: '+f['path'])
  old={'path':f['path'],'existed':exists,'mode':target.stat().st_mode&0o777 if exists else f['mode'],'new_hash':f['sha256']}
  if exists:
   saved=backup/'files'/f['path'];saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
  tx['files'].append(old)
 atomic(backup/'transaction.json',tx);tx['phase']='applying';atomic(STATE/'transaction.json',tx)
 try:
  idle()
  for f in manifest['files']:replace_file(safe_target(f['path'],current['platform']),payload[f['path']],f['mode'])
  ledger=dict(current.get('files',{}));ledger.update({f['path']:f['sha256'] for f in manifest['files']})
  atomic(VERSION,dict(version=manifest['version'],platform=current['platform'],files=ledger))
  if hasattr(os,'sync'):os.sync()
  tx['phase']='checking';atomic(STATE/'transaction.json',tx);restart();probe()
  tx['phase']='committed';atomic(STATE/'transaction.json',tx);(STATE/'staged.json').unlink(missing_ok=True)
  try:prune_backups(tx['id'])
  except OSError:pass
  return 'installed'
 except Exception:
  restore(tx);restart();raise
def rollback(idle=require_idle,probe=health,restart=restart_web):
 idle();tx=read(STATE/'transaction.json',{})
 if tx.get('phase')!='committed':raise ValueError('No completed update to roll back')
 restore(tx,True);restart();probe();return 'rolled_back'
def recover():
 tx=read(STATE/'transaction.json',{})
 if tx.get('phase') in ('applying','checking'):restore(tx);return 'recovered'
 return 'nothing_to_recover'
def boot_recover():
 import fcntl
 STATE.mkdir(parents=True,exist_ok=True)
 with (STATE/'worker.lock').open('w') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:return
  recover()
def launch(action,package=None):
 if action not in ('check','stage','apply','rollback'):raise ValueError('Invalid update action')
 import fcntl
 STATE.mkdir(parents=True,exist_ok=True);os.chmod(STATE,0o700)
 with (STATE/'enqueue.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX)
  if status()['busy']:raise ValueError('An update task is already running')
  if action in ('apply','rollback'):require_idle()
  atomic(STATE/'job.json',{'phase':'queued','time':time.time(),'pid':0,'busy':True})
  log=(STATE/'worker.log').open('ab')
  args=[sys.executable,str(Path(__file__).resolve()),'worker',action]
  if package:args+=['--package',str(package)]
  try:subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
  except Exception:atomic(STATE/'job.json',{'phase':'failed','busy':False,'error':'Could not start update worker'});raise
  finally:log.close()
 return status()
def worker(action,package=None):
 import fcntl
 STATE.mkdir(parents=True,exist_ok=True);os.chmod(STATE,0o700)
 with (STATE/'worker.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  progress(action);time.sleep(2)
  try:
   result={'check':check,'stage':lambda:stage(package),'apply':apply,'rollback':rollback,'recover':recover}[action]()
   atomic(STATE/'job.json',{'phase':result,'time':time.time(),'busy':False})
  except Exception as e:
   atomic(STATE/'job.json',{'phase':'failed','time':time.time(),'busy':False,'error':str(e)[:500]});raise
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['status','check','stage','apply','rollback','recover','worker']);p.add_argument('worker_action',nargs='?');p.add_argument('--package');p.add_argument('--confirmation');a=p.parse_args()
 if a.action=='status':print(json.dumps(status()));return
 if os.geteuid()!=0:raise ValueError('Root required')
 if a.action in ('apply','rollback') and a.confirmation!='YES':raise ValueError('Use --confirmation YES while printer is idle')
 STATE.mkdir(parents=True,exist_ok=True)
 if a.action=='worker':worker(a.worker_action,a.package)
 else:worker(a.action,a.package)
if __name__=='__main__':
 try:main()
 except Exception as e:print('Update failed:',e,file=sys.stderr);sys.exit(1)
