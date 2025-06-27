[app]
title = Monte Card App
package.name = montecard
package.domain = com.akhilkast
source.dir = .
source.main = main.py

# ✅ CRITICAL: Include ALL Python files explicitly
source.include_exts = py,pyc,pyo,png,jpg,jpeg,gif,bmp,webp,tiff,kv,atlas,wav,mp3,mp4,avi,mov,mkv,txt,json

# ✅ CRITICAL: Explicit patterns - include all Python files in root
source.include_patterns = *.py,*.kv,*.json,assets/*

# ✅ CRITICAL: Don't exclude Python files
source.exclude_patterns = tests/*,spec/*,__pycache__/*,.git*,.github/*

# ✅ CRITICAL: All your dependencies
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android

version = 0.1
orientation = portrait
fullscreen = 0

# ✅ ANDROID LICENSE ACCEPTANCE - Critical for GitHub Actions
android.accept_sdk_license = True
android.skip_update = False

# Android permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,MANAGE_EXTERNAL_STORAGE

# ✅ ANDROID BUILD SETTINGS - Updated for GitHub Actions compatibility
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True

# ✅ P4A BOOTSTRAP - Required for proper build
p4a.bootstrap = sdl2

# ✅ BUILDOZER SETTINGS - Critical for GitHub Actions
[buildozer]
log_level = 2
warn_on_root = 1
