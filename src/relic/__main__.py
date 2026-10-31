"""Entry point: `python -m relic`."""

import argparse
import sys

from rich.console import Console
from rich.markup import escape

from relic.agent import Agent
from relic.cli import run_chat
from relic.config import ConfigError, Settings, load_settings
from relic.memory import SQLiteMemoryStore
from relic.persona import PersonaError, load_persona
from relic.providers import OpenAICompatProvider


def _run_voice(agent: Agent, settings: Settings, console: Console) -> None:
    """Imported lazily so text mode works without the voice extras installed."""
    if settings.piper_model is None:
        console.print("[red]Set PIPER_MODEL to a Piper voice .onnx file to use --voice.[/red]")
        return
    from relic.voice.loop import run_voice
    from relic.voice.stt import Microphone, Transcriber
    from relic.voice.text import VOICE_STYLE
    from relic.voice.tts import PiperSpeaker

    agent.style_note = VOICE_STYLE
    wake = settings.wake_phrase or f"hey {agent.persona.name.lower()}"
    run_voice(
        agent,
        console,
        Microphone(settings.mic_threshold),
        Transcriber(settings.whisper_model, prompt=f"{wake.title()}."),
        PiperSpeaker(settings.piper_model),
        wake,
    )


def main() -> int:
    """Wire settings, persona, memory and provider together and start chatting."""
    parser = argparse.ArgumentParser(prog="relic")
    parser.add_argument("--voice", action="store_true", help="talk by voice instead of typing")
    args = parser.parse_args()

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
        if args.voice:
            _run_voice(agent, settings, console)
        else:
            run_chat(agent, console)
    finally:
        memory.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
