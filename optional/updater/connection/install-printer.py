#!/usr/bin/python3
"""Stage USB serial support without starting services or changing MCU transport."""
import argparse,json,os,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);a=p.parse_args()
root=Path(a.root).resolve();source=Path(__file__).resolve().parent
assert (root/'etc/s1-boot-ready').is_file(),'KobraNest root required'
def put(path,data,mode=0o755):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.serial-new');tmp.write_bytes(data);tmp.chmod(mode);os.replace(tmp,path)
for name in ('serial_settings.py','prepare-klipperscreen.py'):
 put(root/'usr/local/lib/kobranest-serial-link'/name,(source/name).read_bytes())
put(root/'usr/local/sbin/s1-serial-link',(source/'s1-serial-link').read_bytes())
changes={}
p=root/'usr/local/sbin/s1-gui';s=p.read_text();line='/usr/bin/python3 /usr/local/lib/kobranest-serial-link/prepare-klipperscreen.py'
if line not in s:
 assert 'XP=; VP=; KP=' in s;s=s.replace('XP=; VP=; KP=',line+'\nXP=; VP=; KP=',1)
changes[p]=s
p=root/'usr/local/sbin/s1-light';s=p.read_text().replace("Server((SETTINGS['printer_ip'], 7126), Handler)","Server(('0.0.0.0', 7126), Handler)");changes[p]=s
p=root/'usr/local/sbin/s1-klipper-autorecover';s=p.read_text()
if 'serial_settings.moonraker_host' not in s:
 assert "        ip = config['pi_ip']" in s
 s=s.replace("        ip = config['pi_ip']","        import sys\n        sys.path.insert(0,'/usr/local/lib/kobranest-serial-link')\n        import serial_settings\n        ip = serial_settings.moonraker_host(config['pi_ip'])")
changes[p]=s
p=root/'etc/inittab';s=p.read_text();line='::respawn:/usr/local/sbin/s1-serial-link >>/var/log/s1-serial-link.log 2>&1'
if line not in s:s=s.rstrip()+'\n'+line+'\n'
changes[p]=s
backup=root/'var/backups/kobranest-serial-link';backup.mkdir(parents=True,exist_ok=True)
for path,text in changes.items():
 if path.read_text()==text:continue
 saved=backup/path.name
 if not saved.exists():shutil.copy2(path,saved)
 put(path,text.encode(),path.stat().st_mode&0o777)
config=root/'etc/s1-serial-link.json'
if not config.exists():
 import importlib.util
 spec=importlib.util.spec_from_file_location('serial_defaults',source/'serial_settings.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 put(config,(json.dumps(module.DEFAULTS,indent=2)+'\n').encode(),0o600)
print('USB serial runtime staged. Existing gadget and MCU services unchanged; link enabled only after Pi setup.')
