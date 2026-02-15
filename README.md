# Tablet as Secondary Touch Monitor

## Setup Instructions

### Laptop Server Setup (Windows)

1. Install Python dependencies:
```bash
cd tablet-monitor\server
pip install -r requirements.txt
```

2. Find your laptop's IP address:
```bash
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

3. Run the server:
```bash
python server.py
```

### Android App Setup

1. Install Android Studio
2. Create a new project and copy files:
   - MainActivity.kt → app/src/main/java/com/tabletmonitor/
   - activity_main.xml → app/src/main/res/layout/
   - AndroidManifest.xml → app/src/main/
   - build.gradle → app/

3. Update MainActivity.kt line 22 with your laptop's IP address

4. Build and install APK on tablet via USB:
```bash
adb install app-debug.apk
```

### USB Connection via ADB

1. Enable USB debugging on tablet (Settings → Developer Options)
2. Connect tablet via USB
3. Run on laptop:
```bash
adb reverse tcp:5555 tcp:5555
```

4. Update MainActivity.kt to use "localhost" instead of IP:
```kotlin
socket = Socket("localhost", 5555)
```

## Usage

1. Start server on laptop
2. Launch app on tablet
3. Tablet will display laptop screen
4. Touch tablet screen to click on laptop

## Notes

- Screen updates at ~10 FPS
- Touch coordinates are mapped to laptop screen
- Works over WiFi or USB (with ADB reverse)
