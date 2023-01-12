#!/usr/bin/env python
import os
import re
import uuid
import json
import subprocess

skpk = []

def gen_wspath():
    return '/' + str(uuid.uuid4())

def gen_uuid():
    return str(uuid.uuid4())

def gen_wgsk():
    sk = subprocess.run('docker run lazynode/wireguard wg genkey', shell=True, check=True, capture_output=True).stdout
    pk = subprocess.run('docker run -i lazynode/wireguard wg pubkey', shell=True, check=True, capture_output=True, input=sk).stdout
    sk = sk.strip().decode()
    pk = pk.strip().decode()
    skpk.append((sk,pk))
    return sk

def gen_peer():
    sk = subprocess.run('docker run lazynode/wireguard wg genkey', shell=True, check=True, capture_output=True).stdout
    pk = subprocess.run('docker run -i lazynode/wireguard wg pubkey', shell=True, check=True, capture_output=True, input=sk).stdout
    sk = sk.strip().decode()
    pk = pk.strip().decode()
    skpk.append((sk,pk))
    return pk

def make_peer(lines, peers):
    for v in lines:
        if v.startswith('wg set wg0 peer'):
            for (n, p) in enumerate(peers):
                buf = re.sub('ABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBA=', p, v)
                buf = re.sub('198.19.0.2/32', '198.19.0.{}/32'.format(n+2), buf)
                yield buf
        else:
            yield v

if __name__ == '__main__':
    domain = os.environ['DOMAIN']
    email = os.environ.get('EMAIL', 'email@example.com')
    wspath = os.environ.get('WSPATH') or gen_wspath()
    wgsk = os.environ.get('WGSK') or gen_wgsk()
    uuids = os.environ.get('UUIDS') or gen_uuid()
    if uuids.isdigit():
        uuids = [gen_uuid() for i in range(int(uuids))]
    else:
        uuids = uuids.split(',')
    peers = os.environ.get('PEERS') or gen_peer()
    if peers.isdigit():
        peers = [gen_peer() for i in range(int(peers))]
    else:
        peers = peers.split(',')
    assert len(uuids) < 128
    assert len(peers) < 128
    with open('private/certbot/run.sh', 'r') as f:
        buf = f.read()
    buf = re.sub('email@example.com', email, buf)
    buf = re.sub('domain.example.com', domain, buf)
    with open('private/certbot/run.sh', 'w') as f:
        f.write(buf)
    with open('private/nginx/conf.d/v2ray.conf', 'r') as f:
        buf = f.read()
    buf = re.sub('domain.example.com', domain, buf)
    buf = re.sub('/lazywebsocketpath', wspath, buf)
    with open('private/nginx/conf.d/v2ray.conf', 'w') as f:
        f.write(buf)
    with open('private/v2ray/config.json', 'r') as f:
        buf = json.load(f)
    buf['inbounds'][0]['settings']['clients'] = [{'id': v} for v in uuids]
    buf['inbounds'][0]['streamSettings']['wsSettings']['path'] = wspath
    with open('private/v2ray/config.json', 'w') as f:
        json.dump(buf, f, indent = 4)
    with open('private/wireguard/sk', 'w') as f:
        f.write(wgsk)
    with open('private/wireguard/init', 'r') as f:
        buf = f.readlines()
    buf = ''.join(make_peer(buf, peers))
    with open('private/wireguard/init', 'w') as f:
        f.write(buf)
    for v in uuids:
        print('V2RAY UUID:', v)
    for (sk, pk) in skpk:
        if sk == wgsk:
            wgpk = pk
    for (n, p) in enumerate(peers):
        for (sk, pk) in skpk:
            if p == pk:
                print('WG:', 'SK:', sk, 'IP:', '198.19.0.{}'.format(n+2),'PEER:', wgpk)

