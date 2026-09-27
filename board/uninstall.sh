#!/bin/sh
# Remove everything board/install.sh added.

MANIFEST=/usr/share/yun-panel/installed-files

if [ ! -f "$MANIFEST" ]; then
	echo "The Yun Panel isn't installed."
	exit 0
fi

while read -r f; do
	rm -f "$f"
done < "$MANIFEST"
rm -f "$MANIFEST"
rmdir /usr/share/yun-panel /www/yun-panel/yun /www/yun-panel 2>/dev/null

/etc/init.d/rpcd restart
echo "Yun Panel removed."
