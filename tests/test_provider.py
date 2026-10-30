from types import SimpleNamespace
from unittest.mock import MagicMock

import openai
import pytest
from tenacity import wait_none

from relic.providers import OpenAICompatProvider, ProviderError

MESSAGES = [{"role": "user", "content": "hi"}]


def _response(status: int) -> MagicMock:
    """Minimal stand-in for the HTTP response the SDK attaches to status errors."""
    return MagicMock(status_code=status, headers={})


def rate_limit() -> openai.RateLimitError:
    return openai.RateLimitError("slow down", response=_response(429), body=None)


def server_error() -> openai.InternalServerError:
    return openai.InternalServerError("boom", response=_response(503), body=None)


def ok(text: str = "pong"):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def make_provider(client: MagicMock, attempts: int = 3) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        base_url="http://test",
        api_key="k",
        model="m",
        temperature=0.5,
        max_attempts=attempts,
        wait=wait_none(),
        client=client,
    )


def test_returns_reply_and_passes_params() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = ok("  pong ")
    assert make_provider(client).chat(MESSAGES) == "pong"
    client.chat.completions.create.assert_called_once_with(
        model="m", messages=MESSAGES, temperature=0.5, extra_body=None
    )


def test_retries_on_429_then_succeeds() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = [rate_limit(), rate_limit(), ok()]
    assert make_provider(client).chat(MESSAGES) == "pong"
    assert client.chat.completions.create.call_count == 3


def test_retries_on_5xx() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = [server_error(), ok()]
    assert make_provider(client).chat(MESSAGES) == "pong"


def test_gives_clean_error_when_retries_exhausted() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = rate_limit()
    with pytest.raises(ProviderError, match="rate-limited"):
        make_provider(client, attempts=3).chat(MESSAGES)
    assert client.chat.completions.create.call_count == 3


def test_does_not_retry_auth_errors() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = openai.AuthenticationError(
        "bad key", response=_response(401), body=None
    )
    with pytest.raises(ProviderError, match="LLM_API_KEY"):
        make_provider(client).chat(MESSAGES)
    assert client.chat.completions.create.call_count == 1


def test_extra_body_is_forwarded() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = ok()
    body = {"chat_template_kwargs": {"enable_thinking": False}}
    provider = OpenAICompatProvider(
        base_url="http://test",
        api_key="k",
        model="m",
        wait=wait_none(),
        client=client,
        extra_body=body,
    )
    provider.chat(MESSAGES)
    assert client.chat.completions.create.call_args.kwargs["extra_body"] == body
