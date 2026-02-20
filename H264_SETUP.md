# H.264 Streaming Setup

## Prerequisites

1. **Download FFmpeg**:
   - Go to https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
   - Extract to `tablet-monitor/ffmpeg/` folder
   - Final path should be: `tablet-monitor/ffmpeg/bin/ffmpeg.exe`

## Server Setup

1. Use the new H.264 server:
```bash
python server\server_h264.py
```

## Android App Setup

1. Replace `MainActivity.kt` with `MainActivity_h264.kt`:
```bash
copy app\src\main\java\com\tabletmonitor\MainActivity_h264.kt app\src\main\java\com\tabletmonitor\MainActivity.kt
```

2. Replace `activity_main.xml` with `activity_main_h264.xml`:
```bash
copy app\src\main\res\layout\activity_main_h264.xml app\src\main\res\layout\activity_main.xml
```

3. Build and install APK using GitHub Actions or locally

## Expected Performance

- **60 FPS** with H.264 hardware encoding/decoding
- Much lower latency than JPEG
- Better quality at lower bandwidth

## Notes

- H.264 uses two ports: 8888 (video) and 8889 (touch)
- FFmpeg uses ultrafast preset for low latency
- MediaCodec provides hardware H.264 decoding on Android
