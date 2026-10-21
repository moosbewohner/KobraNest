from pathlib import Path
import tarfile,json,io,hashlib,subprocess,sys
base=Path(sys.argv[1]).resolve();source=base/'source'
assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()=='67ecd2597f63d29b727a74d679ffcb3dbc848fd3'
archives=list((source/'releases').glob('helixscreen-pi32-fbdev-*.tar.gz'))
assert len(archives)==1,archives
out=base/'helixscreen-kobranest-armhf.tar.gz'
provenance={'upstream':'https://github.com/Kobra-S1/helixscreen','branch':'kobrian','commit':'67ecd2597f63d29b727a74d679ffcb3dbc848fd3','version':(source/'VERSION.txt').read_text().strip(),'target':'pi32-fbdev','toolchain':'Debian trixie crossbuild-essential-armhf, GCC14','adaptation':'Framebuffer compatibility symlink; no upstream C++ changes'}
with tarfile.open(archives[0],'r:gz') as src,tarfile.open(out,'w:gz',compresslevel=1) as dst:
 for item in src:
  dst.addfile(item,src.extractfile(item) if item.isfile() else None)
 link=tarfile.TarInfo('helixscreen/bin/helix-screen-fbdev');link.type=tarfile.SYMTYPE;link.linkname='helix-screen';link.mode=0o755;dst.addfile(link)
 data=(json.dumps(provenance,indent=2)+'\n').encode();item=tarfile.TarInfo('helixscreen/kobranest-build.json');item.size=len(data);item.mode=0o644;dst.addfile(item,io.BytesIO(data))
(base/'helixscreen-build.json').write_text(json.dumps(provenance,indent=2)+'\n')
subprocess.run(['tar','--exclude=.git','--exclude=build','--exclude=releases','--exclude=.venv','--exclude=__pycache__','-czf',str(base/'helixscreen-kobrian-source.tar.gz'),'-C',str(base),'source'],check=True)
for name in ['helixscreen-kobranest-armhf.tar.gz','helixscreen-kobrian-source.tar.gz']:
 p=base/name;h=hashlib.sha256(p.read_bytes()).hexdigest();(base/(name+'.sha256')).write_text(h+'  '+name+'\n');print(name,p.stat().st_size,h)
(base/'package.status').write_text('SUCCESS\n')
