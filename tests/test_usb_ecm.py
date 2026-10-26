"""Offline release checks: no printer/Pi connection or service restarts."""
from pathlib import Path
import base64,copy,hashlib,importlib.util,json,os,struct,subprocess,sys,tarfile,tempfile,time,unittest
BASE=Path(__file__).resolve().parents[1]
SERIAL=BASE/'optional/updater/connection'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class SerialReleaseTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def settings(self):
  m=load(SERIAL/'serial_settings.py','settings_test');m.CONFIG=self.root/'settings.json';m.PENDING=self.root/'pending.json';m.LAST=self.root/'last.json';m.PEER=self.root/'peer.json';m.PEER.write_text(json.dumps({'pi_user':'examplepi'}));m.bootid=lambda:'test-boot';m.pi_host=lambda:'192.168.1.151';return m
 def run_script(self,path,*args):
  r=subprocess.run([sys.executable,str(path),*map(str,args)],capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr+'\n'+r.stdout);return r
 def test_transaction_and_ports(self):
  m=self.settings();original=m.load();v=dict(original,ssh_port=2224);p=m.begin(v)
  self.assertEqual(m.load(),v)
  with self.assertRaises(ValueError):m.begin(original)
  with self.assertRaises(ValueError):m.confirm('wrong-token')
  with self.assertRaises(ValueError):m.confirm(p['token']) # no connected control master
  p=m.pending();p['deadline']=time.monotonic()-1;m.atomic(m.PENDING,p);self.assertTrue(m.expire());self.assertEqual(m.load(),original)
  for value in (dict(original,ssh_port=7130),dict(original,web_port=8088),dict(original,web_port=22),dict(original,web_enabled='true')):
   with self.assertRaises(ValueError):m.validate(value)
  m.begin(v);p=m.pending();p['boot_id']='earlier-boot';m.atomic(m.PENDING,p);self.assertTrue(m.expire());self.assertEqual(m.load(),original)
 def test_disabled_forwards_and_account(self):
  m=self.settings();v=dict(m.DEFAULTS,moonraker_enabled=False,light_enabled=False,ssh_enabled=False);cmd=m.command(v)
  self.assertEqual(cmd[-1],'examplepi@10.55.0.1');self.assertNotIn('-L',cmd)
  self.assertTrue(any('0.0.0.0:18080:127.0.0.1:8080'==x for x in cmd))
  self.assertFalse(any('17126:' in x or ':2222:' in x for x in cmd))
  m.PEER.write_text(json.dumps({'pi_user':'bad; command'}))
  with self.assertRaises(ValueError):m.command(v)
 def test_inactive_printer_install_idempotent(self):
  (self.root/'etc').mkdir();(self.root/'etc/s1-boot-ready').touch()
  for name in ('s1-gui','s1-light','s1-klipper-autorecover'):
   target=self.root/'usr/local/sbin'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((BASE/'overlay/usr/local/sbin'/name).read_bytes())
  (self.root/'etc/inittab').write_bytes((BASE/'overlay/etc/inittab').read_bytes())
  script=SERIAL/'install-printer.py';self.run_script(script,'--root',self.root)
  before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.run_script(script,'--root',self.root)
  after={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.assertEqual(before,after);self.assertFalse((self.root/'etc/s1-serial-link.enabled').exists())
  self.assertIn('prepare-klipperscreen.py',(self.root/'usr/local/sbin/s1-gui').read_text());self.assertIn('serial_settings.moonraker_host',(self.root/'usr/local/sbin/s1-klipper-autorecover').read_text())
 def test_pi_install_preserves_existing_services(self):
  for name in ('opt/ports.sh','etc/systemd/system/klipper.service'):
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('ORIGINAL '+name)
  blob=struct.pack('!I',11)+b'ssh-ed25519'+struct.pack('!I',32)+os.urandom(32);key=self.root/'example.pub';key.write_text('ssh-ed25519 '+base64.b64encode(blob).decode())
  self.run_script(SERIAL/'install-pi.py','--root',self.root,'--pi-user','examplepi','--key',key)
  for name in ('opt/ports.sh','etc/systemd/system/klipper.service'):self.assertEqual((self.root/name).read_text(),'ORIGINAL '+name)
  config=(self.root/'etc/kobranest-serial-link/sshd_ecm_config').read_text();self.assertIn('AllowUsers examplepi',config);self.assertIn('PermitOpen 127.0.0.1:7125',config)
  auth=(self.root/'etc/kobranest-serial-link/authorized_keys').read_text();self.assertTrue(auth.startswith('command="/bin/false",restrict,port-forwarding'))
  self.assertFalse((self.root/'etc/ssh/sshd_config').exists())
 @unittest.skipUnless((BASE/'payload/helixscreen-kobranest-armhf.tar.gz').is_file(),'Runtime payload is supplied in the complete installer')
 def test_helix_defaults_and_legacy_migration(self):
  m=load(BASE/'optional/helixscreen/install.py','helix_install_test')
  with tarfile.open(BASE/'payload/helixscreen-kobranest-armhf.tar.gz') as tar:
   template=json.load(tar.extractfile('helixscreen/config/settings.json.template'))
   binary=tar.extractfile('helixscreen/bin/helix-screen').read();self.assertEqual(hashlib.sha256(binary).hexdigest(),'de14865176144462f17625e72f75a59294525e33a0b4a2c0b89060a0712c898c')
  config=m.configuration(template,'192.168.1.151','en');p=config['printers']['default'];self.assertTrue(p['wizard_completed']);self.assertFalse(config['disable_sound']);self.assertFalse(config['sounds_enabled']);self.assertEqual(config['sound']['pwm_channel'],'0:0');self.assertEqual(p['leds']['strip'],'')
  p['wizard_completed']=False;p['leds']['strip']='output_pin caselight';p['leds']['selected_strips']=['output_pin caselight'];p['hardware']['last_snapshot']={'leds':[],'fans':['controller_fan controller_fan']};config['disable_sound']=True;file=self.root/'settings.json';file.write_text(json.dumps(config))
  m.migrate_kobranest_settings(file);saved=json.loads(file.read_text());self.assertTrue(saved['printers']['default']['wizard_completed']);self.assertEqual(saved['printers']['default']['leds']['strip'],'');self.assertFalse(saved['sounds_enabled'])
  self.assertEqual(saved['printers']['default']['panel_widgets'],p['panel_widgets'])
if __name__=='__main__':unittest.main(verbosity=2)
