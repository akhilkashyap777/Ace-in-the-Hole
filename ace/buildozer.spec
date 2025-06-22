[app]
title = Ace Vault
package.name = acevault
package.domain = com.shyapsneon
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0
requirements = python3,setuptools,kivy==2.1.0,kivymd,pillow,requests,qrcode,imageio,bcrypt,cryptography,mutagen,pygame,plyer,android,pyjnius==1.4.2
main = acevault.py
orientation = portrait
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,WAKE_LOCK,VIBRATE
android.api = 31
android.minapi = 21
android.ndk = 23c
android.sdk = 31
android.arch = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
