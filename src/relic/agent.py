"""Agent: assembles the prompt (persona + facts + history) and calls the provider."""

import uuid

from relic.memory import MemoryStore
from relic.persona import Persona
from relic.providers import LLMProvider, Message


class Agent:
    """Ties persona, memory and provider together for one chat session."""

    def __init__(
        self,
        provider: LLMProvider,
        persona: Persona,
        memory: MemoryStore,
        user_name: str,
        history_limit: int = 20,
    ) -> None:
        self.provider = provider
        self.persona = persona
        self.memory = memory
        self.user_name = user_name
        self.history_limit = history_limit
        self.session_id = uuid.uuid4().hex
        self.style_note: str | None = None  # extra, mode-specific instructions (e.g. voice)

    def system_prompt(self) -> str:
        """Persona prompt, then saved facts (if any), then the style note (if any)."""
        prompt = self.persona.system_prompt
        facts = self.memory.list_facts()
        if facts:
            lines = "\n".join(f"- {fact.content}" for fact in facts)
            prompt += f"\n\n## Things you know about {self.user_name}\n{lines}"
        if self.style_note:
            prompt += f"\n\n## Output style\n{self.style_note}"
        return prompt

    def build_messages(self) -> list[Message]:
        """System prompt first, then the most recent history, oldest to newest."""
        history = self.memory.recent_messages(self.history_limit)
        return [
            {"role": "system", "content": self.system_prompt()},
            *({"role": m.role, "content": m.content} for m in history),
        ]

    def respond(self, user_text: str) -> str:
        """Record the user's message, get a reply and record it too.

        If the provider fails, the user message is left in history and the
        error propagates so the caller can show it.
        """
        self.memory.add_message("user", user_text, self.session_id)
        reply = self.provider.chat(self.build_messages())
        self.memory.add_message("assistant", reply, self.session_id)
        return reply
