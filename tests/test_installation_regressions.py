"""Regressions for activation before flashing and camera provisioning."""
import ast
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]


class InstallationRegressions(unittest.TestCase):
    def test_activation_accepts_native_or_legacy_and_keeps_other_guards(self):
        tree = ast.parse((BASE / 'installer.py').read_text(encoding='utf-8'))
        activate = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'activate')
        block = next(node for node in activate.body if isinstance(node, ast.Try))
        gate = block.body[1].value.args[1]
        shell = 'C:/Program Files/Git/bin/bash.exe' if os.name == 'nt' else shutil.which('bash')
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / 'rootfs'
            required = ['etc/s1-network.conf', 'etc/shadow', 'usr/local/sbin/s1-ui-select', 'opt/KlipperScreen/screen.py']
            for name in required:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'#!/bin/sh\nexit 0\n')
                path.chmod(0o755)
            binary_dir = root / 'opt/helixscreen/bin'
            binary_dir.mkdir(parents=True)
            command = eval(compile(ast.Expression(gate), '<activation gate>', 'eval'), {'ROOT': root.as_posix(), 'BASE': base.as_posix()})

            def accepted():
                return subprocess.run([shell, '-c', command], capture_output=True).returncode == 0

            self.assertFalse(accepted())
            for name in ('helix-screen', 'helix-screen-fbdev'):
                binary = binary_dir / name
                binary.write_bytes(b'#!/bin/sh\nexit 0\n')
                binary.chmod(0o755)
                self.assertTrue(accepted(), name)
                (base / 'boot-attempt').write_text('pending')
                self.assertFalse(accepted(), 'A pending boot attempt must block either binary')
                (base / 'boot-attempt').unlink()
                (root / required[0]).unlink()
                self.assertFalse(accepted(), 'The legacy OR must not bypass common prerequisites')
                (root / required[0]).write_text('network')
                binary.unlink()

    def test_camera_defaults_and_existing_settings_through_installer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'etc').mkdir()
            (root / 'usr/local/sbin').mkdir(parents=True)
            (root / 'etc/inittab').write_text('::once:/usr/local/sbin/s1-health\n')
            (root / 'usr/local/sbin/s1-service').write_text('case "${1:-}" in\n*) exit 1;;\nesac\n')
            script = BASE / 'optional/kobrian-web/install.py'
            arguments = [str(script), '--root', str(root), '--pi-ip', '192.0.2.10']

            def install():
                with patch.object(sys, 'argv', arguments), patch('subprocess.run'), patch.object(os, 'sync', create=True):
                    runpy.run_path(str(script), run_name='__main__')

            install()
            path = root / 'etc/s1-camera.json'
            defaults = json.loads(path.read_text())
            self.assertTrue(defaults['enabled'])
            self.assertEqual((defaults['resolution'], defaults['fps']), ('640x480', 5))
            for enabled in (True, False):
                existing = json.dumps({'enabled': enabled, 'resolution': '1280x720', 'fps': 15, 'slowdown': False}).encode()
                path.write_bytes(existing)
                install()
                self.assertEqual(path.read_bytes(), existing)


if __name__ == '__main__':
    unittest.main()
