[app]
title = Radar Esportivo
package.name = radaresportivo
package.domain = org.radar.esportivo
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy==2.3.0,kivymd==1.2.0,Pillow==9.5.0,cython==0.29.33
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,POST_NOTIFICATIONS,VIBRATE
android.api = 33
android.minapi = 21
android.accept_sdk_license_agreement = True
android.allow_backup = True
android.archs = arm64-v8a
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
