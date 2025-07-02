[app]
title = Monte Card App
package.name = montecard
package.domain = com.akhilkast
source.dir = .
source.main = main.py
source.include_exts = py,pyc,pyo,png,jpg,jpeg,gif,bmp,webp,tiff,kv,atlas,wav,mp3,mp4,avi,mov,mkv,txt,json
source.exclude_patterns = spec/,pycache/,.git,.github/
# REMOVED: pygame and related SDL2 requirements since you're using WebView
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android,cython
version = 0.1
orientation = portrait
fullscreen = 0

android.accept_sdk_license = True
android.skip_update = False
# Keep all vault permissions - needed for photo/video/audio vault features
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,MANAGE_EXTERNAL_STORAGE,VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True

# CHANGED: Using webview bootstrap since you're not using pygame
p4a.bootstrap = webview

[buildozer]
log_level = 5
warn_on_root = 1
