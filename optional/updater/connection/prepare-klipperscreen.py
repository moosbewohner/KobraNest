#!/usr/bin/python3
"""Choose the Moonraker host for the local Kobra S1 KlipperScreen entry."""
from pathlib import Path
import re,json,os,stat
import serial_settings

def prepare(path,host):
 text=path.read_text();lines=text.splitlines(keepends=True);active=False;found=False
 for n,line in enumerate(lines):
  if re.match(r'^\s*\[',line):active=bool(re.match(r'^\s*\[printer Kobra S1\]\s*$',line))
  elif active and re.match(r'^\s*moonraker_host\s*[:=]',line):
   lines[n]=re.sub(r'^(\s*moonraker_host\s*[:=]\s*)[^\r\n]+',lambda m:m.group(1)+host,line);found=True
 if not found:raise ValueError('KlipperScreen printer Kobra S1 host setting missing')
 result=''.join(lines)
 if result!=text:
  pending=path.with_name(path.name+'.serial-new');pending.write_text(result);os.chmod(pending,stat.S_IMODE(path.stat().st_mode));os.replace(pending,path)
 return host
if __name__=='__main__':
 config=Path('/etc/s1-web.json');config=config if config.exists() else Path('/etc/s1-settings.json')
 host=serial_settings.moonraker_host(json.loads(config.read_text())['pi_ip'])
 print('KlipperScreen Moonraker:',prepare(Path('/etc/KlipperScreen.conf'),host))
