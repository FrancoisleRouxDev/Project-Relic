"""Rich-based terminal chat loop."""

from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm
from rich.text import Text

from relic.agent import Agent
from relic.providers import ProviderError

HELP = """\
[bold]Commands[/bold]
  /help             show this help
  /remember <fact>  save a long-term fact
  /facts            list saved facts
  /forget <id>      delete a fact
  /reset            clear conversation history (facts are kept)
  /exit             quit (Ctrl+C works too)"""


def handle_command(line: str, agent: Agent, console: Console) -> bool:
    """Run a slash command. Returns False when the app should exit."""
    command, _, arg = line.partition(" ")
    arg = arg.strip()
    memory = agent.memory

    if command == "/exit":
        return False
    if command == "/help":
        console.print(HELP)
    elif command == "/remember":
        if not arg:
            console.print("[yellow]Usage: /remember <fact>[/yellow]")
        else:
            fact = memory.add_fact(arg)
            console.print(f"[green]Saved fact #{fact.id}.[/green]")
    elif command == "/facts":
        facts = memory.list_facts()
        if not facts:
            console.print("[dim]No facts saved yet. Use /remember <fact>.[/dim]")
        for fact in facts:
            console.print(f"[cyan]#{fact.id}[/cyan] {escape(fact.content)}")
    elif command == "/forget":
        if not arg.isdigit():
            console.print("[yellow]Usage: /forget <id>[/yellow]")
        elif memory.delete_fact(int(arg)):
            console.print(f"[green]Forgot fact #{arg}.[/green]")
        else:
            console.print(f"[yellow]No fact with id {arg}.[/yellow]")
    elif command == "/reset":
        if Confirm.ask("Clear all conversation history?", default=False, console=console):
            memory.clear_history()
            console.print("[green]History cleared.[/green]")
    else:
        console.print(f"[yellow]Unknown command {escape(command)}. Try /help.[/yellow]")
    return True


def run_chat(agent: Agent, console: Console | None = None) -> None:
    """Interactive chat loop. Exits on /exit, EOF or Ctrl+C."""
    console = console or Console()
    name = agent.persona.name
    if agent.persona.greeting:
        console.print(
            f"[bold magenta]{escape(name)}[/bold magenta]: {escape(agent.persona.greeting)}"
        )
    console.print("[dim]Type /help for commands.[/dim]")

    try:
        while True:
            line = console.input(f"[bold cyan]{escape(agent.user_name)}[/bold cyan] > ").strip()
            if not line:
                continue
            if line.startswith("/"):
                if not handle_command(line, agent, console):
                    break
                continue
            try:
                with console.status(f"[magenta]{escape(name)} is thinking...[/magenta]"):
                    reply = agent.respond(line)
            except ProviderError as exc:
                console.print(f"[red]{escape(str(exc))}[/red]")
                continue
            console.print(Text.assemble((f"{name}: ", "bold magenta"), reply))
    except (KeyboardInterrupt, EOFError):
        console.print()
    console.print("[dim]Link closed.[/dim]")
