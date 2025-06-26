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

# (list) Source code patterns to include - COMPREHENSIVE LIST
# This includes ALL your vault modules and their sub-components
source.include_patterns = assets/*,*.py,*.kv,
    photo_vault.py,photo_vault_core.py,photo_vault_ui.py,
    video_vault.py,video_vault_core.py,video_vault_ui.py,
    document_vault.py,document_vault_core.py,document_vault_ui.py,
    audio_vault_main_ui.py,audio_vault_core.py,audio_vault_ui.py,
    recycle_bin_ui.py,recycle_bin_core.py,
    file_transfer_vault.py,file_transfer_core.py,file_transfer_ui.py,
    vault_secure_integration.py,vault_secure_core.py,
    complete_contact_integration.py,contact_vault_core.py,contact_vault_ui.py,
    game_widget.py,game_core.py,game_ui.py,card_game.py,
    secure_storage.py,storage_core.py,storage_utils.py,
    password_manager.py,password_ui.py,password_core.py,
    vault_utils.py,vault_helpers.py,vault_constants.py,
    encryption_utils.py,file_utils.py,platform_utils.py,
    thumbnail_generator.py,image_processor.py,
    notification_manager.py,permission_handler.py,
    settings_manager.py,config_manager.py,
    backup_manager.py,export_manager.py,
    security_manager.py,crypto_utils.py

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# Added comprehensive requirements for all vault features
requirements = python3,kivy,kivymd,pillow,qrcode,requests,mutagen,imageio,jnius,cryptography,bcrypt,plyer,android

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
# Comprehensive permissions for all vault features
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

# (str) python-for-android whitelist
#android.p4a_whitelist =

# (str) python-for-android blacklist
#android.p4a_blacklist =

# (str) python-for-android bootstrap to use
#android.bootstrap = sdl2

# (list) python-for-android private modules 
#android.private_modules =

# (str) python-for-android url, to use for example a git clone
#android.p4a_url =

# (str) python-for-android branch
#android.p4a_branch =

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
#android.p4a_dir =

# (str) python-for-android fork to use in case if you want to use a fork
#android.p4a_fork = kivy

# (str) The directory in which python-for-android should look for your own build recipes (if any)
#p4a.local_recipes =

# (str) Filename to the hook for p4a
#p4a.hook =

# (str) Bootstrap to use for iOS
#ios.bootstrap = kivy

# (list) Application requirements for iOS
#ios.requirements = python3,kivy

# (str) Custom source folders for iOS
#ios.source_dir =

# (list) List of iOS private modules 
#ios.private_modules =

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 1.9.1

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for new android toolchain)
# Supported formats are: #RRGGBB #AARRGGBB or one of the following names:
# red, blue, green, black, white, gray, cyan, magenta, yellow, lightgray,
# darkgray, grey, lightgrey, darkgrey, aqua, fuchsia, lime, maroon, navy,
# olive, purple, silver, teal.
#android.presplash_color = #FFFFFF

# (string) Presplash animation using Lottie format.
# see https://lottiefiles.com/ for examples and https://airbnb.design/lottie/
# for general documentation.
# Lottie files can be created using various tools, like Adobe After Effect or Synfig.
#android.presplash_lottie = "path/to/lottie/file.json"

# (list) Gradle repositories to use (see https://developer.android.com/studio/build/dependencies#dependency-types)
#android.gradle_repositories = google(), mavenCentral()

# (list) Java classes to add as activities to the manifest.
#android.add_activities = com.example.ExampleActivity

# (str) OUYA Console category. Should be one of GAME or APP
# If you leave this blank, OUYA support will not be enabled
#android.ouya.category = GAME

# (str) Filename of OUYA Console icon. It must be a 732x412 png image.
#android.ouya.icon.filename = %(source.dir)s/data/ouya_icon.png

# (str) XML file to include as an intent filter in your .apk manifest
#android.manifest.intent_filters =

# (str) launchMode to set for the main activity
#android.manifest.launch_mode = standard

# (list) Android additional libraries to copy into libs/armeabi
#android.add_libs_armeabi = libs/android/*.so
#android.add_libs_armeabi_v7a = libs/android-v7/*.so
#android.add_libs_arm64_v8a = libs/android-v8/*.so
#android.add_libs_x86 = libs/android-x86/*.so
#android.add_libs_mips = libs/android-mips/*.so

# (bool) Indicate whether the screen should stay on
# Don't forget to add the WAKE_LOCK permission if you set this to True
#android.wakelock = False

# (list) Android application meta-data to set (key=value format)
#android.meta_data =

# (list) Android library project to add (will be added in the
# project.properties automatically.)
#android.library_references = @jar/my-android-project

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# You can set many archs, for example: android.archs = arm64-v8a,armeabi-v7a
# In past, was `android.arch` as we weren't supporting builds for multiple archs at the same time.
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) XML file for backup rules (Android API >=23)
#android.backup_rules =

# (str) If you need to insert variables into your AndroidManifest.xml file,
# you can do so with the manifestPlaceholders property.
# This property takes a map of key-value pairs. (via a string)
# Usage example : android.manifest_placeholders = [myCustomUrl:\"org.kivy.customurl\"]
# android.manifest_placeholders = [:]

# (bool) Skip byte compile for .py files
# android.no-byte-compile-python = False

# (str) The format used to package the app for release mode (aab or apk or aar).
# android.release_artifact = aab

# (str) The format used to package the app for debug mode (apk or aar).
# android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android URL, to use for example a git clone
#p4a.url =

# (str) python-for-android fork to use in case if you want to use a fork
#p4a.fork = kivy

# (str) python-for-android branch to use
#p4a.branch =

# (str) python-for-android specific commit to use
#p4a.commit =

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
#p4a.source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
#p4a.local_recipes =

# (str) Filename to the hook for p4a
#p4a.hook =

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2

# (int) port number to specify an explicit --port= p4a argument (eg for bootstrap flask)
#p4a.port =

# Control passing the --private data-dir to p4a
# (bool) optional, False by default.
# Don't pass --private to p4a (removes separation between app and device storage)
# android.no_private_storage = False

#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios
# Alternately, specify the URL and branch of a git checkout:
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

# Another platform dependency: ios-deploy
# Uncomment to use a custom checkout
#ios.ios_deploy_dir = ../ios_deploy
# Or specify URL and branch
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0

# (bool) Whether or not to sign the code
ios.codesign.allowed = false

# (str) Name of the certificate to use for signing the debug version
# Get a list of available identities: Xcode > Preferences > Accounts > View Details
ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) The development team to use for signing the debug version
ios.codesign.development_team.debug = <hexstring>

# (str) Name of the certificate to use for signing the release version
ios.codesign.release = %(ios.codesign.debug)s

# (str) The development team to use for signing the release version
ios.codesign.development_team.release = <hexstring>

# (str) URL pointing to a git repository containing a kivy-ios recipe
#ios.recipe_fork = 

# (str) Fork branch to use
#ios.recipe_branch = 

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin
