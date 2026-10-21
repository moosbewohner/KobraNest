#!/usr/bin/env python3
"""Local Kobrian setup assistant with explicit preparation and activation steps."""
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import secrets
import sys
import threading
from types import SimpleNamespace
import webbrowser

import paramiko
import installer

PACKAGE = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
installer.PACKAGE = PACKAGE


def fingerprint(key):
    return 'SHA256:' + base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')


class TrustRequired(Exception):
    def __init__(self, role, host, key):
        self.details = dict(role=role, host=host, algorithm=key.get_name(), fingerprint=fingerprint(key))


class HostPolicy(paramiko.MissingHostKeyPolicy):
    def __init__(self, role, approved, trusted=()):
        self.role, self.approved = role, approved
        self.trusted = frozenset(trusted)

    def missing_host_key(self, client, hostname, key):
        if fingerprint(key) not in self.trusted and not secrets.compare_digest(self.approved, fingerprint(key)):
            raise TrustRequired(self.role, hostname, key)
        client.get_host_keys().add(hostname, key.get_name(), key)


def validate(data):
    result = {}
    for role in ('printer', 'pi'):
        source = data[role]
        host = str(ipaddress.IPv4Address(source['host']))
        if not ipaddress.IPv4Address(host).is_private or ipaddress.IPv4Address(host).is_loopback:
            raise ValueError('Bitte eine lokale Geräte-IP eingeben.')
        user = source['user'].strip()
        password = source.get('password', '')
        approved = source.get('approved', '')
        if not user or len(user) > 64 or len(password) > 512 or len(approved) > 120:
            raise ValueError('Ungültige SSH-Zugangsdaten.')
        result[role] = dict(host=host, user=user, password=password, approved=approved)
    if result['printer']['host'] == result['pi']['host']:
        raise ValueError('Drucker und Pi benötigen unterschiedliche IP-Adressen.')
    return result


def public_ssh_key(value):
    if not isinstance(value,str) or len(value)>16384:
        raise ValueError('Ungültiger öffentlicher SSH-Schlüssel.')
    value=value.strip()
    if not value:return ''
    if '\n' in value or '\r' in value or 'PRIVATE KEY' in value:
        raise ValueError('Nur einen öffentlichen SSH-Schlüssel aus einer .pub-Datei verwenden.')
    parts=value.split()
    if len(parts)<2 or parts[0] not in ('ssh-ed25519','ssh-rsa','ecdsa-sha2-nistp256','ecdsa-sha2-nistp384','ecdsa-sha2-nistp521'):
        raise ValueError('Ungültiger öffentlicher SSH-Schlüssel.')
    try:
        import base64
        paramiko.PKey.from_type_string(parts[0],base64.b64decode(parts[1],validate=True))
    except Exception:
        raise ValueError('Ungültiger öffentlicher SSH-Schlüssel.') from None
    return parts[0]+' '+parts[1]+(' '+' '.join(parts[2:]) if len(parts)>2 else '')


def stage_ssh_key(c,key):
    if not key:return
    import shlex
    script="""from pathlib import Path
import os
root=Path(ROOT)
assert root.resolve()==root and root.is_dir()
home=root/'root'; directory=home/'.ssh'; target=directory/'authorized_keys'
assert not home.is_symlink() and not directory.is_symlink() and not target.is_symlink()
directory.mkdir(mode=0o700,exist_ok=True);directory.chmod(0o700)
old=target.read_text() if target.exists() else ''
key=KEY
if not any(line.split()[:2]==key.split()[:2] for line in old.splitlines()):
    temporary=directory/'authorized_keys.kobrian-new'
    assert not temporary.exists() and not temporary.is_symlink()
    with temporary.open('x') as stream:stream.write(old.rstrip()+'\\n'+key+'\\n' if old.strip() else key+'\\n')
    temporary.chmod(0o600);os.replace(temporary,target)
target.chmod(0o600)
""".replace('ROOT',repr(installer.ROOT)).replace('KEY',repr(key))
    installer.run(c,'python3 -',stdin=script)


class Assistant:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.lock = threading.Lock()
        self.state = dict(running=False, rows=[], trust=[], finished=False)
        self.checked_hosts = None

    def snapshot(self):
        with self.lock:
            return json.loads(json.dumps(self.state))

    def row(self, title, status, detail):
        with self.lock:
            self.state['rows'].append(dict(title=title, status=status, detail=detail))

    def start(self, data):
        credentials = validate(data)
        with self.lock:
            if self.state['running']:
                raise RuntimeError('Eine Prüfung läuft bereits.')
            self.state = dict(running=True, rows=[], trust=[], finished=False)
        threading.Thread(target=self.check, args=(credentials,), daemon=True).start()

    def connect(self, role, credentials, namespace=None):
        c = paramiko.SSHClient()
        known = self.data_dir / ((namespace or role) + '_known_hosts')
        trusted = set()
        if role == 'printer':
            # Stock and Debian legitimately share an IP but have different keys.
            # Keep each approved identity; never replace an old key on a switch.
            files = {self.data_dir / 'printer_known_hosts', self.data_dir / 'printer_debian_known_hosts'}
            files.update(self.data_dir.glob('printer-slot-*.known_hosts'))
            for path in files:
                if path.exists():
                    entries = paramiko.HostKeys(str(path)).lookup(credentials['host'])
                    if entries:
                        trusted.update(fingerprint(key) for key in entries.values())
        elif known.exists():
            c.load_host_keys(str(known))
        c.set_missing_host_key_policy(HostPolicy(role, credentials['approved'], trusted))
        try:
            c.connect(credentials['host'], username=credentials['user'], password=credentials['password'],
                      allow_agent=False, look_for_keys=False, timeout=30, auth_timeout=30, banner_timeout=30)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            if role == 'printer':
                key = c.get_transport().get_remote_server_key()
                known = self.data_dir / ('printer-slot-' + hashlib.sha256(key.asbytes()).hexdigest() + '.known_hosts')
            c.save_host_keys(str(known))
            return c
        except Exception:
            c.close()
            raise

    def check_printer(self, c):
        run = lambda cmd: installer.run(c, cmd, timeout=90).strip()
        cmdline = run('cat /proc/cmdline')
        if 'root=/dev/mmcblk0p9' in cmdline:
            self.row('Drucker', 'ok', 'KobraNest läuft bereits auf Slot B.')
            self.row('Neuinstallation', 'info', 'Bestehende Installation bleibt erhalten. Keine Neuinstallation vorbereitet.')
            import shlex
            # Import only definitions; never invoke the boot-confirmation main().
            script = "import json,runpy; from pathlib import Path; h=runpy.run_path('/usr/local/sbin/s1-health',run_name='kobrian_read_only'); s=h['local_status'](); print(json.dumps({'healthy':h['acceptable'](s),'pending':h['MARKER'].exists(),'status':s}))"
            health = json.loads(run('python3 -c ' + shlex.quote(script)))
            status, detail = boot_summary(health)
            self.row('Lokale Startprüfung', status, detail)
            return
        self.row('Firmwareprüfung', 'info', 'Originalsystem, Partitionslayout und Prüfsummen werden gelesen …')
        installer.inspect(c)
        self.row('Modell & Firmware', 'ok', 'ARMv7, Original-Slot A und die geprüften Firmware-Hashes stimmen überein.')
        available = int(run("df -Pk /useremain | tail -n 1 | awk '{print $4}'"))
        self.row('Druckerspeicher', 'ok' if available > 1600000 else 'fail', f'{available // 1024} MiB frei; benötigt: mehr als 1562 MiB.')
        existing = run('if test -e /useremain/s1-klipperscreen-test; then echo existing; else echo fresh; fi')
        self.row('Installationsziel', 'ok' if existing == 'fresh' else 'warn',
                 'Noch keine KobraNest-Installation vorhanden.' if existing == 'fresh' else 'KobraNest-Dateien vorhanden. Keine automatische Überschreibung.')
        rinkhals = run('if test -r /useremain/rinkhals/.current/tools.sh; then echo yes; else echo no; fi')
        self.row('Rinkhals', 'ok' if rinkhals == 'yes' else 'warn',
                 'Framework für die Rückkehr-App vorhanden.' if rinkhals == 'yes' else 'Framework fehlt; Rückkehr-App noch nicht installierbar.')

    def check_pi(self, c):
        run = lambda cmd: installer.run(c, cmd, timeout=20).strip()
        self.row('Raspberry Pi', 'ok', 'SSH verbunden · ' + run('uname -m'))
        docker = run('if sudo -n docker info >/dev/null 2>&1; then echo ready; else echo missing; fi')
        self.row('Build-Voraussetzung', 'ok' if docker == 'ready' else 'warn',
                 'Docker über sudo ohne Passwort verfügbar.' if docker == 'ready' else 'Docker oder sudo-Freigabe fehlt. Es wird nichts nachinstalliert.')
        script = "import json,urllib.request; r=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/info',timeout=5)); print(json.dumps(r.get('result',{})))"
        import shlex
        info = json.loads(run('python3 -c ' + shlex.quote(script)))
        state = info.get('state', 'unbekannt')
        self.row('Moonraker / Klipper', 'ok' if state == 'ready' else 'warn', 'Klipper-Status: ' + state)
        script = "import json,urllib.request; r=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?print_stats',timeout=5)); print(r.get('result',{}).get('status',{}).get('print_stats',{}).get('state','unknown'))"
        try:
            print_state = run('python3 -c ' + shlex.quote(script))
        except RuntimeError:
            print_state = 'unknown'
        self.row('Druckstatus', 'warn' if print_state in ('printing', 'paused', 'unknown') else 'ok',
                 'Nur gelesen: ' + print_state + '. Es werden keine Dienste oder Druckaufträge verändert.')
        for number in (1, 2):
            service = run(f'systemctl is-active mcu{number}.service 2>/dev/null || true')
            self.row(f'MCU-Tunnel {number}', 'ok' if service == 'active' else 'info', service or 'Noch nicht eingerichtet')

    def check(self, credentials):
        self.checked_hosts = None
        try:
            try:
                installer.verify_package()
                self.row('Installationspaket', 'ok', 'Dateien und SHA-256-Prüfsummen vollständig geprüft.')
            except Exception:
                self.row('Installationspaket', 'fail', 'Paket unvollständig oder verändert. Originalpaket neu entpacken.')
                return
            for role, label, check in (('printer', 'Drucker', self.check_printer), ('pi', 'Raspberry Pi', self.check_pi)):
                c = None
                try:
                    c = self.connect(role, credentials[role])
                    check(c)
                except TrustRequired as exc:
                    with self.lock:
                        self.state['trust'].append(exc.details)
                    self.row(label, 'warn', 'SSH-Fingerabdruck vor der ersten Anmeldung bestätigen.')
                except paramiko.BadHostKeyException:
                    self.row(label, 'fail', 'SSH-Schlüssel hat sich geändert. Verbindung gesperrt; Schlüssel zuerst unabhängig prüfen.')
                except paramiko.AuthenticationException:
                    self.row(label, 'fail', 'SSH-Anmeldung fehlgeschlagen. Benutzername und Passwort prüfen.')
                except Exception as exc:
                    # Never echo supplied credentials, commands, or authentication responses.
                    self.row(label, 'fail', 'Prüfung fehlgeschlagen (' + type(exc).__name__ + '). Verbindung und Voraussetzungen prüfen.')
                finally:
                    if c:
                        c.close()
        finally:
            with self.lock:
                if not self.state['trust'] and not any(row['status'] == 'fail' for row in self.state['rows']):
                    self.checked_hosts = {role: item['host'] for role, item in credentials.items()}
            for item in credentials.values():
                item.clear()
            with self.lock:
                self.state['running'] = False
                self.state['finished'] = True

    def operate(self, data):
        action = data.get('action')
        if action not in ('prepare', 'stage', 'activate', 'status'):
            raise ValueError('Unbekannter Installationsschritt.')
        credentials = validate(data)
        # Use the exact same validation as the CLI without saving passwords.
        settings = data.get('settings', {})
        if not isinstance(settings, dict):
            raise ValueError('Netzwerkeinstellungen fehlen.')
        settings = dict(settings, printer_ip=credentials['printer']['host'], pi_ip=credentials['pi']['host'])
        for key in ('printer_ip', 'pi_ip', 'gateway'):
            settings[key] = str(ipaddress.IPv4Address(settings[key]))
        prefix = settings.get('prefix')
        if type(prefix) is not int or not 1 <= prefix <= 30:
            raise ValueError('Ungültige Netzmaske.')
        subnet = ipaddress.IPv4Network(settings['printer_ip'] + '/' + str(prefix), strict=False)
        if ipaddress.IPv4Address(settings['gateway']) not in subnet:
            raise ValueError('Gateway liegt außerhalb des Druckernetzes.')
        transport=settings.get('tunnel_mode','usb')
        if transport not in ('usb','network'):
            raise ValueError('Ungültige MCU-Verbindung.')
        settings = {key: settings[key] for key in ('printer_ip', 'pi_ip', 'gateway', 'prefix')}
        settings['tunnel_mode']=transport
        settings['light_auto_on'] = True
        if data.get('risk_accepted') is not True:
            raise ValueError('Bitte zuerst den Warnhinweis bestätigen.')
        expected = {step: 'YES' for step in ('prepare','stage','activate')}
        if action != 'status':
            if data.get('idle_confirmed') is not True or data.get('confirmation') != expected[action]:
                raise ValueError('Stillstand und dieser Schritt müssen ausdrücklich bestätigt werden.')
            if self.checked_hosts != {role: item['host'] for role, item in credentials.items()}:
                raise ValueError('Diese Geräte zuerst erfolgreich prüfen.')
        ssh_key = public_ssh_key(data.get('ssh_public_key',''))
        root_password = data.get('root_password') or 'rockchip'
        if not isinstance(root_password, str) or len(root_password) > 512 or any(char in root_password for char in ':\r\n'):
            raise ValueError('Ungültiges Debian-root-Passwort.')
        if action == 'activate' and data.get('pi_ready') is not True:
            raise ValueError('Pi-Tunnelkonfiguration vor dem Bootwechsel bestätigen.')
        with self.lock:
            if self.state['running']:
                raise RuntimeError('Ein Vorgang läuft bereits.')
            self.state = dict(running=True, rows=[], trust=[], finished=False, action=action)
        threading.Thread(target=self.install_step, args=(action, credentials, settings, root_password, action == 'stage' and data.get('transfer_light') is True, ssh_key), daemon=False).start()

    def install_step(self, action, credentials, settings, root_password, transfer_light=False, ssh_key=''):
        work = self.data_dir / 'devices' / settings['printer_ip']
        secrets_to_hide = [root_password] + [item['password'] for item in credentials.values()]
        def clean(value):
            result = str(value)
            for secret in secrets_to_hide:
                if secret:
                    result = result.replace(secret, '[Passwort]')
            return result
        def emit(*parts, **kwargs):
            self.row('Fortschritt', 'info', clean(' '.join(str(item) for item in parts)))
        original = {name: getattr(installer, name, None) for name in ('connect', 'getpass', 'input', 'print')}
        clients = []
        def connect(host, user, known, default_password=None):
            role = 'printer' if host == settings['printer_ip'] else 'pi' if host == settings['pi_ip'] else None
            if role is None or user != credentials[role]['user']:
                raise RuntimeError('Unerwartetes Installationsziel.')
            c = self.connect(role, credentials[role], 'printer_debian' if action == 'status' and role == 'printer' else None)
            clients.append(c)
            return c
        def answer(prompt):
            if action == 'activate' and prompt.startswith('Type INSTALL B '):
                return 'INSTALL B ' + settings['printer_ip']
            raise RuntimeError('Unerwartete Bestätigungsabfrage; Vorgang abgebrochen.')
        try:
            installer.verify_package()
            work.mkdir(parents=True, exist_ok=True)
            with self.lock:
                self.state['workspace'] = str(work)
            if action != 'status':
                # Always recheck the Pi immediately before any device writes.
                pi = connect(settings['pi_ip'], credentials['pi']['user'], None)
                script = "import json,urllib.request; r=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?print_stats',timeout=5)); print(r.get('result',{}).get('status',{}).get('print_stats',{}).get('state','unknown'))"
                import shlex
                try:
                    current = installer.run(pi, 'python3 -c ' + shlex.quote(script), timeout=15).strip()
                except RuntimeError:
                    current = 'unknown'
                installer.require(current not in ('printing', 'paused'), 'Druck läuft oder ist pausiert. Keine Installation.')
                pi.close()
            # Only this worker can use the CLI bridge; the HTTP API admits one job.
            installer.connect = connect
            installer.getpass = SimpleNamespace(getpass=lambda prompt: root_password)
            installer.input = answer
            installer.print = emit
            args = SimpleNamespace(builder_user=credentials['pi']['user'])
            if action == 'prepare':
                installer.require(credentials['printer']['user'] == 'root', 'Installation benötigt root auf dem Drucker.')
                # Guard before making the PC backup or writing the Pi build directory.
                c = connect(settings['printer_ip'], 'root', None)
                installer.inspect(c)
                installer.run(c, 'test ! -e ' + installer.BASE)
                c.close()
            if action in ('stage', 'activate'):
                installer.require((work / 'device.json').is_file(), 'Zuerst Sicherung und Build ausführen.')
            if action == 'activate':
                installer.require((work / 'assistant-addons.json').is_file(), 'Zusatzmodule noch nicht vollständig vorbereitet. Bootwechsel gesperrt.')
                c = connect(settings['printer_ip'], 'root', None)
                for remote, local in (
                    (installer.ROOT + '/usr/local/sbin/s1-web', PACKAGE / 'optional/kobrian-web/s1-web'),
                    (installer.ROOT + '/opt/kobrian-web/index.html', PACKAGE / 'optional/kobrian-web/index.html'),
                    ('/useremain/home/rinkhals/apps/kobrian-start/app.sh', PACKAGE / 'optional/kobrian-start/app.sh')):
                    installer.require(installer.run(c, 'sha256sum ' + remote).split()[0] == installer.sha(local),
                                      'Zusatzmodul fehlt oder wurde verändert. Bootwechsel gesperrt.')
                c.close()
            if action == 'status':
                c = connect(settings['printer_ip'], 'root', None)
                installer.require('root=/dev/mmcblk0p9' in installer.run(c, 'cat /proc/cmdline'),
                                  'Startprüfung benötigt KobraNest auf Slot B.')
                self.check_printer(c)
                c.close()
            elif action == 'stage' and (work / 'staged.json').exists():
                # Resume only the add-ons after a successful CLI stage, never
                # remove or blindly overwrite a partial rootfs installation.
                manifest = installer.device(work, settings)
                c = connect(settings['printer_ip'], 'root', None)
                installer.confirm_live(c, manifest)
                installer.run(c, 'test -x ' + installer.ROOT + '/usr/local/sbin/s1-boot && test -f ' + installer.ROOT + '/etc/s1-settings.json')
                c.close()
                emit('Vorbereitete Debian-Dateien vorhanden; nur Zusatzmodule fortsetzen.')
            else:
                getattr(installer, action)(args, settings, work)
            if action == 'stage':
                self.stage_addons(connect, settings, work)
                if ssh_key:
                    c = connect(settings['printer_ip'], 'root', None)
                    stage_ssh_key(c,ssh_key)
                    c.close()
                    self.row('SSH-Schlüssel', 'ok', 'Öffentlicher Schlüssel für root in KobraNest hinterlegt.')
                if transfer_light:
                    pi = connect(settings['pi_ip'], credentials['pi']['user'], None)
                    import base64, shlex
                    template = base64.b64encode((PACKAGE / 'source/bauraumlicht.cfg.template').read_bytes()).decode()
                    script = (PACKAGE / 'source/install-pi-light.py').read_text(encoding='utf-8')
                    result = installer.run(pi, 'python3 - ' + shlex.quote(settings['printer_ip']) + ' ' + shlex.quote(template), stdin=script, timeout=75)
                    self.row('Pi-Bauraumlicht', 'ok', result.strip())
                    pi.close()
            if action == 'prepare':
                target = work / 'pi-config'
                target.mkdir(exist_ok=True)
                for n in (1, 2):
                    source = (PACKAGE / f'source/mcu{n}.service.template').read_text()
                    (target / f'mcu{n}.service').write_bytes(source.replace('@PRINTER_IP@', settings['printer_ip']).encode())
                source = (PACKAGE / 'source/bauraumlicht.cfg.template').read_text()
                (target / 'bauraumlicht.cfg').write_bytes(source.replace('192.168.10.67', settings['printer_ip']).encode())
                (work / 'settings.json').write_text(json.dumps(settings, indent=2) + '\n')
                self.row('Pi-Konfiguration', 'info', 'Passende Dienstdateien erzeugt: ' + str(target) + '. Anleitung: docs/PI.md.')
            self.row('Schritt abgeschlossen', 'ok', {
                'prepare': 'Originalpartitionen gesichert und geprüft. Bootdateien vorbereitet; noch keine Druckerpartition geschrieben.',
                'stage': 'HelixScreen, KlipperScreen, WebUI und Rinkhals-Rückkehr-App vorbereitet. Bootpartitionen unverändert. Pi-Konfiguration vor Aktivierung prüfen.',
                'activate': 'Slot B geschrieben, Rückleseprüfung abgeschlossen und Neustart angefordert. Anschließend Start prüfen.',
                'status': 'Startprüfung vom Drucker gelesen.'}[action])
            with self.lock:
                self.state['completed_action'] = action
            (work / 'assistant-last-step.json').write_text(json.dumps({'completed_action': action}) + '\n')
        except TrustRequired as exc:
            with self.lock:
                self.state['trust'].append(exc.details)
            self.row('SSH-Schlüssel', 'warn', 'Neuen Schlüssel unabhängig prüfen und bestätigen. Kein automatischer Schlüsselwechsel.')
        except paramiko.BadHostKeyException:
            self.row('SSH-Schlüssel', 'fail', 'Gespeicherter Schlüssel stimmt nicht überein. Verbindung abgebrochen.')
        except Exception as exc:
            self.row('Vorgang angehalten', 'fail', clean(str(exc))[:5000])
        finally:
            for name, previous in original.items():
                if previous is None:
                    installer.__dict__.pop(name, None)
                else:
                    setattr(installer, name, previous)
            for c in clients:
                c.close()
            for item in credentials.values():
                item.clear()
            secrets_to_hide.clear()
            root_password = None
            with self.lock:
                self.state['running'] = False
                self.state['finished'] = True

    def stage_addons(self, connect, settings, work):
        """Populate the inactive Debian tree; no service startup or boot writes."""
        c = connect(settings['printer_ip'], 'root', None)
        root = installer.ROOT
        installer.stage_display(c, settings)
        web = PACKAGE / 'optional/kobrian-web'
        self.row('Zusatzmodule', 'info', 'WebUI und Rinkhals-Rückkehr-App werden vorbereitet.')
        installer.run(c, 'test -r /useremain/rinkhals/.current/tools.sh && mkdir -p ' + root + '/opt/kobrian-web-installer')
        for name in ('s1-web', 'index.html', 'install.py', 's1-return-to-stock', 's1-camera'):
            installer.put(c, root + '/opt/kobrian-web-installer/' + name, web / name)
        installer.run(c, 'chroot ' + root + ' /usr/bin/python3 /opt/kobrian-web-installer/install.py --root / --pi-ip ' + settings['pi_ip'])
        appdir = '/useremain/home/rinkhals/apps/kobrian-start'
        existing = installer.run(c, 'if test -e ' + appdir + '; then echo existing; else echo missing; fi').strip()
        if existing == 'existing':
            for name in ('app.sh', 'app.json'):
                expected = installer.sha(PACKAGE / 'optional/kobrian-start' / name)
                installer.require(installer.run(c, 'sha256sum ' + appdir + '/' + name).split()[0] == expected,
                                  'Andere Rückkehr-App vorhanden; keine automatische Überschreibung.')
        else:
            installer.run(c, 'test ! -e ' + appdir + '.installing && mkdir -p ' + appdir + '.installing')
            for name in ('app.sh', 'app.json', '.disabled'):
                installer.put(c, appdir + '.installing/' + name, PACKAGE / 'optional/kobrian-start' / name, 0o755 if name == 'app.sh' else 0o644)
            installer.run(c, '/bin/sh -n ' + appdir + '.installing/app.sh && mv ' + appdir + '.installing ' + appdir + ' && sync')
        c.close()
        (work / 'assistant-addons.json').write_text(json.dumps({'web': True, 'rinkhals_return_app': True, 'ui': 'helix', 'klipperscreen_alternative': True}) + '\n')


def boot_summary(health):
    if health.get('pending'):
        return 'warn', 'Bootbestätigung noch ausstehend. Der Fehlstartmarker ist vorhanden.'
    if health.get('healthy'):
        return 'ok', 'Lokales System betriebsbereit. Kein offener Fehlstartmarker.'
    return 'warn', 'Lokale Dienste noch nicht vollständig verfügbar. Erneut prüfen.'


def make_server(assistant, port=0):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def reply(self, status, payload, kind='application/json; charset=utf-8'):
            body = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            return self.valid_host() and secrets.compare_digest(self.headers.get('X-Kobrian-Token', ''), token)

        def do_GET(self):
            if not self.valid_host():
                return self.reply(403, {'error': 'Ungültiger Zugriff.'})
            if self.path == '/':
                return self.reply(200, (PACKAGE / 'assistant/index.html').read_bytes(), 'text/html; charset=utf-8')
            if self.path == '/api/status' and self.authorized():
                return self.reply(200, assistant.snapshot())
            self.reply(403, {'error': 'Zugriff nicht erlaubt.'})

        def do_POST(self):
            origin = f'http://127.0.0.1:{self.server.server_port}'
            if not self.authorized() or self.headers.get('Origin') != origin:
                return self.reply(403, {'error': 'Zugriff nicht erlaubt.'})
            if self.path not in ('/api/check', '/api/operate'):
                return self.reply(404, {'error': 'Unbekannte Aktion.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16384:
                    raise ValueError('Ungültige Anfragelänge.')
                data = json.loads(self.rfile.read(length))
                if data.get('risk_accepted') is not True:
                    raise ValueError('Bitte zuerst den Warnhinweis bestätigen.')
                if self.path == '/api/check':
                    assistant.start(data)
                else:
                    assistant.operate(data)
                self.reply(202, {'started': True})
            except RuntimeError as exc:
                self.reply(409, {'error': str(exc)})
            except (ValueError, KeyError, TypeError) as exc:
                self.reply(400, {'error': str(exc) if isinstance(exc, ValueError) else 'Eingaben unvollständig oder ungültig.'})

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server, token


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    data = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.local/share'))) / 'Kobrian/Assistant'
    server, token = make_server(Assistant(data), args.port)
    url = f'http://127.0.0.1:{server.server_port}/#' + token
    print('KobraNest-Assistent: Installation nur nach ausdruecklicher Bestaetigung. Mit Strg+C beenden.')
    print(url, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
