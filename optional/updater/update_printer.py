#!/usr/bin/env python3
"""Apply the signed preparation and native-layout updates on the PRINTER only."""
import argparse,json,os,subprocess,tarfile,tempfile
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--confirmation',required=True);a=p.parse_args()
 if a.confirmation!='YES':raise ValueError('Use --confirmation YES while the printer is idle, heaters off')
 if os.geteuid()!=0 or not Path('/etc/s1-boot-ready').is_file():raise ValueError('Run as root on the KobraNest printer, not on the Pi')
 here=Path(__file__).resolve().parent;target=(here/'RELEASE_VERSION').read_text().strip();bridge=(here/'BRIDGE_VERSION').read_text().strip()
 trusted=Path('/usr/share/kobranest-update/release.pub')
 if not trusted.is_file() or trusted.read_bytes().strip()!=(here/'release.pub').read_bytes().strip():raise ValueError('Missing or different installed signing key; use complete setup first')
 packages=[here/'packages'/('KobraNest-printer-update-'+number+'.tar.gz') for number in (bridge,target)]
 # Authenticate BOTH packages before making any change; regular updater performs
 # full file/platform/version/idle validation again before each installation.
 for package,number in zip(packages,(bridge,target)):
  with tarfile.open(package,'r:gz') as tar:
   raw=tar.extractfile('manifest.json').read();sig=tar.extractfile('manifest.sig').read();manifest=json.loads(raw)
  if manifest.get('platform')!='printer' or manifest.get('version')!=number:raise ValueError('Wrong bundled printer update')
  with tempfile.TemporaryDirectory() as tmp:
   raw_path=Path(tmp)/'manifest';sig_path=Path(tmp)/'signature';raw_path.write_bytes(raw);sig_path.write_bytes(sig)
   subprocess.run(['openssl','pkeyutl','-verify','-pubin','-inkey',str(trusted),'-rawin','-in',str(raw_path),'-sigfile',str(sig_path)],check=True)
 status=json.loads(subprocess.check_output(['/usr/local/sbin/s1-update','status']))
 if status.get('platform')!='printer' or status.get('busy'):raise ValueError('Printer updater is unavailable or busy')
 version=lambda value:tuple(map(int,value.split('.')))
 if version(status['current'])>version(target):raise ValueError('Newer release installed; downgrade refused')
 for package,number in zip(packages,(bridge,target)):
  status=json.loads(subprocess.check_output(['/usr/local/sbin/s1-update','status']))
  if version(status['current'])>=version(number):continue
  subprocess.run(['/usr/local/sbin/s1-update','stage','--package',str(package)],check=True)
  subprocess.run(['/usr/local/sbin/s1-update','apply','--confirmation','YES'],check=True)
 status=json.loads(subprocess.check_output(['/usr/local/sbin/s1-update','status']))
 if status['current']!=target:raise ValueError('Target update did not complete')
 print('Printer update complete: '+target+'. No Pi setup or firmware flash performed.')

if __name__=='__main__':
 try:main()
 except Exception as error:print('Update stopped:',error);raise SystemExit(1)
