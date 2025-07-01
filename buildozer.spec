[app]
title = Monte Card App
package.name = montecard
package.domain = com.akhilkast
source.dir = .
source.main = main.py
# Explicitly include all supported source types
source.include_exts = py,pyc,pyo,png,jpg,jpeg,gif,bmp,webp,tiff,kv,atlas,wav,mp3,mp4,avi,mov,mkv,txt,json
# FIXED: Added Python stdlib test exclusions to prevent Unicode errors
source.exclude_patterns = spec/,pycache/,.git,.github/
# Requirements: keep your versions as they are
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android,cython,psutil,pygame==2.1.3,sdl2,sdl2_image,sdl2_mixer,sdl2_ttf
version = 0.1
orientation = portrait
fullscreen = 0
android.accept_sdk_license = True
android.skip_update = False
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
p4a.bootstrap = sdl2
# NEW: This is the crucial line to address the SSE2 symbol error.
# It tells Pygame's build process to use SDL2's generic alpha blending.
p4a.env_vars = PYGAME_BLEND_ALPHA_SDL2=1

[buildozer]
log_level = 5
warn_on_root = 1
