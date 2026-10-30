"""Provider interface: anything that can turn chat messages into a reply."""

from abc import ABC, abstractmethod

Message = dict[str, str]  # {"role": "system" | "user" | "assistant", "content": "..."}


class ProviderError(Exception):
    """Raised with a user-presentable message when the LLM call ultimately fails."""


class LLMProvider(ABC):
    """Abstract chat-completion provider."""

    @abstractmethod
    def chat(self, messages: list[Message]) -> str:
        """Send `messages` to the model and return the assistant's reply text."""
