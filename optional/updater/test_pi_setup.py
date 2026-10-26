import importlib.util,io,json,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class PiSetupTests(unittest.TestCase):
 def test_existing_newer_pi_version_and_local_changes_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   command=[sys.executable,str(HERE/'install.py'),'--root',str(root),'--platform','pi','--if-missing']
   subprocess.run(command,check=True,capture_output=True)
   v=root/'usr/share/kobranest-update/version.json';state=json.loads(v.read_text());state['version']='0.1.9';v.write_text(json.dumps(state))
   module=root/'usr/local/lib/kobranest-update/updater.py';module.write_text(module.read_text()+'\n# existing custom version\n')
   for name in ('opt/ports.sh','etc/systemd/system/klipper.service','etc/systemd/system/ports.service'):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('preserve this')
   before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
   subprocess.run(command,check=True,capture_output=True)
   after={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
   self.assertEqual(before,after)
 def test_different_trust_key_refused_without_changes(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);args=[sys.executable,str(HERE/'install.py'),'--root',str(root),'--platform','pi','--if-missing']
   subprocess.run(args,check=True,capture_output=True);p=root/'usr/share/kobranest-update/release.pub';p.write_text('different key')
   version=(root/'usr/share/kobranest-update/version.json').read_bytes();result=subprocess.run(args,capture_output=True)
   self.assertNotEqual(result.returncode,0);self.assertEqual(p.read_text(),'different key');self.assertEqual((root/'usr/share/kobranest-update/version.json').read_bytes(),version)
 def test_existing_file_with_missing_api_not_silently_accepted(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);args=[sys.executable,str(HERE/'install.py'),'--root',str(root),'--platform','pi','--if-missing']
   subprocess.run(args,check=True,capture_output=True);module=root/'usr/local/lib/kobranest-update/updater.py';module.write_text('def status():return {}\n')
   before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()};r=subprocess.run(args,capture_output=True)
   self.assertNotEqual(r.returncode,0);self.assertIn(b'API incomplete',r.stderr);self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()})
 def test_transfer_archive_has_no_device_data_or_private_key(self):
  spec=importlib.util.spec_from_file_location('pi_setup',HERE/'setup.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tarfile.open(fileobj=io.BytesIO(m.package()),mode='r:gz') as tar:
   self.assertIn('release.pub',tar.getnames());self.assertIn('install.py',tar.getnames())
   for member in tar:
    self.assertTrue(member.isfile());self.assertNotIn('..',member.name);self.assertNotIn(b'-----BEGIN PRIVATE KEY-----',tar.extractfile(member).read())
 def test_ecm_service_preserves_mcu_files(self):
  import base64
  for transport in ('ecm',):
   with self.subTest(transport=transport),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);key=root/'printer.pub';key.write_text('ssh-ed25519 '+base64.b64encode(bytes(51)).decode())
    for name in ('opt/ports.sh','etc/systemd/system/klipper.service'):
     p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('keep')
    subprocess.run([sys.executable,str(HERE/'connection/install-pi.py'),'--root',str(root),'--pi-user','tester','--key',str(key),'--transport',transport],check=True,capture_output=True)
    self.assertEqual((root/'opt/ports.sh').read_text(),'keep');self.assertEqual((root/'etc/systemd/system/klipper.service').read_text(),'keep')
    config=(root/'etc/kobranest-serial-link'/('sshd_ecm_config' if transport=='ecm' else 'sshd_config')).read_text();self.assertIn('AllowUsers tester',config)
    if transport=='ecm':self.assertIn('ListenAddress 10.55.0.1',config);self.assertIn('Port 2223',config)
 def test_ecm_connection_does_not_use_third_serial_channel(self):
  spec=importlib.util.spec_from_file_location('connection_settings',HERE/'connection/serial_settings.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as tmp:
   m.PEER=Path(tmp)/'peer.json'
   for transport in ('ecm',):
    m.PEER.write_text(json.dumps({'pi_user':'tester','transport':transport}));cmd=m.command(m.DEFAULTS)
    self.assertEqual(any(s.startswith('ProxyCommand=') for s in cmd),transport=='serial')
    self.assertEqual(cmd[-1],'tester@'+('10.55.0.1' if transport=='ecm' else 'kobranest-pi-serial'))
   m.PEER.write_text(json.dumps({'pi_user':'tester','transport':'serial'}))
   with self.assertRaises(ValueError):m.command(m.DEFAULTS)
 def test_prepare_ecm_only_stages_files_and_keeps_klipper(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);path=root/'etc/systemd/system/klipper.service';path.parent.mkdir(parents=True);path.write_text('keep')
   subprocess.run([sys.executable,str(HERE/'connection/prepare-ecm.py'),'--root',str(root)],check=True,capture_output=True)
   self.assertEqual(path.read_text(),'keep');self.assertIn('functions/ecm.usb0',(root/'opt/ports.sh').read_text());self.assertIn('for i in 0 1;',(root/'opt/ports.sh').read_text())
 def test_public_key_comment_is_accepted_but_invalid_structure_rejected(self):
  import base64
  spec=importlib.util.spec_from_file_location('key_setup',HERE/'setup.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  raw=b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20'+bytes(range(32))
  key='ssh-ed25519 '+base64.b64encode(raw).decode()
  for suffix in ('',' root@kobra-s1',' tester comment with spaces'):
   self.assertEqual(m.printer_public_key((key+suffix+'\n').encode()),key)
  for bad in (key+'\n'+key,'ssh-ed25519 '+base64.b64encode(bytes(51)).decode(),'ssh-ed25519 NOT_BASE64','ssh-rsa AAAA'):
   with self.assertRaises(ValueError):m.printer_public_key(bad.encode())
if __name__=='__main__':unittest.main()
