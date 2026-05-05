import tempfile
from pathlib import Path


class VoiceRecognitionError(RuntimeError):
    pass


class VoiceTranscriber:
    def __init__(self, language="ru-RU"):
        self.language = language

    def transcribe_upload(self, uploaded_file, language=None):
        try:
            import speech_recognition as sr
        except ImportError as exc:
            raise VoiceRecognitionError(
                "Install SpeechRecognition to enable voice transcription."
            ) from exc

        suffix = Path(uploaded_file.name or "voice.wav").suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_path = Path(tmp_file.name)

        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(str(tmp_path)) as source:
                audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data, language=language or self.language)
        except sr.UnknownValueError as exc:
            raise VoiceRecognitionError("Could not recognize speech in the uploaded audio.") from exc
        except sr.RequestError as exc:
            raise VoiceRecognitionError(f"Speech recognition service error: {exc}") from exc
        finally:
            tmp_path.unlink(missing_ok=True)

