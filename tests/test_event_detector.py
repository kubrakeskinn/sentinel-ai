import unittest

from src.events.event_detector import EventDetector, TrackedObject


class TestEventDetectorLoitering(unittest.TestCase):
    def _make_track(self, positions, first_seen, last_seen):
        return TrackedObject(
            position_history=positions,
            first_seen=first_seen,
            last_seen=last_seen,
        )

    def test_loitering_false_when_duration_below_threshold(self):
        detector = EventDetector(loiter_duration_threshold=5.0, loiter_movement_threshold=10.0)
        detector.track_history[7] = self._make_track(
            positions=[(0.0, 0.0), (0.1, 0.0)],
            first_seen=1.0,
            last_seen=4.0,
        )

        self.assertFalse(detector.detect_loitering(7))

    def test_loitering_false_when_movement_above_threshold(self):
        detector = EventDetector(loiter_duration_threshold=5.0, loiter_movement_threshold=10.0)
        detector.track_history[8] = self._make_track(
            positions=[(0.0, 0.0), (20.0, 0.0)],
            first_seen=1.0,
            last_seen=6.0,
        )

        self.assertFalse(detector.detect_loitering(8))

    def test_loitering_true_when_duration_and_movement_conditions_are_met(self):
        detector = EventDetector(loiter_duration_threshold=5.0, loiter_movement_threshold=10.0)
        detector.track_history[9] = self._make_track(
            positions=[(0.0, 0.0), (0.2, 0.0), (0.4, 0.0)],
            first_seen=1.0,
            last_seen=6.5,
        )

        self.assertTrue(detector.detect_loitering(9))


if __name__ == "__main__":
    unittest.main()
