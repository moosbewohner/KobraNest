import base64,ipaddress,json,os,re,subprocess,sys,time,urllib.request
from pathlib import Path
usb='--usb' in sys.argv[3:]
address='127.0.0.1' if usb else str(ipaddress.IPv4Address(sys.argv[1]))
port=17126 if usb else 7126
template=base64.b64decode(sys.argv[2]).decode().replace('192.168.10.67',address).replace(':7126/',':'+str(port)+'/')
root=Path.home()/'printer_data/config'
main=root/'moonraker.conf';light=root/'bauraumlicht.cfg'
assert root.is_dir() and main.is_file() and not main.is_symlink() and not light.is_symlink(),'Unexpected Moonraker configuration path'
config=main.read_text()
assert not re.search(r'^\s*\[power Bauraumlicht\]',config,re.M),'Light is defined in moonraker.conf; automatic replacement refused'
for other in root.glob('*.cfg'):
    if other!=light and re.search(r'^\s*\[power Bauraumlicht\]',other.read_text(),re.M):
        raise RuntimeError('Another light definition exists; automatic replacement refused')
old=light.read_text() if light.exists() else None
if old is None:new=template
else:
    assert len(re.findall(r'^\s*\[power Bauraumlicht\]',old,re.M))==1,'Unexpected light configuration'
    new=old
    for key,endpoint in [('on_url','on'),('off_url','off'),('status_url','status')]:
        new,count=re.subn(r'^'+key+r'\s*:.*$',key+': http://'+address+':'+str(port)+'/light/'+endpoint,new,flags=re.M)
        assert count==1,'Missing or duplicate '+key
include='[include bauraumlicht.cfg]'
updated=config if re.search(r'^\s*\[include bauraumlicht\.cfg\]\s*$',config,re.M) else config.rstrip()+'\n\n'+include+'\n'
if new==old and updated==config:
    print('Light configuration already matches the selected printer IP.');sys.exit(0)
status=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?print_stats',timeout=5))['result']['status']['print_stats']['state']
assert status not in ('printing','paused'),'Print active; refusing Moonraker restart'
subprocess.run(['sudo','-n','-l','/usr/bin/systemctl','restart','moonraker'],check=True,stdout=subprocess.DEVNULL)
stamp=time.strftime('%Y%m%d-%H%M%S')+'-'+str(os.getpid())
changes=[(light,new,old),(main,updated,config)]
for path,text,previous in changes:
    if text==previous:continue
    if previous is not None:
        backup=path.with_name(path.name+'.kobrian-backup-'+stamp)
        with backup.open('xb') as stream:stream.write(path.read_bytes())
    temporary=path.with_name(path.name+'.kobrian-new-'+stamp)
    with temporary.open('x',encoding='utf-8') as stream:stream.write(text)
    temporary.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
    os.replace(temporary,path)
subprocess.run(['sudo','-n','/usr/bin/systemctl','restart','moonraker'],check=True,timeout=45)
print('Light configuration transferred; previous files backed up; Moonraker restarted.')
