"""Pure text helpers for voice mode (no audio or model dependencies)."""

import re
from difflib import SequenceMatcher

VOICE_STYLE = (
    "You are being spoken aloud right now. Reply in one to three short sentences, "
    "plain spoken language, and no stage directions or text between asterisks."
)


def clean_for_speech(text: str) -> str:
    """Strip markdown and *stage directions* that sound wrong when read aloud."""
    text = re.sub(r"\*[^*]*\*", "", text)
    text = re.sub(r"[`_#>]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_command(heard: str, wake_phrase: str) -> str | None:
    """Return the text after the wake phrase ('' if none), or None if it wasn't said.

    Fuzzy match, because Whisper may hear "Hey, Relick." for "hey relic".
    """
    words = heard.split()
    norm = [re.sub(r"\W", "", w.lower()) for w in words]
    wake = wake_phrase.lower().split()
    n = len(wake)
    for i in range(len(norm) - n + 1):
        window = " ".join(norm[i : i + n])
        if SequenceMatcher(None, window, " ".join(wake)).ratio() >= 0.7:
            return " ".join(words[i + n :])
    return None
