#!/bin/sh
# Remove everything board/install.sh added.

MANIFEST=/usr/share/yun-panel/installed-files

if [ ! -f "$MANIFEST" ]; then
	echo "The Yun Panel isn't installed."
	exit 0
fi

# Put back the root page the panel replaced.
if grep -q 'yun-panel redirect' /www/index.html 2>/dev/null; then
	if [ -f /usr/share/yun-panel/index.html.orig ]; then
		cp /usr/share/yun-panel/index.html.orig /www/index.html
	else
		rm -f /www/index.html
	fi
fi
rm -f /usr/share/yun-panel/index.html.orig

while read -r f; do
	rm -f "$f"
done < "$MANIFEST"
rm -f "$MANIFEST"
rmdir /usr/share/yun-panel /www/yun-panel/yun /www/yun-panel 2>/dev/null

/etc/init.d/rpcd restart
echo "Yun Panel removed."
