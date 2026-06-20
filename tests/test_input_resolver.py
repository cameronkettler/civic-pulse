import asyncio

import httpx
import pytest

from packages.agents.bill_lookup.input_resolver import BillInputResolutionError, BillInputResolver
from packages.shared.config import Settings


class _FakeAsyncClient:
    last_request: dict | None = None

    def __init__(self, **_: object) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def post(self, url: str, **kwargs: object) -> httpx.Response:
        self.__class__.last_request = {"url": url, **kwargs}
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": (
                                    '{"bill_id":"hr-22-119",'
                                    '"confidence":"high",'
                                    '"explanation":"Matched the SAVE Act."}'
                                ),
                            }
                        ]
                    }
                ]
            },
        )


def test_input_resolver_normalizes_bill_identifiers_without_openai():
    settings = Settings(openai_api_live=False)

    result = asyncio.run(BillInputResolver(settings).resolve("H.R. 22"))

    assert result.bill_id == "hr-22-119"
    assert result.confidence == "medium"


def test_input_resolver_rejects_natural_language_when_resolver_is_disabled():
    settings = Settings(openai_api_live=False)

    with pytest.raises(BillInputResolutionError):
        asyncio.run(BillInputResolver(settings).resolve("National Defense Authorization Act"))


def test_input_resolver_uses_openai_for_natural_language(monkeypatch):
    _FakeAsyncClient.last_request = None
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    settings = Settings(
        openai_api_key="test-key",
        openai_api_live=True,
        openai_model="gpt-5.4-mini",
    )

    result = asyncio.run(BillInputResolver(settings).resolve("SAVE Act"))

    assert result.bill_id == "hr-22-119"
    assert result.confidence == "high"
    assert _FakeAsyncClient.last_request is not None
    assert _FakeAsyncClient.last_request["headers"]["Authorization"] == "Bearer test-key"
