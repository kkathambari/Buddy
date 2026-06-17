@echo off
@echo Checking dependencies...
pip install -r requirements.txt >nul 2>&1
pip install pyttsx3 SpeechRecognition pyaudio >nul 2>&1

start pythonw main.py
exit
