#!/usr/bin/env python3
"""Embed the complete public Pi setup archive in the signed WebUI file."""
import argparse,base64,io,re,zipfile
from pathlib import Path
def archive(here):
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for name in ('RELEASE_VERSION','BRIDGE_VERSION','complete.py','setup.sh','setup.py','bootstrap.sh','install.py','repair.py','patch_web.py','s1-update','s1-time-sync','updater.py','release.pub'):
   z.write(here/name,'KobraNest-Pi-Einrichtung/'+name)
  for p in sorted((here/'connection').iterdir()):
   if p.is_file() and p.suffix!='.pyc' and p.name!='transport.py':z.write(p,'KobraNest-Pi-Einrichtung/connection/'+p.name)
  license=here.parents[1]/'LICENSE'
  if license.is_file():z.write(license,'KobraNest-Pi-Einrichtung/LICENSE')
  z.writestr('KobraNest-Pi-Einrichtung/README.txt','Run on the Pi: bash setup.sh\nConfigures the restricted SSH service, device key, USB forwards, chamber-light URLs and both updaters. Uses the new two-ACM plus ECM gadget. Older gadget setup can be prepared using bash setup.sh --prepare-ecm; reboot Pi then printer and rerun setup.sh. Requires an idle printer and temporary SSH access to it. Existing ports.sh, MCU tunnels and klipper.service remain unchanged. Verify the printer SSH fingerprint. No password is stored. Moonraker restarts only if its light configuration changes. Known ECM startup instability is not permanently fixed; restarting the printer after the Pi may still be required.\n')
 return out.getvalue()
def backend(text):
 if "route.path == '/download/pi-setup.zip'" in text:return text
 needle="        if route.path == '/api/setup':"
 assert needle in text
 block="""        if route.path == '/download/pi-setup.zip':
            import base64
            match = re.search(rb'data:application/zip;base64,([A-Za-z0-9+/=]+)', PAGE)
            if not match:
                return self.reply(404, {'error': 'Pi setup archive is not included in this release'})
            return self.reply(200, base64.b64decode(match.group(1), validate=True), 'application/zip')
"""
 text=text.replace(needle,block+needle,1);compile(text,'s1-web','exec');return text
def frontend(text,data):
 release=(Path(__file__).resolve().parent/'RELEASE_VERSION').read_text().strip()
 block='''<!-- BEGIN COMPLETE PI SETUP -->
<div id="piSetupArea" style="margin-top:18px;padding-top:16px;border-top:1px solid var(--line)"><h3 id="piSetupTitle">Pi-Verbindung einrichten</h3><p id="piSetupHint" class="small muted">Für die Helix-Korrektur ist keine Pi-Einrichtung nötig. Für eine vollständige USB-/ECM-Einrichtung das Komplettpaket auf dem Pi entpacken und bash setup.sh --complete starten. Nach erfolgreichem COMPLETE ist keine erneute Pi-Einrichtung nötig.</p><a id="piSetupDownload" download="KobraNest-Komplett-REPLACE_VERSION.zip" href="https://github.com/moosbewohner/KobraNest/releases/download/vREPLACE_VERSION/KobraNest-Komplett-REPLACE_VERSION.zip" style="display:inline-block;border:1px solid #515940;border-radius:9px;padding:11px 15px;color:var(--ink);text-decoration:none">Komplettpaket herunterladen</a><template id="piSetupArchive">data:application/zip;base64,REPLACE_ARCHIVE</template></div>
<!-- END COMPLETE PI SETUP -->'''.replace('REPLACE_ARCHIVE',base64.b64encode(data).decode()).replace('REPLACE_VERSION',release)
 if '<!-- BEGIN COMPLETE PI SETUP -->' in text:text=re.sub(r'<!-- BEGIN COMPLETE PI SETUP -->.*?<!-- END COMPLETE PI SETUP -->',lambda _:block,text,flags=re.S)
 else:
  pattern=r'(<p[^>]*id="updateScope"[^>]*>.*?</p>)';text,n=re.subn(pattern,lambda m:m[1]+block,text,count=1,flags=re.S);assert n==1
 script="""<script>// PI SETUP LOCALIZATION
(()=>{function label(){const en=language==='en';document.getElementById('piSetupTitle').textContent=en?'Set up Pi connection':'Pi-Verbindung einrichten';document.getElementById('piSetupHint').textContent=en?'No Pi setup is needed for the Helix fix. For complete USB/ECM setup, unpack the complete bundle on the Pi and run bash setup.sh --complete. After successful COMPLETE, no additional Pi setup is needed.':'Für die Helix-Korrektur ist keine Pi-Einrichtung nötig. Für eine vollständige USB-/ECM-Einrichtung das Komplettpaket auf dem Pi entpacken und bash setup.sh --complete starten. Nach erfolgreichem COMPLETE ist keine erneute Pi-Einrichtung nötig.';document.getElementById('piSetupDownload').textContent=en?'Download complete bundle':'Komplettpaket herunterladen'}document.getElementById('languageSelect').addEventListener('change',label);label()})();</script>"""
 if '// PI SETUP LOCALIZATION' in text:text=re.sub(r'<script>// PI SETUP LOCALIZATION.*?</script>',lambda _:script,text,flags=re.S)
 else:text+=script
 return text
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();here=Path(__file__).resolve().parent
 data=archive(here)
 web=a.source/'optional/kobrian-web'
 for name,patch in [('s1-web',backend),('index.html',lambda text:frontend(text,data))]:
  path=web/name;path.write_bytes(patch(path.read_text(encoding='utf-8')).encode())
 print('Complete Pi setup embedded:',len(data),'bytes')
