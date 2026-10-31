"""Text-to-speech via the Piper CLI."""

import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from relic.voice.text import clean_for_speech


def beep() -> None:
    """Short tone meaning 'I'm listening'."""
    t = np.linspace(0, 0.12, int(16_000 * 0.12), endpoint=False)
    sd.play((0.2 * np.sin(2 * np.pi * 880 * t)).astype("float32"), 16_000)
    sd.wait()


class PiperSpeaker:
    """Speaks text aloud and blocks until playback ends (so the mic never hears it)."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path

    def speak(self, text: str) -> None:
        text = clean_for_speech(text)
        if not text:
            return
        with tempfile.TemporaryDirectory() as tmp:
            wav_path = Path(tmp) / "reply.wav"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "piper",
                    "--model",
                    str(self.model_path),
                    "--output_file",
                    str(wav_path),
                ],
                input=text.encode(),
                check=True,
                capture_output=True,
            )
            with wave.open(str(wav_path)) as wav:
                rate = wav.getframerate()
                audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
        sd.play(audio, rate)
        sd.wait()
