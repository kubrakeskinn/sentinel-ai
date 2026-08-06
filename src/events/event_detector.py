from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from src.core.types import Centroid


@dataclass
class TrackedObject:
    position_history: List[Centroid] = field(default_factory=list)
    first_seen: float = 0.0
    last_seen: float = 0.0


class EventDetector:
    def __init__(self, max_positions: int = 30) -> None:
        self.track_history: Dict[int, TrackedObject] = {}
        self.max_positions = max_positions

    def update(self, tracks: List[Tuple[int, Centroid, Tuple[float, float, float, float]]]) -> None:
        timestamp = time.time()

        for track_id, centroid, _bbox in tracks:
            if track_id not in self.track_history:
                self.track_history[track_id] = TrackedObject(
                    position_history=[centroid],
                    first_seen=timestamp,
                    last_seen=timestamp,
                )
                continue

            obj = self.track_history[track_id]
            obj.position_history.append(centroid)
            if len(obj.position_history) > self.max_positions:
                obj.position_history = obj.position_history[-self.max_positions :]
            obj.last_seen = timestamp

    def reset(self) -> None:
        self.track_history.clear()
