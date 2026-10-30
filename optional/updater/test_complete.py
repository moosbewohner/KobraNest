import importlib.util,io,json,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('complete_setup',HERE/'complete.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CompleteTests(unittest.TestCase):
 def test_versions_and_platforms(self):
  self.assertTrue(m.needs_update({'platform':'printer','version':'0.1.4'},'printer'))
  self.assertFalse(m.needs_update({'platform':'pi','version':m.NUMBER},'pi'))
  for info,kind in [({'platform':'printer','version':'0.1.3'},'pi'),({'platform':'pi','version':'9999.0.0'},'pi')]:
   with self.assertRaises(ValueError):m.needs_update(info,kind)
 def test_wrong_bundle_rejected_before_signature_or_device_changes(self):
  with tempfile.TemporaryDirectory() as tmp:
   here=Path(tmp);p=m.package_path(here,'pi');p.parent.mkdir()
   with tarfile.open(p,'w:gz') as tar:
    for name,data in {'manifest.json':json.dumps({'version':m.NUMBER,'platform':'printer'}).encode(),'manifest.sig':bytes(64)}.items():
     info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
   with patch.object(m.subprocess,'run') as command:
    with self.assertRaises(ValueError):m.validate_bundle(here)
    command.assert_not_called()
 def test_remote_update_resumes_and_never_uses_wrong_platform(self):
  calls=[]
  def remote(command,data=None):
   calls.append((command,data))
   return json.dumps({'platform':'printer','version':'0.1.4'}).encode() if command.startswith('cat /usr/share') else b'OK'
  with tempfile.TemporaryDirectory() as tmp:
   here=Path(tmp);p=m.package_path(here,'printer');p.parent.mkdir();p.write_bytes(b'PACKAGE');m.bridge_path(here).write_bytes(b'BRIDGE')
   m.update_remote(here,remote,'/tmp/known')
  self.assertEqual(calls[1],('cat > /tmp/known/printer-bridge.tar.gz',b'BRIDGE'))
  self.assertEqual(calls[4],('cat > /tmp/known/printer-update.tar.gz',b'PACKAGE'))
  self.assertIn('stage --package',calls[2][0]);self.assertIn('apply --confirmation YES',calls[3][0])
  calls.clear()
  def done(command,data=None):calls.append(command);return json.dumps({'platform':'printer','version':m.NUMBER}).encode()
  m.update_remote(HERE,done,'/tmp/known');self.assertEqual(len(calls),1)
 def test_complete_transfers_repair_and_connection_runtime(self):
  spec=importlib.util.spec_from_file_location('setup_transfer',HERE/'setup.py');setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
  with tarfile.open(fileobj=io.BytesIO(setup.package()),mode='r:gz') as tar:
   names=set(tar.getnames())
   self.assertTrue({'repair.py','connection/install-pi.py','connection/configure-printer.py','connection/s1-usb-ecm','connection/ports-ecm.sh'}<=names)
if __name__=='__main__':unittest.main()
