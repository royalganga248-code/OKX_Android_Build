[app]
title = OKX Margin Calculator
package.name = okx_calculator
package.domain = org.okx
source.dir = .
source.include_exts = py, png, jpg, txt, kv
version = 1.0.0
requirements = python3, kivy
orientation = portrait
fullscreen = 0

android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.permissions = INTERNET

# указываем путь, где workflow ставит SDK:
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
android.sdk_tools = /home/runner/.buildozer/android/platform/android-sdk/cmdline-tools/latest/bin
