[app]
title = Monte Card App
package.name = montecard
package.domain = com.akhilkast
source.dir = .
source.main = main.py
source.include_exts = py,pyc,pyo,png,jpg,jpeg,gif,bmp,webp,tiff,kv,atlas,wav,mp3,mp4,avi,mov,mkv,txt,json
source.exclude_patterns = spec/,pycache/,.git,.github/

# Fixed requirements - removed conflicting and redundant packages
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,pyjnius,cryptography,bcrypt,plyer

version = 0.1
orientation = portrait
fullscreen = 0

# Android configuration
android.accept_sdk_license = True
android.skip_update = False

# Vault app permissions - including MANAGE_EXTERNAL_STORAGE for deep system access
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,MANAGE_EXTERNAL_STORAGE,VIBRATE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True

# Bootstrap configuration
p4a.bootstrap = sdl2

# Required configurations for MANAGE_EXTERNAL_STORAGE on API 33
android.gradle_dependencies = androidx.core:core:1.8.0,androidx.appcompat:appcompat:1.4.2
android.add_compile_options = sourceCompatibility JavaVersion.VERSION_1_8, targetCompatibility JavaVersion.VERSION_1_8
android.add_aars = 

# Request legacy external storage behavior
android.add_xml = true

[buildozer]
log_level = 5
warn_on_root = 1
