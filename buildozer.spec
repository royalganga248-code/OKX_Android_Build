[app]
# Основные параметры
title = OKX Calculator
package.name = okx_calculator
package.domain = org.okx
source.dir = .
version = 1.0

# Точка входа
source.main = main.py

# Зависимости
requirements = python3, kivy, requests, pandas

# Иконка (опционально)
# icon.filename = %(source.dir)s/data/icon.png

# Разрешения Android
android.permissions = INTERNET

# Минимальная версия Android SDK
android.minapi = 21
android.sdk = 31
android.ndk = 25b

# Настройки экрана
fullscreen = 0
orientation = portrait

# Архитектуры
android.archs = armeabi-v7a, arm64-v8a

# (Необязательно) Имя выходного apk
# android.filename = OKX_Calculator.apk


[buildozer]
log_level = 2
warn_on_root = 1
