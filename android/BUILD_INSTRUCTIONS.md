# Build Android APK - Step by Step Guide

## Prerequisites
1. Download and install Android Studio from: https://developer.android.com/studio
2. During installation, make sure to install Android SDK

## Step-by-Step Instructions

### 1. Create New Project
1. Open Android Studio
2. Click "New Project"
3. Select "Empty Views Activity"
4. Click "Next"
5. Set:
   - Name: `TabletMonitor`
   - Package name: `com.tabletmonitor`
   - Save location: Choose any folder
   - Language: `Kotlin`
   - Minimum SDK: `API 24 (Android 7.0)`
6. Click "Finish"
7. Wait for Gradle sync to complete (may take 5-10 minutes first time)

### 2. Replace Files

#### Replace MainActivity.kt
1. In Android Studio, navigate to: `app/src/main/java/com/tabletmonitor/MainActivity.kt`
2. Delete all content
3. Copy content from your `android/MainActivity.kt` file
4. Paste into Android Studio

#### Replace activity_main.xml
1. Navigate to: `app/src/main/res/layout/activity_main.xml`
2. Delete all content
3. Copy content from your `android/activity_main.xml` file
4. Paste into Android Studio

#### Update AndroidManifest.xml
1. Navigate to: `app/src/main/manifests/AndroidManifest.xml`
2. Add this line inside `<manifest>` tag (before `<application>`):
   ```xml
   <uses-permission android:name="android.permission.INTERNET" />
   ```

#### Update build.gradle (app level)
1. Navigate to: `app/build.gradle.kts` (or `build.gradle`)
2. Find the `dependencies` section
3. Add these lines if not present:
   ```kotlin
   implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
   implementation("androidx.appcompat:appcompat:1.6.1")
   ```

### 3. Build APK

#### Option A: Build via Android Studio (Easiest)
1. Click "Build" menu → "Build Bundle(s) / APK(s)" → "Build APK(s)"
2. Wait for build to complete (1-3 minutes)
3. Click "locate" in the popup notification
4. APK will be at: `app/build/outputs/apk/debug/app-debug.apk`

#### Option B: Build via Command Line
1. Open Terminal in Android Studio (bottom panel)
2. Run:
   ```bash
   gradlew assembleDebug
   ```
3. APK will be at: `app/build/outputs/apk/debug/app-debug.apk`

### 4. Install APK on Tablet

#### Method 1: Direct Install via USB (Easiest)
1. Enable USB debugging on tablet (Settings → Developer Options)
2. Connect tablet via USB
3. In Android Studio, click the green "Run" button (▶)
4. Select your tablet from the device list
5. App will install and launch automatically

#### Method 2: Install via ADB
1. Connect tablet via USB
2. Open command prompt in the folder containing `app-debug.apk`
3. Run:
   ```bash
   adb -s HA0YW1UK install app-debug.apk
   ```

#### Method 3: Manual Install
1. Copy `app-debug.apk` to tablet (via USB file transfer)
2. On tablet, open file manager
3. Tap the APK file
4. Allow "Install from unknown sources" if prompted
5. Tap "Install"

### 5. Run the App

1. Start the Python server on laptop:
   ```bash
   python server.py
   ```

2. Run ADB reverse:
   ```bash
   adb -s HA0YW1UK reverse tcp:8888 tcp:8888
   ```

3. Launch "TabletMonitor" app on tablet

4. You should see your laptop screen on the tablet!

## Troubleshooting

### Build Errors
- If you get "SDK not found": Go to Tools → SDK Manager → Install latest Android SDK
- If Gradle sync fails: File → Invalidate Caches → Restart

### Connection Issues
- Make sure server is running on laptop
- Verify ADB reverse is active: `adb reverse --list`
- Check tablet is connected: `adb devices`

### App Crashes
- Check Android Studio Logcat (bottom panel) for error messages
- Make sure INTERNET permission is in AndroidManifest.xml
