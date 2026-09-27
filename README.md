# yun-webpanel-2026

The Yún Panel: a modern web panel for the Arduino Yún that installs on the **stock Yún firmware** as well as on [Arduino Yún 2026](https://github.com/cowboydaniel/arduino-yun-2026). You don't need to update the firmware to use it.

It's added next to the stock panel, at `http://arduino.local/yun-panel/`, and doesn't change the firmware, the Bridge or the stock web panel. Only the Yún Rev1 is supported.

The front end is a copy of the panel in arduino-yun-2026 (`feed/yun-webpanel`, as of commit `b7e4bcd`). That copy stays where it is. This repo adds a back end that runs on both firmwares, plus a few small front-end changes for the stock firmware.

## What it does

- Shows the board's status: Wi-Fi, Ethernet, memory, storage, uptime and load
- Scans for Wi-Fi networks and joins one, or switches to setup (access point) mode
- Uploads a sketch: drag and drop the `.hex` from **Sketch → Export Compiled Binary**
- Restarts the sketch
- Shows and edits the Bridge datastore, and sends Mailbox messages
- Changes the hostname, time zone, REST API password setting and root password
- Restarts the Yún

Firmware updates from the panel aren't available yet. The panel says so, and doesn't pretend the board is up to date.

## Install

From a PC that can reach the Yún over SSH:

```sh
./install.sh root@arduino.local
```

Then open `http://arduino.local/yun-panel/` and sign in as root with the board's password.

The stock firmware's SSH server is old, so recent OpenSSH clients need legacy options. Add this to `~/.ssh/config`:

```
Host arduino.local
    KexAlgorithms +diffie-hellman-group14-sha1
    HostKeyAlgorithms +ssh-rsa
    PubkeyAcceptedAlgorithms +ssh-rsa
```

To remove it:

```sh
./uninstall.sh root@arduino.local
```

You can also copy the repo onto the board and run `sh board/install.sh` or `sh board/uninstall.sh` there.

The installer only adds files, and lists every one in `/usr/share/yun-panel/installed-files`, so uninstalling removes exactly what it added. It then restarts `rpcd`, which signs out any open panel sessions.

| File on the board | Purpose |
| --- | --- |
| `/www/yun-panel/` | The panel |
| `/usr/libexec/rpcd/yun` | The `yun` ubus object (the back end) |
| `/usr/share/rpcd/acl.d/yun-panel.json` | Access rights for signed-in users |
| `/usr/share/yun-panel/helper.py` | Bridge datastore, Mailbox, password hash |
| `/usr/share/yun-panel/upload.py`, `/www/cgi-bin/cgi-upload` | Sketch upload. Installed only if the board has no `cgi-upload` of its own. |

## How it works

The panel talks to the board over ubus JSON-RPC at `/ubus`, which both firmwares' web servers provide, and signs in with rpcd's `session.login`.

The back end, [`backend/rpcd/yun`](backend/rpcd/yun), is an rpcd plugin written in shell. It detects which firmware it's on and uses that firmware's own tools:

| Task | Stock firmware | Arduino Yún 2026 |
| --- | --- | --- |
| Join Wi-Fi | Same uci changes as the stock panel, then reboot | `yun-wifi client` |
| Setup mode | `wifi-reset-and-reboot` | `yun-wifi ap` |
| Sketch upload | `merge-sketch-with-bootloader.lua`, `kill-bridge`, `run-avrdude` | same |
| Restart sketch | `reset-mcu` | same |
| Bridge datastore and Mailbox | JSON socket on port 5700 (Python 2) | same socket (Python 3) |

A few stock-firmware limits shape the design:

- **No floats or large integers.** The 2015 ubus on the stock firmware has no floating-point type and caps integers at 2,147,483,647. The back end sends byte counts and load averages as strings, and the panel turns them back into numbers.
- **No `cgi-io`.** Sketch uploads use a small Python stand-in for `/cgi-bin/cgi-upload`. It only writes `/tmp/sketch.hex`, and only for a session that may call `yun.sketch_flash`.
- **No `system.reboot`.** The panel falls back to `yun.reboot`.
- **Changing Wi-Fi reboots the board**, as the stock panel did.

If the firmware already has its own `yun` ubus object, the installer leaves it alone and installs only the front end. Arduino Yún 2026 may ship such an object.

## Tested

The panel was tested on a Yún Rev1 running the stock firmware, OpenWrtYun ChaosCalmer 1.6.2 (`built=Fri May 13 09:22:20 UTC 2016`). These worked:
- status, Wi-Fi scan and the update check, both in the browser and over `/ubus`
- the access checks, including refusing a method the session wasn't granted
- sketch upload and flashing: a plain `.hex` was merged with the bootloader and verified at 32,768 bytes in about 5 seconds
- the upload stand-in refusing a bad session and a path other than `/tmp/sketch.hex`

Not tested yet:
- joining Wi-Fi, setup mode, settings, and changing the password (these change the board, and some reboot it)
- the Bridge pages with a sketch that uses Bridge
- anything on Arduino Yún 2026

## Preview without a board

```sh
python3 demo/serve.py
```

Then open `http://localhost:8080/` and sign in with the password `arduino`. The demo uses a fake board.
