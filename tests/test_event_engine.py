import unittest

from src.events.event_engine import EventEngine, EventEngineConfig
from src.events.models import EventType


class TestEventEngine(unittest.TestCase):
    def test_loitering_event_generated_for_stationary_track(self):
        config = EventEngineConfig(
            history_size=5,
            smoothing_window=1,
            loiter_speed_threshold=1.0,
            loiter_min_frames=3,
            cooldown_frames=0,
        )
        engine = EventEngine(config)

        tracks = [
            (1, (0.0, 0.0), (0.0, 0.0, 2.0, 2.0)),
            (1, (0.1, 0.0), (0.0, 0.0, 2.0, 2.0)),
            (1, (0.1, 0.1), (0.0, 0.0, 2.0, 2.0)),
        ]

        events = engine.update(tracks)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, EventType.LOITERING)
        self.assertEqual(events[0].object_id, 1)
        self.assertEqual(events[0].centroid, (0.1, 0.1))

    def test_rapid_movement_event_generated_when_speed_threshold_exceeded(self):
        config = EventEngineConfig(
            history_size=5,
            smoothing_window=1,
            rapid_speed_threshold=1.0,
            rapid_min_frames=2,
            cooldown_frames=0,
        )
        engine = EventEngine(config)

        tracks = [
            (1, (0.0, 0.0), (0.0, 0.0, 2.0, 2.0)),
            (1, (3.0, 0.0), (0.0, 0.0, 2.0, 2.0)),
            (1, (6.0, 0.0), (0.0, 0.0, 2.0, 2.0)),
        ]

        events = engine.update(tracks)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, EventType.RAPID_MOVEMENT)
        self.assertEqual(events[0].object_id, 1)
        self.assertEqual(events[0].centroid, (6.0, 0.0))

    def test_sudden_stop_event_generated_when_speed_drops_significantly(self):
        config = EventEngineConfig(
            history_size=5,
            smoothing_window=1,
            sudden_stop_prev_speed_threshold=1.0,
            sudden_stop_current_speed_threshold=0.2,
            cooldown_frames=0,
        )
        engine = EventEngine(config)

        tracks = [
            (1, (0.0, 0.0), (0.0, 0.0, 2.0, 2.0)),
            (1, (3.0, 0.0), (0.0, 0.0, 2.0, 2.0)),
            (1, (3.0, 0.0), (0.0, 0.0, 2.0, 2.0)),
        ]

        events = engine.update(tracks)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, EventType.SUDDEN_STOP)
        self.assertEqual(events[0].object_id, 1)
        self.assertEqual(events[0].centroid, (3.0, 0.0))


if __name__ == "__main__":
    unittest.main()
