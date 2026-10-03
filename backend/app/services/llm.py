"""
Thin wrapper around an OpenAI-compatible client. Kept in one place so the
provider can be swapped (any OpenAI-compatible endpoint, via llm_base_url)
without touching the services that call it.
"""

import json
import re
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.core.config import settings


@lru_cache
def get_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.llm_base_url)


def get_embedding(text: str) -> list[float]:
    client = get_client()
    response = client.embeddings.create(model=settings.embedding_model, input=text)
    return response.data[0].embedding


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Batched version -- one API call for many chunks, used during ingestion."""
    if not texts:
        return []
    client = get_client()
    response = client.embeddings.create(model=settings.embedding_model, input=texts)
    return [item.embedding for item in response.data]


def generate_text(system_prompt: str, user_prompt: str, max_tokens: int = 1200, temperature: float = 0.4) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _strip_code_fences(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return match.group(1) if match else text


def generate_json(system_prompt: str, user_prompt: str, max_tokens: int = 1500, temperature: float = 0.3) -> Any:
    """
    Requests JSON-mode output and parses it. Raises ValueError if the model's
    response isn't valid JSON even after stripping markdown code fences --
    callers should catch this and degrade gracefully rather than crash the
    request (e.g. quiz generation falling back to the existing question bank).
    """
    client = get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt + " Respond with valid JSON only, no commentary."},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content or ""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            return json.loads(_strip_code_fences(raw))
        except json.JSONDecodeError as e:
            raise ValueError(f"Model did not return valid JSON: {e}") from e
