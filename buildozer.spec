[app]
title = Monte Card App
package.name = montecard
package.domain = com.akhilkast
source.dir = .
source.main = main.py
source.include_exts = py,png,jpg,jpeg,gif,bmp,webp,tiff,kv,atlas,wav,mp3,mp4,avi,mov,mkv,txt,json
source.include_patterns = assets/*,*.py,*.kv
version = 0.1
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
p4a.bootstrap = sdl2
osx.python_version = 3
osx.kivy_version = 1.9.1

[buildozer]
log_level = 2
warn_on_root = 1
