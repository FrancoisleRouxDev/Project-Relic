"""Entry point: `python -m relic`."""

import sys

from rich.console import Console
from rich.markup import escape

from relic.agent import Agent
from relic.cli import run_chat
from relic.config import ConfigError, load_settings
from relic.memory import SQLiteMemoryStore
from relic.persona import PersonaError, load_persona
from relic.providers import OpenAICompatProvider


def main() -> int:
    """Wire settings, persona, memory and provider together and start chatting."""
    console = Console()
    try:
        settings = load_settings()
        persona = load_persona(settings.persona_file, settings.user_name)
    except (ConfigError, PersonaError) as exc:
        console.print(f"[red]{escape(str(exc))}[/red]")
        return 1

    extra_body = None
    if settings.llm_enable_thinking is not None:
        extra_body = {"chat_template_kwargs": {"enable_thinking": settings.llm_enable_thinking}}
    provider = OpenAICompatProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        extra_body=extra_body,
    )
    memory = SQLiteMemoryStore(settings.data_dir / "relic.db")
    agent = Agent(provider, persona, memory, settings.user_name, settings.history_limit)
    try:
        run_chat(agent, console)
    finally:
        memory.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
