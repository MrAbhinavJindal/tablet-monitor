@rem Gradle startup script for Windows

@if "%DEBUG%" == "" @echo off
set DIRNAME=%~dp0
if "%DIRNAME%" == "" set DIRNAME=.
set APP_BASE_NAME=%~n0
set GRADLE_USER_HOME=%USERPROFILE%\.gradle

"%GRADLE_USER_HOME%\wrapper\dists\gradle-8.0-bin\*\gradle-8.0\bin\gradle.bat" %*
