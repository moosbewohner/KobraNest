#!/usr/bin/python3
"""Install WLAN packages without starting services in the inactive root."""
from pathlib import Path
import os, signal, subprocess

def command(args, timeout):
    process=subprocess.Popen(args, env={**os.environ,'DEBIAN_FRONTEND':'noninteractive'}, start_new_session=True)
    try:
        elapsed=0
        while True:
            try:
                result=process.wait(timeout=20)
                if result: raise subprocess.CalledProcessError(result,args)
                return
            except subprocess.TimeoutExpired:
                elapsed+=20
                print('WLAN package preparation: '+str(elapsed)+' seconds; waiting for '+args[0],flush=True)
                if elapsed>=timeout: raise
    except BaseException:
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
        raise

policy=Path('/usr/sbin/policy-rc.d')
assert not policy.is_symlink(), 'Unexpected policy-rc.d symlink'
old=policy.read_bytes() if policy.exists() else None
mode=policy.stat().st_mode & 0o777 if policy.exists() else 0o755
try:
    policy.write_bytes(b'#!/bin/sh\nexit 101\n');policy.chmod(0o755)
    command(['dpkg','--configure','-a'],300)
    options=['-o','Acquire::Retries=3','-o','Acquire::http::Timeout=30','-o','Acquire::https::Timeout=30','-o','Dpkg::Use-Pty=0']
    command(['apt-get',*options,'update'],600)
    command(['apt-get',*options,'install','-y','--no-install-recommends','wpasupplicant','iproute2','wireless-regdb'],1200)
    for package in ('wpasupplicant','iproute2','wireless-regdb'):
        assert subprocess.check_output(['dpkg-query','-W','-f=${Status}',package]).decode().strip()=='install ok installed',package+' incomplete'
    assert not subprocess.check_output(['dpkg','--audit']).strip(),'Package configuration incomplete'
finally:
    if old is None:policy.unlink(missing_ok=True)
    else:policy.write_bytes(old);policy.chmod(mode)
