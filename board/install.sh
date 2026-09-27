#!/bin/sh
# Install the Yun Panel on this Yun. Run from an unpacked copy of the repo;
# install.sh on a PC does this over SSH.
#
# Only adds files: the panel goes in /www/yun-panel/, next to whatever web
# panel the firmware already has. Every file written is listed in
# /usr/share/yun-panel/installed-files so board/uninstall.sh can remove them.

set -e

SRC=$(cd "$(dirname "$0")/.." && pwd)
LIB=/usr/share/yun-panel
MANIFEST=$LIB/installed-files
PLUGIN=/usr/libexec/rpcd/yun
ACL=/usr/share/rpcd/acl.d/yun-panel.json
UPLOAD=/www/cgi-bin/cgi-upload

mkdir -p "$LIB"
: > "$MANIFEST.new"

put() {
	# put <source> <destination> <mode>
	mkdir -p "$(dirname "$2")"
	cp "$1" "$2"
	chmod "$3" "$2"
	echo "$2" >> "$MANIFEST.new"
}

# Front end
for f in $(cd "$SRC/www" && find yun-panel -type f); do
	put "$SRC/www/$f" "/www/$f" 644
done

# Back end, unless the firmware already has its own "yun" ubus object (Yun
# 2026 may ship one). Ours is recognised by its first comment.
BACKEND=1
if ubus list yun >/dev/null 2>&1 && ! grep -q 'rpcd plugin for the Yun Panel' "$PLUGIN" 2>/dev/null; then
	BACKEND=0
	echo "This firmware already has a \"yun\" ubus object; using it and installing only the front end."
fi

if [ $BACKEND = 1 ]; then
	put "$SRC/backend/rpcd/yun" "$PLUGIN" 755
	put "$SRC/backend/acl/yun-panel.json" "$ACL" 644
	put "$SRC/backend/lib/helper.py" "$LIB/helper.py" 644
	put "$SRC/backend/lib/upload.py" "$LIB/upload.py" 644

	# Sketch uploads go through cgi-io's /cgi-bin/cgi-upload. Stock firmware
	# doesn't have it, so add a stand-in, but never replace the real one.
	if [ ! -e "$UPLOAD" ] || grep -q 'Stand-in for cgi-io' "$UPLOAD" 2>/dev/null; then
		put "$SRC/backend/cgi/cgi-upload" "$UPLOAD" 755
	fi

	if ! command -v python3 >/dev/null && ! command -v python >/dev/null; then
		echo "Warning: no Python found, so sketch upload and the Bridge page won't work."
	fi
fi

echo "$MANIFEST" >> "$MANIFEST.new"
mv "$MANIFEST.new" "$MANIFEST"

# rpcd reads plugins and ACLs at start. Restarting it signs out open sessions.
[ $BACKEND = 1 ] && /etc/init.d/rpcd restart

echo "Yun Panel installed: http://$(uci -q get system.@system[0].hostname || echo arduino).local/yun-panel/"
