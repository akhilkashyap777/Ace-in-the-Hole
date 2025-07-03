[app]
title = Monte Card App
package.name = montecard
package.domain = com.montecard
source.dir = .
source.include_exts = py,pyc,pyo,png,jpg,jpeg,gif,bmp,webp,tiff,kv,atlas,wav,mp3,mp4,avi,mov,mkv,txt,json,html,css,js
source.exclude_patterns = spec/,pycache/,.git,.github/,tests/,bin/,venv/,backup/
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android,cython,psutil
version = 1.0
orientation = portrait
fullscreen = 0
android.accept_sdk_license = True
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
p4a.bootstrap = sdl2
icon.filename = %(source.dir)s/data/icon.png

[buildozer]
log_level = 5
warn_on_root = 1
