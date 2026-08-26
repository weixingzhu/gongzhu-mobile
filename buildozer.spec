[app]
title = 拱猪
package.name = gongzhu
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 0.1
requirements = python3==3.9.0,kivy,pyjnius,plyer,pillow,pip==23.0.1
icon.filename = icon.png
orientation = landscape
osx.kivy_version = 2.2.0
fullscreen = 1
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.enable_androidx = True
android.used_permissions = INTERNET
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.12.2
ios.codesign.allowed = false
[buildozer]
# 强制使用国内镜像源，屏蔽国外源！
p4a.branch = master
p4a.env = PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
log_level = 2
warn_on_root = 1