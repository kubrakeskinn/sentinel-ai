from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

from src.core.types import Centroid, Rect, TrackInput
from src.events.models import Event, EventType


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
    restricted_zone_polygon: Optional[List[Tuple[float, float]]] = None


@dataclass
class _TrackState:
    centroids: Deque[Centroid] = field(default_factory=lambda: deque(maxlen=60))
    speeds: Deque[float] = field(default_factory=lambda: deque(maxlen=60))
    loiter_frames: int = 0
    rapid_frames: int = 0
    inside_restricted_zone: bool = False
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
            events.extend(self._detect_restricted_area(object_id, state, centroid))

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

    def _detect_restricted_area(self, object_id: int, state: _TrackState, centroid: Centroid) -> List[Event]:
        if not self.config.restricted_zone_polygon:
            return []

        is_inside = self._point_in_polygon(centroid, self.config.restricted_zone_polygon)
        if is_inside == state.inside_restricted_zone:
            return []

        state.inside_restricted_zone = is_inside
        event_type = EventType.RESTRICTED_AREA_ENTRY if is_inside else EventType.RESTRICTED_AREA_EXIT
        return [
            Event(
                event_type=event_type,
                object_id=object_id,
                frame=self._frame,
                speed=0.0,
                centroid=centroid,
                metadata={},
            )
        ]

    @staticmethod
    def _point_in_polygon(point: Centroid, polygon: List[Tuple[float, float]]) -> bool:
        x, y = point
        inside = False
        for i in range(len(polygon)):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]
            intersects = ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1)
            if intersects:
                inside = not inside
        return inside

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
