import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class RepairTests(unittest.TestCase):
 def test_broken_module_repaired_without_changing_user_config_or_version(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   files={'etc/s1-boot-ready':b'1','etc/s1-web.json':b'{"password_hash":"KEEP","username":"tester"}','usr/share/kobranest-update/version.json':b'{"version":"0.1.2","platform":"printer","files":{}}','usr/local/lib/kobranest-update/updater.py':b'def status():return {}\n','usr/local/sbin/s1-web':(HERE.parent/'kobrian-web/s1-web').read_bytes(),'opt/kobrian-web/index.html':(HERE.parent/'kobrian-web/index.html').read_bytes(),'usr/share/kobranest-update/release.pub':(HERE/'release.pub').read_bytes()}
   for n,data in files.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   subprocess.run([sys.executable,str(HERE/'repair.py'),'--root',str(root)],check=True,capture_output=True)
   self.assertIn('def boot_recover()', (root/'usr/local/lib/kobranest-update/updater.py').read_text());self.assertEqual((root/'etc/s1-web.json').read_bytes(),files['etc/s1-web.json']);self.assertEqual(json.loads((root/'usr/share/kobranest-update/version.json').read_text())['version'],'0.1.2')
   web=(root/'usr/local/sbin/s1-web').read_text();self.assertIn('updater_startup()',web);self.assertIn('spec_from_file_location',web)
 def test_missing_version_gets_explicit_repair_scope_and_real_hashes(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for name,data in {'etc/s1-boot-ready':b'1','usr/local/sbin/s1-web':(HERE.parent/'kobrian-web/s1-web').read_bytes(),'opt/kobrian-web/index.html':(HERE.parent/'kobrian-web/index.html').read_bytes()}.items():
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   subprocess.run([sys.executable,str(HERE/'repair.py'),'--root',str(root)],check=True,capture_output=True)
   info=json.loads((root/'usr/share/kobranest-update/version.json').read_text())
   self.assertEqual(info['version'],'0.0.0');self.assertEqual(info['version_scope'],'repair-bootstrap');self.assertEqual(info['original_system_version'],'unknown')
   import hashlib
   self.assertEqual(len(info['files']),5)
   for name,digest in info['files'].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
if __name__=='__main__':unittest.main()
