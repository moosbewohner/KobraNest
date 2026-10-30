import base64,hashlib,importlib.util,io,json,os,subprocess,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
HERE=Path(__file__).resolve().parent
class UpdateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.keys=tempfile.TemporaryDirectory();p=Path(cls.keys.name);cls.key=p/'key.pem';cls.pub=p/'pub.pem'
  subprocess.run(['openssl','genpkey','-algorithm','ED25519','-out',str(cls.key)],check=True,capture_output=True)
  subprocess.run(['openssl','pkey','-in',str(cls.key),'-pubout','-out',str(cls.pub)],check=True,capture_output=True)
 @classmethod
 def tearDownClass(cls):cls.keys.cleanup()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  spec=importlib.util.spec_from_file_location('testcore',HERE/'updater.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
  m=self.m;m.ROOT=self.root;m.STATE=self.root/'state';m.STATE.mkdir();m.KEY=self.pub;m.VERSION=self.root/'version.json';m.CONFIG=self.root/'config.json'
  self.path='usr/local/sbin/s1-web';p=self.root/self.path;p.parent.mkdir(parents=True);p.write_bytes(b'print("old")\n');self.old=p.read_bytes()
  m.atomic(m.VERSION,{'version':'0.1.0','platform':'printer','files':{self.path:m.digest(self.old)}})
  cfg=self.root/'etc/s1-web.json';cfg.parent.mkdir();cfg.write_text('{"username":"keep","password_hash":"keep"}')
 def signed(self,data):
  p=self.root/'raw';p.write_bytes(data);sig=self.root/'sig'
  subprocess.run(['openssl','pkeyutl','-sign','-inkey',str(self.key),'-rawin','-in',str(p),'-out',str(sig)],check=True,capture_output=True);return sig.read_bytes()
 def package(self,path=None,number='0.1.1',corrupt=False):
  m=self.m;path=path or self.path;payload=b'print("new")\n'
  manifest={'format':1,'platform':'printer','version':number,'minimum_version':'0.1.0','files':[{'path':path,'size':len(payload),'sha256':m.digest(payload),'mode':0o755}]}
  raw=json.dumps(manifest).encode();items={'manifest.json':raw,'manifest.sig':self.signed(raw),'files/'+path:payload+(b'x' if corrupt else b'')};buf=io.BytesIO()
  with tarfile.open(fileobj=buf,mode='w:gz') as tar:
   for name,data in items.items():info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
  return buf.getvalue()
 def stage(self,**kw):
  p=self.root/'update.tar.gz';p.write_bytes(self.package(**kw));self.m.stage(p)
 def test_apply_and_manual_rollback_preserve_credentials(self):
  self.stage();self.m.apply(idle=lambda:None,probe=lambda:None,restart=lambda:None)
  self.assertEqual(self.m.installed()['version'],'0.1.1');self.assertIn(b'new',(self.root/self.path).read_bytes())
  self.m.rollback(idle=lambda:None,probe=lambda:None,restart=lambda:None)
  self.assertEqual((self.root/self.path).read_bytes(),self.old);self.assertEqual(self.m.installed()['version'],'0.1.0')
  self.assertEqual(json.loads((self.root/'etc/s1-web.json').read_text())['password_hash'],'keep')
 def test_missing_version_does_not_invent_platform_or_release(self):
  self.m.VERSION.unlink()
  with self.assertRaisesRegex(ValueError,'Version metadata missing'):self.m.installed()
 def test_catalog_offers_preparation_then_native_update(self):
  m=self.m
  offer=lambda number,minimum:dict(format=1,platform='printer',version=number,minimum_version=minimum,sha256='0'*64,size=1,url='https://example.org/update.tar.gz')
  catalog={'printer':offer('0.1.7','0.0.0'),'printer_updates':[offer('0.1.8','0.1.7')]}
  for current,expected in [('0.1.6','0.1.7'),('0.1.7','0.1.8'),('0.1.8',None)]:
   m.atomic(m.VERSION,{'version':current,'platform':'printer','files':{}})
   selected=m.select_offer(catalog);self.assertEqual(selected['version'] if selected else None,expected)
 def test_helix_probe_tracks_only_selected_changed_interface(self):
  m=self.m;p=self.root/'etc/s1-ui';p.write_text('helix')
  m.atomic(m.STATE/'transaction.json',{'files':[{'path':'usr/local/sbin/s1-helix'}]})
  self.assertTrue(m.helix_health_required());self.assertFalse(m.helix_running())
  pid=self.root/'run/s1/helix.pid';pid.parent.mkdir(parents=True);pid.write_text('4321')
  cmd=self.root/'proc/4321/cmdline';cmd.parent.mkdir(parents=True);cmd.write_bytes(b'./bin/helix-screen\0--size\0800x480')
  self.assertTrue(m.helix_running());cmd.write_bytes(b'unrelated-process');self.assertFalse(m.helix_running())
  p.write_text('klipperscreen');self.assertFalse(m.helix_health_required())
 def test_bad_health_rolls_back_all_files(self):
  self.stage()
  def fail():raise ValueError('health failed')
  with self.assertRaisesRegex(ValueError,'health'):self.m.apply(idle=lambda:None,probe=fail,restart=lambda:None)
  self.assertEqual((self.root/self.path).read_bytes(),self.old);self.assertEqual(self.m.read(self.m.STATE/'transaction.json')['phase'],'rolled_back')
 def test_modified_managed_file_not_overwritten(self):
  self.stage();(self.root/self.path).write_bytes(b'print("personal edit")')
  with self.assertRaisesRegex(ValueError,'Locally modified'):self.m.apply(idle=lambda:None,probe=lambda:None,restart=lambda:None)
 def test_active_print_stops_before_writes(self):
  self.stage()
  def fail():raise ValueError('printing')
  with self.assertRaisesRegex(ValueError,'printing'):self.m.apply(idle=fail,probe=lambda:None,restart=lambda:None)
  self.assertEqual((self.root/self.path).read_bytes(),self.old)
 def test_checksum_corruption_refused(self):
  with self.assertRaises(ValueError):self.stage(corrupt=True)
 def test_sensitive_and_traversal_targets_refused(self):
  for path in ('etc/s1-web.json','root/.ssh/authorized_keys','opt/ports.sh','etc/systemd/system/klipper.service','../escape'):
   with self.subTest(path=path),self.assertRaises(ValueError):self.m.inspect_package(self.package(path=path))
 def test_invalid_signature_refused(self):
  with self.assertRaises(ValueError):self.m.verify_signature(b'fake',self.signed(b'other'))
 def test_no_downgrades(self):
  with self.assertRaises(ValueError):self.stage(number='0.1.0')
 def test_invalid_clock_uses_internal_moonraker(self):
  m=self.m;m.ROOT=Path('/');m.installed=lambda:{'platform':'printer'};m.moonraker_address=lambda:'127.0.0.1'
  response=MagicMock();response.__enter__.return_value.headers={'Date':'Mon, 26 Oct 2026 14:35:18 GMT'}
  opener=MagicMock();opener.open.return_value=response
  with patch.object(m.time,'time',return_value=0),patch.object(m.time,'CLOCK_REALTIME',0,create=True),patch.object(m.time,'clock_settime',create=True) as clock,patch.object(m,'build_opener',return_value=opener):
   m.sync_clock();clock.assert_called_once();self.assertIn('127.0.0.1:7125',opener.open.call_args.args[0])
 def test_backup_retention_only_own_transactions(self):
  base=self.m.STATE/'backups';base.mkdir()
  for n in range(6):(base/format(n,'032x')).mkdir()
  (base/'personal-backup').mkdir();self.m.prune_backups(format(0,'032x'))
  self.assertTrue((base/'personal-backup').exists());self.assertEqual(len(list(base.iterdir())),4)
 def test_interrupted_transaction_recovered(self):
  self.stage();self.m.apply(idle=lambda:None,probe=lambda:None,restart=lambda:None)
  tx=self.m.read(self.m.STATE/'transaction.json');tx['phase']='checking';self.m.atomic(self.m.STATE/'transaction.json',tx)
  self.assertEqual(self.m.recover(),'recovered');self.assertEqual((self.root/self.path).read_bytes(),self.old)
 def test_rollback_does_not_erase_later_edits(self):
  self.stage();self.m.apply(idle=lambda:None,probe=lambda:None,restart=lambda:None);(self.root/self.path).write_bytes(b'manual')
  with self.assertRaisesRegex(ValueError,'changed after'):self.m.rollback(idle=lambda:None,probe=lambda:None,restart=lambda:None)
if __name__=='__main__':unittest.main()
