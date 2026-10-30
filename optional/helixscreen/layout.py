#!/usr/bin/python3
"""Retire recognized KobraNest bookkeeping; never replace upstream Helix files."""
import argparse,json,os,time
from pathlib import Path
KNOWN={'361269dce1faa43e4acb5f06b1365490667b317d40f9a52e53e03586ecca29a3','c6655f4fca7b004d26595a808db3da89e02207dc0c2aa6a87d384aa819235b66','6cb694d4b5935e027de5fa08598ea42445087b9dc13e4ad799064243e6556f32','10b99850874f2324573151497974b1547912042aeca6c763c9af6d12df41d094'}

def _migrate(root,retire_home=False):
 root=Path(root).resolve();destination=root/'opt/helixscreen'
 if not (destination/'bin/helix-screen').is_file():return 'legacy-preserved'
 marker=destination/'.kobrian-release';backup=None
 if marker.is_file() and not marker.is_symlink() and marker.read_text().strip() in KNOWN:
  backup=root/'var/backups/kobrian-display'/('layout-'+str(time.time_ns()));backup.mkdir(parents=True,mode=0o700)
  alias=destination/'bin/helix-screen-fbdev'
  if alias.is_symlink() and os.readlink(alias)=='helix-screen':os.replace(alias,backup/'helix-screen-fbdev')
  os.replace(marker,backup/'.kobrian-release')
 target=root/'var/lib/kobranest-display/helixscreen.json';target.parent.mkdir(parents=True,exist_ok=True)
 value=json.loads(target.read_text()) if target.exists() else {}
 value.update(layout='upstream',upstream_managed=True)
 if backup:value['legacy_backup']=str(backup.relative_to(root))
 # Only the wrapper requests this after the previous GUI has exited. Preserve
 # the entire former fake HOME rather than deleting potentially useful caches.
 old_home=destination/'test-home'
 if retire_home and old_home.is_dir() and not old_home.is_symlink():
  home_backup=backup or root/'var/backups/kobrian-display'/('layout-'+str(time.time_ns()))
  home_backup.mkdir(parents=True,exist_ok=True,mode=0o700)
  os.replace(old_home,home_backup/'test-home');value['test_home_backup']=str((home_backup/'test-home').relative_to(root))
 data=(json.dumps(value)+'\n').encode()
 if not target.exists() or target.read_bytes()!=data:
  tmp=target.with_name(target.name+'.new')
  with tmp.open('wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
  tmp.chmod(0o644);os.replace(tmp,target)
  if os.name!='nt':
   fd=os.open(str(target.parent),os.O_RDONLY)
   try:os.fsync(fd)
   finally:os.close(fd)
 return 'upstream'

def migrate(root=Path('/'),retire_home=False):
 root=Path(root).resolve()
 if os.name=='nt':return _migrate(root,retire_home)
 import fcntl
 directory=root/'run/s1';directory.mkdir(parents=True,exist_ok=True)
 with (directory/'helix-layout.lock').open('a') as stream:
  fcntl.flock(stream,fcntl.LOCK_EX)
  return _migrate(root,retire_home)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retire-home',action='store_true');args=p.parse_args()
 if os.geteuid()!=0:raise SystemExit('Printer root required')
 print(migrate(retire_home=args.retire_home))
