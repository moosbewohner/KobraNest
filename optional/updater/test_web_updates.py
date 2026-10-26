import hashlib,http.cookiejar,importlib.util,importlib.machinery,json,os,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from types import SimpleNamespace
class WebTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);root=Path(self.tmp.name)
  cfg=root/'web.json';cfg.write_text(json.dumps({'pi_ip':'127.0.0.1','username':'tester','salt':'00'*16,'iterations':10,'password_hash':hashlib.pbkdf2_hmac('sha256',b'password123',bytes(16),10).hex()}))
  self.old={k:os.environ.get(k) for k in ('KOBRIAN_WEB_CONFIG','KOBRIAN_WEB_PAGE','KOBRANEST_UPDATE_MODULE','KOBRANEST_VERSION_FILE')}
  version=root/'version.json';version.write_text('{"version":"0.1.0"}');os.environ['KOBRANEST_VERSION_FILE']=str(version)
  module=root/'updater.py';module.write_text("def boot_recover():pass\ndef status():return {'installed':True,'busy':False}\ndef launch(*args):pass\n");os.environ['KOBRANEST_UPDATE_MODULE']=str(module)
  os.environ['KOBRIAN_WEB_CONFIG']=str(cfg);os.environ['KOBRIAN_WEB_PAGE']=str(Path(__file__).resolve().parent.parent/'kobrian-web/index.html')
  loader=importlib.machinery.SourceFileLoader('webtest',str(Path(__file__).resolve().parent.parent/'kobrian-web/s1-web'));spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m);self.m=m
  self.actions=[]
  def launch(action,package=None):self.actions.append((action,package));return {'busy':True}
  m.system_updater=SimpleNamespace(status=lambda:{'installed':True,'current':'0.1.0','busy':False},STATE=root/'updates',MAX_PACKAGE=16*1024*1024,launch=launch)
  self.server=m.Server(('127.0.0.1',0),m.Handler);threading.Thread(target=self.server.serve_forever,daemon=True).start();self.base='http://127.0.0.1:'+str(self.server.server_port)
  self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 def tearDown(self):
  self.server.shutdown();self.server.server_close()
  for k,v in self.old.items():
   if v is None:os.environ.pop(k,None)
   else:os.environ[k]=v
 def call(self,path,data=None,token=None,origin=None,raw=False):
  headers={}
  if data is not None:
   data=data if raw else json.dumps(data).encode();headers['Content-Type']='application/octet-stream' if raw else 'application/json'
  if token:headers['X-CSRF-Token']=token
  if origin:headers['Origin']=origin
  try:
   with self.opener.open(urllib.request.Request(self.base+path,data=data,headers=headers),timeout=5) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def login(self):return self.call('/api/login',{'username':'tester','password':'password123'})[1]['csrf']
 def test_status_requires_login(self):
  self.assertEqual(self.call('/api/updates')[0],401);self.login();self.assertEqual(self.call('/api/updates')[1]['current'],'0.1.0')
 def test_missing_boot_recover_keeps_web_alive_and_version_visible(self):
  module=Path(os.environ['KOBRANEST_UPDATE_MODULE']);module.write_text("def status():return {}\ndef launch(*args):pass\n")
  Path(os.environ['KOBRANEST_VERSION_FILE']).write_text('{"version":"0.1.2"}')
  loader=importlib.machinery.SourceFileLoader('web_missing_api',str(Path(__file__).resolve().parent.parent/'kobrian-web/s1-web'));spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
  m.updater_startup();self.assertIsNone(m.system_updater);self.assertEqual(m.updates_status()['current'],'0.1.2');self.assertIn('error',m.updates_status())
  server=m.Server(('127.0.0.1',0),m.Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port)+'/',timeout=5) as response:self.assertEqual(response.status,200)
  finally:server.shutdown();server.server_close()
 def test_embedded_pi_setup_download_is_complete_public_code(self):
  import io,zipfile
  with self.opener.open(self.base+'/download/pi-setup.zip',timeout=5) as response:
   self.assertEqual(response.headers.get_content_type(),'application/zip')
   with zipfile.ZipFile(io.BytesIO(response.read())) as archive:
    self.assertIsNone(archive.testzip());self.assertIn('KobraNest-Pi-Einrichtung/connection/install-pi.py',archive.namelist());self.assertIn('KobraNest-Pi-Einrichtung/setup.sh',archive.namelist())
    self.assertIn('KobraNest-Pi-Einrichtung/connection/ports-ecm.sh',archive.namelist());self.assertNotIn('KobraNest-Pi-Einrichtung/connection/transport.py',archive.namelist())
 def test_action_requires_csrf_origin_and_confirmation(self):
  t=self.login();self.assertEqual(self.call('/api/updates/action',{'action':'check'})[0],403)
  self.assertEqual(self.call('/api/updates/action',{'action':'check'},t,'http://evil.invalid')[0],403)
  self.assertEqual(self.call('/api/updates/action',{'action':'apply'},t)[0],409)
  self.assertEqual(self.call('/api/updates/action',{'action':'check'},t)[0],200);self.assertEqual(self.actions,[('check',None)])
 def test_upload_requires_auth_and_is_staged_not_applied(self):
  self.assertEqual(self.call('/api/updates/upload',b'fake',raw=True)[0],403)
  t=self.login();self.assertEqual(self.call('/api/updates/upload',b'package',t,raw=True)[0],200)
  self.assertEqual(self.actions[0][0],'stage');self.assertEqual(self.actions[0][1].read_bytes(),b'package')
 def test_other_mutations_blocked_during_update(self):
  self.m.system_updater.status=lambda:{'busy':True}
  with self.assertRaisesRegex(ValueError,'Update task'):self.m.perform('light_on',{})
if __name__=='__main__':unittest.main()
