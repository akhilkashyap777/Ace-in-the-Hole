[app]
title = Ace Vault
package.name = acevault
package.domain = com.shyapsneon
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0

# Use crystax workaround to avoid hostpython3 version conflicts
requirements = python3,kivy,kivymd,pillow,requests,qrcode,pygame,bcrypt,plyer,android,pyjnius,cryptography,httplib2
main = main.py
orientation = portrait

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,VIBRATE

# Use versions required by current p4a
android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 31

android.arch = arm64-v8a
android.accept_sdk_license = True

# Add gradle and build optimizations
android.gradle_dependencies = 
android.add_jars = 
android.add_aars = 

# Increase build timeout and memory
android.ant_path = 
p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
android.python_version = 3.13
log_level = 2
warn_on_root = 1