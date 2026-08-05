from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, List, Optional, Tuple


Centroid = Tuple[float, float]
Rect = Tuple[int, int, int, int]
TrackInput = Tuple[int, Centroid, Rect]


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


@dataclass
class EventEngineConfig:
    history_size: int = 60
    smoothing_window: int = 5
    rapid_speed_threshold: float = 25.0
    rapid_min_frames: int = 3
    loiter_speed_threshold: float = 3.0
    loiter_min_frames: int = 45
    sudden_stop_prev_speed_threshold: float = 20.0
    sudden_stop_current_speed_threshold: float = 3.0
    cooldown_frames: int = 20


@dataclass
class _TrackState:
    centroids: Deque[Centroid] = field(default_factory=lambda: deque(maxlen=60))
    speeds: Deque[float] = field(default_factory=lambda: deque(maxlen=60))
    loiter_frames: int = 0
    rapid_frames: int = 0
    last_event_frame: Dict[EventType, int] = field(default_factory=dict)


class EventEngine:
    def __init__(self, config: Optional[EventEngineConfig] = None):
        self.config = config or EventEngineConfig()
        self._tracks: Dict[int, _TrackState] = {}
        self._frame = 0

    def update(self, tracks: List[TrackInput]) -> List[Event]:
        self._frame += 1
        events: List[Event] = []
        active_ids = {object_id for object_id, _, _ in tracks}

        for object_id, centroid, rect in tracks:
            state = self._get_or_create_state(object_id)
            self._append_observation(state, centroid)
            smoothed_speed = self._smoothed_speed(state)

            events.extend(self._detect_rapid_movement(object_id, state, smoothed_speed, centroid, rect))
            events.extend(self._detect_loitering(object_id, state, smoothed_speed, centroid, rect))
            events.extend(self._detect_sudden_stop(object_id, state, smoothed_speed, centroid, rect))

        self._prune_inactive(active_ids)
        return events

    def reset(self) -> None:
        self._tracks.clear()
        self._frame = 0

    def _get_or_create_state(self, object_id: int) -> _TrackState:
        if object_id not in self._tracks:
            track_state = _TrackState(
                centroids=deque(maxlen=self.config.history_size),
                speeds=deque(maxlen=self.config.history_size),
            )
            self._tracks[object_id] = track_state
        return self._tracks[object_id]

    def _append_observation(self, state: _TrackState, centroid: Centroid) -> None:
        if state.centroids:
            prev = state.centroids[-1]
            speed = self._distance(prev, centroid)
            state.speeds.append(speed)
        state.centroids.append(centroid)

    def _smoothed_speed(self, state: _TrackState) -> float:
        if not state.speeds:
            return 0.0

        window = list(state.speeds)[-self.config.smoothing_window :]
        return sum(window) / len(window)

    def _previous_smoothed_speed(self, state: _TrackState) -> float:
        if len(state.speeds) < 2:
            return 0.0

        end = len(state.speeds) - 1
        start = max(0, end - self.config.smoothing_window)
        window = list(state.speeds)[start:end]
        if not window:
            return 0.0
        return sum(window) / len(window)

    def _detect_rapid_movement(
        self,
        object_id: int,
        state: _TrackState,
        smoothed_speed: float,
        centroid: Centroid,
        rect: Rect,
    ) -> List[Event]:
        if smoothed_speed >= self.config.rapid_speed_threshold:
            state.rapid_frames += 1
        else:
            state.rapid_frames = 0

        if state.rapid_frames < self.config.rapid_min_frames:
            return []

        if not self._can_emit(state, EventType.RAPID_MOVEMENT):
            return []

        state.last_event_frame[EventType.RAPID_MOVEMENT] = self._frame
        return [
            Event(
                event_type=EventType.RAPID_MOVEMENT,
                object_id=object_id,
                frame=self._frame,
                speed=smoothed_speed,
                centroid=centroid,
                metadata={
                    "threshold": self.config.rapid_speed_threshold,
                    "consecutive_frames": float(state.rapid_frames),
                    "bbox_width": float(rect[2] - rect[0]),
                    "bbox_height": float(rect[3] - rect[1]),
                },
            )
        ]

    def _detect_loitering(
        self,
        object_id: int,
        state: _TrackState,
        smoothed_speed: float,
        centroid: Centroid,
        rect: Rect,
    ) -> List[Event]:
        if smoothed_speed <= self.config.loiter_speed_threshold:
            state.loiter_frames += 1
        else:
            state.loiter_frames = 0

        if state.loiter_frames < self.config.loiter_min_frames:
            return []

        if not self._can_emit(state, EventType.LOITERING):
            return []

        state.last_event_frame[EventType.LOITERING] = self._frame
        return [
            Event(
                event_type=EventType.LOITERING,
                object_id=object_id,
                frame=self._frame,
                speed=smoothed_speed,
                centroid=centroid,
                metadata={
                    "threshold": self.config.loiter_speed_threshold,
                    "duration_frames": float(state.loiter_frames),
                    "bbox_width": float(rect[2] - rect[0]),
                    "bbox_height": float(rect[3] - rect[1]),
                },
            )
        ]

    def _detect_sudden_stop(
        self,
        object_id: int,
        state: _TrackState,
        smoothed_speed: float,
        centroid: Centroid,
        rect: Rect,
    ) -> List[Event]:
        previous_speed = self._previous_smoothed_speed(state)

        is_sudden_stop = (
            previous_speed >= self.config.sudden_stop_prev_speed_threshold
            and smoothed_speed <= self.config.sudden_stop_current_speed_threshold
        )

        if not is_sudden_stop:
            return []

        if not self._can_emit(state, EventType.SUDDEN_STOP):
            return []

        state.last_event_frame[EventType.SUDDEN_STOP] = self._frame
        return [
            Event(
                event_type=EventType.SUDDEN_STOP,
                object_id=object_id,
                frame=self._frame,
                speed=smoothed_speed,
                centroid=centroid,
                metadata={
                    "previous_speed": previous_speed,
                    "current_speed": smoothed_speed,
                    "prev_speed_threshold": self.config.sudden_stop_prev_speed_threshold,
                    "stop_speed_threshold": self.config.sudden_stop_current_speed_threshold,
                    "bbox_width": float(rect[2] - rect[0]),
                    "bbox_height": float(rect[3] - rect[1]),
                },
            )
        ]

    def _can_emit(self, state: _TrackState, event_type: EventType) -> bool:
        last_frame = state.last_event_frame.get(event_type)
        if last_frame is None:
            return True
        return (self._frame - last_frame) >= self.config.cooldown_frames

    def _prune_inactive(self, active_ids: set[int]) -> None:
        inactive_ids = set(self._tracks) - active_ids
        for object_id in inactive_ids:
            del self._tracks[object_id]

    @staticmethod
    def _distance(a: Centroid, b: Centroid) -> float:
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        return float((dx * dx + dy * dy) ** 0.5)
