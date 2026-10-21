#!/usr/bin/python3
"""Install into this project's Debian root. Never writes a boot partition."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import shutil
import signal

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', required=True)
p.add_argument('--pi-ip', required=True)
p.add_argument('--port', type=int, default=8080)
p.add_argument('--start', action='store_true', help='Reread BusyBox init after installation')
a = p.parse_args()
root = Path(a.root).resolve()
pi_ip = str(ipaddress.IPv4Address(a.pi_ip))
assert 1024 <= a.port <= 65535
if a.start:
    assert str(root) == '/' and 'busybox' in os.readlink('/proc/1/exe'), 'Expected the S1 BusyBox init'
source = Path(__file__).resolve().parent
service = root / 'usr/local/sbin/s1-service'
inittab = root / 'etc/inittab'
s = service.read_text()
i = inittab.read_text()
if '# Kobrian local web service' not in s:
    needle = 'case "${1:-}" in'
    assert s.count(needle) == 1, 'Unknown service dispatcher; nothing installed'
    s = s.replace(needle, needle + '\n# Kobrian local web service\nweb)\n    exec /usr/local/sbin/s1-web >>/var/log/s1-web.log 2>&1 ;;')
if '::respawn:/usr/local/sbin/s1-service web' not in i:
    needle = '::once:/usr/local/sbin/s1-health'
    assert i.count(needle) == 1, 'Unknown inittab; nothing installed'
    i = i.replace(needle, '::respawn:/usr/local/sbin/s1-service web\n' + needle)


def put(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + '.web-new')
    pending.write_bytes(data)
    pending.chmod(mode)
    os.replace(pending, path)


camera_line='::respawn:/usr/local/sbin/s1-camera >>/var/log/s1-camera.log 2>&1'
if camera_line not in i:
    i=i.replace('::once:/usr/local/sbin/s1-health',camera_line+'\n::once:/usr/local/sbin/s1-health')

for path, text in ((service, s), (inittab, i)):
    backup = path.with_name(path.name + '.before-web')
    if not backup.exists():
        shutil.copy2(path, backup)
    put(path, text.encode(), path.stat().st_mode & 0o777)
put(root / 'usr/local/sbin/s1-camera', (source / 's1-camera').read_bytes(), 0o755)
camera_config=root/'etc/s1-camera.json'
if not camera_config.exists():
    put(camera_config,(json.dumps({'enabled':False,'resolution':'1280x720','fps':15,'slowdown':True})+'\n').encode(),0o600)
put(root / 'usr/local/sbin/s1-web', (source / 's1-web').read_bytes(), 0o755)
put(root / 'usr/local/sbin/s1-return-to-stock', (source / 's1-return-to-stock').read_bytes(), 0o755)
put(root / 'opt/kobrian-web/index.html', (source / 'index.html').read_bytes(), 0o644)
config = root / 'etc/s1-web.json'
if not config.exists():
    settings = {'pi_ip': pi_ip, 'port': a.port, 'setup_required': True}
    put(config, (json.dumps(settings, indent=2) + '\n').encode(), 0o600)
os.sync()
if a.start:
    os.kill(1, signal.SIGHUP)
print('Kobrian Web installed. Existing web credentials preserved. Port:', a.port)
