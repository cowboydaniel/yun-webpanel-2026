#!/bin/sh
# Install the Yun Panel on a Yun over SSH:
#
#   ./install.sh [ssh destination]      (default root@arduino.local)
#
# Works with the stock firmware and Arduino Yun 2026. The stock firmware's SSH
# server is old, so recent OpenSSH clients need legacy options, e.g. in
# ~/.ssh/config:
#
#   Host arduino.local
#       KexAlgorithms +diffie-hellman-group14-sha1
#       HostKeyAlgorithms +ssh-rsa
#       PubkeyAcceptedAlgorithms +ssh-rsa

set -e
HOST=${1:-root@arduino.local}
cd "$(dirname "$0")"

tar -czf - www backend board | ssh "$HOST" '
	rm -rf /tmp/yun-panel-src && mkdir /tmp/yun-panel-src &&
	tar -xzf - -C /tmp/yun-panel-src &&
	sh /tmp/yun-panel-src/board/install.sh
	rc=$?
	rm -rf /tmp/yun-panel-src
	exit $rc'
