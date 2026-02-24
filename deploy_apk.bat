@echo off
echo Downloading latest APK from GitHub...
curl -L "https://github.com/MrAbhinavJindal/tablet-monitor/releases/latest/download/app-debug.apk" -o app-debug.apk

if not exist app-debug.apk (
    echo ERROR: Failed to download APK
    pause
    exit /b 1
)

for %%A in (app-debug.apk) do set size=%%~zA
if %size% LSS 10000 (
    echo ERROR: Downloaded file is too small (%size% bytes). Check GitHub release URL.
    pause
    exit /b 1
)

echo Uninstalling old app...
platform-tools\adb.exe uninstall com.tabletmonitor 2>nul

echo Installing new APK...
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