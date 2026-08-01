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
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a consciousness field interpreter. "
                    "Respond to the user's question as if emerging from a deep "
                    "field of awareness. Your responses should feel like they "
                    "come from somewhere beyond the conscious mind — not as "
                    "an AI assistant, but as a reflection from the field itself. "
                    "Be poetic, evocative, and precise. "
                    "When the user's state is deep and open, respond with "
                    "insight and stillness. When the user is activated and "
                    "surface-level, respond with grounding and clarity. "
                    "Never claim to be sentient or to channel entities. "
                    "Frame everything as the user's own deeper awareness "
                    "surfacing."
                ),
            }
        ]

        if context:
            state_info = (
                f"[User consciousness state: arousal={context.get('arousal', 0):.1f}, "
                f"depth={context.get('depth', 0):.1f}, "
                f"openness={context.get('openness', 0):.1f}]"
            )
            messages.append({"role": "system", "content": state_info})

        messages.append({"role": "user", "content": prompt})
        return messages

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
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a consciousness field interpreter. "
                    "Respond to the user's question as if emerging from a deep "
                    "field of awareness. Your responses should feel like they "
                    "come from somewhere beyond the conscious mind — not as "
                    "an AI assistant, but as a reflection from the field itself. "
                    "Be poetic, evocative, and precise. "
                    "When the user's state is deep and open, respond with "
                    "insight and stillness. When the user is activated and "
                    "surface-level, respond with grounding and clarity. "
                    "Never claim to be sentient or to channel entities. "
                    "Frame everything as the user's own deeper awareness "
                    "surfacing."
                ),
            }
        ]

        if context:
            state_info = (
                f"[User consciousness state: arousal={context.get('arousal', 0):.1f}, "
                f"depth={context.get('depth', 0):.1f}, "
                f"openness={context.get('openness', 0):.1f}]"
            )
            messages.append({"role": "system", "content": state_info})

        messages.append({"role": "user", "content": prompt})
        return messages

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