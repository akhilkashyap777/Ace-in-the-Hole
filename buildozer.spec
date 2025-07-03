[app]
title = Monte Card App
package.name = montecard
package.domain = com.montecard
version = 1.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,html,css,js,json
source.exclude_dirs = tests,bin,venv,__pycache__,.git,backup
requirements = python3,kivy,kivymd,android,jnius,plyer,Pillow,bcrypt,cryptography,mutagen,qrcode,imageio,imageio-ffmpeg,psutil
icon.filename = %(source.dir)s/data/icon.png

[buildozer]
log_level = 5
warn_on_root = 1

[android]
android.arch = arm64-v8a,armeabi-v7a
minapi = 21
api = 33
ndk = 25.2.9519653
sdk = 33
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO
android.private_storage = True
android.allow_backup = False
p4a.branch = develop
p4a.bootstrap = sdl2
