#!/usr/bin/env python3
"""Build a signed printer-only ZIP that applies both compatibility steps."""
import argparse,hashlib,zipfile
from pathlib import Path
from build import sign

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--packages',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=Path,required=True);a=p.parse_args()
 here=a.source/'optional/updater';target=(here/'RELEASE_VERSION').read_text().strip();bridge=(here/'BRIDGE_VERSION').read_text().strip();root='KobraNest-Drucker-Update-'+target
 items={root+'/'+name:(here/name).read_bytes() for name in ('RELEASE_VERSION','BRIDGE_VERSION','release.pub','update_printer.py')}
 for number in (bridge,target):
  name='KobraNest-printer-update-'+number+'.tar.gz';items[root+'/packages/'+name]=(a.packages/name).read_bytes()
 items[root+'/LICENSE']=(a.source/'LICENSE').read_bytes()
 items[root+'/README.txt']=('KobraNest '+target+' PRINTER update / DRUCKER-Update\n\nOn the PRINTER, not the Pi. / Auf dem DRUCKER, nicht dem Pi.\nNo print, heaters off. / Kein Druck, Heizungen aus.\nUnpack, enter this directory as root, then:\nEntpacken, als root in diesen Ordner wechseln, dann:\n\npython3 update_printer.py --confirmation YES\n\nInstalls preparation '+bridge+' if required, then the main update '+target+'.\nFuehrt bei Bedarf Vorbereitung '+bridge+' aus, danach Hauptupdate '+target+'.\nBoth packages are signed; the installed public key is required.\nHelix program version, settings, images, Pi, MCU services and firmware are preserved.\nThe Helix interface restarts only if selected. No printer reboot.\nRecognized obsolete KobraNest links/markers are archived under /var/backups/kobrian-display.\nRollback via s1-update rollback --confirmation YES restores the last file-update step\nand leaves the preparation version installed. The archived bookkeeping has separate backups.\n\nAlternative: in the printer WebUI install '+bridge+', check again, install '+target+'.\nVerify ZIP before unpacking if a trusted installed release key is available:\nopenssl pkeyutl -verify -pubin -inkey /usr/share/kobranest-update/release.pub -rawin -in '+root+'.zip -sigfile '+root+'.zip.sig\n').encode()
 items[root+'/SHA256SUMS']=''.join(hashlib.sha256(data).hexdigest()+'  '+name.removeprefix(root+'/')+'\n' for name,data in sorted(items.items())).encode()
 a.out.mkdir(parents=True,exist_ok=True);dest=a.out/(root+'.zip')
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in sorted(items.items()):z.writestr(name,data)
 sign(dest.read_bytes(),a.key,dest.with_suffix('.zip.sig'))
 dest.with_suffix('.zip.sha256').write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+'  '+dest.name+'\n',encoding='utf-8')
 print('Signed printer-only bundle:',dest)
if __name__=='__main__':main()
