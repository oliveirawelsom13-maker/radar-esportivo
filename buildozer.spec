[app]

# (str) Title of your application
title = Radar Esportivo

# (str) Package name
package.name = radaresportivo

# (str) Package domain (needed for android/ios packaging)
package.domain = com.welson.radar

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (python files, images, etc.)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 1.0

# (list) Application requirements
requirements = python3,kivy==2.3.0,kivymd==1.2.0,Pillow,cython<3.0.0

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) Permissions
android.permissions = INTERNET,POST_NOTIFICATIONS,VIBRATE

# (int) Target Android API, should be at least 33 for modern devices
android.api = 33

# (int) Minimum API required (Android 5.0+)
android.minapi = 21

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (bool) Allow backup
android.allow_backup = True

# (list) The Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (str) The Bootstrap to use for Android builds
p4a.bootstrap = sdl2

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
