[app]
# (str) Title of your application
title = Monte Card App

# (str) Package name
package.name = montecard

# (str) Package domain (needed for android/ios packaging)
package.domain = com.akhilkast

# (str) Source code where the main.py live
source.dir = .

# (list) Source code where the main.py live
source.include_exts = py,png,jpg,jpeg,gif,bmp,webp,tiff,kv,atlas,wav,mp3,mp4,avi,mov,mkv,txt,json

# (list) Source code patterns to include - ALL YOUR EXISTING FILES
source.include_patterns = assets/*,*.py,*.kv

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO

# (int) Target Android API
android.api = 33

# (int) Minimum API
android.minapi = 21

# (str) Android NDK version
android.ndk = 25b

# (int) Android SDK version
android.sdk = 33

# (str) Android arch
android.archs = arm64-v8a,armeabi-v7a

# (bool) enables Android auto backup
android.allow_backup = True

# (str) Android bootstrap
android.bootstrap = sdl2

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 1.9.1

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
