[app]
title = Ace Vault
package.name = acevault
package.domain = com.shyapsneon

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json

version = 1.0
# Fixed requirements with compatible versions
requirements = python3,setuptools,kivy==2.1.0,kivymd,pillow,requests,qrcode,imageio,bcrypt,cryptography,mutagen,plyer,android,pyjnius==1.4.2

main = acevault.py

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,WAKE_LOCK,VIBRATE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.entrypoint = org.kivy.android.PythonActivity
android.theme = "@android:style/Theme.NoTitleBar"
android.allow_backup = True
android.release_artifact = apk

# Add these optimization settings
android.arch = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
