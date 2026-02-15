# Tablet Monitor - GitHub Actions Build

## Automatic APK Build Setup

This project is configured to automatically build an APK using GitHub Actions.

### Setup Instructions:

1. **Create a GitHub account** (if you don't have one):
   - Go to https://github.com/signup

2. **Create a new repository**:
   - Click "+" in top right → "New repository"
   - Name: `tablet-monitor`
   - Make it Public or Private (your choice)
   - Don't initialize with README
   - Click "Create repository"

3. **Upload your code to GitHub**:
   
   Open Command Prompt in this folder and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/tablet-monitor.git
   git push -u origin main
   ```
   
   Replace `YOUR_USERNAME` with your GitHub username.

4. **GitHub Actions will automatically build**:
   - Go to your repository on GitHub
   - Click "Actions" tab
   - You'll see the build running
   - Wait 5-10 minutes for build to complete

5. **Download the APK**:
   - Once build is complete (green checkmark)
   - Click on the build
   - Scroll down to "Artifacts"
   - Download `tablet-monitor-apk`
   - Extract the ZIP file
   - You'll find `app-debug.apk` inside

6. **Install on tablet**:
   ```bash
   adb -s HA0YW1UK install app-debug.apk
   ```

### Manual Trigger:
- Go to Actions tab → "Build Android APK" → "Run workflow"

### Every time you make changes:
```bash
git add .
git commit -m "Your changes description"
git push
```
GitHub will automatically rebuild the APK!

## Alternative: Local Build

If you prefer to build locally without GitHub:
1. Install Android Studio
2. Open this folder as a project
3. Click Build → Build APK
