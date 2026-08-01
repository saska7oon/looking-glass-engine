"""
Visual Renderer for the Looking Glass Engine.

Terminal-based TUI using rich and blessed for real-time
consciousness field visualization.
"""

import logging
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from looking_glass.field import ConsciousnessField, FieldPoint
from looking_glass.state import StateVector

logger = logging.getLogger(__name__)


class FieldRenderer:
    """Renders the consciousness field in the terminal."""

    def __init__(self):
        self.console = Console()
        self.width = 80
        self.height = 24

    def render_field_map(
        self,
        field: ConsciousnessField,
        state: Optional[StateVector] = None,
        response: Optional[str] = None,
        region: Optional[str] = None,
    ) -> str:
        """Render the consciousness field as an ASCII map."""
        lines = []

        # Header
        lines.append("╔══════════════════════════════════════════════╗")
        lines.append("║         CONSCIOUSNESS FIELD MAP               ║")
        lines.append("╚══════════════════════════════════════════════╝")

        # Build the field grid
        grid_size = 20
        grid = [[" " for _ in range(grid_size)] for _ in range(grid_size)]

        # Plot field history
        for point in field.history[-50:]:
            gx = int((point.x + field.x_range) / (2 * field.x_range) * (grid_size - 1))
            gy = int((point.y + field.y_range) / (2 * field.y_range) * (grid_size - 1))
            gx = max(0, min(grid_size - 1, gx))
            gy = max(0, min(grid_size - 1, gy))
            if grid[gy][gx] == " ":
                grid[gy][gx] = "·"

        # Plot current position (bright)
        if field.current:
            cx = int(
                (field.current.x + field.x_range)
                / (2 * field.x_range)
                * (grid_size - 1)
            )
            cy = int(
                (field.current.y + field.y_range)
                / (2 * field.y_range)
                * (grid_size - 1)
            )
            cx = max(0, min(grid_size - 1, cx))
            cy = max(0, min(grid_size - 1, cy))
            grid[cy][cx] = "●"

        # Draw grid
        for row in grid:
            lines.append("║ " + "".join(row) + " " + " " * (grid_size - len(row)) + "║")

        # Axis labels
        lines.append("║  +Y = Deep  ──── 0 ────  -Y = Surface        ║")
        lines.append("║  +X = Activated  0  -X = Calm                 ║")
        lines.append("║  +Z = Open  0  -Z = Closed                    ║")

        # State info
        if state:
            lines.append("")
            lines.append(f"  State: A={state.arousal:+.1f}  D={state.depth:+.1f}  O={state.openness:+.1f}")
            lines.append(f"  Magnitude: {state.magnitude():.2f}  Confidence: {state.confidence:.2f}")

        if region:
            lines.append(f"  Region: {region}")

        if response:
            lines.append("")
            lines.append("  ── Field Response ──")
            # Wrap response text
            for chunk in self._wrap_text(response, 50):
                lines.append(f"  {chunk}")

        lines.append("")
        return "\n".join(lines)

    def render_tui(
        self,
        field: ConsciousnessField,
        state: Optional[StateVector] = None,
        response: Optional[str] = None,
        resonance: Optional[dict] = None,
    ) -> str:
        """Render a full TUI layout."""
        output = []

        # Field map
        region = None
        if state and hasattr(state, "raw_text"):
            # Use the field's nearest region for the current state
            pass
        output.append(self.render_field_map(field, state, response, region))

        # Resonance table
        if resonance:
            table = Table(title="Field Resonance", show_header=True, header_style="bold cyan")
            table.add_column("Region", style="magenta")
            table.add_column("Score", style="green")
            table.add_column("Bar", style="yellow")

            for name, score in sorted(resonance.items(), key=lambda x: x[1], reverse=True)[:5]:
                bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
                table.add_row(name, f"{score:.3f}", bar)

            self.console.print(table)

        return "\n".join(output)

    def render_simple(
        self,
        state: StateVector,
        response: str,
        region: str,
    ) -> str:
        """Render a simple text output (no TUI)."""
        lines = []
        lines.append(f"┌─ State ──────────────────────────────────────┐")
        lines.append(f"│  Arousal:  {state.arousal:+6.2f}                    │")
        lines.append(f"│  Depth:    {state.depth:+6.2f}                    │")
        lines.append(f"│  Openness: {state.openness:+6.2f}                    │")
        lines.append(f"│  Region:   {region:<30s}│")
        lines.append(f"│  Magnitude: {state.magnitude():.2f}                     │")
        lines.append(f"└──────────────────────────────────────────────┘")
        lines.append("")
        lines.append("┌─ Field Response ─────────────────────────────┐")
        for chunk in self._wrap_text(response, 50):
            lines.append(f"│ {chunk:<46s}│")
        lines.append(f"└──────────────────────────────────────────────┘")
        return "\n".join(lines)

    def _wrap_text(self, text: str, width: int) -> list[str]:
        """Wrap text to a given width."""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 > width:
                if current:
                    lines.append(current)
                current = word
            else:
                current = f"{current} {word}" if current else word
        if current:
            lines.append(current)
        return lines


class TuiRenderer:
    """Live TUI renderer using blessed for real-time updates."""

    def __init__(self):
        try:
            from blessed import Terminal

            self.term = Terminal()
            self._has_blessed = True
        except ImportError:
            self._has_blessed = False
            self.term = None

    def render_live(
        self,
        field: ConsciousnessField,
        state: StateVector,
        response: str,
        resonance: dict,
    ):
        """Render a live-updating TUI."""
        renderer = FieldRenderer()
        output = renderer.render_tui(field, state, response, resonance)
        print(output)