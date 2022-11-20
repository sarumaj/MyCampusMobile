[app]
title = MyCampus Mobil
package.name = mycampus_mobile
package.domain = org.github.sarumaj
source.dir = .
source.include_exts = py, png, jpg, kv, atlas
source.include_patterns = data/img/*, data/logo/*
source.exclude_exts = spec
source.exclude_dirs = tests, bin, venv, mock
#source.exclude_patterns = data/mock/*
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py
# requirements.source.mycampus_mobile = %(source.dir)s/mycampus_mobile
icon.filename = %(source.dir)s/data/logo/icon.png

# (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

################
#              #
# OSX Specific #
#              #
################

osx.python_version = 3.10.1
osx.kivy_version = 2.1.0

####################
#                  #
# Android specific #
#                  #
####################

fullscreen = 0

# False doesn't work -- bug in the buildozer API (toolchain.py)
android.private_storage = True
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.release_artifact = apk
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

p4a.bootstrap = sdl2
p4a.fork = kivy
p4a.branch = master

[app:requirements]
android
asyncgui==0.5.5
asynckivy==0.5.4
beautifulsoup4==4.11.1
chardet==3.0.4
certifi==2022.9.24
expiringdict==1.2.2
icalendar==4.1.0
idna==2.10
kivymd==1.0.2
libbz2
matplotlib==3.5.2
networkx==2.8.8
plyer==2.0.0
pyjnius==1.4.2
python3
pytz==2022.1
requests==2.28.1
six==1.15.0
urllib3==1.26.12

# (list) Permissions
[app:android.permissions]
INTERNET
READ_EXTERNAL_STORAGE
WRITE_EXTERNAL_STORAGE
ACCESS_NETWORK_STATE
ACCESS_NOTIFICATION_POLICY
ACCESS_WIFI_STATE

[buildozer]

# (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2
warn_on_root = 0
build_dir = ./.buildozer
bin_dir = ./bin
