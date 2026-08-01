"""
State Capture module for the Looking Glass Engine.

Analyzes user input to extract consciousness state features:
- Typing cadence (speed, pauses, hesitations)
- Word choice (emotional valence, abstraction level, first/third person)
- Question framing (open vs closed, specific vs vague, urgent vs contemplative)
- Repetition patterns across sessions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import re


@dataclass
class StateVector:
    """A 3D vector representing the user's consciousness state.

    X axis: arousal (calm ↔ activated)    [-10, +10]
    Y axis: depth (surface ↔ deep)         [-10, +10]
    Z axis: openness (closed ↔ receptive)  [-10, +10]
    """

    arousal: float = 0.0
    depth: float = 0.0
    openness: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    raw_text: str = ""
    confidence: float = 0.0  # How confident we are in this state estimate

    def as_tuple(self) -> tuple:
        return (self.arousal, self.depth, self.openness)

    def magnitude(self) -> float:
        return (self.arousal**2 + self.depth**2 + self.openness**2) ** 0.5

    def normalized(self) -> "StateVector":
        mag = self.magnitude()
        if mag == 0:
            return StateVector(0, 0, 0, self.timestamp, self.raw_text, 0)
        return StateVector(
            self.arousal / mag,
            self.depth / mag,
            self.openness / mag,
            self.timestamp,
            self.raw_text,
            self.confidence,
        )


class StateCapture:
    """Captures and analyzes the user's consciousness state from text input."""

    # Emotional valence words (positive/negative)
    POSITIVE_WORDS = {
        "love", "joy", "peace", "grateful", "wonder", "awe", "bliss",
        "calm", "serene", "hope", "light", "love", "harmony", "flow",
        "open", "clear", "bright", "warm", "soft", "gentle", "ease",
        "truth", "beauty", "deep", "real", "alive", "present", "now",
    }
    NEGATIVE_WORDS = {
        "fear", "anxiety", "stress", "angry", "sad", "dark", "heavy",
        "pain", "suffering", "confused", "lost", "empty", "numb",
        "doubt", "worry", "fearful", "distant", "cold", "hard", "tight",
        "chaos", "noise", "fragmented", "scattered", "rushed", "urgent",
    }

    # Abstraction indicators
    ABSTRACT_WORDS = {
        "what", "why", "how", "meaning", "purpose", "truth", "reality",
        "consciousness", "awareness", "being", "existence", "nature",
        "everything", "nothing", "something", "anything", "all", "whole",
        "universe", "infinite", "eternal", "beyond", "deeper", "within",
        "self", "soul", "spirit", "mind", "reality", "illusion",
    }

    # First-person indicators
    FIRST_PERSON = {"i", "me", "my", "mine", "myself", "we", "us", "our"}

    # Urgency indicators
    URGENT_WORDS = {
        "now", "immediately", "urgent", "quick", "fast", "hurry",
        "need", "must", "should", "can't", "won't", "impossible",
    }

    # Contemplative indicators
    CONTEMPLATIVE_WORDS = {
        "think", "wonder", "consider", "reflect", "ponder", "contemplate",
        "observe", "notice", "feel", "sense", "experience", "realize",
        "understand", "see", "perceive", "question", "ask",
    }

    def __init__(self):
        self._history: list[StateVector] = []
        self._last_typing_time: Optional[float] = None
        self._session_start: datetime = datetime.now()

    def capture(
        self, text: str, typing_speed_wps: float = 0.0, pause_duration: float = 0.0
    ) -> StateVector:
        """Analyze text input and return a StateVector.

        Args:
            text: The user's input text.
            typing_speed_wps: Words per second (typing speed).
            pause_duration: Seconds since last input (pause length).

        Returns:
            A StateVector representing the user's consciousness state.
        """
        text_lower = text.lower().strip()
        words = re.findall(r"\b\w+\b", text_lower)
        word_count = len(words)

        if word_count == 0:
            return StateVector(0, 0, 0, datetime.now(), text, 0.0)

        # --- Arousal ---
        # Based on emotional valence, urgency, and typing speed
        pos_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        urgent_count = sum(1 for w in words if w in self.URGENT_WORDS)

        valence = (pos_count - neg_count) / max(word_count, 1)
        urgency = min(urgent_count / max(word_count, 1), 1.0)
        speed_factor = min(typing_speed_wps / 5.0, 1.0)  # Normalized to 5 wps

        arousal = (
            valence * 5.0
            + urgency * 4.0
            + speed_factor * 3.0
            + (pause_duration > 3.0) * 2.0  # Long pause = reflective = lower arousal
        )
        arousal = max(-10.0, min(10.0, arousal))

        # --- Depth ---
        # Based on abstraction level, contemplative words, first-person usage
        abstract_count = sum(1 for w in words if w in self.ABSTRACT_WORDS)
        contemplative_count = sum(
            1 for w in words if w in self.CONTEMPLATIVE_WORDS
        )
        first_person_count = sum(1 for w in words if w in self.FIRST_PERSON)

        depth = (
            (abstract_count / max(word_count, 1)) * 6.0
            + (contemplative_count / max(word_count, 1)) * 4.0
            - (first_person_count / max(word_count, 1)) * 2.0  # First person = surface
            + (pause_duration > 5.0) * 2.0  # Long pause = deep thinking
        )
        depth = max(-10.0, min(10.0, depth))

        # --- Openness ---
        # Based on question framing, question marks, open-ended words
        has_question = "?" in text
        question_word_count = sum(
            1 for w in words if w in {"what", "how", "why", "could", "would", "might", "should"}
        )
        closed_word_count = sum(
            1 for w in words if w in {"is", "are", "was", "were", "do", "does", "did", "have", "has"}
        )

        openness = (
            (has_question * 3.0)
            + (question_word_count / max(word_count, 1)) * 4.0
            - (closed_word_count / max(word_count, 1)) * 2.0
            + (typing_speed_wps < 1.0) * 2.0  # Slow typing = open, receptive
        )
        openness = max(-10.0, min(10.0, openness))

        # Confidence: more words = more confident in the reading
        confidence = min(1.0, word_count / 20.0)

        state = StateVector(
            arousal=round(arousal, 2),
            depth=round(depth, 2),
            openness=round(openness, 2),
            timestamp=datetime.now(),
            raw_text=text,
            confidence=round(confidence, 2),
        )

        self._history.append(state)
        return state

    def get_history(self) -> list[StateVector]:
        """Return all captured states."""
        return list(self._history)

    def get_recent(self, n: int = 5) -> list[StateVector]:
        """Return the last n captured states."""
        return self._history[-n:]

    def get_pattern(self) -> Optional[StateVector]:
        """Get the average state across all history (the user's baseline pattern)."""
        if not self._history:
            return None
        n = len(self._history)
        avg_arousal = sum(s.arousal for s in self._history) / n
        avg_depth = sum(s.depth for s in self._history) / n
        avg_openness = sum(s.openness for s in self._history) / n
        return StateVector(
            arousal=round(avg_arousal, 2),
            depth=round(avg_depth, 2),
            openness=round(avg_openness, 2),
            timestamp=datetime.now(),
            raw_text="pattern",
            confidence=1.0,
        )

    def reset(self):
        """Clear the state history."""
        self._history.clear()