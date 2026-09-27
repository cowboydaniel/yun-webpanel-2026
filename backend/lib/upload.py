# A minimal stand-in for OpenWrt's cgi-io upload, for boards that don't have
# it (the stock Yun firmware). Installed behind /www/cgi-bin/cgi-upload only
# when that file doesn't already exist.
#
# The panel POSTs multipart/form-data with the fields sessionid, filename,
# filemode and filedata. Only /tmp/sketch.hex can be written, and only by a
# ubus session that may call yun.sketch_flash.
#
# Runs under Python 2.7 and Python 3, without the cgi module (removed in
# Python 3.13).

import json
import os
import re
import subprocess
import sys

ALLOWED = '/tmp/sketch.hex'
MAX_SIZE = 512 * 1024


def reply(status, obj):
    out = getattr(sys.stdout, 'buffer', sys.stdout)
    body = json.dumps(obj).encode('utf-8')
    out.write(('Status: %s\r\nContent-Type: application/json\r\n\r\n' % status).encode('ascii'))
    out.write(body)
    out.flush()
    return 0


def parse_multipart(body, boundary):
    fields = {}
    delim = b'--' + boundary
    for part in body.split(delim)[1:]:
        if part.startswith(b'--'):
            break
        part = part[2:] if part.startswith(b'\r\n') else part
        head, sep, data = part.partition(b'\r\n\r\n')
        if not sep:
            continue
        if data.endswith(b'\r\n'):
            data = data[:-2]
        m = re.search(br'name="([^"]*)"', head)
        if m:
            fields[m.group(1).decode('utf-8', 'replace')] = data
    return fields


def session_may_flash(sid):
    if not re.match(r'^[0-9a-f]{32}$', sid):
        return False
    args = json.dumps({'ubus_rpc_session': sid, 'scope': 'ubus',
                       'object': 'yun', 'function': 'sketch_flash'})
    try:
        out = subprocess.check_output(['ubus', 'call', 'session', 'access', args])
    except (OSError, subprocess.CalledProcessError):
        return False
    try:
        return json.loads(out.decode('utf-8')).get('access') is True
    except ValueError:
        return False


def main():
    if os.environ.get('REQUEST_METHOD') != 'POST':
        return reply('405 Method Not Allowed', {'error': 'POST only'})

    ctype = os.environ.get('CONTENT_TYPE', '')
    m = re.search(r'boundary="?([^";]+)"?', ctype)
    if not ctype.startswith('multipart/form-data') or not m:
        return reply('400 Bad Request', {'error': 'Expected multipart/form-data'})

    try:
        length = int(os.environ.get('CONTENT_LENGTH', '0'))
    except ValueError:
        length = 0
    if length <= 0 or length > MAX_SIZE:
        return reply('413 Request Entity Too Large', {'error': 'Upload too large'})

    stdin = getattr(sys.stdin, 'buffer', sys.stdin)
    body = stdin.read(length)
    fields = parse_multipart(body, m.group(1).encode('ascii'))

    sid = fields.get('sessionid', b'').decode('ascii', 'replace').strip()
    name = fields.get('filename', b'').decode('utf-8', 'replace').strip()
    data = fields.get('filedata')

    if not session_may_flash(sid):
        return reply('403 Forbidden', {'error': 'Access denied'})
    if name != ALLOWED:
        return reply('403 Forbidden', {'error': 'Only %s can be uploaded' % ALLOWED})
    if data is None:
        return reply('400 Bad Request', {'error': 'No file'})

    fd = os.open(ALLOWED, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return reply('200 OK', {'size': len(data)})


if __name__ == '__main__':
    sys.exit(main())
