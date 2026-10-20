#!/usr/bin/python3
"""Install the pinned S1 HelixScreen runtime and preserve KlipperScreen."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile

RELEASE_SHA = 'c6655f4fca7b004d26595a808db3da89e02207dc0c2aa6a87d384aa819235b66'
SOURCE = Path(__file__).resolve().parent


def put(path, data, mode=0o755):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + '.display-new')
    pending.write_bytes(data)
    pending.chmod(mode)
    os.replace(pending, path)


def configuration(template, ip, language):
    result = json.loads(json.dumps(template))
    result.update(wizard_completed=True, language=language, sounds_enabled=False,
                  ui_sounds_enabled=False, disable_sound=True, telemetry_enabled=False)
    result['input']['touch_device'] = '/dev/input/event0'
    result['display'].update(rotate=180, animations_enabled=False, screensaver_type=0,
                             sleep_sec=0, dim_sec=0, time_format=1)
    printer = result['printers']['default']
    printer.update(name='Kobra S1', moonraker_host=ip, moonraker_port=7125, moonraker_api_key=False)
    widgets = [
        {'id':'printer_image','col':0,'row':0,'colspan':2,'rowspan':2,'enabled':True},
        {'id':'temp_graph','col':2,'row':0,'colspan':4,'rowspan':2,'enabled':True},
        {'id':'ams','col':0,'row':2,'colspan':4,'rowspan':1,'enabled':True},
        {'id':'power_device','col':0,'row':3,'colspan':1,'rowspan':1,'enabled':True,
         'config':{'device':'Bauraumlicht','icon':'lightbulb_on'}},
    ]
    for col, name in enumerate(('fan_stack','temperature','bed_temperature','filament','notifications'), 1):
        widgets.append({'id':name,'col':col,'row':3,'colspan':1,'rowspan':1,'enabled':True})
    # Explicitly disable unused defaults so migration does not insert widgets
    # into cells already occupied by the compact S1 layout.
    unused = ('print_status','tips','shutdown','lock','network','firmware_restart',
              'tool_switcher','led','led_controls','fan','nozzle_temps','chamber_temperature',
              'temp_stack','thermistor','preheat','bypass','active_spool','humidity',
              'width_sensor','favorite_macro','macros','motion','clock','control_buttons',
              'job_queue','clog_detection','print_stats','gcode_console','camera')
    for name in unused:
        widgets.append({'id':name,'col':-1,'row':-1,'colspan':1,'rowspan':1,'enabled':False})
    printer['panel_widgets'] = {'home':{'main_page_index':0,'next_page_id':1,
                                       'pages':[{'id':'main','widgets':widgets}]}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--pi-ip', required=True)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--language', choices=('de','en'), default='de')
    parser.add_argument('--default', choices=('helix','klipperscreen'))
    parser.add_argument('--start', action='store_true')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    ip = str(ipaddress.IPv4Address(args.pi_ip))
    if args.start:
        assert root == Path('/') and 'busybox' in os.readlink('/proc/1/exe')
    assert (root/'etc/s1-boot-ready').is_file(), 'Kobrian root required'
    assert (root/'opt/KlipperScreen/screen.py').is_file(), 'Keep working KlipperScreen first'
    archive = args.archive or SOURCE/'helixscreen-pi32-v1.0.5.tar.gz'
    if not archive.exists():
        archive = SOURCE.parents[1]/'payload/helixscreen-pi32-v1.0.5.tar.gz'
    digest = hashlib.sha256()
    with archive.open('rb') as file:
        for block in iter(lambda:file.read(1048576), b''):
            digest.update(block)
    assert digest.hexdigest() == RELEASE_SHA, 'HelixScreen release checksum mismatch'
    destination = root/'opt/helixscreen'
    marker = destination/'.kobrian-release'
    if destination.exists():
        assert marker.is_file() and marker.read_text().strip() == RELEASE_SHA, 'Existing unknown HelixScreen installation; not overwritten'
    else:
        staging = root/'opt/helixscreen-install-pending'
        assert not staging.exists(), 'Previous partial install present; inspect before retry'
        staging.mkdir(parents=True)
        with tarfile.open(archive, 'r:gz') as tar:
            for item in tar:
                assert item.name == 'helixscreen' or item.name.startswith('helixscreen/')
                assert '..' not in Path(item.name).parts
            tar.extractall(staging, filter='data')
        os.replace(staging/'helixscreen', destination)
        staging.rmdir()
        put(marker, (RELEASE_SHA+'\n').encode(), 0o644)
    settings = destination/'config/settings.json'
    if not settings.exists():
        template = json.loads((destination/'config/settings.json.template').read_text())
        put(settings, (json.dumps(configuration(template, ip, args.language), indent=2)+'\n').encode(), 0o600)
    else:
        json.loads(settings.read_text())  # Never reset user settings on reinstall.
    command = ['/usr/bin/ldd', '/opt/helixscreen/bin/helix-screen-fbdev']
    if root != Path('/'):
        command = [shutil.which('chroot') or '/usr/sbin/chroot', str(root)] + command
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert 'not found' not in result.stdout+result.stderr, 'Runtime library missing'
    service = root/'usr/local/sbin/s1-service'
    text = service.read_text()
    previous = 'exec /usr/local/sbin/s1-gui >>/var/log/s1-gui.log 2>&1'
    replacement = 'exec /usr/local/sbin/s1-ui >>/var/log/s1-gui.log 2>&1'
    assert previous in text or replacement in text, 'Unknown GUI dispatcher'
    backup = root/'var/backups/kobrian-display'
    backup.mkdir(parents=True, exist_ok=True)
    if not (backup/'s1-service').exists():
        shutil.copy2(service, backup/'s1-service')
    for name in ('s1-ui','s1-ui-select','s1-helix'):
        put(root/'usr/local/sbin'/name, (SOURCE/name).read_bytes())
    put(service, text.replace(previous, replacement).encode())
    selection = root/'etc/s1-ui'
    target = args.default or (selection.read_text().strip() if selection.exists() else 'helix')
    assert target in ('helix','klipperscreen')
    put(selection, (target+'\n').encode(), 0o644)
    os.sync()
    if args.start:
        # Only the init-owned GUI supervisor is stopped. MCU services are untouched.
        candidates = []
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():
                continue
            try:
                argv = (proc/'cmdline').read_bytes().split(b'\0')
                parent = next(line for line in (proc/'status').read_text().splitlines() if line.startswith('PPid:')).split()[1]
            except (OSError, StopIteration):
                continue
            if parent == '1' and any(arg in (b'/usr/local/sbin/s1-gui', b'/usr/local/sbin/s1-helix', b'/usr/local/sbin/s1-ui') for arg in argv):
                candidates.append(int(proc.name))
        assert len(candidates) == 1, 'Expected exactly one init GUI supervisor'
        os.kill(candidates[0], signal.SIGTERM)
    print('HelixScreen installed; KlipperScreen preserved; default:', target)


if __name__ == '__main__':
    main()
