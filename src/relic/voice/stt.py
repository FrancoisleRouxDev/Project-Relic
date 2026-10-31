"""Microphone capture and speech-to-text (faster-whisper)."""

from collections import deque

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16_000  # Whisper expects 16 kHz mono float32
BLOCK_SECONDS = 0.1


class Microphone:
    """Records one utterance at a time using a simple loudness threshold."""

    def __init__(
        self, threshold: float = 0.015, silence_seconds: float = 0.8, max_seconds: float = 15.0
    ) -> None:
        self.threshold = threshold
        self.silence_seconds = silence_seconds
        self.max_seconds = max_seconds

    def record_utterance(self, wait_seconds: float | None = None) -> np.ndarray | None:
        """Block until speech starts, then return it once silence follows.

        Returns None if `wait_seconds` passes without any speech.
        """
        block = int(SAMPLE_RATE * BLOCK_SECONDS)
        preroll: deque[np.ndarray] = deque(maxlen=3)  # keeps the first syllable
        chunks: list[np.ndarray] = []
        started = False
        waited = silent = 0.0
        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=block
        ) as stream:
            while True:
                data, _ = stream.read(block)
                data = data[:, 0]
                loud = float(np.sqrt(np.mean(data**2))) > self.threshold
                if not started:
                    if loud:
                        started = True
                        chunks = [*preroll, data]
                    else:
                        preroll.append(data)
                        waited += BLOCK_SECONDS
                        if wait_seconds is not None and waited >= wait_seconds:
                            return None
                    continue
                chunks.append(data)
                silent = 0.0 if loud else silent + BLOCK_SECONDS
                if (
                    silent >= self.silence_seconds
                    or len(chunks) * BLOCK_SECONDS >= self.max_seconds
                ):
                    return np.concatenate(chunks)


class Transcriber:
    """Local speech-to-text. The model downloads on first use."""

    def __init__(self, model_size: str = "small.en", prompt: str | None = None) -> None:
        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self._prompt = prompt  # biases Whisper towards words it should expect (the wake phrase)

    def transcribe(self, audio: np.ndarray) -> str:
        if len(audio) < SAMPLE_RATE * 0.4:  # clicks and coughs: skip
            return ""
        segments, _ = self._model.transcribe(
            audio,
            language="en",
            vad_filter=True,
            beam_size=5,
            initial_prompt=self._prompt,
            condition_on_previous_text=False,
        )
        return " ".join(s.text.strip() for s in segments).strip()
