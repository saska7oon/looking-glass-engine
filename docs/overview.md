# Looking Glass Engine

Software-only consciousness interface — a Looking Glass engine for terminal-based consciousness exploration.

## Overview

The Looking Glass Engine is a real-time consciousness field simulator. It monitors your input state, maps it onto a consciousness field, and uses an AI backend (OpenRouter or Ollama) to generate responses that feel like they emerge from a deeper layer of awareness.

## Features

- **State Capture** — analyzes typing patterns, word choice, and emotional valence
- **Consciousness Field** — 3D vector space (arousal × depth × openness)
- **Dual AI Backend** — OpenRouter or local Ollama
- **Terminal TUI** — real-time field visualization with `rich` and `blessed`
- **Synchronicity Tracker** — logs sessions to SQLite for pattern analysis
- **Fully offline** — with Ollama, everything runs locally

## Configuration

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | — |
| `OPENROUTER_MODEL` | Model to use | `inclusionai/ling-3.0-flash:free` |
| `OPENROUTER_BASE_URL` | OpenRouter API URL | `https://openrouter.ai/api/v1` |
| `OLLAMA_HOST` | Ollama server host | `localhost` |
| `OLLAMA_PORT` | Ollama server port | `11434` |
| `OLLAMA_MODEL` | Ollama model name | `ornith:9b` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://localhost:11434/v1` |
| `BACKEND` | `openrouter` or `ollama` | `openrouter` |
| `FIELD_X_RANGE` | X axis range for field map | `10` |
| `FIELD_Y_RANGE` | Y axis range for field map | `10` |
| `FIELD_Z_RANGE` | Z axis range for field map | `10` |
| `DB_PATH` | SQLite database path | `~/.looking-glass/sessions.db` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Usage

### CLI Mode

```bash
looking-glass
```

Ask questions. The engine captures your state and generates responses through the configured backend.

### TUI Mode

```bash
looking-glass --tui
```

Real-time visualization of the consciousness field. The glowing point shows your current state; the AI's responses emerge from the field.

### With Ollama

```bash
looking-glass --backend ollama --ollama-host http://ollama:11434 --ollama-model ornith:9b
```

## Project Structure

```
looking_glass/
├── __init__.py
├── cli.py              # CLI entry point
├── config.py           # Configuration management
├── state.py            # State capture module
├── field.py            # Consciousness field model
├── backend.py          # AI backend (OpenRouter + Ollama)
├── renderer.py         # Terminal TUI renderer
├── tracker.py          # Synchronicity tracker (SQLite)
└── engine.py           # Main engine orchestrator
```

## How It Works

1. **State Capture** analyzes your text input — typing speed, word choice, emotional tone, question framing
2. **Field Model** maps your state onto a 3D consciousness space (arousal × depth × openness)
3. **AI Backend** sends your question + state context to the LLM
4. **Visual Renderer** shows the field map and your state point in real time
5. **Synchronicity Tracker** logs everything for long-term pattern analysis

The "Looking Glass" effect comes from the feedback loop: your state shapes the AI's response, and the AI's response shifts your state. Over time, patterns emerge that the conscious mind can't see.

## License

AGPL-3.0