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

1. Download APK from GitHub Actions (Actions tab → latest build → Artifacts)
2. Connect tablet via USB
3. Install/Update APK:
```bash
install_apk.bat
```
Or manually:
```bash
adb install -r app-debug.apk
```

Note: Use `-r` flag to reinstall without uninstalling previous version

### USB Connection via ADB

1. Enable USB debugging on tablet (Settings → Developer Options)
2. Connect tablet via USB
3. Server automatically sets up ADB reverse and launches app

## Usage

1. Connect tablet via USB
2. Start server on laptop: `python server\server.py`
3. App launches automatically on tablet
4. Touch/drag on tablet to control laptop

## Features

- Drag support for drawing in Paint and other apps
- Screen stays on while app is running
- Auto-reconnect on USB disconnect/reconnect
- Auto-launch app when server starts
- Touch coordinates mapped to actual screen resolution

## Notes

- Screen updates at ~10 FPS
- Touch coordinates mapped to actual laptop screen resolution
- Works via USB with ADB reverse (localhost connection)
- Supports drag gestures for drawing
- Tested on Lenovo TB-X605L (1920x1200)
