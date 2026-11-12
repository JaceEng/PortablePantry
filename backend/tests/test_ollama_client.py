"""OllamaClient tests with a fake Ollama server, so no model is needed."""
import json
from typing import Any, List

import pytest
import requests

from services import ollamaClient
from services.ollamaClient import OllamaClient, OllamaError

RECIPE = {"title": "Egg Fried Rice", "description": "Quick.", "foodCategory": "Stir-fry", "servings": 2,
          "calories": 450, "difficulty": 1, "spiceLevel": 1,
          "ingredients": [{"name": "Eggs", "quantity": 2, "unit": ""}],
          "steps": [{"stepNumber": 1, "instructionText": "Fry everything."}]}


class FakeStream:
    def __init__(self, lines: List[bytes]) -> None:
        self._lines = lines

    def __enter__(self) -> "FakeStream":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def raise_for_status(self) -> None:
        pass

    def iter_lines(self):
        return iter(self._lines)


def stream_of(text: str, size: int = 7) -> List[bytes]:
    """Split text into Ollama-style streamed chunks."""
    chunks = [json.dumps({"message": {"content": text[i:i + size]}, "done": False}).encode()
              for i in range(0, len(text), size)]
    return chunks + [b"", json.dumps({"message": {"content": ""}, "done": True}).encode()]


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> List[dict]:
    seen: List[dict] = []
    replies = [stream_of(json.dumps({"recipes": [RECIPE]}))]

    def fake_post(url: str, json: dict, stream: bool, timeout: Any) -> FakeStream:
        seen.append({"url": url, "payload": json, "stream": stream, "timeout": timeout})
        return FakeStream(replies.pop(0) if len(replies) > 1 else replies[0])

    monkeypatch.setattr(ollamaClient.requests, "post", fake_post)
    seen.append({"replies": replies})
    return seen


def test_joins_streamed_pieces_into_recipes(calls: List[dict]) -> None:
    recipes = OllamaClient(base_url="http://fake", model="m", num_recipes=1).generate({"ingredients": ["eggs"]})
    assert recipes[0]["title"] == "Egg Fried Rice" and recipes[0]["foodCategory"] == "Stir-fry"
    assert recipes[0]["id"]
    request = calls[1]
    assert request["stream"] is True and request["payload"]["stream"] is True
    assert request["payload"]["keep_alive"] == OllamaClient.KEEP_ALIVE
    assert request["timeout"] == (OllamaClient.CONNECT_TIMEOUT, OllamaClient.READ_TIMEOUT)


def test_schema_has_no_removed_fields() -> None:
    fields = ollamaClient.RecipeOut.model_json_schema(by_alias=True)["properties"]
    for removed in ["prepTime", "cookTime", "cuisine", "mealType", "cookMethod", "flavor"]:
        assert removed not in fields


def test_empty_steps_are_retried(calls: List[dict]) -> None:
    bad = dict(RECIPE, steps=[])
    calls[0]["replies"].insert(0, stream_of(json.dumps({"recipes": [bad]})))
    recipes = OllamaClient(base_url="http://fake", model="m").generate({"ingredients": ["eggs"]})
    assert len(calls) == 3 and recipes[0]["steps"]  # one bad reply, one good one


def test_stalled_stream_gives_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def stall(*args: Any, **kwargs: Any) -> None:
        raise requests.exceptions.ReadTimeout()

    monkeypatch.setattr(ollamaClient.requests, "post", stall)
    with pytest.raises(OllamaError, match="stopped responding"):
        OllamaClient(base_url="http://fake", model="m").generate({"ingredients": ["eggs"]})


def test_error_line_from_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ollamaClient.requests, "post",
                        lambda *a, **k: FakeStream([json.dumps({"error": "model not found"}).encode()]))
    with pytest.raises(OllamaError, match="model not found"):
        OllamaClient(base_url="http://fake", model="m").generate({"ingredients": ["eggs"]})
