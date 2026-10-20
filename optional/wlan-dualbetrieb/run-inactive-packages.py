#!/usr/bin/python3
"""Provide temporary virtual filesystems only to the inactive staging root."""
from pathlib import Path
import subprocess
root=Path('/useremain/s1-klipperscreen-test/rootfs')
assert root.resolve()==root and root.is_dir()
assert 'root=/dev/mmcblk0p8' in Path('/proc/cmdline').read_text(),'Original slot A required'
assert (root/'etc/s1-settings.json').is_file()
mounted=[]
try:
    for name,arguments in [('dev',['--bind','/dev']),('proc',['-t','proc','-o','nosuid,nodev,noexec','proc'])]:
        target=root/name
        assert target.resolve()==target and target.is_dir()
        assert not any(line.split()[1]==str(target) for line in Path('/proc/mounts').read_text().splitlines()),'Staging mount already exists'
        subprocess.run(['mount',*arguments,str(target)],check=True)
        mounted.append(target)
    subprocess.run(['chroot',str(root),'/usr/bin/python3','/opt/kobrian-wifi-installer/prepare-runtime.py'],check=True)
finally:
    failures=[]
    for target in reversed(mounted):
        if subprocess.run(['umount',str(target)]).returncode:failures.append(str(target))
    if failures:raise RuntimeError('Could not unmount staging filesystem: '+', '.join(failures))
