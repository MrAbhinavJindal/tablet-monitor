@echo off
echo Uninstalling old version...
platform-tools\adb uninstall com.tabletmonitor
echo.
echo Installing/Updating Tablet Monitor APK...
platform-tools\adb install app-debug.apk
echo.
echo Done! App installed/updated.
pause
