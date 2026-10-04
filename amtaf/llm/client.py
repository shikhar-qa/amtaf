"""Provider-agnostic LLM interface with schema-enforced output.

Everything that needs a model decision goes through ``LLMClient.structured``,
so swapping providers is an environment change (``LLM_PROVIDER``/``LLM_MODEL``).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
RECORDINGS_DIR = Path(__file__).resolve().parents[2] / "recordings"


class LLMClient(Protocol):
    def structured(self, prompt: str, schema: type[T], *, key: str) -> T:
        """Return an instance of ``schema``; ``key`` names the call site."""


class RecordedClient:
    """Replays canned responses from ``recordings/<key>.json`` (offline demo)."""

    def __init__(self, directory: Path = RECORDINGS_DIR) -> None:
        self.directory = directory

    def structured(self, prompt: str, schema: type[T], *, key: str) -> T:
        path = self.directory / f"{key}.json"
        if not path.exists():
            raise FileNotFoundError(f"No recorded response for key '{key}'")
        return schema.model_validate_json(path.read_text())


class LiteLLMClient:
    """Real provider via LiteLLM. Output is validated, with one retry."""

    def __init__(self, model: str, retries: int = 1) -> None:
        self.model = model
        self.retries = retries

    def structured(self, prompt: str, schema: type[T], *, key: str) -> T:
        import litellm  # imported lazily so offline mode needs no extra deps

        system = (
            "Reply with ONLY a JSON object matching this JSON Schema:\n"
            + json.dumps(schema.model_json_schema())
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        last_error: ValidationError | None = None
        for _ in range(self.retries + 1):
            response = litellm.completion(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            try:
                return schema.model_validate_json(content)
            except ValidationError as exc:
                last_error = exc
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {"role": "user", "content": f"Invalid output, fix it: {exc}"}
                )
        assert last_error is not None
        raise last_error


def get_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "recorded").lower()
    if provider == "recorded":
        return RecordedClient()
    model = os.getenv("LLM_MODEL")
    if not model:
        raise RuntimeError("Set LLM_MODEL (a LiteLLM model string) for real providers")
    return LiteLLMClient(model)
