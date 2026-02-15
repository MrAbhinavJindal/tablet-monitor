# Tablet Client Setup (Python)

## On Your Tablet

### Option 1: Pydroid 3 (Android - Easiest)
1. Install "Pydroid 3" from Play Store
2. In Pydroid, install Pillow: Pip → Install → "Pillow"
3. Copy `tablet_client.py` to tablet
4. Run in Pydroid 3

### Option 2: Termux (Android - Advanced)
```bash
pkg install python python-tkinter
pip install pillow
python tablet_client.py
```

### Option 3: Windows Tablet
```bash
pip install pillow
python tablet_client.py
```

## Connection Setup

### For USB (with adb reverse):
- Keep `HOST = 'localhost'` in tablet_client.py
- Run on laptop: `adb reverse tcp:5555 tcp:5555`

### For WiFi:
- Change `HOST = 'localhost'` to your laptop's IP (e.g., `HOST = '192.168.1.100'`)
- Find laptop IP: `ipconfig` on Windows

## Usage

1. Start server on laptop: `python server.py`
2. Run client on tablet: `python tablet_client.py`
3. Press ESC to exit fullscreen

## Transfer tablet_client.py to Tablet

### Method 1: ADB Push
```bash
adb push tablet_client.py /sdcard/Download/
```

### Method 2: USB File Transfer
- Connect tablet via USB
- Copy file to tablet's Download folder

### Method 3: Cloud/Email
- Email file to yourself or use Google Drive
