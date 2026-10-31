import pytest

from relic.voice.text import clean_for_speech, extract_command


@pytest.mark.parametrize(
    ("heard", "expected"),
    [
        ("Hey Relic, how's it going?", "how's it going?"),
        ("Hey Relic.", ""),
        ("hey relick what time is it", "what time is it"),
        ("Hey Ralik. Have you seen David?", "Have you seen David?"),
        ("Okay so I was thinking", None),
        ("", None),
    ],
)
def test_extract_command(heard: str, expected: str | None) -> None:
    assert extract_command(heard, "hey relic") == expected


def test_clean_for_speech_strips_actions_and_markdown() -> None:
    raw = "*tilts head*  You `rock`.\n\n# Done_"
    assert clean_for_speech(raw) == "You rock. Done"
