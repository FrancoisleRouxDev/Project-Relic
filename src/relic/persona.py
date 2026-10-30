"""Persona loading: the character lives in YAML, never in code."""

from dataclasses import dataclass
from pathlib import Path

import yaml


class PersonaError(Exception):
    """Raised when a persona file is missing or malformed."""


@dataclass(frozen=True)
class Persona:
    """A character: display name, rendered system prompt and optional greeting."""

    name: str
    system_prompt: str
    greeting: str | None = None


def _render(text: str, user_name: str) -> str:
    """Substitute `{user_name}`. Plain replace so other braces are left alone."""
    return text.replace("{user_name}", user_name)


def load_persona(path: Path, user_name: str) -> Persona:
    """Load a persona YAML file and fill in template variables."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PersonaError(f"Persona file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise PersonaError(f"Persona file is not valid YAML: {path}") from exc
    if not isinstance(data, dict) or not data.get("name") or not data.get("system_prompt"):
        raise PersonaError(f"Persona file needs 'name' and 'system_prompt': {path}")
    greeting = data.get("greeting")
    return Persona(
        name=str(data["name"]),
        system_prompt=_render(str(data["system_prompt"]).strip(), user_name),
        greeting=_render(str(greeting), user_name) if greeting else None,
    )
