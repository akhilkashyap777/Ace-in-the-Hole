[app]
title = Monte Card App
package.name = montecard
package.domain = com.akhilkast

source.dir = .
source.main = main.py
source.include_exts = py,png,jpg,kv,json
source.include_patterns = *.py,**/*.py
source.exclude_patterns = __pycache__/*,.git*

requirements = python3,kivy,kivymd,pillow,jnius,plyer,android

version = 0.1
orientation = portrait

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a

p4a.bootstrap = sdl2

[buildozer]
log_level = 2
