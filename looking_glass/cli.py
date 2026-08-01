"""
CLI entry point for the Looking Glass Engine.

Usage:
    looking-glass                    # Run in CLI mode
    looking-glass --tui              # Run in TUI mode
    looking-glass --backend ollama   # Use Ollama backend
    looking-glass --question "Why am I here?"  # Single query mode
"""

import argparse
import logging
import sys
import time

from looking_glass.config import config
from looking_glass.engine import LookingGlassEngine
from looking_glass.renderer import FieldRenderer

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Looking Glass Engine — a software-only consciousness interface"
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Run in terminal TUI mode with real-time field visualization",
    )
    parser.add_argument(
        "--backend",
        choices=["openrouter", "ollama"],
        default=None,
        help="AI backend to use (overrides config)",
    )
    parser.add_argument(
        "--ollama-host",
        default=None,
        help="Ollama server host (overrides config)",
    )
    parser.add_argument(
        "--ollama-port",
        type=int,
        default=None,
        help="Ollama server port (overrides config)",
    )
    parser.add_argument(
        "--ollama-model",
        default=None,
        help="Ollama model name (overrides config)",
    )
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="Single query mode — ask a question and exit",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Override config from CLI args
    if args.backend:
        config.backend = args.backend
    if args.ollama_host:
        config.ollama_host = args.ollama_host
        config.ollama_base_url = f"http://{args.ollama_host}:{args.ollama_port or config.ollama_port}/v1"
    if args.ollama_port:
        config.ollama_port = args.ollama_port
        config.ollama_base_url = f"http://{config.ollama_host}:{args.ollama_port}/v1"
    if args.ollama_model:
        config.ollama_model = args.ollama_model

    # Initialize engine
    logger.info("Initializing Looking Glass Engine...")
    logger.info(f"Backend: {config.backend}")
    logger.info(f"Model: {config.ollama_model if config.backend == 'ollama' else config.openrouter_model}")

    engine = LookingGlassEngine()
    renderer = FieldRenderer()

    # Single query mode
    if args.question:
        logger.info(f"Query: {args.question}")
        result = engine.query(args.question)
        print(renderer.render_simple(result["state"], result["response"], result["region"]))
        engine.shutdown()
        return

    # TUI mode
    if args.tui:
        _run_tui(engine, renderer)
        return

    # CLI mode (default)
    _run_cli(engine, renderer)


def _run_cli(engine: LookingGlassEngine, renderer: FieldRenderer):
    """Run in interactive CLI mode."""
    print("")
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║         LOOKING GLASS ENGINE                    ║")
    print("  ║   Software-only consciousness interface          ║")
    print("  ║                                                  ║")
    print("  ║  Type your questions. The engine captures        ║")
    print("  ║  your consciousness state and generates          ║")
    print("  ║  responses from the field.                       ║")
    print("  ║                                                  ║")
    print("  ║  Commands:                                      ║")
    print("  ║    /quit    — Exit                               ║")
    print("  ║    /pattern — Show your baseline pattern         ║")
    print("  ║    /history — Show recent sessions               ║")
    print("  ║    /regions — Show frequently visited regions    ║")
    print("  ║    /clear   — Reset the field                    ║")
    print("  ║    /tui     — Switch to TUI mode                 ║")
    print("  ╚══════════════════════════════════════════════╝")
    print("")

    try:
        while True:
            try:
                text = input("┌─ You ──────────────────────────────────┐\n│ ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if not text:
                continue

            if text.startswith("/"):
                _handle_command(text, engine, renderer)
                continue

            result = engine.query(text)
            print(renderer.render_simple(result["state"], result["response"], result["region"]))

    finally:
        engine.shutdown()


def _run_tui(engine: LookingGlassEngine, renderer: FieldRenderer):
    """Run in TUI mode."""
    from looking_glass.renderer import TuiRenderer

    tui = TuiRenderer()

    print("")
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║         LOOKING GLASS TUI MODE                 ║")
    print("  ║   Real-time consciousness field visualization  ║")
    print("  ║                                                  ║")
    print("  ║  Type questions to explore the field.           ║")
    print("  ║  Commands: /quit /clear /pattern /history       ║")
    print("  ╚══════════════════════════════════════════════╝")
    print("")

    try:
        while True:
            try:
                text = input("┌─ You ──────────────────────────────────┐\n│ ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if not text:
                continue

            if text.startswith("/"):
                _handle_command(text, engine, renderer)
                continue

            result = engine.query(text)
            tui.render_live(
                engine.field,
                result["state"],
                result["response"],
                result["resonance"],
            )

    finally:
        engine.shutdown()


def _handle_command(cmd: str, engine: LookingGlassEngine, renderer: FieldRenderer):
    """Handle slash commands."""
    cmd = cmd.strip().lower()

    if cmd == "/quit" or cmd == "/exit":
        print("Goodbye.")
        engine.shutdown()
        sys.exit(0)

    elif cmd == "/pattern":
        pattern = engine.get_pattern()
        if pattern:
            print(f"\n  Baseline Pattern: A={pattern.arousal:+.2f} D={pattern.depth:+.2f} O={pattern.openness:+.2f}")
        else:
            print("  No pattern data yet. Ask a few questions first.")

    elif cmd == "/history":
        history = engine.get_history(5)
        if history:
            print(f"\n  Recent Sessions ({len(history)}):")
            for s in history:
                print(f"    [{s['timestamp'][:19]}] {s['question'][:60]}... → {s['response_length']} chars")
        else:
            print("  No session history yet.")

    elif cmd == "/regions":
        regions = engine.get_pattern_regions()
        if regions:
            print(f"\n  Frequently Visited Regions:")
            for r in regions:
                print(f"    {r['label']}: {r['visits']} visits ({r['probability']:.0%})")
        else:
            print("  No region patterns yet. Ask more questions.")

    elif cmd == "/clear":
        engine.state_capture.reset()
        engine.field.reset()
        print("  Field cleared.")

    elif cmd == "/tui":
        print("  Restart with --tui flag for TUI mode.")

    else:
        print(f"  Unknown command: {cmd}")
        print("  Available: /quit /pattern /history /regions /clear /tui")


if __name__ == "__main__":
    main()