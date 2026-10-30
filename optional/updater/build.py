#!/usr/bin/env python3
"""Create a signed file-only update from a reviewed package directory."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path
MAP={
 'printer':{'usr/local/sbin/s1-web':'optional/kobrian-web/s1-web','opt/kobrian-web/index.html':'optional/kobrian-web/index.html','usr/local/sbin/s1-update':'optional/updater/s1-update','usr/local/lib/kobranest-update/updater.py':'optional/updater/updater.py','usr/local/sbin/s1-helix':'optional/helixscreen/s1-helix','usr/local/lib/kobranest-display/layout.py':'optional/helixscreen/layout.py'},
 'pi':{'usr/local/sbin/s1-update':'optional/updater/s1-update','usr/local/lib/kobranest-update/updater.py':'optional/updater/updater.py'},
}
def canonical(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def sign(data,key,out):
 raw=out.with_suffix(out.suffix+'.unsigned');raw.write_bytes(data)
 try:subprocess.run(['openssl','pkeyutl','-sign','-inkey',str(key),'-rawin','-in',str(raw),'-out',str(out)],check=True)
 finally:raw.unlink(missing_ok=True)
 return out.read_bytes()
def build(source,out,key,number,minimum,kind,base_url,notes=None,compatibility=False):
 from updater import version
 version(number);version(minimum);out.mkdir(parents=True,exist_ok=True)
 files=[];payload={}
 for dest,src in MAP[kind].items():
  if compatibility and dest in ('usr/local/sbin/s1-helix','usr/local/lib/kobranest-display/layout.py'):continue
  data=(source/src).read_bytes();mode=0o755 if dest.startswith('usr/local/sbin/') else 0o644
  if src.endswith('.py') or dest.endswith('/s1-web'):compile(data,src,'exec')
  files.append({'path':dest,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'mode':mode});payload['files/'+dest]=data
 manifest={'format':1,'platform':kind,'version':number,'minimum_version':minimum,'pi_required':False,'files':files,'notes':notes or {'de':'KobraNest-Wartungsupdate. Einstellungen bleiben erhalten. Helix und Debian werden separat aktualisiert.','en':'KobraNest maintenance update. Settings are preserved. Helix and Debian are updated separately.'}}
 raw=canonical(manifest);sig=sign(raw,key,out/(kind+'-manifest.sig'))
 package=out/('KobraNest-'+kind+'-update-'+number+'.tar.gz')
 with tarfile.open(package,'w:gz') as tar:
  for name,data in {'manifest.json':raw,'manifest.sig':sig,**payload}.items():
   info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0;tar.addfile(info,io.BytesIO(data))
 data=package.read_bytes();offer={'format':1,'platform':kind,'version':number,'minimum_version':minimum,'url':base_url.rstrip('/')+'/'+package.name,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'notes':manifest['notes'],'pi_required':False}
 return offer
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=Path,required=True);p.add_argument('--version',required=True);p.add_argument('--minimum-version',default='0.1.0');p.add_argument('--base-url',required=True);p.add_argument('--notes-de');p.add_argument('--notes-en');a=p.parse_args()
 catalog={'format':1}
 notes={'de':a.notes_de or a.notes_en,'en':a.notes_en or a.notes_de} if a.notes_de or a.notes_en else None
 from updater import version
 bridge=(a.source/'optional/updater/BRIDGE_VERSION').read_text().strip()
 if version(a.version)<=version(bridge):raise ValueError('Target release must be newer than its compatibility bridge')
 printer_min=max((a.minimum_version,bridge),key=version)
 final=build(a.source,a.out,a.key,a.version,printer_min,'printer',a.base_url,notes)
 bridge_notes={'de':'Vorbereitungsupdate fuer die native Helix-Einbindung. Danach erneut Updates pruefen und das Hauptupdate installieren. Keine Pi-Einrichtung erforderlich.','en':'Preparation for native Helix integration. Check again afterwards and install the main update. No Pi setup required.'}
 catalog['printer']=build(a.source,a.out,a.key,bridge,'0.0.0','printer',a.base_url,bridge_notes,compatibility=True)
 catalog['printer_updates']=[final]
 catalog['pi']=build(a.source,a.out,a.key,a.version,a.minimum_version,'pi',a.base_url,notes)
 raw=canonical(catalog);(a.out/'kobranest-update.json').write_bytes(raw);sign(raw,a.key,a.out/'kobranest-update.json.sig')
 print('Signed update packages and catalog written to',a.out)
if __name__=='__main__':main()
