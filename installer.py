#!/usr/bin/env python3
"""Conservative installer for the one verified Kobra S1 firmware layout."""
import argparse
import base64
import getpass
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import shlex
import sys
import tarfile
import uuid
import paramiko

PACKAGE=Path(__file__).resolve().parent
BASE='/useremain/s1-klipperscreen-test'
ROOT=BASE+'/rootfs'
PARTS={1:32768,5:262144,6:16777216,7:16777216,8:50331648,9:50331648}

def require(ok,message):
    if not ok:raise RuntimeError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def run(client,command,stdin=None,timeout=300,progress=False):
    # Original S1 BusyBox has no sha256sum applet. Rinkhals supplies Python.
    # Define a shell-local fallback only; never install tools into Stock.
    digest_code = "import hashlib,sys\nfor name in (sys.argv[1:] or ['-']):\n f=sys.stdin.buffer if name=='-' else open(name,'rb')\n h=hashlib.sha256()\n for block in iter(lambda:f.read(1048576),b''): h.update(block)\n print(h.hexdigest()+'  '+name)\n if name!='-': f.close()"
    fallback = 'if ! command -v sha256sum >/dev/null 2>&1; then sha256sum() { python3 -c ' + shlex.quote(digest_code) + ' "$@"; }; fi\n'
    inp,out,err=client.exec_command(fallback+command,timeout=timeout)
    if stdin is not None:inp.write(stdin);inp.flush()
    inp.channel.shutdown_write()
    # Merge output streams to avoid a full stderr pipe blocking long builds.
    out.channel.set_combine_stderr(True)
    if progress:
        chunks=[]
        for line in out:
            if isinstance(line,bytes):line=line.decode(errors='replace')
            print(line.rstrip(),flush=True);chunks.append(line)
        data=''.join(chunks)
    else:data=out.read().decode(errors='replace')
    rc=out.channel.recv_exit_status()
    require(rc==0,f'Command failed ({rc}): {command}\n{data[-8000:]}')
    return data

def put(client,path,data,mode=0o644):
    if isinstance(data,Path):
        with data.open('rb') as f:put_stream(client,path,f,mode)
    else:
        import io
        put_stream(client,path,io.BytesIO(data.encode() if isinstance(data,str) else data),mode)

def put_stream(client,path,stream,mode):
    command='umask 077; cat >'+shlex.quote(path+'.new')+' && chmod '+oct(mode)[2:]+' '+shlex.quote(path+'.new')+' && mv '+shlex.quote(path+'.new')+' '+shlex.quote(path)
    inp,out,err=client.exec_command(command,timeout=600)
    while True:
        block=stream.read(256*1024)
        if not block:break
        inp.channel.sendall(block)
    inp.channel.shutdown_write()
    result=out.read()+err.read();require(out.channel.recv_exit_status()==0,result.decode(errors='replace'))

def upload_inventory(client,files):
    """Only adopt untouched upload directories; never resume unpacked roots."""
    script="""from pathlib import Path
import json,stat
base=Path('/useremain/s1-klipperscreen-test')
allowed=set(json.loads(ALLOWED))
if not base.exists():base.mkdir(mode=0o700)
assert base.resolve()==base and base.is_dir() and not base.is_symlink(),'Unexpected staging path'
items={}
for path in base.iterdir():
 info=path.lstat()
 assert path.name in allowed and stat.S_ISREG(info.st_mode),'Existing installation or unknown file; manual review required'
 items[path.name]=info.st_size
print(json.dumps(items))
""".replace('ALLOWED',repr(json.dumps([name+suffix for name in files for suffix in ('','.new')])))
    return json.loads(run(client,'python3 -c '+shlex.quote(script),timeout=30))


def verify_upload_prefix(client,remote,local,size):
    require(0<=size<=local.stat().st_size,'Upload file is larger than its expected source; preserved for review')
    h=hashlib.sha256()
    with local.open('rb') as source:
        remaining=size
        while remaining:
            data=source.read(min(1048576,remaining));require(bool(data),'Source file changed');h.update(data);remaining-=len(data)
    actual=run(client,'sha256sum '+shlex.quote(remote),timeout=180).split()[0]
    require(actual==h.hexdigest(),'Partial upload does not match source; file preserved for review')


def put_resumable(client,remote,local):
    """Append only to a verified prefix and rename after full checksum success."""
    local=Path(local);partial=remote+'.new';total=local.stat().st_size
    sftp=client.open_sftp();sftp.get_channel().settimeout(120)
    try:
        def size(path):
            try:return sftp.lstat(path).st_size
            except FileNotFoundError:return None
        current=size(remote);pending=size(partial)
        if current is not None:
            verify_upload_prefix(client,remote,local,current)
            if current==total:
                print('Upload already verified:',local.name);return
            require(pending is None,'Two partial uploads exist; preserve both for review')
            run(client,'mv '+shlex.quote(remote)+' '+shlex.quote(partial))
            pending=current
        offset=pending or 0
        if pending is not None:verify_upload_prefix(client,partial,local,offset)
        print('Uploading',local.name,'from',offset//1048576,'MiB of',total//1048576,'MiB')
        import time
        last=time.monotonic()
        with local.open('rb') as source:
            source.seek(offset)
            with sftp.open(partial,'ab' if offset else 'wb') as target:
                target.set_pipelined(True)
                for block in iter(lambda:source.read(131072),b''):
                    target.write(block);offset+=len(block)
                    if time.monotonic()-last>=15:
                        print('Upload progress:',local.name,offset//1048576,'/',total//1048576,'MiB');last=time.monotonic()
                target.flush()
        require(size(partial)==total,'Incomplete upload; retry stage to resume the verified prefix')
        verify_upload_prefix(client,partial,local,total)
        run(client,'chmod 644 '+shlex.quote(partial)+' && mv '+shlex.quote(partial)+' '+shlex.quote(remote))
    finally:sftp.close()


def get(client,remote,local):
    _,out,err=client.exec_command('cat '+shlex.quote(remote),timeout=600)
    with Path(local).open('wb') as f:
        while True:
            block=out.read(256*1024)
            if not block:break
            f.write(block)
    require(out.channel.recv_exit_status()==0,err.read().decode(errors='replace'))

class ConfirmHost(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self,client,hostname,key):
        fp=base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')
        print(f'SSH server {hostname}: SHA256:{fp}')
        require(input('Trust this host? Type yes: ').strip()=='yes','Host not trusted')
        client.get_host_keys().add(hostname,key.get_name(),key)

def connect(host,user,known,default_password=None):
    c=paramiko.SSHClient()
    if known.exists():c.load_host_keys(str(known))
    c.set_missing_host_key_policy(ConfirmHost())
    hint='; Enter = stock rockchip' if default_password else ''
    password=getpass.getpass(f'SSH password for {user}@{host} (not saved{hint}): ') or default_password
    c.connect(host,username=user,password=password,allow_agent=False,look_for_keys=False,timeout=12)
    c.save_host_keys(str(known));return c

def settings(path):
    s=json.loads(path.read_text(encoding='utf-8'))
    for name in ('printer_ip','pi_ip','gateway'):s[name]=str(ipaddress.IPv4Address(s[name]))
    require(type(s['prefix']) is int and 1<=s['prefix']<=30,'Invalid subnet prefix')
    network=ipaddress.IPv4Network(s['printer_ip']+'/'+str(s['prefix']),strict=False)
    require(ipaddress.IPv4Address(s['gateway']) in network,'Gateway is outside printer subnet')
    require(s['printer_ip']!=s['pi_ip'],'Printer and Pi need different addresses')
    require(type(s.get('light_auto_on',True)) is bool,'light_auto_on must be boolean')
    s['tunnel_mode']=s.get('tunnel_mode','usb')
    require(s['tunnel_mode'] in ('usb','network'),'Invalid MCU transport')
    return s

def verify_package():
    require(not sys.flags.optimize,'Do not run this installer with python -O')
    manifest=PACKAGE/'SHA256SUMS.txt';require(manifest.exists(),'Package manifest missing')
    for line in manifest.read_text(encoding='utf-8').splitlines():
        expected,name=line.split('  ',1);p=PACKAGE/name
        require(p.resolve().is_relative_to(PACKAGE),'Invalid package path')
        require(p.is_file() and sha(p)==expected,'Package checksum mismatch: '+name)

def inspect(c,require_a=True):
    arch=run(c,'uname -m').strip();require(arch=='armv7l','Only the verified ARMv7 S1 is supported')
    cmdline=run(c,'cat /proc/cmdline')
    if require_a:require('root=/dev/mmcblk0p8 ' in cmdline+' ','Start in ORIGINAL slot A before installation')
    for number,size in PARTS.items():
        sectors=int(run(c,f'cat /sys/class/block/mmcblk0p{number}/size').strip())
        require(sectors*512==size,f'Partition p{number} has unexpected size')
    require('rootfstype=squashfs' in cmdline,'Unexpected root filesystem')
    # Capability checks, not a byte-for-byte firmware whitelist. Only read
    # headers and platform metadata here; full backup hashes are checked later.
    code="import json,os; from pathlib import Path; print(json.dumps({'uid':os.geteuid(),'compatible':Path('/proc/device-tree/compatible').read_bytes().decode().split('\\0'),'kernel':os.uname().release,'boot_magic':Path('/dev/mmcblk0p6').open('rb').read(4).hex(),'system_magic':Path('/dev/mmcblk0p8').open('rb').read(4).hex(),'devices':all(Path(p).exists() for p in ('/dev/ttyS3','/dev/ttyS5','/dev/fb0'))}))"
    platform=json.loads(run(c,'python3 -c '+shlex.quote(code)))
    require(platform['uid']==0,'Printer installation requires root')
    require('rockchip,rv1106' in platform['compatible'],'Unsupported printer platform; Rockchip RV1106 required')
    require(platform['kernel'].startswith('5.10.'),'Unsupported printer kernel; Linux 5.10 required')
    require(platform['devices'],'Required S1 UART or display device missing')
    require(platform['boot_magic']=='d00dfeed','Original boot image is not a supported FIT image')
    require(platform['system_magic']=='68737173','Original system image is not SquashFS')
    run(c,'test -b /dev/mmcblk0p17 && test -x /usr/bin/rk_ota') if require_a else None
    mounts=run(c,'cat /proc/mounts')
    if require_a:
        # Stock uses /dev/block/by-name aliases: compare actual device IDs.
        code="import json,os; from pathlib import Path; mounted={line.split()[2] for line in Path('/proc/self/mountinfo').read_text(encoding='utf-8').splitlines()}; print(json.dumps({'b_unmounted':all(Path('/sys/class/block/mmcblk0p'+str(n)+'/dev').read_text(encoding='utf-8').strip() not in mounted for n in (7,9)), 'data_device':os.stat('/useremain').st_dev==os.stat('/dev/mmcblk0p17').st_rdev}))"
        state=json.loads(run(c,'python3 -c '+shlex.quote(code)))
        require(state['b_unmounted'],'Slot B is mounted')
        require(state['data_device'] and any(len(parts)>2 and parts[1]=='/useremain' and parts[2]=='ext4' for parts in (line.split() for line in mounts.splitlines())), 'Expected ext4 data mount /useremain missing')
    return cmdline

def misc_reference(data):
    """Hash all misc bytes except the tail of the 512-byte AVB sector.

    AVB AB metadata occupies 32 bytes at offset 2048, including its CRC.
    Stock boot writes may vary the trailing sector padding. Metadata itself,
    recovery messages and every other byte remain part of this comparison.
    """
    import zlib
    if len(data)!=PARTS[5]:return None
    block=data[2048:2080]
    if block[:8]!=b'\x00AB0\x01\x00\x00\x00':return None
    if zlib.crc32(block[:28])!=int.from_bytes(block[28:32],'big'):return None
    return hashlib.sha256(data[:2080]+bytes(480)+data[2560:]).hexdigest()


def confirm_live(c,manifest):
    inspect(c)
    live={}
    for n in PARTS:
        expected=manifest['partitions'][str(n)]
        actual=run(c,f'sha256sum /dev/mmcblk0p{n}').split()[0]
        live[str(n)]=actual
        if actual==expected:continue
        require(n==5 and manifest.get('misc_reference'),'Partition '+str(n)+' changed after backup')
        # Read the entire current misc image; no device bytes are written.
        import io
        _,out,err=c.exec_command('cat /dev/mmcblk0p5',timeout=30)
        data=out.read();require(out.channel.recv_exit_status()==0,'Unable to read current misc metadata')
        require(hashlib.sha256(data).hexdigest()==actual,'Misc changed during verification')
        require(misc_reference(data)==manifest['misc_reference'],'Boot metadata or protected misc data changed after backup')
        print('Misc sector padding changed after reboot; valid A/B metadata and all protected bytes are unchanged.')
    return live


def stock_network(c,host,root=None):
    script=(PACKAGE/'optional/wlan-dualbetrieb/stock-network.py').read_text(encoding='utf-8')
    command='python3 - --host '+shlex.quote(host)
    if root is not None:command+=' --root '+shlex.quote(root)
    return json.loads(run(c,command,stdin=script,timeout=30))


def prepare(args,s,work):
    require(not (work/'device.json').exists(),'Device backup already exists; preserve it, use another --work directory')
    c=connect(s['printer_ip'],'root',work/'stock_known_hosts','rockchip')
    try:
        inspect(c);stock_network(c,s['printer_ip']);run(c,'test ! -e '+BASE)
        backup=work/'backup';backup.mkdir(exist_ok=True)
        hashes={}
        for n,size in PARTS.items():
            p=backup/f'p{n}.img';print('Backing up partition',n)
            get(c,f'/dev/mmcblk0p{n}',p)
            require(p.stat().st_size==size,'Incomplete partition backup')
            hashes[str(n)]=sha(p)
            require(hashes[str(n)]==run(c,f'sha256sum /dev/mmcblk0p{n}').split()[0],'Backup checksum mismatch')
    finally:c.close()
    # Original firmware tools are extracted from this device, never bundled in the release.
    builder=connect(s['pi_ip'],args.builder_user,work/'builder_known_hosts')
    remote='/tmp/kobrian-prepare-'+uuid.uuid4().hex
    try:
        run(builder,'sudo -n docker info >/dev/null && mkdir -p '+remote)
        put(builder,remote+'/system_a.img',backup/'p8.img')
        put(builder,remote+'/bootstrap-init.sh',PACKAGE/'source/bootstrap-init.sh')
        put(builder,remote+'/build-device.sh',PACKAGE/'source/build-device.sh',0o755)
        print('Building bootstrap from the printer backup on the Pi (Docker required)...')
        log=run(builder,'sudo -n docker run --rm -v '+remote+':/build -w /build debian:trixie-slim sh /build/build-device.sh',timeout=900)
        (work/'bootstrap-build.log').write_text(log)
        get(builder,remote+'/bootstrap.img',work/'bootstrap.img')
        get(builder,remote+'/bootcontrol.tar.gz',work/'bootcontrol.tar.gz')
    finally:builder.close()
    spec=importlib.util.spec_from_file_location('patch_bootlogo',PACKAGE/'source/patch_bootlogo.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    image=module.patch((backup/'p6.img').read_bytes(),(PACKAGE/'payload/logo.bmp').read_bytes())
    (work/'boot_b.img').write_bytes(image)
    manifest={'settings':s,'partitions':hashes,'files':{name:sha(work/name) for name in ['bootstrap.img','bootcontrol.tar.gz','boot_b.img']},'builder_directory':remote}
    (work/'device.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Backup and candidate ready. No printer partitions were written. Next: stage')

def device(work,s):
    m=json.loads((work/'device.json').read_text(encoding='utf-8'));require(m['settings']==s,'Settings changed; do not mix device preparations')
    for name,h in m['files'].items():require(sha(work/name)==h,'Prepared file changed: '+name)
    for n,h in m['partitions'].items():require(sha(work/'backup'/f'p{n}.img')==h,'Device backup changed')
    m['misc_reference']=misc_reference((work/'backup/p5.img').read_bytes())
    return m

def stage_display(c,s):
    """Populate the inactive root with both supported display interfaces."""
    put(c,ROOT+'/usr/local/share/s1-splash/kobrian.bgrx',PACKAGE/'payload/kobranest.bgrx')
    directory=ROOT+'/opt/kobrian-display-installer'
    run(c,'mkdir -p '+directory)
    for name in ('install.py','s1-ui','s1-ui-select','s1-helix'):
        put(c,directory+'/'+name,PACKAGE/'optional/helixscreen'/name,0o755)
    archive=PACKAGE/'payload/helixscreen-pi32-v1.0.5.tar.gz'
    remote=directory+'/'+archive.name
    present=run(c,'if test -f '+remote+'; then sha256sum '+remote+'; else echo missing; fi').split()[0]
    if present!=sha(archive):put(c,remote,archive)
    run(c,'chroot '+ROOT+' /usr/bin/python3 /opt/kobrian-display-installer/install.py --root / --pi-ip '+s['pi_ip'],timeout=180)

    # Install both transport choices without selecting USB or changing the Pi.
    usb_directory=ROOT+'/opt/usb-otg'
    run(c,'mkdir -p '+usb_directory+'/printer')
    for name in ('install-printer.py','printer/s1-usb-bridge'):
        put(c,usb_directory+'/'+name,PACKAGE/'optional/usb-otg'/name,0o755)
    run(c,'chroot '+ROOT+' /usr/bin/python3 /opt/usb-otg/install-printer.py --root /',timeout=60)
    require(s.get('tunnel_mode','usb') in ('usb','network'),'Invalid MCU transport')
    put(c,ROOT+'/etc/s1-tunnel-mode',s.get('tunnel_mode','usb')+'\n',0o644)

    stage_wifi(c,s)


def stage_wifi(c,s):
    """Copy this printer's OEM modules; retain private WLAN setup at the display."""
    directory=ROOT+'/opt/kobrian-wifi-installer'
    run(c,'mkdir -p '+directory+' '+ROOT+'/opt/s1-wifi')
    # Vendor modules stay device-local: no OEM binaries in the public package.
    for name in ('cfg80211.ko','RTL8723DS.ko'):
        destination=ROOT+'/opt/s1-wifi/'+name
        command='if test -s '+destination+'; then :; '
        for source in ('/oem/usr/ko/','/usr/ko/'):
            command+='elif test -s '+source+name+'; then cp '+source+name+' '+destination+'; '
        command+='else echo "Original WLAN module missing: '+name+'" >&2; exit 1; fi'
        run(c,command)
    for name in ('install-printer.py','prepare-runtime.py','run-inactive-packages.py','s1-realtek-init','s1-dual-network','s1-wifi-dhcp','s1.conf.example'):
        put(c,directory+'/'+name,PACKAGE/'optional/wlan-dualbetrieb'/name,0o755 if name!='s1.conf.example' else 0o600)
    run(c,'mkdir -p '+directory+'/firmware/rtl_nic')
    for name in ('rtl_nic/rtl8153b-2.fw','LICENCE.rtlwifi_firmware.txt'):
        put(c,directory+'/firmware/'+name,PACKAGE/'optional/wlan-dualbetrieb/firmware'/name,0o644)
    ready=run(c,'chroot '+ROOT+' /bin/sh -c '+shlex.quote('test -x /usr/bin/ustreamer && test -x /usr/sbin/wpa_supplicant && test -x /usr/sbin/ip && test -s /lib/firmware/regulatory.db && echo ready || echo missing')).strip()
    if ready!='ready':
        print('Installing WLAN dependencies from Debian repositories; Internet access required.')
        run(c,'python3 '+directory+'/run-inactive-packages.py',timeout=2200,progress=True)
    access=stock_network(c,s['printer_ip'],ROOT)
    run(c,'chroot '+ROOT+' /usr/bin/python3 /opt/kobrian-wifi-installer/install-printer.py --root / --address '+s['printer_ip']+'/'+str(s['prefix'])+' --gateway '+s['gateway']+' --primary-interface '+access['interface'],timeout=60)
    print('Network prepared:',access['interface'],'; saved WLAN copied on-device only' if access['saved_wifi'] else '; static LAN')




def base_checkpoint(c,s,work,record=False):
    files={'rootfs-armhf.tar.gz':PACKAGE/'payload/rootfs-armhf.tar.gz','bootstrap.img':work/'bootstrap.img','bootcontrol.tar.gz':work/'bootcontrol.tar.gz','boot_b.img':work/'boot_b.img'}
    evidence={'settings':s,'device_sha256':sha(work/'device.json'),'files':{name:sha(path) for name,path in files.items()}}
    for name,digest in evidence['files'].items():
        require(run(c,'sha256sum '+BASE+'/'+name).split()[0]==digest,'Staged upload changed: '+name)
    code="from pathlib import Path; import json; p=Path("+repr(ROOT)+"); assert p.is_dir() and not p.is_symlink(); print(json.dumps({'dev':p.stat().st_dev,'ino':p.stat().st_ino,'settings':json.loads((p/'etc/s1-settings.json').read_text(encoding='utf-8'))}))"
    remote=json.loads(run(c,'python3 -c '+shlex.quote(code)))
    require(remote.pop('settings')==s,'Inactive root settings differ')
    evidence['root_identity']=remote
    run(c,'test -x '+ROOT+'/usr/local/sbin/s1-boot && test -x '+ROOT+'/opt/rockchip-bootcontrol/rk_ota && chroot '+ROOT+' /bin/sh -n /usr/local/sbin/s1-service')
    checkpoint=work/'base-staged.json'
    if record:checkpoint.write_text(json.dumps(evidence),encoding='utf-8')
    else:require(json.loads(checkpoint.read_text(encoding='utf-8'))==evidence,'Base checkpoint changed; refusing resume')


def stage(args,s,work):
    m=device(work,s)
    # Fail early if the intended Moonraker is not reachable. Its trusted_clients must include the S1.
    import urllib.request
    with urllib.request.urlopen('http://'+s['pi_ip']+':7125/server/info',timeout=8) as r:
        require('result' in json.load(r),'Moonraker unavailable')
    password=getpass.getpass('Debian root password (Enter = stock rockchip; not stored on PC): ')
    if not password:password='rockchip'
    else:require(password==getpass.getpass('Repeat Debian root password: '),'Passwords differ')
    require(bool(password) and ':' not in password and '\n' not in password,'Invalid password')
    c=connect(s['printer_ip'],'root',work/'stock_known_hosts','rockchip')
    try:
        confirm_live(c,m)
        if (work/'base-staged.json').exists():
            base_checkpoint(c,s,work)
            print('Verified base checkpoint; continuing additional modules without extracting again.')
        else:
            free=int(run(c,"df -Pk /useremain | tail -n 1 | awk '{print $4}'").strip())
            require(free>1600000,'At least 1.6 GB free data space required')
            files={'rootfs-armhf.tar.gz':PACKAGE/'payload/rootfs-armhf.tar.gz','bootstrap.img':work/'bootstrap.img','bootcontrol.tar.gz':work/'bootcontrol.tar.gz','boot_b.img':work/'boot_b.img'}
            inventory=upload_inventory(c,files)
            for name,length in inventory.items():
                verify_upload_prefix(c,BASE+'/'+name,files[name.removesuffix('.new')],length)
            c.get_transport().set_keepalive(15)
            for name,path in files.items():
                put_resumable(c,BASE+'/'+name,path)
                require(run(c,'sha256sum '+BASE+'/'+name).split()[0]==sha(path),'Upload checksum mismatch')
            run(c,'mkdir '+ROOT+' && tar xzf '+BASE+'/rootfs-armhf.tar.gz -C '+ROOT+' && tar xzf '+BASE+'/bootcontrol.tar.gz -C '+ROOT)
            put(c,ROOT+'/usr/local/sbin/s1-health',(PACKAGE/'overlay/usr/local/sbin/s1-health').read_text(encoding='utf-8'),0o755)
            put(c,ROOT+'/usr/local/sbin/s1-return-to-stock',(PACKAGE/'overlay/usr/local/sbin/s1-return-to-stock').read_text(encoding='utf-8'),0o755)
            put(c,ROOT+'/usr/local/sbin/s1-klipper-autorecover',(PACKAGE/'overlay/usr/local/sbin/s1-klipper-autorecover').read_text(encoding='utf-8'),0o755)
            put(c,ROOT+'/etc/inittab',(PACKAGE/'overlay/etc/inittab').read_text(encoding='utf-8'),0o644)
            put(c,ROOT+'/usr/bin/ping',(PACKAGE/'overlay/usr/bin/ping').read_text(encoding='utf-8'),0o755)
            network='\n'.join(f'{k}={v}' for k,v in [('PRINTER_IP',s['printer_ip']),('PI_IP',s['pi_ip']),('GATEWAY',s['gateway']),('PREFIX',s['prefix'])])+'\n'
            put(c,ROOT+'/etc/s1-network.conf',network)
            put(c,ROOT+'/etc/s1-settings.json',json.dumps(s)+'\n')
            put(c,ROOT+'/etc/resolv.conf','nameserver '+s['gateway']+'\n')
            for path in ['etc/KlipperScreen.conf','etc/ssh/sshd-avnc-test.conf']:
                text=(PACKAGE/'overlay'/path).read_text(encoding='utf-8').replace('@PI_IP@',s['pi_ip']).replace('@PRINTER_IP@',s['printer_ip'])
                put(c,ROOT+'/'+path,text,0o644)
            if not s.get('light_auto_on',True):
                text=(PACKAGE/'overlay/usr/local/sbin/s1-light').read_text(encoding='utf-8').replace("write_text('high')","write_text('low')")
                put(c,ROOT+'/usr/local/sbin/s1-light',text,0o755)
            run(c,'chroot '+ROOT+' /usr/sbin/chpasswd',stdin='root:'+password+'\n')
            base_checkpoint(c,s,work,record=True)
        stage_display(c,s)
        run(c,'chroot '+ROOT+' /bin/sh -n /usr/local/sbin/s1-boot && chroot '+ROOT+' /bin/sh -n /usr/local/sbin/s1-service && test -s '+ROOT+'/usr/local/share/s1-splash/kobrian.bgrx && test -x '+ROOT+'/opt/rockchip-bootcontrol/rk_ota')
        put(c,BASE+'/device.json',json.dumps(m,indent=2)+'\n')
        run(c,'sync')
        (work/'staged.json').write_text(json.dumps({'rootfs_sha256':sha(PACKAGE/'payload/rootfs-armhf.tar.gz')}))
    finally:c.close()
    print('Debian staged. No boot partition written. Set up the Pi using docs/PI.md, then activate.')

def activate(args,s,work):
    m=device(work,s);require((work/'staged.json').exists(),'Run stage first')
    require(json.loads((work/'staged.json').read_text(encoding='utf-8'))['rootfs_sha256']==sha(PACKAGE/'payload/rootfs-armhf.tar.gz'),'Runtime changed since staging')
    print('Will write ONLY boot_b p7 and system_b p9, select B, and reboot. A is preserved.')
    require(input('Type INSTALL B '+s['printer_ip']+': ').strip()=='INSTALL B '+s['printer_ip'],'Cancelled')
    c=connect(s['printer_ip'],'root',work/'stock_known_hosts','rockchip')
    try:
        live_partitions=confirm_live(c,m)
        run(c,'test -f '+ROOT+'/etc/s1-network.conf && test -f '+ROOT+'/etc/shadow && test ! -e '+BASE+'/boot-attempt && test -x '+ROOT+'/usr/local/sbin/s1-ui-select && test -x '+ROOT+'/opt/helixscreen/bin/helix-screen-fbdev && test -f '+ROOT+'/opt/KlipperScreen/screen.py')
        for name in ('boot_b.img','bootstrap.img'):
            require(run(c,'sha256sum '+BASE+'/'+name).split()[0]==m['files'][name],'Staged image changed')
        # Also keep fresh backups on the device before any flash write.
        run(c,'mkdir -p '+BASE+'/sicherung-vor-installation')
        for n in PARTS:
            run(c,f'dd if=/dev/mmcblk0p{n} of={BASE}/sicherung-vor-installation/p{n}.img bs=1048576')
            require(run(c,f'sha256sum {BASE}/sicherung-vor-installation/p{n}.img').split()[0]==live_partitions[str(n)],'On-device backup invalid')
        run(c,'sync')
        # Kernel B is not mounted; only its resource images differ from the verified A kernel.
        run(c,'dd if='+BASE+'/boot_b.img of=/dev/mmcblk0p7 bs=1048576 && sync')
        require(run(c,'sha256sum /dev/mmcblk0p7').split()[0]==m['files']['boot_b.img'],'Boot B readback mismatch: stay in A and restore from backup')
        run(c,'dd if='+BASE+'/bootstrap.img of=/dev/mmcblk0p9 bs=1048576 && sync')
        size=(work/'bootstrap.img').stat().st_size
        require(run(c,f'head -c {size} /dev/mmcblk0p9 | sha256sum').split()[0]==m['files']['bootstrap.img'],'System B readback mismatch: stay in A and restore from backup')
        require(run(c,'sha256sum /dev/mmcblk0p6').split()[0]==live_partitions['6'],'Unexpected A kernel change')
        require(run(c,'sha256sum /dev/mmcblk0p8').split()[0]==live_partitions['8'],'Unexpected A system change')
        run(c,'/usr/bin/rk_ota --misc=other --mode=retry && sync')
        print('B activated and verified. Rebooting. New Debian SSH host keys will differ.')
        c.exec_command('/bin/busybox reboot')
    finally:c.close()

def status(args,s,work):
    c=connect(s['printer_ip'],'root',work/'debian_known_hosts','rockchip')
    try:print(run(c,'cat /proc/cmdline; cat /var/log/s1-boot-health.log; cat /run/s1/splash.progress; test ! -e '+BASE+'/boot-attempt && echo BOOT_CONFIRMED'))
    finally:c.close()

def rollback(args,s,work):
    c=connect(s['printer_ip'],'root',work/'debian_known_hosts','rockchip')
    try:
        require('root=/dev/mmcblk0p9' in run(c,'cat /proc/cmdline'),'Rollback command requires Debian slot B')
        require(input('Prepare original slot A and shut down? Type RETURN TO A: ').strip()=='RETURN TO A','Cancelled')
        c.exec_command('/usr/local/sbin/s1-return-to-stock')
        print('Original A selected; shutdown requested. Wait 15 seconds, power off, wait 10 seconds and power on. Runtime files retained.')
    finally:c.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['verify','prepare','stage','activate','status','rollback'])
    p.add_argument('--settings',type=Path,default=Path('settings.json'))
    p.add_argument('--work',type=Path,default=Path('device-work'))
    p.add_argument('--builder-user',default='pi',help='Pi SSH user with passwordless sudo docker access; used only by prepare')
    args=p.parse_args();verify_package()
    if args.action=='verify':print('Package checksums OK');return
    s=settings(args.settings);work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
    require(not work.is_relative_to(PACKAGE/'payload'),'Do not store device data in payload')
    globals()[args.action](args,s,work)

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print('STOP:',exc,file=sys.stderr);sys.exit(1)
