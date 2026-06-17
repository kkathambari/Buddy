import threading

def speak_text(text):
    """
    Text-to-Speech Engine.
    Detects platform (Android vs Desktop) and executes the correct TTS library.
    Runs asynchronously so it doesn't freeze the UI.
    """
    def _speak():
        # Check if we should use Android plyer tts
        use_android = False
        try:
            from plyer import tts
            # If tts is imported, try to use it
            tts.speak(message=text)
            use_android = True
        except Exception:
            pass

        if not use_android:
            # Desktop pyttsx3 implementation
            try:
                import pyttsx3
                engine = pyttsx3.init()
                
                # Try to find a male/ghostly voice
                voices = engine.getProperty('voices')
                for voice in voices:
                    if "david" in voice.name.lower() or "zira" not in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                        
                engine.setProperty('rate', 140) # Slower for a ghost
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"Desktop TTS Failed: {e}")
            
    threading.Thread(target=_speak, daemon=True).start()

def listen_to_voice(callback):
    """
    Speech-to-Text Engine.
    Records from the microphone and passes the transcribed text to the callback.
    For Android, native STT via JNI is experimental without custom Java Activity classes.
    """
    def _listen():
        # Check for Android
        is_android = False
        try:
            # Simple check if running on Kivy on Android
            import kivy
            from jnius import autoclass
            is_android = True
        except ImportError:
            pass

        if is_android:
            # Android STT stub/experimental
            callback(None)
        else:
            # Desktop SpeechRecognition implementation
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                text = recognizer.recognize_google(audio)
                if text:
                    callback(text)
            except Exception as e:
                print(f"STT Failed: {e}")
                callback(None)
            
    threading.Thread(target=_listen, daemon=True).start()
