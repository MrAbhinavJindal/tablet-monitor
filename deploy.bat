@echo off
echo Committing and pushing changes to GitHub...
cd /d "c:\Users\abhinav.jindal\PycharmProjects\PythonProject\tablet-monitor"
git add .
git commit -m "Merged clock app, optimized with OpenCV, removed client folder"
git push origin main
echo.
echo Done! Check GitHub Actions tab for build status.
pause
