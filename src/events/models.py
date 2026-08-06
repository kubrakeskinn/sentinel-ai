from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

from src.core.types import Centroid


class EventType(str, Enum):
    RAPID_MOVEMENT = "rapid_movement"
    LOITERING = "loitering"
    SUDDEN_STOP = "sudden_stop"


@dataclass(frozen=True)
class Event:
    event_type: EventType
    object_id: int
    frame: int
    speed: float
    centroid: Centroid
    metadata: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.value,
            "object_id": self.object_id,
            "frame": self.frame,
            "speed": round(self.speed, 3),
            "centroid": (round(self.centroid[0], 1), round(self.centroid[1], 1)),
            "metadata": {key: round(value, 3) for key, value in self.metadata.items()},
        }
