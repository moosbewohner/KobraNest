#!/usr/bin/python3
"""Install update support into an existing or staged KobraNest root."""
import argparse,ast,hashlib,json,os,shutil,time
from pathlib import Path
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path);p.add_argument('--platform',choices=['printer','pi'],default='printer');p.add_argument('--baseline');p.add_argument('--patch-web',action='store_true');p.add_argument('--if-missing',action='store_true');a=p.parse_args()
 root=a.root.resolve();here=Path(__file__).resolve().parent
 if a.baseline is None:a.baseline=(here/'RELEASE_VERSION').read_text().strip() if a.platform=='pi' else '0.0.0'
 if root==Path('/') and os.geteuid()!=0:raise ValueError('Root required')
 if a.platform=='printer' and not (root/'etc/s1-boot-ready').is_file():raise ValueError('KobraNest root required')
 version=root/'usr/share/kobranest-update/version.json'
 if a.if_missing and version.exists():
  info=json.loads(version.read_text())
  if info.get('platform')!=a.platform:raise ValueError('Existing updater belongs to another platform')
  key=root/'usr/share/kobranest-update/release.pub'
  if not key.is_file() or key.read_bytes().strip()!=(here/'release.pub').read_bytes().strip():raise ValueError('Existing update signing key differs; refused')
  if not all((root/name).is_file() for name in ('usr/local/sbin/s1-update','usr/local/lib/kobranest-update/updater.py')):raise ValueError('Incomplete existing updater; recover it before setup')
  functions={n.name for n in ast.parse((root/'usr/local/lib/kobranest-update/updater.py').read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  if not {'boot_recover','status','launch','recover'}<=functions:raise ValueError('Installed updater API incomplete; use repair.py')
  if a.platform=='printer' and '# BEGIN KOBRANEST UPDATER' not in (root/'usr/local/sbin/s1-web').read_text():raise ValueError('Existing updater is missing WebUI integration; recover before setup')
  print('Existing '+a.platform+' updater '+info['version']+' preserved; use signed updates to upgrade it.');return
 if version.exists() and json.loads(version.read_text())['version']!=a.baseline:raise ValueError('Use a signed update for an already upgraded system')
 trusted=root/'usr/share/kobranest-update/release.pub'
 if trusted.exists() and trusted.read_bytes().strip()!=(here/'release.pub').read_bytes().strip():raise ValueError('Different trusted update key; no files changed')
 required={'boot_recover','status','launch','recover'}
 source_functions={n.name for n in ast.parse((here/'updater.py').read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
 if not required<=source_functions:raise ValueError('Incomplete bundled updater API; WebUI was not patched')
 backup=root/'var/backups/kobranest-updater-bootstrap'/str(time.time_ns())
 paths=[('usr/local/sbin/s1-update','s1-update',0o755),('usr/local/lib/kobranest-update/updater.py','updater.py',0o644),('usr/share/kobranest-update/release.pub','release.pub',0o644)]
 if a.platform=='printer' and (here/'s1-time-sync').is_file():paths.append(('usr/local/sbin/s1-time-sync','s1-time-sync',0o755))
 for name,source,mode in paths:
  dest=root/name;data=(here/source).read_bytes()
  if dest.exists() and dest.read_bytes()==data:continue
  if dest.exists():
   if source=='release.pub':raise ValueError('A different trusted update key is already installed')
   saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,saved)
  dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_name(dest.name+'.bootstrap-new');tmp.write_bytes(data);tmp.chmod(mode);os.replace(tmp,dest)
 if a.patch_web and a.platform=='printer':
  import patch_web
  for name,patch in [('usr/local/sbin/s1-web',patch_web.backend),('opt/kobrian-web/index.html',patch_web.frontend)]:
   dest=root/name;old=dest.read_text(encoding='utf-8');new=patch(old)
   if old==new:continue
   saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,saved)
   tmp=dest.with_name(dest.name+'.bootstrap-new');tmp.write_text(new,encoding='utf-8');tmp.chmod(dest.stat().st_mode&0o777);os.replace(tmp,dest)
 state=root/'var/lib/kobranest-updates';state.mkdir(parents=True,exist_ok=True);state.chmod(0o700)
 if not version.exists() or a.patch_web:
  files={}
  names=['usr/local/sbin/s1-web','opt/kobrian-web/index.html','usr/local/sbin/s1-update','usr/local/lib/kobranest-update/updater.py']
  if a.platform=='printer' and a.baseline!='0.0.0':names+=['usr/local/sbin/s1-helix','usr/local/lib/kobranest-display/layout.py']
  for name in names:
   path=root/name
   if path.is_file():files[name]=hashlib.sha256(path.read_bytes()).hexdigest()
  info={'version':a.baseline,'platform':a.platform,'files':files}
  if a.platform=='printer' and a.baseline=='0.0.0':info.update(version_scope='updater-bootstrap',original_system_version='unknown')
  version.write_text(json.dumps(info)+'\n');version.chmod(0o600)
 print('KobraNest update support installed; account, network, SSH keys and tunnels preserved.')
if __name__=='__main__':main()
