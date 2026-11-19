"""無料枠 LLM プロバイダー（SDK を使わず HTTP で直接呼ぶ）。

いずれも「JSON 文字列」を返す。キーが無いプロバイダーは自動でスキップされる。
"""
from __future__ import annotations

import os
from typing import Callable

import requests

TIMEOUT = 90


class ProviderUnavailable(Exception):
    pass


def _openai_compatible(url: str, key: str, model: str, system: str, user: str, temperature: float) -> str:
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        },
        timeout=TIMEOUT,
    )
    if r.status_code == 429:
        raise ProviderUnavailable("rate limited")
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def gemini(system: str, user: str, temperature: float) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ProviderUnavailable("GEMINI_API_KEY not set")
    model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"},
        },
        timeout=TIMEOUT,
    )
    if r.status_code == 429:
        raise ProviderUnavailable("rate limited")
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def groq(system: str, user: str, temperature: float) -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise ProviderUnavailable("GROQ_API_KEY not set")
    return _openai_compatible("https://api.groq.com/openai/v1/chat/completions", key,
                              os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"), system, user, temperature)


def openrouter(system: str, user: str, temperature: float) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ProviderUnavailable("OPENROUTER_API_KEY not set")
    return _openai_compatible("https://openrouter.ai/api/v1/chat/completions", key,
                              os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
                              system, user, temperature)


def ollama(system: str, user: str, temperature: float) -> str:
    host = os.environ.get("OLLAMA_HOST")
    if not host:
        raise ProviderUnavailable("OLLAMA_HOST not set")
    r = requests.post(
        f"{host.rstrip('/')}/api/chat",
        json={
            "model": os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"),
            "format": "json",
            "stream": False,
            "options": {"temperature": temperature},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        },
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


PROVIDERS: dict[str, Callable[[str, str, float], str]] = {
    "gemini": gemini,
    "groq": groq,
    "openrouter": openrouter,
    "ollama": ollama,
}
