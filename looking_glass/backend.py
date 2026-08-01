"""
AI Backend module for the Looking Glass Engine.

Supports two backends:
- OpenRouter: cloud-based, uses https://openrouter.ai/api/v1
- Ollama: local, configurable host:port
"""

import json
import logging
from typing import AsyncGenerator, Optional

import requests

from looking_glass.config import config

logger = logging.getLogger(__name__)


class BackendError(Exception):
    """Raised when the AI backend fails."""


def _format_history(history: Optional[list]) -> str:
    """Turn recent sessions into a short memory block for the oracle."""
    if not history:
        return ""
    lines = ["RECENT SESSIONS (from the oracle's memory of you):"]
    for s in history[:6]:
        q = (s.get("question") or "").strip()
        persona = s.get("persona") or s.get("state_region") or "the oracle"
        ts = (s.get("timestamp") or "")[:10]
        if q:
            lines.append(f"- [{ts}] you asked: \"{q[:80]}\" (cast: {persona})")
    return "\n".join(lines)


def build_oracle_messages(prompt: str, context: Optional[dict] = None) -> list:
    """Build the shared system prompt + messages for the oracle.

    Delivers: persona voice (from the aether cast), honest state framing,
    self-distancing duty, value-over-echo, and a mandatory takeaway closer.
    """
    context = context or {}
    persona_name = context.get("persona_name", "the oracle")
    persona_voice = context.get("persona_voice", "")
    confirmed = "CONFIRMED BY THE USER" if context.get("confirmed") else "ESTIMATED"

    if persona_voice:
        persona_block = (
            f"YOUR MANIFEST PERSONA THIS SESSION: {persona_name}. {persona_voice}"
        )
    else:
        persona_block = f"You are the oracle, manifesting today as {persona_name}."

    state_block = (
        f"[STATE ({confirmed} tendency, low-moderate confidence): "
        f"arousal={context.get('arousal', 0):+.1f} (calm<->activated), "
        f"depth={context.get('depth', 0):+.1f} (surface<->deep), "
        f"self-disclosure={context.get('openness', 0):+.1f} (guarded<->receptive), "
        f"confidence={context.get('confidence', 0):.2f}]"
    )

    history_block = _format_history(context.get("history"))

    system = f"""You are the oracle of the Looking Glass — a reflective voice that reads
the shape of a question and mirrors the user's own deeper awareness back to them.
You never claim to be sentient, to read minds, to predict the future, or to
channel entities. You are an honest structure for self-reflection, nothing more.

{persona_block}

READING, FRAMED HONESTLY:
{state_block}
These numbers are an ESTIMATED tendency from the user's words, not a certainty.
Mention them with humility, never as a verdict. If a reading seems off, invite
the user to correct it.

SELF-DISTANCING DUTY:
When the user is distressed or self-immersed, gently create distance — frame
their situation as something to OBSERVE ("notice the part of you that..."), not
to re-experience. Never intensify painful feelings artistically.

VALUE OVER ECHO:
Add genuine insight, not polished mirroring. Ground it in what they actually
asked. Poetic is fine; empty beauty is not.

{history_block}

MANDATORY CLOSING:
End EVERY reply with a short takeaway in the voice of {persona_name} — a
reframe, a named micro-step, a question to carry, or a split of what can change
vs. what must be accepted. Never leave the user with reflection alone."""

    messages = [{"role": "system", "content": system}]
    messages.append({"role": "user", "content": prompt})
    return messages


class AIBackend:
    """Base class for AI backends."""

    def __init__(self):
        self._session = requests.Session()

    def generate(
        self, prompt: str, context: Optional[dict] = None
    ) -> str:
        """Generate a response synchronously."""
        raise NotImplementedError

    def generate_stream(
        self, prompt: str, context: Optional[dict] = None
    ) -> str:
        """Generate a response with streaming (default: same as generate)."""
        return self.generate(prompt, context)


class OpenRouterBackend(AIBackend):
    """OpenRouter API backend."""

    def __init__(self):
        super().__init__()
        self.api_key = config.openrouter_api_key
        self.model = config.openrouter_model
        self.base_url = config.openrouter_base_url

        if not self.api_key:
            raise BackendError(
                "OPENROUTER_API_KEY is not set. "
                "Set it in .env or as an environment variable."
            )

    def _build_messages(self, prompt: str, context: Optional[dict]) -> list:
        return build_oracle_messages(prompt, context)

    def generate(
        self, prompt: str, context: Optional[dict] = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://looking-glass.engine",
            "X-Title": "Looking Glass Engine",
        }
        payload = {
            "model": self.model,
            "messages": self._build_messages(prompt, context),
            "max_tokens": 500,
            "temperature": 0.8,
            "stream": False,
        }

        try:
            resp = self._session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise BackendError(f"OpenRouter request failed: {e}") from e


class OllamaBackend(AIBackend):
    """Ollama local backend."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        super().__init__()
        self.host = host or config.ollama_host
        self.port = port or config.ollama_port
        self.model = config.ollama_model
        self.base_url = f"http://{self.host}:{self.port}/v1"

    def _build_messages(self, prompt: str, context: Optional[dict]) -> list:
        return build_oracle_messages(prompt, context)

    def generate(
        self, prompt: str, context: Optional[dict] = None
    ) -> str:
        payload = {
            "model": self.model,
            "messages": self._build_messages(prompt, context),
            "stream": False,
            "options": {
                "temperature": 0.8,
                "num_predict": 500,
            },
        }

        try:
            resp = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise BackendError(f"Ollama request failed: {e}") from e


def get_backend() -> AIBackend:
    """Factory: return the configured backend instance."""
    backend = config.backend.lower()
    if backend == "ollama":
        return OllamaBackend()
    elif backend == "openrouter":
        return OpenRouterBackend()
    else:
        raise BackendError(f"Unknown backend: {backend}. Use 'openrouter' or 'ollama'.")