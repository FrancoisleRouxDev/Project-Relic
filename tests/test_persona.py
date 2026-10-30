from pathlib import Path

import pytest

from relic.persona import PersonaError, load_persona

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_substitutes_user_name(tmp_path: Path) -> None:
    f = tmp_path / "p.yaml"
    f.write_text(
        "name: Bot\ngreeting: 'Hi {user_name}'\n"
        "system_prompt: |\n  Serve {user_name} and {user_name}.\n"
    )
    p = load_persona(f, "Sam")
    assert p.name == "Bot"
    assert p.system_prompt == "Serve Sam and Sam."
    assert p.greeting == "Hi Sam"


def test_greeting_is_optional(tmp_path: Path) -> None:
    f = tmp_path / "p.yaml"
    f.write_text("name: Bot\nsystem_prompt: hello\n")
    assert load_persona(f, "Sam").greeting is None


def test_missing_file_and_missing_fields(tmp_path: Path) -> None:
    with pytest.raises(PersonaError, match="not found"):
        load_persona(tmp_path / "nope.yaml", "Sam")
    f = tmp_path / "bad.yaml"
    f.write_text("name: Bot\n")
    with pytest.raises(PersonaError, match="system_prompt"):
        load_persona(f, "Sam")


def test_bundled_relic_persona_loads() -> None:
    p = load_persona(REPO_ROOT / "personas" / "relic.yaml", "Sam")
    assert p.name == "Relic"
    assert "{user_name}" not in p.system_prompt
    assert "Sam's machine" in p.system_prompt
    assert p.greeting
