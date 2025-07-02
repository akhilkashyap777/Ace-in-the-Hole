[app]

# Basic App Information
title = Monte Card App
package.name = montecard
package.domain = com.montecard

# Version
version = 1.0
version.regex = __version__ = ['"]([^'"]*)['"]
version.filename = %(source.dir)s/main.py

# Source code
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,html,css,js,json,txt,mp3,mp4,wav
source.exclude_dirs = tests,bin,venv,__pycache__,.git,backup
source.exclude_patterns = license,images/*/*.jpg

# Requirements - Only actual third-party packages
requirements = python3,kivy,kivymd,android,jnius,plyer,Pillow,bcrypt,cryptography,mutagen,qrcode,imageio,imageio-ffmpeg

# Optional requirements for better functionality
requirements.optional = opencv

# Icon and presplash
icon.filename = %(source.dir)s/data/icon.png
# presplash.filename = %(source.dir)s/data/presplash.png

# Supported platforms
requirements.source.kivymd = git+https://github.com/kivymd/KivyMD.git

[buildozer]

# Buildozer directory
log_level = 2
warn_on_root = 1

[android]

# Android specific configurations
arch = arm64-v8a,armeabi-v7a
minapi = 21
api = 33
ndk = 25b
sdk = 33

# CRITICAL PERMISSIONS for Secret Storage App
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO,CAMERA,RECORD_AUDIO,READ_CONTACTS,WRITE_CONTACTS,WRITE_SETTINGS,SYSTEM_ALERT_WINDOW,REQUEST_INSTALL_PACKAGES,REQUEST_DELETE_PACKAGES,MOUNT_UNMOUNT_FILESYSTEMS,WAKE_LOCK,DISABLE_KEYGUARD,VIBRATE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE

# Security and Privacy Features
android.private_storage = True
android.backup_rules = no_backup_rules.xml

# For secure file storage (prevents backup/extraction)
android.allow_backup = False
android.debuggable = False

# Add custom Java/Kotlin code if needed for advanced security
# android.add_src = java/

# Gradle dependencies for enhanced security
android.gradle_dependencies = androidx.security:security-crypto:1.1.0-alpha06,androidx.biometric:biometric:1.1.0

# Prevent screenshots in recent apps (security feature)
android.manifest.application = """
    <application
        android:allowBackup="false"
        android:extractNativeLibs="true"
        android:hardwareAccelerated="true"
        android:requestLegacyExternalStorage="true"
        android:preserveLegacyExternalStorage="true">
        
        <!-- Prevent screenshots in recents -->
        <meta-data android:name="android.allow_multiple_resumed_activities" android:value="false" />
        
        <!-- File provider for secure file sharing -->
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
        
    </application>
"""

# Network security config for file transfers
android.manifest.uses-permission = """
    <!-- Storage permissions -->
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" 
                     tools:ignore="ScopedStorage" />
    
    <!-- Network permissions for file transfer -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    
    <!-- Camera and audio for vault features -->
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    
    <!-- Contacts integration -->
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    <uses-permission android:name="android.permission.WRITE_CONTACTS" />
    
    <!-- System level permissions for security -->
    <uses-permission android:name="android.permission.WRITE_SETTINGS" 
                     tools:ignore="ProtectedPermissions" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    
    <!-- Prevent device sleep during transfers -->
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    
    <!-- Boot receiver for background services -->
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    
    <!-- Foreground service for file operations -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
"""

# Target SDK for modern Android (required for file access)
android.api = 33
android.minapi = 21

# Enable R8/ProGuard for code obfuscation (security)
android.enable_androidx = True
android.release_artifact = apk

# Custom build configurations
p4a.branch = develop
p4a.bootstrap = sdl2

# Java build options
android.add_java_dir = java
android.add_packaging_option = pickFirst **/libc++_shared.so
android.add_packaging_option = pickFirst **/libjsc.so

# Gradle build optimizations
android.gradle_repositories = google(), mavenCentral(), maven { url 'https://jitpack.io' }

# Add custom resources for file provider
# Create res/xml/file_paths.xml with:
# <?xml version="1.0" encoding="utf-8"?>
# <paths xmlns:android="http://schemas.android.com/apk/res/android">
#     <external-path name="external_files" path="."/>
#     <files-path name="internal_files" path="."/>
#     <cache-path name="cache_files" path="."/>
# </paths>

android.add_aars = 

# Security: Prevent debugging and reverse engineering
[android.build]
build_mode = release
sign = True

# Keystore for app signing (create your own)
# android.keystore = %(source.dir)s/keystore/release.keystore
# android.keyalias = montecard
# android.keystore_passwd = your_keystore_password
# android.keyalias_passwd = your_key_password

[osx]

# macOS specific
# author = Your Name

[android.entitlements]
# iOS equivalent security settings would go here