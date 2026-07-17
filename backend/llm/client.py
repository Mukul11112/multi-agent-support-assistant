"""
One interface over every LLM provider the brief allows, plus a deterministic
mock so the system runs with no API key at all.

Usage:
    from backend.llm.client import get_llm
    llm = get_llm()
    text = llm.complete(system="You are...", user="Question here")
    data = llm.complete_json(system="...", user="...")   # parsed dict
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from backend import config

log = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


def _extract_json(text: str) -> Any:
    """LLMs wrap JSON in prose and code fences no matter how firmly you ask.
    Strip fences, then fall back to the first balanced {...} or [...] block."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise LLMError(f"Could not parse JSON from LLM output: {text[:300]}") from exc
    raise LLMError(f"No JSON found in LLM output: {text[:300]}")


class BaseLLM:
    name = "base"

    def complete(self, system: str, user: str, temperature: float | None = None) -> str:
        raise NotImplementedError

    def complete_json(self, system: str, user: str) -> Any:
        raw = self.complete(system=system, user=user, temperature=0.0)
        return _extract_json(raw)


class GroqLLM(BaseLLM):
    name = "groq"

    def __init__(self):
        from groq import Groq  # imported lazily so unused providers need no install
        if not config.GROQ_API_KEY:
            raise LLMError("GROQ_API_KEY is not set in .env")
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.active_model()

    def complete(self, system: str, user: str, temperature: float | None = None) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=config.LLM_TEMPERATURE if temperature is None else temperature,
            max_tokens=config.LLM_MAX_TOKENS,
        )
        return resp.choices[0].message.content.strip()


class OpenAILLM(BaseLLM):
    name = "openai"

    def __init__(self):
        from openai import OpenAI
        if not config.OPENAI_API_KEY:
            raise LLMError("OPENAI_API_KEY is not set in .env")
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.active_model()

    def complete(self, system: str, user: str, temperature: float | None = None) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=config.LLM_TEMPERATURE if temperature is None else temperature,
            max_tokens=config.LLM_MAX_TOKENS,
        )
        return resp.choices[0].message.content.strip()


class GeminiLLM(BaseLLM):
    name = "gemini"

    def __init__(self):
        import google.generativeai as genai
        if not config.GEMINI_API_KEY:
            raise LLMError("GEMINI_API_KEY is not set in .env")
        genai.configure(api_key=config.GEMINI_API_KEY)
        self._genai = genai
        self.model = config.active_model()

    def complete(self, system: str, user: str, temperature: float | None = None) -> str:
        model = self._genai.GenerativeModel(self.model, system_instruction=system)
        resp = model.generate_content(
            user,
            generation_config={
                "temperature": config.LLM_TEMPERATURE if temperature is None else temperature,
                "max_output_tokens": config.LLM_MAX_TOKENS,
            },
        )
        return resp.text.strip()


class OllamaLLM(BaseLLM):
    name = "ollama"

    def __init__(self):
        import requests
        self._requests = requests
        self.model = config.active_model()
        self.base_url = config.OLLAMA_BASE_URL

    def complete(self, system: str, user: str, temperature: float | None = None) -> str:
        resp = self._requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "stream": False,
                "options": {
                    "temperature": config.LLM_TEMPERATURE if temperature is None else temperature
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()


class MockLLM(BaseLLM):
    """Deterministic keyword-driven stand-in.

    It is not pretending to be intelligent. Its job is to keep every other
    component honest: routing, retrieval, memory, aggregation, and the API all
    run identically to production, so tests exercise real code paths and the
    project is demonstrable with zero credentials.
    """

    name = "mock"

    DOMAIN_KEYWORDS = {
        "billing": ["refund", "payment", "paid", "invoice", "subscription", "charge",
                    "charged", "money", "premium", "emi", "cod", "wallet", "price drop",
                    "cancel", "billing", "debited", "gst"],
        "technical": ["login", "password", "reset", "error", "bug", "crash", "not working",
                      "install", "setup", "pair", "wifi", "wi-fi", "locked", "blue screen",
                      "battery", "charging", "offline", "otp", "connect", "overheating"],
        "product": ["price", "cost", "spec", "feature", "compare", "comparison", "difference",
                    "available", "stock", "ship", "shipping", "delivery", "warranty period",
                    "which laptop", "recommend"],
        "complaint": ["complaint", "terrible", "worst", "angry", "furious", "unacceptable",
                      "escalate", "manager", "sue", "consumer court", "disgusted", "fed up",
                      "third time", "still waiting"],
        "faq": ["hours", "contact", "policy", "who are you", "where are you", "address",
                "email", "phone", "privacy", "data"],
    }

    def complete(self, system: str, user: str, temperature: float | None = None) -> str:
        low = user.lower()

        # Router prompts ask for JSON with an "agents" key.
        if "route" in system.lower() and "json" in system.lower():
            hits = [d for d, kws in self.DOMAIN_KEYWORDS.items()
                    if any(k in low for k in kws)]
            hits = [h for h in hits if h != "faq"] or hits or ["faq"]
            return json.dumps({
                "agents": hits[:2],
                "confidence": 0.55,
                "reasoning": "mock router: keyword match",
            })

        # Aggregator prompts.
        if "aggregat" in system.lower() or "merge" in system.lower():
            return ("[mock LLM] Combined answer assembled from the specialist agent "
                    "responses above. Set LLM_PROVIDER=groq in .env for real generation.")

        # Agent answer prompts: echo retrieved context so retrieval quality is
        # visible in the demo even without a real model.
        context = ""
        marker = "CONTEXT:"
        if marker in user:
            context = user.split(marker, 1)[1].strip()
            context = context.split("CUSTOMER QUESTION:")[0].strip()
        snippet = " ".join(context.split())[:600]
        if not snippet:
            return ("[mock LLM] No relevant information was retrieved from the knowledge "
                    "base for this question. I would escalate this to a human agent.")
        return (f"[mock LLM] Based on the knowledge base:\n\n{snippet}\n\n"
                f"(Set LLM_PROVIDER=groq and GROQ_API_KEY in .env for real answers.)")


_PROVIDERS = {
    "groq": GroqLLM,
    "openai": OpenAILLM,
    "gemini": GeminiLLM,
    "ollama": OllamaLLM,
    "mock": MockLLM,
}

_instance: BaseLLM | None = None


def get_llm() -> BaseLLM:
    """Cached singleton. Falls back to the mock rather than crashing at import
    time, so a missing API key degrades the demo instead of killing the server."""
    global _instance
    if _instance is not None:
        return _instance
    provider = config.LLM_PROVIDER
    cls = _PROVIDERS.get(provider)
    if cls is None:
        log.warning("Unknown LLM_PROVIDER %r, falling back to mock", provider)
        cls = MockLLM
    try:
        _instance = cls()
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not initialise provider %r (%s). Falling back to MockLLM.",
                    provider, exc)
        _instance = MockLLM()
    log.info("LLM provider active: %s (%s)", _instance.name, config.active_model())
    return _instance


def reset_llm() -> None:
    """Test hook."""
    global _instance
    _instance = None
