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

    def test_no_polygon_configured_no_restricted_area_events(self):
        engine = EventEngine(EventEngineConfig(cooldown_frames=0))
        events = engine.update([(1, (3.0, 1.0), (0.0, 0.0, 2.0, 2.0))])

        self.assertEqual(events, [])

    def test_restricted_area_entry_event_when_track_enters_zone(self):
        config = EventEngineConfig(
            cooldown_frames=0,
            restricted_zone_polygon=[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)],
        )
        engine = EventEngine(config)

        engine.update([(1, (3.0, 1.0), (0.0, 0.0, 2.0, 2.0))])
        events = engine.update([(1, (1.0, 1.0), (0.0, 0.0, 2.0, 2.0))])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, EventType.RESTRICTED_AREA_ENTRY)
        self.assertEqual(events[0].object_id, 1)
        self.assertEqual(events[0].centroid, (1.0, 1.0))

    def test_restricted_area_exit_event_when_track_leaves_zone(self):
        config = EventEngineConfig(
            cooldown_frames=0,
            restricted_zone_polygon=[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)],
        )
        engine = EventEngine(config)

        engine.update([(1, (1.0, 1.0), (0.0, 0.0, 2.0, 2.0))])
        events = engine.update([(1, (3.0, 1.0), (0.0, 0.0, 2.0, 2.0))])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, EventType.RESTRICTED_AREA_EXIT)
        self.assertEqual(events[0].object_id, 1)
        self.assertEqual(events[0].centroid, (3.0, 1.0))

    def test_staying_inside_zone_does_not_emit_duplicate_entry(self):
        config = EventEngineConfig(
            cooldown_frames=0,
            restricted_zone_polygon=[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)],
        )
        engine = EventEngine(config)

        first_events = engine.update([(1, (1.0, 1.0), (0.0, 0.0, 2.0, 2.0))])
        second_events = engine.update([(1, (1.2, 1.0), (0.0, 0.0, 2.0, 2.0))])

        self.assertEqual(len(first_events), 1)
        self.assertEqual(first_events[0].event_type, EventType.RESTRICTED_AREA_ENTRY)
        self.assertEqual(second_events, [])


if __name__ == "__main__":
    unittest.main()
