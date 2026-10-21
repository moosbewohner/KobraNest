"""Guided recovery through an existing trusted SSH connection; never USB flashing."""
import hashlib
import ipaddress
import json
from pathlib import Path
import secrets
import shlex
import threading
import time

import installer


def credentials(data):
    source = data['printer']
    host = ipaddress.IPv4Address(source['host'])
    if not host.is_private or host.is_loopback:
        raise ValueError('Bitte eine lokale Geräte-IP eingeben.')
    if source['user'].strip() != 'root':
        raise ValueError('Recovery benötigt root auf dem Drucker.')
    password, approved = source.get('password', ''), source.get('approved', '')
    if not isinstance(password, str) or len(password) > 512 or not isinstance(approved, str) or len(approved) > 120:
        raise ValueError('Ungültige SSH-Zugangsdaten.')
    return dict(host=str(host), user='root', password=password, approved=approved)


def start(app, data):
    printer = credentials(data)
    action = data.get('action')
    if action not in ('diagnose', 'stock', 'archive', 'restore_b'):
        raise ValueError('Unbekannte Recovery-Aktion.')
    if action != 'diagnose':
        if data.get('confirmation') != 'YES' or data.get('idle_confirmed') is not True:
            raise ValueError('YES eingeben und bestätigen, dass kein Druck aktiv ist.')
        binding = getattr(app, 'recovery_binding', None)
        if not binding or binding['host'] != printer['host'] or time.time() - binding['time'] > 900:
            raise ValueError('Zuerst die Recovery-Diagnose für diesen Drucker ausführen.')
    with app.lock:
        if app.state['running']:
            raise RuntimeError('Ein Vorgang läuft bereits.')
        if action == 'diagnose':app.recovery_binding = None
        app.state = dict(running=True, rows=[], trust=[], finished=False, action='recovery_' + action)
    threading.Thread(target=worker, args=(app, action, printer), daemon=False).start()


def probe(client):
    script = """import json,os
from pathlib import Path
base=Path('/useremain/s1-klipperscreen-test');root=base/'rootfs'
cmd=Path('/proc/cmdline').read_text()
print(json.dumps({'slot':'A' if 'root=/dev/mmcblk0p8 ' in cmd+' ' else 'B' if 'root=/dev/mmcblk0p9 ' in cmd+' ' else 'unknown',
'architecture':os.uname().machine,'root':os.geteuid()==0,
'parts':{str(n):int(Path('/sys/class/block/mmcblk0p'+str(n)+'/size').read_text())*512 for n in (1,5,6,7,8,9)},
'installation':base.exists(),'base_files':all((root/p).is_file() for p in ('etc/s1-boot-ready','usr/local/sbin/s1-boot','bin/busybox')),
'stock_helper':Path('/usr/local/sbin/s1-return-to-stock').is_file(),
'health_pending':(base/'boot-attempt').exists()}))
"""
    result = json.loads(installer.run(client, 'python3 -c ' + shlex.quote(script), timeout=20))
    installer.require(result['root'] and result['architecture'] == 'armv7l', 'Unsupported recovery platform')
    installer.require(result['parts'] == {str(k): v for k, v in installer.PARTS.items()}, 'Unexpected recovery partition layout')
    return result


def backup(work, host):
    manifest = json.loads((work / 'device.json').read_text(encoding='utf-8'))
    installer.require(manifest['settings']['printer_ip'] == host, 'Backup belongs to another installation target')
    for n in (1, 6, 7, 8, 9):
        path = work / 'backup' / ('p' + str(n) + '.img')
        installer.require(path.is_file() and path.stat().st_size == installer.PARTS[n], 'Backup partition missing or wrong size')
        installer.require(installer.sha(path) == manifest['partitions'][str(n)], 'Backup checksum mismatch')
        if n in (7, 9):
            with path.open('rb') as image:magic=image.read(4)
            installer.require(magic == (b'\xd0\x0d\xfe\xed' if n == 7 else b'hsqs'), 'Backup B image format is unsupported')
    return manifest


def guard_stock(client):
    # Includes root, platform, active A, data mount and unmounted B checks.
    installer.inspect(client)


def check_idle(client):
    # If Klipper has a known active job, a human acknowledgement cannot bypass it.
    script = """import json,ipaddress,urllib.request
from pathlib import Path
for path in ('/etc/s1-web.json','/etc/s1-settings.json'):
 try:
  p=Path(path)
  if not p.is_file():continue
  ip=ipaddress.IPv4Address(json.loads(p.read_text())['pi_ip'])
  if not ip.is_private or ip.is_loopback:continue
  url='http://'+str(ip)+':7125/printer/objects/query?print_stats'
  print(json.load(urllib.request.urlopen(url,timeout=3))['result']['status']['print_stats']['state']);break
 except Exception:continue
else:print('unknown')
"""
    state = installer.run(client, 'python3 -c ' + shlex.quote(script), timeout=10).strip()
    installer.require(state not in ('printing', 'paused'), 'Druck läuft oder ist pausiert. Recovery gesperrt.')


def archive(client):
    guard_stock(client)
    target = installer.BASE + '.recovery-' + time.strftime('%Y%m%d-%H%M%S', time.gmtime()) + '-' + secrets.token_hex(3)
    script = """from pathlib import Path
import os
base=Path(BASE);target=Path(TARGET)
assert base.resolve()==base and base.is_dir() and not base.is_symlink()
assert target.parent==base.parent and not target.exists() and not target.is_symlink()
assert not any(line.split()[1]==str(base) or line.split()[1].startswith(str(base)+'/') for line in Path('/proc/mounts').read_text().splitlines()),'Installation still mounted'
for process in Path('/proc').glob('[0-9]*/root'):
 try:
  root=process.resolve()
 except OSError:continue
 assert root!=base and base not in root.parents,'Process still uses installation'
os.rename(base,target);os.sync()
""".replace('BASE', repr(installer.BASE)).replace('TARGET', repr(target))
    installer.run(client, 'python3 -c ' + shlex.quote(script), timeout=30)
    return target


def restore_b(client, work, host, report):
    guard_stock(client)
    manifest = backup(work, host)
    # Device binding: immutable reference A plus this device's env must match.
    for n in (1, 6, 8):
        digest = installer.run(client, 'sha256sum /dev/mmcblk0p' + str(n), timeout=120).split()[0]
        installer.require(digest == manifest['partitions'][str(n)], 'Live device does not match backup; no restore performed')
    free = int(installer.run(client, "df -Pk /useremain | tail -n 1 | awk '{print $4}'").strip())
    installer.require(free > 524288, 'Recovery needs at least 512 MiB free data space')
    directory = '/useremain/kobranest-recovery-' + secrets.token_hex(8)
    installer.run(client, 'mkdir ' + directory)
    for n in (7, 9):
        destination = directory + '/restore-p' + str(n) + '.img'
        installer.put(client, destination, work / 'backup' / ('p' + str(n) + '.img'), 0o600)
        installer.require(installer.run(client, 'sha256sum ' + destination).split()[0] == manifest['partitions'][str(n)], 'Recovery upload checksum mismatch')
    # Preserve current B before writing; select the running A through the stock tool.
    for n in (7, 9):
        before = installer.run(client, 'sha256sum /dev/mmcblk0p' + str(n)).split()[0]
        destination = directory + '/before-p' + str(n) + '.img'
        installer.run(client, 'dd if=/dev/mmcblk0p' + str(n) + ' of=' + destination + ' bs=1048576 && sync')
        installer.require(installer.run(client, 'sha256sum ' + destination).split()[0] == before, 'Current B backup failed; no restore performed')
    guard_stock(client)
    installer.run(client, '/usr/bin/rk_ota --misc=now --mode=retry && sync')
    for n in (7, 9):
        report('Slot B p' + str(n), 'info', 'Sicherung wird geschrieben und vollständig zurückgelesen.')
        installer.run(client, 'dd if=' + directory + '/restore-p' + str(n) + '.img of=/dev/mmcblk0p' + str(n) + ' bs=1048576 && sync')
        installer.require(installer.run(client, 'sha256sum /dev/mmcblk0p' + str(n)).split()[0] == manifest['partitions'][str(n)], 'Slot B restore readback failed; stay in original A')
    for n in (1, 6, 8):
        installer.require(installer.run(client, 'sha256sum /dev/mmcblk0p' + str(n)).split()[0] == manifest['partitions'][str(n)], 'Protected partition changed; remain in A')
    return directory


def worker(app, action, printer):
    client = None
    try:
        installer.verify_package()
        client = app.connect('printer', printer)
        key = hashlib.sha256(client.get_transport().get_remote_server_key().asbytes()).hexdigest()
        status = probe(client)
        work = app.data_dir / 'devices' / printer['host']
        if action != 'diagnose':
            installer.require(key == app.recovery_binding['key'], 'SSH identity changed since recovery diagnosis')
            check_idle(client)
        if action == 'diagnose':
            valid = False
            try:
                backup(work, printer['host']);valid = True
            except (OSError, ValueError, KeyError, RuntimeError):pass
            app.row('Startsystem', 'ok', status['slot'])
            app.row('KobraNest-Dateien', 'info', 'Grunddateien vorhanden.' if status['base_files'] else 'Installation fehlt oder ist unvollständig.')
            app.row('PC-Sicherung', 'ok' if valid else 'warn', 'Sicherung vorhanden und geprüft.' if valid else 'Keine passende vollständige PC-Sicherung gefunden.')
            app.row('Recovery', 'info', 'Slot-B-Wiederherstellung nur aus Anycubic A. Kein USB-/Bootloader-Recovery enthalten.')
            with app.lock:
                app.recovery_binding = dict(host=printer['host'], key=key, time=time.time())
                app.state['recovery'] = dict(slot=status['slot'], can_stock=status['slot'] == 'B' and status['stock_helper'],
                                             can_archive=status['slot'] == 'A' and status['installation'], can_restore=status['slot'] == 'A' and valid)
        elif action == 'stock':
            installer.require(status['slot'] == 'B' and status['stock_helper'], 'Stock return requires running KobraNest and its return helper')
            installer.run(client, '/usr/local/sbin/s1-return-to-stock --prepare && sync', timeout=30)
            app.row('Anycubic', 'ok', 'Vorbereitet. Drucker fährt herunter. 15 Sekunden warten, ausschalten, zehn Sekunden warten und wieder einschalten.')
            client.exec_command('/sbin/poweroff')
        elif action == 'archive':
            target = archive(client)
            local = None
            if work.exists():
                local = work.with_name(work.name + '-recovery-' + secrets.token_hex(5))
                installer.require(work.resolve().parent == (app.data_dir / 'devices').resolve(), 'Unexpected local backup path')
                work.rename(local)
            app.row('Alte Installation gesichert', 'ok', target)
            if local:app.row('PC-Sicherung erhalten', 'ok', str(local))
            app.row('Neuinstallation', 'info', 'Jetzt im normalen Assistenten Geräte prüfen, Sicherung & Build und Installation neu ausführen.')
        elif action == 'restore_b':
            target = restore_b(client, work, printer['host'], app.row)
            app.row('Slot B wiederhergestellt', 'ok', 'Anycubic A bleibt aktiv. Vorheriger Slot B gesichert unter ' + target)
        if action != 'diagnose':app.recovery_binding = None
    except Exception as error:
        # TrustRequired is owned by assistant; do not introduce a circular import.
        if hasattr(error, 'details'):
            with app.lock:app.state['trust'].append(error.details)
            app.row('SSH-Vertrauen', 'warn', 'SSH-Fingerabdruck vor der ersten Anmeldung bestätigen.')
        else:
            detail = str(error)
            if printer['password']:detail = detail.replace(printer['password'], '[Passwort]')
            # Never return remote command strings or arbitrary authentication output.
            if 'Command failed' in detail:detail = 'Recovery-Schritt fehlgeschlagen. Diagnose erneut ausführen; Originalsystem nicht löschen.'
            app.row('Recovery angehalten', 'fail', detail[:1500] or type(error).__name__)
    finally:
        if client:client.close()
        with app.lock:
            app.state['running'] = False
            app.state['finished'] = True
