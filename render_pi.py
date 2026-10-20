#!/usr/bin/env python3
"""Render example Pi files without connecting to or modifying a Pi."""
import argparse,ipaddress,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--settings',type=Path,default=Path('settings.json'));p.add_argument('--output',type=Path,default=Path('pi-config'));a=p.parse_args()
s=json.loads(a.settings.read_text());ip=str(ipaddress.IPv4Address(s['printer_ip']));a.output.mkdir(parents=True,exist_ok=True)
base=Path(__file__).resolve().parent
for n in [1,2]:
 text=(base/f'source/mcu{n}.service.template').read_text().replace('@PRINTER_IP@',ip)
 (a.output/f'mcu{n}.service').write_bytes(text.encode())
text=(base/'source/bauraumlicht.cfg.template').read_text().replace('192.168.10.67',ip)
(a.output/'bauraumlicht.cfg').write_bytes(text.encode())
print('Pi configuration rendered in',a.output,'; nothing installed')
