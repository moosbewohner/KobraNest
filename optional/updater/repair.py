#!/usr/bin/env python3
"""Repair mixed WebUI/updater files; no boot, MCU, account or network changes."""
import argparse,ast,hashlib,json,os,shutil,signal,time
from pathlib import Path
import patch_web
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('/'));p.add_argument('--restart-web',action='store_true');a=p.parse_args();root=a.root.resolve();here=Path(__file__).resolve().parent;release=(here/'RELEASE_VERSION').read_text().strip()
 if root==Path('/') and os.geteuid()!=0:raise ValueError('Run as root on the printer')
 if a.restart_web and root!=Path('/'):raise ValueError('Restart is only valid on the live printer')
 if not (root/'etc/s1-boot-ready').is_file():raise ValueError('KobraNest printer required')
 version=root/'usr/share/kobranest-update/version.json';info=json.loads(version.read_text()) if version.exists() else None
 if info and tuple(map(int,info['version'].split('.')))>tuple(map(int,release.split('.'))):raise ValueError('Use a repair bundle matching the newer installed release')
 tx=root/'var/lib/kobranest-updates/transaction.json'
 if tx.exists() and json.loads(tx.read_text()).get('phase') in ('applying','checking'):raise ValueError('Interrupted update journal found; preserve it and recover the transaction before file repair')
 key=root/'usr/share/kobranest-update/release.pub'
 if key.exists() and key.read_bytes().strip()!=(here/'release.pub').read_bytes().strip():raise ValueError('Different update trust key; refused')
 functions={n.name for n in ast.parse((here/'updater.py').read_text()).body if isinstance(n,ast.FunctionDef)}
 if not {'boot_recover','recover','status','launch'}<=functions:raise ValueError('Repair bundle itself has an incomplete updater API')
 web=root/'usr/local/sbin/s1-web';page=root/'opt/kobrian-web/index.html'
 changes={web:(patch_web.backend(web.read_text(encoding='utf-8')).encode(),web.stat().st_mode&0o777),page:(patch_web.frontend(page.read_text(encoding='utf-8')).encode(),page.stat().st_mode&0o777),root/'usr/local/lib/kobranest-update/updater.py':((here/'updater.py').read_bytes(),0o644),root/'usr/local/sbin/s1-update':((here/'s1-update').read_bytes(),0o755)}
 if not key.exists():changes[key]=((here/'release.pub').read_bytes(),0o644)
 backup=root/'var/backups/kobranest-web-repair'/str(time.time_ns())
 for path,(data,mode) in changes.items():
  if path.exists() and path.read_bytes()==data:continue
  if path.exists():saved=backup/path.relative_to(root);saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,saved)
  path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.repair-new');tmp.write_bytes(data);tmp.chmod(mode);os.replace(tmp,path)
 if info:
  saved=backup/'version.json';saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(version,saved)
 else:
  info={'version':'0.0.0','platform':'printer','files':{},'version_scope':'repair-bootstrap','repair_runtime':release,'original_system_version':'unknown'}
 if info:
  info.setdefault('files',{}).update({str(path.relative_to(root)).replace('\\','/'):hashlib.sha256(data).hexdigest() for path,(data,_) in changes.items()})
  tmp=version.with_name('version.repair-new');tmp.write_bytes((json.dumps(info)+'\n').encode());tmp.chmod(0o600);os.replace(tmp,version)
 if hasattr(os,'sync'):os.sync()
 if a.restart_web:
  if root!=Path('/'):raise ValueError('Restart is only valid on the live printer')
  for proc in Path('/proc').iterdir():
   if not proc.name.isdigit():continue
   try:
    if b'/usr/local/sbin/s1-web' in (proc/'cmdline').read_bytes().split(b'\0')[:2]:os.kill(int(proc.name),signal.SIGTERM)
   except OSError:pass
 print('WebUI/updater repaired. Registered version:',info['version']);print('Version scope:',info.get('version_scope','existing installation'));print('Backup:',backup)
if __name__=='__main__':
 try:main()
 except Exception as error:print('Repair stopped:',error);raise SystemExit(1)
