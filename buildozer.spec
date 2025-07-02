[app]
title = Monte Card App
package.name = montecard
package.domain = com.montecard
version = 1.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,html,css,js,json
source.exclude_dirs = tests,bin,venv,__pycache__,.git,backup
requirements = python3,kivy,kivymd,android,jnius,plyer,PIL,bcrypt,cryptography,mutagen,pygame,qrcode,imageio,imageio-ffmpeg,psutil,webbrowser
icon.filename = %(source.dir)s/data/icon.png

[buildozer]
log_level = 2
warn_on_root = 1

[android]
arch = arm64-v8a
minapi = 21
api = 33
ndk = 25b
sdk = 33
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO
android.private_storage = True
android.allow_backup = False
p4a.branch = develop
p4a.bootstrap = sdl2
