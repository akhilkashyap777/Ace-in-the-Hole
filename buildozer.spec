[app]
title = Monte Card App
package.name = montecard
package.domain = com.akhilkast
source.dir = .
source.main = main.py
# Explicitly include all supported source types
source.include_exts = py,pyc,pyo,png,jpg,jpeg,gif,bmp,webp,tiff,kv,atlas,wav,mp3,mp4,avi,mov,mkv,txt,json
source.include_patterns = modules/secure_storage.py,modules/*,password_manager.py,password_ui.py,game_widget.py,vault_secure_integration.py,document_vault.py,complete_contact_integration.py,audio_vault_main_ui.py,photo_vault.py,video_vault.py,recycle_bin_ui.py,file_transfer_vault.py
# FIXED: Added Python stdlib test exclusions to prevent Unicode errors
source.exclude_patterns = spec/*,__pycache__/*,.git*,.github/*
# Requirements: keep your versions as they are
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android,cython
version = 0.1
orientation = portrait
fullscreen = 0
android.accept_sdk_license = True
android.skip_update = False
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
p4a.bootstrap = sdl2
[buildozer]
log_level = 2
warn_on_root = 1
