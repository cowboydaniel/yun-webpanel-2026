#!/bin/sh
# Remove the Yun Panel from a Yun over SSH: ./uninstall.sh [ssh destination]
HOST=${1:-root@arduino.local}
exec ssh "$HOST" 'sh -s' < "$(dirname "$0")/board/uninstall.sh"
