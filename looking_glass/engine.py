"""
Main engine orchestrator for the Looking Glass Engine.

Ties together State Capture, Field Model, AI Backend, and Synchronicity Tracker.
"""

import logging
from typing import Optional

from looking_glass.backend import get_backend, BackendError
from looking_glass.config import config
from looking_glass.field import ConsciousnessField
from looking_glass.state import StateCapture, StateVector
from looking_glass.tracker import SynchronicityTracker

logger = logging.getLogger(__name__)


class LookingGlassEngine:
    """The main Looking Glass Engine orchestrator.

    Coordinates state capture, field mapping, AI generation,
    and synchronicity tracking into a single consciousness interface.
    """

    def __init__(self):
        self.state_capture = StateCapture()
        self.field = ConsciousnessField(
            x_range=config.field_x_range,
            y_range=config.field_y_range,
            z_range=config.field_z_range,
        )
        self.tracker = SynchronicityTracker()
        self.backend = get_backend()

    def query(
        self,
        question: str,
        typing_speed_wps: float = 0.0,
        pause_duration: float = 0.0,
    ) -> dict:
        """Process a question through the consciousness field.

        Args:
            question: The user's question or prompt.
            typing_speed_wps: Words per second (for state analysis).
            pause_duration: Seconds since last input.

        Returns:
            dict with keys: response, state, field_point, region, resonance
        """
        # 1. Capture the user's state
        state = self.state_capture.capture(
            question, typing_speed_wps, pause_duration
        )

        # 2. Map to the consciousness field
        field_point = self.field.state_to_field(state)

        # 3. Get resonance with field regions
        resonance = self.field.get_resonance(state)

        # 4. Find the nearest region
        region = field_point.label

        # 5. Generate AI response with state context
        context = {
            "arousal": state.arousal,
            "depth": state.depth,
            "openness": state.openness,
        }

        try:
            response = self.backend.generate(question, context)
        except BackendError as e:
            logger.error(f"Backend error: {e}")
            response = f"[Backend error: {e}. Check your configuration.]"

        # 6. Log the session
        session_id = self.tracker.log_session(
            question=question,
            state_arousal=state.arousal,
            state_depth=state.depth,
            state_openness=state.openness,
            state_magnitude=state.magnitude(),
            state_region=region,
            backend=config.backend,
            model=config.ollama_model if config.backend == "ollama" else config.openrouter_model,
            response=response,
        )

        # 7. Log field trajectory point
        self.tracker.log_field_point(
            session_id=session_id,
            x=field_point.x,
            y=field_point.y,
            z=field_point.z,
            label=region,
            intensity=field_point.intensity,
        )

        return {
            "response": response,
            "state": state,
            "field_point": field_point,
            "region": region,
            "resonance": resonance,
            "session_id": session_id,
        }

    def get_pattern(self) -> Optional[StateVector]:
        """Return the user's baseline consciousness pattern."""
        return self.state_capture.get_pattern()

    def get_history(self, limit: int = 10) -> list[dict]:
        """Return recent session history."""
        return self.tracker.get_session_history(limit)

    def get_synchronicities(self, limit: int = 5) -> list[dict]:
        """Return recent synchronicity events."""
        return self.tracker.get_synchronicities(limit)

    def get_pattern_regions(self) -> list[dict]:
        """Return frequently visited field regions."""
        return self.tracker.get_pattern_regions()

    def shutdown(self):
        """Clean up resources."""
        self.tracker.close()