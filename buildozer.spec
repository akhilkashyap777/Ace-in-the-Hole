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
source.include_exts = py,png,jpg,kv,atlas,wav,mp3

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements - Fixed pygame conflict
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions - Added critical storage permissions for Kivy
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,WRITE_INTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android SDK version to use
android.sdk = 33

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The Android bootstrap to use.
android.bootstrap = sdl2

# Android 13+ compatibility settings
android.enable_androidx = True
android.manifest_placeholders = {'requestLegacyExternalStorage': 'true'}

# Additional permissions for internal storage access
android.add_permissions = android.permission.WRITE_INTERNAL_STORAGE

# Gradle dependencies for modern Android compatibility
android.gradle_dependencies = androidx.core:core:1.7.0

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 1.9.1

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
