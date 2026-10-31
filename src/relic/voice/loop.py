"""Voice chat loop: wait for the wake phrase, then talk."""

from rich.console import Console
from rich.markup import escape

from relic.agent import Agent
from relic.providers import ProviderError
from relic.voice.stt import Microphone, Transcriber
from relic.voice.text import extract_command
from relic.voice.tts import PiperSpeaker, beep


def run_voice(
    agent: Agent,
    console: Console,
    mic: Microphone,
    stt: Transcriber,
    speaker: PiperSpeaker,
    wake_phrase: str,
) -> None:
    """Listen forever; answer out loud when the wake phrase is heard. Ctrl+C exits."""
    name = agent.persona.name
    console.print(f"[dim]Say '{escape(wake_phrase)}' to talk. Ctrl+C to quit.[/dim]")
    try:
        if agent.persona.greeting:
            speaker.speak(agent.persona.greeting)
        while True:
            audio = mic.record_utterance()
            heard = stt.transcribe(audio) if audio is not None else ""
            if heard:
                console.print(f"[dim]heard: {escape(heard)}[/dim]")
            command = extract_command(heard, wake_phrase) if heard else None
            if command is None:
                continue
            if not command:  # wake phrase alone: beep, then take the next utterance
                beep()
                audio = mic.record_utterance(wait_seconds=6)
                command = stt.transcribe(audio) if audio is not None else ""
                if not command:
                    continue
            console.print(f"[bold cyan]{escape(agent.user_name)}[/bold cyan] > {escape(command)}")
            try:
                with console.status(f"[magenta]{escape(name)} is thinking...[/magenta]"):
                    reply = agent.respond(command)
            except ProviderError as exc:
                console.print(f"[red]{escape(str(exc))}[/red]")
                continue
            console.print(f"[bold magenta]{escape(name)}[/bold magenta]: {escape(reply)}")
            speaker.speak(reply)
    except KeyboardInterrupt:
        console.print("\n[dim]Link closed.[/dim]")
