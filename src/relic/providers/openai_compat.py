"""One provider for any OpenAI-compatible API (NIM, OpenAI, OpenRouter, Ollama...)."""

from typing import Any

import openai
from openai import OpenAI
from tenacity import (
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base

from relic.providers.base import LLMProvider, Message, ProviderError


def _is_retryable(exc: BaseException) -> bool:
    """Retry rate limits (429), 5xx responses and dropped connections."""
    if isinstance(exc, openai.RateLimitError | openai.APIConnectionError):
        return True
    return isinstance(exc, openai.APIStatusError) and exc.status_code >= 500


class OpenAICompatProvider(LLMProvider):
    """Chat via the `openai` client pointed at any compatible `base_url`."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.8,
        max_attempts: int = 5,
        wait: wait_base | None = None,
        client: OpenAI | None = None,
    ) -> None:
        # The SDK's own retries are disabled; tenacity owns the retry policy.
        self._client = client or OpenAI(base_url=base_url, api_key=api_key, max_retries=0)
        self._model = model
        self._temperature = temperature
        self._max_attempts = max_attempts
        self._wait = wait or wait_exponential(multiplier=1, min=1, max=30)

    def chat(self, messages: list[Message]) -> str:
        """Return the model's reply, retrying transient failures with backoff."""
        retrying = Retrying(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(self._max_attempts),
            wait=self._wait,
        )
        try:
            response = retrying(self._request, messages)
        except RetryError as exc:
            raise ProviderError(
                "The model is rate-limited or unavailable right now. Try again in a moment."
            ) from exc.last_attempt.exception()
        except openai.AuthenticationError as exc:
            raise ProviderError("The API rejected your key. Check LLM_API_KEY.") from exc
        except openai.APIError as exc:
            raise ProviderError(f"The LLM request failed: {exc}") from exc
        return (response.choices[0].message.content or "").strip()

    def _request(self, messages: list[Message]) -> Any:
        return self._client.chat.completions.create(
            model=self._model, messages=messages, temperature=self._temperature
        )
