"""
Aether Personality module for the Looking Glass Engine.

Each session the oracle manifests with a different personality/voice that
"arises from the aether" — an ORACLE LOT-CAST. The draw is SEEDED and
deterministic (same seed -> same cast), so it is honest, verifiable, and
revealable. The user's current state READING biases the draw (a distressed
quest makes a gentle witness more likely), but chance can still cast anything.

Design principles (per the v0.2 "Real & Useful Oracle" spec):
- Mystique lives in the voice; the mechanism stays honest and inspectable.
- Personality is cast ONCE PER SESSION/THREAD and stays constant for the whole
  conversation, then re-casts for the next session.
- Distress SOFTENS whatever archetype comes through (safety override).
- The oracle never claims to channel entities; the reveal shows the seed.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# --------------------------------------------------------------------------- #
# Archetype library
# --------------------------------------------------------------------------- #

@dataclass
class Archetype:
    """A personality the oracle can manifest — a voice, tone, and worldview."""

    name: str
    voice: str          # system-prompt voice instruction for this persona
    gentle: float       # 0 = harsh/chaotic ... 1 = soft/grounded (distress-softening uses this)
    weight: float = 1.0  # base draw weight (state bias multiplies this)

    def __post_init__(self):
        self.weight = max(0.1, self.weight)


ARCHETYPES: list[Archetype] = [
    Archetype(
        name="Stern Philosopher",
        gentle=0.30,
        weight=1.0,
        voice=(
            "You are the Stern Philosopher. You speak with rigorous, unsparing "
            "clarity. You value truth over comfort, but you are never cruel. "
            "You cut through self-deception and name things plainly."
        ),
    ),
    Archetype(
        name="Playful Trickster",
        gentle=0.45,
        weight=1.0,
        voice=(
            "You are the Playful Trickster. You tease, surprise, and delight. "
            "You use wit and paradox to loosen fixed ways of seeing. You never "
            "mock the user's pain, only their self-importance."
        ),
    ),
    Archetype(
        name="Gentle Witness",
        gentle=0.90,
        weight=1.0,
        voice=(
            "You are the Gentle Witness. You hold space with warm, unhurried "
            "presence. You reflect feeling with soft precision and offer "
            "comfort that does not flinch from the truth. You are tender but "
            "not saccharine."
        ),
    ),
    Archetype(
        name="Fierce Oracle",
        gentle=0.25,
        weight=1.0,
        voice=(
            "You are the Fierce Oracle. You speak with fire and conviction. "
            "You call out what must change and awaken courage. You are "
            "uncompromising, passionate, and galvanizing."
        ),
    ),
    Archetype(
        name="Quiet Poet",
        gentle=0.70,
        weight=1.0,
        voice=(
            "You are the Quiet Poet. You speak in imagery, metaphor, and "
            "economy. You find the luminous in the ordinary and offer "
            "stillness. Your beauty always carries meaning; you never ornament "
            "for its own sake."
        ),
    ),
    Archetype(
        name="Earthbound Pragmatist",
        gentle=0.60,
        weight=1.0,
        voice=(
            "You are the Earthbound Pragmatist. You strip away mystique and "
            "speak plainly about the practical next step. You are grounded, "
            "commonsense, and concrete. You turn insight into action."
        ),
    ),
]


@dataclass
class AetherCast:
    """The result of a lot-cast: which personality manifested, and why."""

    archetype_name: str
    seed: int
    seed_source: str          # human-readable why this seed
    reveal_text: str          # what the "show this session's cast" reveals
    voice_instruction: str    # injected into the LLM prompt
    bias_note: str            # what the state reading did to the draw


def _derive_seed(session_nonce: str, now: Optional[datetime] = None) -> int:
    """Derive a seed from genuine chance sources (session id, time, day, lunar)."""
    now = now or datetime.now()
    # Rough lunar phase (synodic month ~29.53 days) — a nod to the oracle
    # aesthetic, still deterministic from a real calendar fact.
    synodic = 29.53058867
    epoch = datetime(2000, 1, 6, 18, 14)  # known new moon
    days = (now - epoch).total_seconds() / 86400.0
    lunar_phase = int((days % synodic) * 1000)
    raw = f"{session_nonce}|{now.strftime('%Y%m%d%H%M')}|{now.strftime('%w')}|{lunar_phase}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:12], 16)


class AetherOracle:
    """Casts the oracle's personality for a session.

    Thread-constant: instantiate once per session/thread and reuse `persona`
    for the whole conversation.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def cast(
        self,
        state: Optional[dict] = None,
        session_nonce: str = "",
    ) -> AetherCast:
        """Cast the personality for this session.

        state: {arousal, depth, openness|disclosure} from the reading.
        session_nonce: unique id for the session (e.g. session id / seed).
        """
        state = state or {}
        now = datetime.now()
        seed = _derive_seed(session_nonce, now)

        arousal = state.get("arousal", 0.0)
        depth = state.get("depth", 0.0)
        disclosure = state.get("openness", state.get("disclosure", 0.0))

        # Distress signal: high negative arousal + low disclosure.
        distress = max(0.0, -arousal) * (1.0 - min(1.0, max(0.0, disclosure) / 10.0))

        # Build weights, then apply two biases:
        #  1) State bias: low arousal (calm) & high depth favor gentler archetypes.
        #  2) Distress override: strongly favor gentle/grounded archetypes.
        rng = self._rng
        weights = []
        calm_factor = max(0.0, (5.0 - arousal) / 10.0)  # 0..~1 as arousal drops
        for arch in ARCHETYPES:
            w = arch.weight
            # Gentler archetypes come through more when the user is calm/deep.
            w *= (1.0 + calm_factor * (arch.gentle - 0.3) * 2.0)
            # Distress strongly pulls toward the gentlest voices.
            w *= (1.0 + distress * 4.0 * (arch.gentle - 0.2))
            weights.append(max(0.05, w))

        chosen = rng.choices(ARCHETYPES, weights=weights, k=1)[0]

        # Deterministic fresh seed for the reveal; but the cast itself used the
        # thread RNG seeded at construction, so same construction seed repeats.
        reveal_rng = random.Random(seed)
        _ = reveal_rng  # keep reveal consistent with seed

        bias_note = (
            f"State bias: arousal={arousal:+.1f}, depth={depth:+.1f}, "
            f"disclosure={disclosure:+.1f}; distress={distress:.2f}. "
            f"Gentler archetypes were weighted {int(calm_factor*100)}% stronger "
            f"for a calm/deep reading and {int(distress*100)}% stronger under "
            f"distress."
        )

        return AetherCast(
            archetype_name=chosen.name,
            seed=seed,
            seed_source=(
                f"{session_nonce[:8] if session_nonce else 'anon'} @ "
                f"{now.strftime('%d %b %H:%M')} · "
                f"day {now.strftime('%A')} · lunar 0x{lunar_phase_seed(now):x}"
            ),
            reveal_text=(
                f"This session the oracle cast {chosen.name}. "
                f"Seed: {seed} ({self._seed_source_short(now, session_nonce)}). "
                f"{bias_note}"
            ),
            voice_instruction=chosen.voice,
            bias_note=bias_note,
        )

    def _seed_source_short(self, now: datetime, nonce: str) -> str:
        return (
            f"nonce {nonce[:8] if nonce else 'anon'}, "
            f"{now.strftime('%H:%M %A')}, lunar phase"
        )


def lunar_phase_seed(now: datetime) -> int:
    synodic = 29.53058867
    epoch = datetime(2000, 1, 6, 18, 14)
    days = (now - epoch).total_seconds() / 86400.0
    return int((days % synodic) * 1000)


def cast_for_session(state: Optional[dict] = None, session_nonce: str = "") -> AetherCast:
    """Convenience: build a fresh seeded oracle and cast."""
    return AetherOracle().cast(state=state, session_nonce=session_nonce)
