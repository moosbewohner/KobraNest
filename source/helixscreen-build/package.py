#!/usr/bin/env python3
"""Wrap the verified official HelixScreen archive; never copies a running printer."""
import argparse,hashlib,io,json,tarfile,urllib.request,zipfile
from pathlib import Path
METADATA={'repository': 'prestonbrown/helixscreen', 'version': 'v1.1.0-beta.11', 'commit': '3f4f594092d419f26866995478ba7c54a12378e2', 'official_asset': 'https://github.com/prestonbrown/helixscreen/releases/download/v1.1.0-beta.11/helixscreen-pi32.zip', 'official_asset_sha256': 'f318adc869f20d7adb9a98ab3cb9decca16f3df5ee7c2338ea3531ea5c38a45d', 'binary_sha256': 'de14865176144462f17625e72f75a59294525e33a0b4a2c0b89060a0712c898c', 'archive_sha256': '361269dce1faa43e4acb5f06b1365490667b317d40f9a52e53e03586ecca29a3', 'source_url': 'https://codeload.github.com/prestonbrown/helixscreen/tar.gz/3f4f594092d419f26866995478ba7c54a12378e2'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 raw=a.output/'helixscreen-pi32.zip'
 if not raw.exists():urllib.request.urlretrieve(METADATA['official_asset'],raw)
 assert hashlib.file_digest(raw.open('rb'),'sha256').hexdigest()==METADATA['official_asset_sha256']
 archive=a.output/'helixscreen-kobranest-armhf.tar.gz'
 # Fixed tar metadata and gzip timestamp make the wrapper reproducible.
 import gzip
 with raw.open('rb') as stream,zipfile.ZipFile(stream) as z,archive.open('wb') as file,gzip.GzipFile(filename='',mode='wb',compresslevel=6,fileobj=file,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as tar:
  for entry in z.infolist():
   name=entry.filename.rstrip('/');assert name and '..' not in Path(name).parts and not name.startswith('/')
   item=tarfile.TarInfo('helixscreen/'+name);item.mtime=0;item.mode=(entry.external_attr>>16)&0o777 or (0o755 if entry.is_dir() else 0o644)
   if entry.is_dir():item.type=tarfile.DIRTYPE;tar.addfile(item)
   else:
    if name.startswith('bin/') or name.endswith('.sh'):item.mode|=0o111
    item.size=entry.file_size
    with z.open(entry) as source:tar.addfile(item,source)
  alias=tarfile.TarInfo('helixscreen/bin/helix-screen-fbdev');alias.type=tarfile.SYMTYPE;alias.linkname='helix-screen';alias.mode=0o777;tar.addfile(alias)
 (a.output/'helix-official.json').write_text(json.dumps(dict(METADATA,archive_sha256=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()),indent=2)+'\n')
 print(archive,hashlib.file_digest(archive.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main()
