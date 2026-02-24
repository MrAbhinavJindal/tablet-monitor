@echo off
echo Adding changes to git...
git add .

echo Committing changes...
git commit -m "Update H.264 streaming - %date% %time%"

echo Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo ERROR: Git push failed
    pause
    exit /b 1
)

echo Changes pushed! GitHub Actions will build the APK.
echo Check: https://github.com/MrAbhinavJindal/tablet-monitor/actions
pause