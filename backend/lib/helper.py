# Helpers for the Yun Panel's rpcd plugin that are easier in Python than in
# shell. Runs under Python 2.7 (stock Yun firmware) and Python 3 (Yun 2026).
#
#   helper.py bridge-getall          print {"values": {...}} from the datastore
#   helper.py bridge-put KEY VALUE
#   helper.py bridge-delete KEY
#   helper.py mailbox MESSAGE
#   helper.py sha256                 hash stdin, print the hex digest
#
# The bridge commands talk to the bridge's JSON socket on 127.0.0.1:5700
# directly. Both the stock YunBridge and its Python 3 port speak the same
# protocol there, so this doesn't depend on either one's client library.

import hashlib
import json
import socket
import sys
import time

HOST = '127.0.0.1'
PORT = 5700
TIMEOUT = 5


class Bridge(object):
    def __init__(self):
        self.sock = socket.create_connection((HOST, PORT), TIMEOUT)
        self.buf = ''
        self.decoder = json.JSONDecoder()

    def send(self, obj):
        self.sock.sendall(json.dumps(obj).encode('utf-8'))

    def recv(self, deadline):
        # Replies are JSON objects written back to back on the socket.
        while True:
            text = self.buf.lstrip()
            if text:
                try:
                    obj, end = self.decoder.raw_decode(text)
                    self.buf = text[end:]
                    return obj
                except ValueError:
                    pass
            left = deadline - time.time()
            if left <= 0:
                return None
            self.sock.settimeout(left)
            try:
                chunk = self.sock.recv(4096)
            except socket.timeout:
                return None
            if not chunk:
                return None
            self.buf += chunk.decode('utf-8', 'replace')

    def request(self, obj, key=None):
        self.send(obj)
        deadline = time.time() + TIMEOUT
        while True:
            r = self.recv(deadline)
            if r is None:
                return None
            if not isinstance(r, dict) or 'value' not in r:
                continue
            if key is None or r.get('key') == key:
                return r

    def close(self):
        self.sock.close()


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ''

    if cmd == 'sha256':
        data = sys.stdin.read()
        if not isinstance(data, bytes):
            data = data.encode('utf-8')
        print(hashlib.sha256(data).hexdigest())
        return 0

    b = Bridge()
    try:
        if cmd == 'bridge-getall':
            r = b.request({'command': 'get'})
            values = r.get('value') if r else None
            if not isinstance(values, dict):
                values = {}
            print(json.dumps({'values': values}))
        elif cmd == 'bridge-put':
            b.request({'command': 'put', 'key': argv[2], 'value': argv[3]}, argv[2])
        elif cmd == 'bridge-delete':
            b.request({'command': 'delete', 'key': argv[2]}, argv[2])
        elif cmd == 'mailbox':
            b.send({'command': 'raw', 'data': argv[2]})
        else:
            sys.stderr.write('usage: helper.py bridge-getall|bridge-put|bridge-delete|mailbox|sha256\n')
            return 2
    finally:
        b.close()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
