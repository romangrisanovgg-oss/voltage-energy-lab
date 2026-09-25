[app]

title = Voltage Energy Lab
package.name = voltageenergylab
package.domain = org.example

source.dir = .
source.include_exts = py,json,png,jpg,kv,atlas,ttf,otf

version = 1.0.0

requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk_api = 24

android.archs = arm64-v8a

android.accept_sdk_license = True
android.allow_backup = True

android.release_artifact = apk
android.debug_artifact = apk

# Если появится файл иконки, можно раскомментировать:
# icon.filename = %(source.dir)s/icon.png

[buildozer]

log_level = 2
warn_on_root = 1