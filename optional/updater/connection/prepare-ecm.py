#!/usr/bin/python3
"""Prepare supplied ECM gadget for NEXT boot; never rebind a running gadget."""
import argparse,json,os,shutil,subprocess,time,urllib.request
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('/'));a=p.parse_args();root=a.root.resolve();here=Path(__file__).resolve().parent
if root==Path('/'):
 assert os.geteuid()==0,'Run with sudo'
 assert Path('/dev/ttyGS0').is_char_device() and Path('/dev/ttyGS1').is_char_device(),'An existing USB MCU gadget is required first'
 with urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?print_stats&extruder&heater_bed',timeout=5) as r:state=json.load(r)['result']['status']
 assert state['print_stats']['state'] in ('standby','complete','cancelled') and all(state[h]['target']==0 for h in ('extruder','heater_bed')),'Printer must be idle, heaters off'
backup=root/'var/backups/kobranest-ecm-setup'/str(time.time_ns())
for name,source in [('opt/ports.sh','ports-ecm.sh'),('etc/systemd/system/ports.service','ports-ecm.service')]:
 target=root/name;data=(here/source).read_bytes()
 if target.exists() and target.read_bytes()==data:continue
 if target.exists():saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
 target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name(target.name+'.ecm-new');tmp.write_bytes(data);tmp.chmod(0o755 if name.endswith('.sh') else 0o644);os.replace(tmp,target)
if root==Path('/'):
 subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['systemctl','enable','ports.service'],check=True);os.sync()
print('ECM ports.sh prepared for next boot. No running USB gadget was changed. Restart Pi, wait until it is reachable, restart printer, then rerun setup.sh. Do not start a print before setup is complete.')
