#!/usr/bin/env python3
"""Package reviewed public setup code with both signed platform updates."""
import argparse,hashlib,zipfile
from pathlib import Path
from build import sign

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--packages',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--key',required=True,type=Path);a=p.parse_args()
 here=a.source/'optional/updater';version=(here/'RELEASE_VERSION').read_text().strip()
 import importlib.util
 spec=importlib.util.spec_from_file_location('complete_bundle',here/'complete.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.validate_bundle(a.packages.parent if a.packages.name=='packages' and (a.packages.parent/'release.pub').exists() else _validation_root(here,a.packages))
 root='KobraNest-Komplett-'+version;items={}
 for name in ('RELEASE_VERSION','setup.sh','setup.py','complete.py','bootstrap.sh','install.py','repair.py','patch_web.py','s1-update','s1-time-sync','updater.py','release.pub'):
  items[root+'/'+name]=(here/name).read_bytes()
 for path in sorted((here/'connection').iterdir()):
  if path.is_file() and path.suffix!='.pyc' and path.name!='transport.py':items[root+'/connection/'+path.name]=path.read_bytes()
 for kind in ('pi','printer'):
  name='KobraNest-'+kind+'-update-'+version+'.tar.gz';items[root+'/packages/'+name]=(a.packages/name).read_bytes()
 for name in ('kobranest-update.json','kobranest-update.json.sig'):
  items[root+'/packages/'+name]=(a.packages/name).read_bytes()
 items[root+'/LICENSE']=(a.source/'LICENSE').read_bytes()
 items[root+'/README.md']=(a.source/'docs/UPDATES.md').read_bytes()
 for name in ('PI.md','USB.md','RECOVERY.md'):items[root+'/'+name]=(a.source/'docs'/name).read_bytes()
 items[root+'/README.txt']=('KobraNest '+version+' COMPLETE setup\nRun ON THE PI, from this directory: bash setup.sh --complete\nAuf dem Pi ausfuehren: bash setup.sh --complete\nFresh USB installation: prepare ECM on Pi first: bash setup.sh --prepare-ecm\nErstinstallation: ECM vorbereiten; Pi neu starten, dann Drucker neu starten.\nThen use the PC installer. / Danach PC-Assistent verwenden.\nBoth devices must be idle, heaters off. Verify printer SSH fingerprint.\nSee README.md for update/rollback limits, LAN instructions and known ECM startup issue.\n').encode()
 items[root+'/SHA256SUMS']=''.join(hashlib.sha256(data).hexdigest()+'  '+name.removeprefix(root+'/')+'\n' for name,data in sorted(items.items())).encode()
 a.out.mkdir(parents=True,exist_ok=True);dest=a.out/(root+'.zip')
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in sorted(items.items()):z.writestr(name,data)
 sign(dest.read_bytes(),a.key,dest.with_suffix('.zip.sig'))
 dest.with_suffix('.zip.sha256').write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+'  '+dest.name+'\n',encoding='utf-8')
 print('Complete signed setup:',dest)

def _validation_root(here,packages):
 # validate_bundle needs only release.pub and the packages directory.
 # Use a temporary local view without changing reviewed source files.
 import tempfile,shutil,atexit
 temp=tempfile.TemporaryDirectory();atexit.register(temp.cleanup);root=Path(temp.name)
 shutil.copy2(here/'release.pub',root/'release.pub');(root/'packages').mkdir()
 for path in packages.glob('*.tar.gz'):shutil.copy2(path,root/'packages'/path.name)
 return root

if __name__=='__main__':main()
