@echo off
echo Uninstalling old app...
platform-tools\adb.exe uninstall com.tabletmonitor 2>nul

echo Installing APK...
platform-tools\adb.exe install app-debug.apk
if errorlevel 1 (
    echo ERROR: APK installation failed
    pause
    exit /b 1
)

echo Setting up ADB reverse...
platform-tools\adb.exe reverse tcp:8888 tcp:8888
platform-tools\adb.exe reverse tcp:8889 tcp:8889

echo Launching app...
platform-tools\adb.exe shell am start -n com.tabletmonitor/.MainActivity

echo Done! App deployed and running on tablet.
pause