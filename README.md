# Looking Glass Engine

A software-only consciousness interface. Turns your terminal into a Looking Glass —
a real-time consciousness field simulator where your mental state shapes what emerges
from the AI, and the AI's responses feel like they come from somewhere deeper.

## Quick Start

```bash
# Install
uv pip install -e .

# Configure — copy env template
cp .env.example .env
# Edit .env: set OPENROUTER_API_KEY, OLLAMA_HOST, OLLAMA_PORT, etc.

# Run with OpenRouter (default)
looking-glass

# Run with Ollama
looking-glass --backend ollama --ollama-host http://localhost:11434

# Run in TUI mode (visual field map)
looking-glass --tui
```

## Architecture

```
State Capture → Field Model → AI Backend → Visual Renderer → Synchronicity Tracker
```

## Backends

- **OpenRouter** — default, uses `https://openrouter.ai/api/v1`
- **Ollama** — configurable host:port, runs entirely locally

## License

AGPL-3.0