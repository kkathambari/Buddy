@echo off
cd /d "%~dp0"
echo Resuming Android APK Build...
wsl.exe bash ./resume_build.sh
pause