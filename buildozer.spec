[app]
title = Radar Esportivo
package.name = radaresportivo
package.domain = com.welson.radar
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.1.1,Pillow==9.5.0

orientation = portrait

android.permissions = INTERNET,POST_NOTIFICATIONS,VIBRATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.allow_backup = True
android.archs = arm64-v8a, armeabi-v7a
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
