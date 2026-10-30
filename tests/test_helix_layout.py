"""Offline checks for native upstream HelixScreen layouts and self-updates."""
from pathlib import Path
import importlib.util,importlib.machinery,io,json,os,tarfile,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1]

def load(path,name):
 loader=importlib.machinery.SourceFileLoader(name,str(path));spec=importlib.util.spec_from_loader(name,loader);module=importlib.util.module_from_spec(spec);loader.exec_module(module);return module

class HelixLayoutTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.dest=self.root/'opt/helixscreen';(self.dest/'bin').mkdir(parents=True);(self.dest/'config').mkdir()
  (self.dest/'config/settings.json.template').write_text('{}')
  self.m=load(BASE/'optional/helixscreen/install.py','layout_install')
 def ldd(self):return patch.object(self.m.subprocess,'run',return_value=SimpleNamespace(stdout='',stderr=''))
 def test_native_only_runtime_is_valid(self):
  (self.dest/'bin/helix-screen').write_bytes(b'NEW-UPSTREAM-BINARY')
  with self.ldd() as run:self.m.validate_runtime(self.root,self.dest)
  self.assertIn('/opt/helixscreen/bin/helix-screen',run.call_args.args[0]);self.assertFalse((self.dest/'bin/helix-screen-fbdev').exists())
 def test_legacy_runtime_remains_supported_without_creating_an_alias(self):
  (self.dest/'bin/helix-screen-fbdev').write_bytes(b'OLD-BINARY')
  with self.ldd() as run:self.m.validate_runtime(self.root,self.dest)
  self.assertIn('/opt/helixscreen/bin/helix-screen-fbdev',run.call_args.args[0]);self.assertFalse((self.dest/'bin/helix-screen').exists())
 def test_missing_binary_is_rejected(self):
  with self.ldd() as run:
   with self.assertRaisesRegex(AssertionError,'binary missing'):self.m.validate_runtime(self.root,self.dest)
   run.assert_not_called()
 def test_upstream_self_update_is_not_downgraded_or_overwritten(self):
  (self.dest/'config/settings.json.template').unlink()
  for name,data in {'bin/helix-screen':b'NEWER-UPSTREAM-VERSION','config/settings.json':b'{"custom":"KEEP"}','config/custom_images/my.png':b'CUSTOM-IMAGE'}.items():
   p=self.dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  before={p.relative_to(self.dest).as_posix():p.read_bytes() for p in self.dest.rglob('*') if p.is_file()}
  with self.ldd():result=self.m.install_release(self.root,self.root/'NONEXISTENT-OLD-ARCHIVE')
  self.assertEqual(result,self.dest)
  self.assertEqual(before,{p.relative_to(self.dest).as_posix():p.read_bytes() for p in self.dest.rglob('*') if p.is_file()})
  self.assertFalse((self.dest/'.kobrian-release').exists())
  self.assertTrue((self.root/'var/lib/kobranest-display/helixscreen.json').is_file())
 def test_fresh_install_keeps_bookkeeping_outside_upstream_tree(self):
  (self.dest/'config/settings.json.template').unlink();(self.dest/'config').rmdir();(self.dest/'bin').rmdir();self.dest.rmdir()
  archive=self.root/'native.tar.gz'
  with tarfile.open(archive,'w:gz') as tar:
   for name,data in {'helixscreen/bin/helix-screen':b'NATIVE','helixscreen/config/settings.json.template':b'{}'}.items():
    info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o755;tar.addfile(info,io.BytesIO(data))
  with self.ldd():self.m.install_release(self.root,archive)
  self.assertEqual((self.dest/'bin/helix-screen').read_bytes(),b'NATIVE')
  self.assertFalse((self.dest/'bin/helix-screen-fbdev').exists());self.assertFalse((self.dest/'.kobrian-release').exists())
  ledger=json.loads((self.root/'var/lib/kobranest-display/helixscreen.json').read_text());self.assertEqual(ledger['layout'],'upstream')
 def test_old_marker_is_archived_but_real_legacy_binary_is_preserved(self):
  (self.dest/'bin/helix-screen').write_bytes(b'UPSTREAM')
  (self.dest/'bin/helix-screen-fbdev').write_bytes(b'REAL-UPSTREAM-FILE')
  (self.dest/'.kobrian-release').write_text('361269dce1faa43e4acb5f06b1365490667b317d40f9a52e53e03586ecca29a3')
  with self.ldd():self.m.install_release(self.root,self.root/'unused')
  self.assertFalse((self.dest/'.kobrian-release').exists());self.assertEqual((self.dest/'bin/helix-screen-fbdev').read_bytes(),b'REAL-UPSTREAM-FILE')
  self.assertEqual(len(list((self.root/'var/backups/kobrian-display').glob('layout-*/.kobrian-release'))),1)
 def test_webui_recognizes_native_and_legacy_layouts(self):
  cfg=self.root/'web.json';cfg.write_text('{"pi_ip":"127.0.0.1"}')
  updater=self.root/'updater.py';updater.write_text('def boot_recover():pass\ndef status():return {}\ndef launch(*args):pass\n')
  env={'KOBRIAN_WEB_CONFIG':str(cfg),'KOBRIAN_WEB_PAGE':str(BASE/'optional/kobrian-web/index.html'),'KOBRANEST_UPDATE_MODULE':str(updater)}
  with patch.dict(os.environ,env):web=load(BASE/'optional/kobrian-web/s1-web','layout_web')
  self.assertFalse(web.helix_runtime_available(self.dest))
  for name in ('helix-screen','helix-screen-fbdev'):
   binary=self.dest/'bin'/name;binary.write_bytes(b'HELIX');self.assertTrue(web.helix_runtime_available(self.dest));binary.unlink()
 def test_wrapper_uses_real_home_and_does_not_modify_upstream_layout(self):
  script=(BASE/'optional/helixscreen/s1-helix').read_text()
  self.assertNotIn('test-home',script);self.assertIn('HOME=/root ',script)
  self.assertNotIn('ln -s',script);self.assertIn('HELIX_BIN=./bin/helix-screen',script)
 def test_fake_home_is_archived_only_when_explicitly_requested(self):
  (self.dest/'bin/helix-screen').write_bytes(b'UPSTREAM')
  home=self.dest/'test-home';home.mkdir();(home/'cache').write_bytes(b'KEEP-CACHE')
  helper=load(BASE/'optional/helixscreen/layout.py','layout_cache')
  helper.migrate(self.root);self.assertTrue(home.is_dir())
  helper.migrate(self.root,retire_home=True);self.assertFalse(home.exists())
  ledger=json.loads((self.root/'var/lib/kobranest-display/helixscreen.json').read_text())
  self.assertEqual((self.root/ledger['test_home_backup']/'cache').read_bytes(),b'KEEP-CACHE')

if __name__=='__main__':unittest.main()
