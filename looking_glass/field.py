"""
Consciousness Field Model for the Looking Glass Engine.

Maps user consciousness states onto a 3D field space and computes
trajectories, resonance patterns, and probability regions.

Axes:
  X: Arousal (calm ↔ activated)
  Y: Depth (surface ↔ deep/unconscious)
  Z: Openness (closed/defensive ↔ receptive/flowing)
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from looking_glass.state import StateVector

logger = logging.getLogger(__name__)


@dataclass
class FieldPoint:
    """A point in the consciousness field with metadata."""

    x: float
    y: float
    z: float
    timestamp: float = 0.0
    label: str = ""
    intensity: float = 1.0

    def distance_to(self, other: "FieldPoint") -> float:
        return math.sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )


@dataclass
class FieldRegion:
    """A region in the field with a label and center."""

    name: str
    center: FieldPoint
    radius: float = 3.0
    description: str = ""
    intensity: float = 1.0


class ConsciousnessField:
    """The 3D consciousness field model.

    The field is a bounded space where the user's state is plotted.
    Over time, the field accumulates history points that reveal patterns.
    """

    # Named regions in the field — archetypal consciousness states
    REGIONS = [
        FieldRegion(
            name="Surface Mind",
            center=FieldPoint(0, -8, 0),
            radius=3.0,
            description="Everyday waking consciousness, logical, task-oriented",
            intensity=1.0,
        ),
        FieldRegion(
            name="Deep Stillness",
            center=FieldPoint(0, 8, 2),
            radius=3.0,
            description="Meditative, reflective, inner quiet",
            intensity=1.0,
        ),
        FieldRegion(
            name="Activated Flow",
            center=FieldPoint(6, 0, 4),
            radius=3.0,
            description="Engaged, creative, in the zone",
            intensity=1.0,
        ),
        FieldRegion(
            name="Anxiety Spiral",
            center=FieldPoint(-6, -4, -6),
            radius=3.0,
            description="Racing thoughts, worry, closed patterns",
            intensity=1.0,
        ),
        FieldRegion(
            name="Open Receptivity",
            center=FieldPoint(2, 4, 8),
            radius=3.0,
            description="Aware, present, open to insight",
            intensity=1.0,
        ),
        FieldRegion(
            name="Shadow Depth",
            center=FieldPoint(-2, -6, -2),
            radius=3.0,
            description="Confronting hidden patterns, uncomfortable truths",
            intensity=1.0,
        ),
        FieldRegion(
            name="Transcendent Peak",
            center=FieldPoint(0, 9, 0),
            radius=2.0,
            description="Peak awareness, unity consciousness, awe",
            intensity=1.0,
        ),
    ]

    def __init__(self, x_range: float = 10.0, y_range: float = 10.0, z_range: float = 10.0):
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.history: list[FieldPoint] = []
        self.current: Optional[FieldPoint] = None

    def state_to_field(self, state: StateVector) -> FieldPoint:
        """Convert a StateVector to a FieldPoint.

        Maps the normalized state axes onto the field coordinates.
        """
        # Normalate state values to field range
        x = state.arousal * (self.x_range / 10.0)
        y = state.depth * (self.y_range / 10.0)
        z = state.openness * (self.z_range / 10.0)

        # Clamp to field bounds
        x = max(-self.x_range, min(self.x_range, x))
        y = max(-self.y_range, min(self.y_range, y))
        z = max(-self.z_range, min(self.z_range, z))

        point = FieldPoint(
            x=round(x, 2),
            y=round(y, 2),
            z=round(z, 2),
            timestamp=state.timestamp.timestamp(),
            label=self._nearest_region(x, y, z),
            intensity=state.magnitude(),
        )

        self.current = point
        self.history.append(point)
        return point

    def _nearest_region(self, x: float, y: float, z: float) -> str:
        """Find the nearest named region to the given coordinates."""
        point = FieldPoint(x, y, z)
        nearest = min(self.REGIONS, key=lambda r: point.distance_to(r.center))
        if point.distance_to(nearest.center) < nearest.radius:
            return nearest.name
        return "Unmapped"

    def get_trajectory(self, window: int = 10) -> list[FieldPoint]:
        """Return the recent trajectory through the field."""
        return self.history[-window:]

    def get_field_vector(self) -> np.ndarray:
        """Return the current field position as a numpy array."""
        if self.current is None:
            return np.array([0.0, 0.0, 0.0])
        return np.array([self.current.x, self.current.y, self.current.z])

    def get_velocity(self, window: int = 5) -> np.ndarray:
        """Compute the velocity vector (direction of movement) from recent history."""
        traj = self.get_trajectory(window)
        if len(traj) < 2:
            return np.array([0.0, 0.0, 0.0])
        recent = np.array([[p.x, p.y, p.z] for p in traj[-window:]])
        return np.mean(np.diff(recent, axis=0), axis=0)

    def get_resonance(self, state: StateVector) -> dict:
        """Compute resonance scores with each field region."""
        point = self.state_to_field(state)
        resonance = {}
        for region in self.REGIONS:
            dist = point.distance_to(region.center)
            # Resonance = inverse distance, weighted by intensity
            score = region.intensity / (1.0 + dist)
            resonance[region.name] = round(score, 3)
        return resonance

    def get_probability_regions(self, threshold: float = 0.3) -> list[dict]:
        """Return regions where the user has spent significant time.

        Returns regions sorted by probability (time spent).
        """
        if not self.history:
            return []

        region_counts = {}
        for point in self.history:
            name = point.label
            region_counts[name] = region_counts.get(name, 0) + 1

        total = len(self.history)
        regions = []
        for name, count in region_counts.items():
            prob = count / total
            if prob >= threshold:
                regions.append({"name": name, "probability": round(prob, 3), "count": count})

        regions.sort(key=lambda r: r["probability"], reverse=True)
        return regions

    def reset(self):
        """Clear the field history."""
        self.history.clear()
        self.current = None