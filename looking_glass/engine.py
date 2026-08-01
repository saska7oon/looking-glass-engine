"""
Main engine orchestrator for the Looking Glass Engine.

Ties together State Capture, Field Model, AI Backend, and Synchronicity Tracker.
"""

import logging
from typing import Optional

from looking_glass.aether import AetherOracle, AetherCast
from looking_glass.backend import get_backend, BackendError
from looking_glass.config import config
from looking_glass.field import ConsciousnessField
from looking_glass.state import StateCapture, StateVector
from looking_glass.tracker import SynchronicityTracker

logger = logging.getLogger(__name__)


class LookingGlassEngine:
    """The main Looking Glass Engine orchestrator.

    Coordinates state capture, field mapping, AI generation,
    synchronicity tracking, and the aether personality cast.
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
        self.current_user: str = "default"
        # Cast the aether personality once per engine lifetime. The engine is
        # cached per session in the UI, so this is thread-constant: the oracle
        # stays the same across a session's multi-turn follow-ups, then
        # re-casts for the next session.
        self.persona: Optional[AetherCast] = None

    def query(
        self,
        question: str,
        typing_speed_wps: float = 0.0,
        pause_duration: float = 0.0,
        confirmed_state: Optional[dict] = None,
        history: Optional[list] = None,
    ) -> dict:
        """Process a question through the consciousness field.

        Args:
            question: The user's question or prompt.
            typing_speed_wps: Words per second (for state analysis).
            pause_duration: Seconds since last input.
            confirmed_state: User-corrected state (overrides/anchors the read).
            history: Recent past sessions to feed the oracle's memory.

        Returns:
            dict with keys: response, state, field_point, region, resonance,
            persona, confirmed.
        """
        # 1. Cast the aether personality (once per session/thread).
        session_nonce = f"{config.backend}-{id(self):x}"
        state_dict = {}
        if confirmed_state:
            state_dict = dict(confirmed_state)
        if not self.persona:
            self.persona = AetherOracle().cast(
                state=state_dict or {
                    "arousal": 0.0, "depth": 0.0, "openness": 0.0,
                },
                session_nonce=session_nonce,
            )

        # 2. Capture the user's state (confirmed state anchors the reading).
        state = self.state_capture.capture(
            question, typing_speed_wps, pause_duration
        )
        if confirmed_state:
            # User-confirmed state wins on any axis the user set.
            for k in ("arousal", "depth", "openness"):
                if k in confirmed_state and confirmed_state[k] is not None:
                    setattr(state, k, float(confirmed_state[k]))

        # 3. Map to the consciousness field.
        field_point = self.field.state_to_field(state)

        # 4. Get resonance with field regions.
        resonance = self.field.get_resonance(state)

        # 5. Find the nearest region.
        region = field_point.label

        # 6. Build the context + history for the backend.
        context = {
            "arousal": state.arousal,
            "depth": state.depth,
            "openness": state.openness,
            "magnitude": state.magnitude(),
            "confidence": state.confidence,
            "confirmed": bool(confirmed_state),
            "persona_name": self.persona.archetype_name,
            "persona_voice": self.persona.voice_instruction,
        }
        if history:
            context["history"] = history

        try:
            response = self.backend.generate(question, context)
        except BackendError as e:
            logger.error(f"Backend error: {e}")
            response = f"[Backend error: {e}. Check your configuration.]"

        # 7. Log the session.
        session_id = self.tracker.log_session(
            question=question,
            state_arousal=state.arousal,
            state_depth=state.depth,
            state_openness=state.openness,
            state_magnitude=state.magnitude(),
            state_region=region,
            user=self.current_user,
            backend=config.backend,
            model=config.ollama_model if config.backend == "ollama" else config.openrouter_model,
            response=response,
            persona=self.persona.archetype_name,
        )

        # 8. Log field trajectory point.
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
            "persona": self.persona,
            "confirmed": bool(confirmed_state),
        }

    def get_pattern(self) -> Optional[StateVector]:
        """Return the user's baseline consciousness pattern."""
        return self.state_capture.get_pattern()

    def get_history(self, limit: int = 10) -> list[dict]:
        """Return recent session history for the current user."""
        return self.tracker.get_session_history(limit, user=self.current_user)

    def get_users(self) -> list[str]:
        """Return the distinct users who have accounts."""
        return self.tracker.get_users()

    def create_user(self, username: str, password: str) -> bool:
        """Create a user account. Returns False if username already taken."""
        ok = self.tracker.create_user(username, password)
        if ok:
            self.current_user = username.strip()
        return ok

    def authenticate_user(self, username: str, password: str) -> bool:
        """Verify a username/password pair."""
        ok = self.tracker.authenticate_user(username, password)
        if ok:
            self.current_user = username.strip()
        return ok

    def set_user(self, username: str):
        """Switch the active user (per-user session history + patterns)."""
        username = (username or "default").strip() or "default"
        self.current_user = username

    def get_synchronicities(self, limit: int = 5) -> list[dict]:
        """Return recent synchronicity events."""
        return self.tracker.get_synchronicities(limit)

    def get_pattern_regions(self) -> list[dict]:
        """Return frequently visited field regions for the current user."""
        return self.tracker.get_pattern_regions(user=self.current_user)

    def shutdown(self):
        """Clean up resources."""
        self.tracker.close()