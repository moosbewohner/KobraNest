#!/usr/bin/env python3
"""Wrap the verified official HelixScreen archive; never copies a running printer."""
import argparse,hashlib,io,json,tarfile,urllib.request,zipfile
from pathlib import Path
METADATA={'repository': 'prestonbrown/helixscreen', 'version': 'v1.1.0', 'commit': 'e82a1bb844794153f8c9d3f5f590a3f930463cb4', 'official_asset': 'https://github.com/prestonbrown/helixscreen/releases/download/v1.1.0/helixscreen-pi32.zip', 'official_asset_sha256': '831b9e4c80e9b79f8c8b454cb7b46a381192c8e9d7ac53010ac14ba6054a2e0b', 'binary_sha256': '68f923405013c09f77756848f76579a5a3fd2fd2f150dfb507073acd825f0041', 'source_url': 'https://codeload.github.com/prestonbrown/helixscreen/tar.gz/e82a1bb844794153f8c9d3f5f590a3f930463cb4', 'archive_sha256': '9edf3516b5b2e9b58d0490bf50c4e4008242ec018221a17736b8ba8a4934969a'}
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
 (a.output/'helix-official.json').write_text(json.dumps(dict(METADATA,archive_sha256=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()),indent=2)+'\n')
 print(archive,hashlib.file_digest(archive.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main()
