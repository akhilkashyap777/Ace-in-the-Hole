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

# (list) Source code patterns to include - EXACTLY YOUR FILES
source.include_patterns = assets/*,*.py,*.kv,main.py,photo_vault.py,photo_vault_core.py,photo_vault_ui.py,video_vault.py,video_vault_core.py,video_vault_ui.py,document_vault.py,document_vault_core.py,document_vault_ui.py,audio_vault_main_ui.py,audio_vault_core.py,recycle_bin_ui.py,recycle_bin_core.py,file_transfer_vault.py,vault_secure_integration.py,secure_storage.py,complete_contact_integration.py,game_widget.py,password_manager.py,password_ui.py,audio_vault_dialogs.py,audio_vault_player.py,audio_vault_stats.py,contact_manager.py,contact_ui_integration.py,document_vault_ui_components.py,monte_game.py,photo_camera_module.py,recycle_bin_dialogs.py,video_camera_module.py,video_vault_core_optimized.py,video_vault_dialogs.py,video_vault_operations.py

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,ACCESS_NETWORK_STATE,WAKE_LOCK,VIBRATE,READ_PHONE_STATE,ACCESS_WIFI_STATE

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

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 1.9.1

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
