import unittest


class TestSrcImports(unittest.TestCase):
    def test_tracking_import(self):
        from src.tracking import CentroidTracker

        self.assertTrue(callable(CentroidTracker))

    def test_events_import(self):
        from src.events import EventEngine

        self.assertTrue(callable(EventEngine))

    def test_legacy_tracker_shim(self):
        from tracker import CentroidTracker

        self.assertTrue(callable(CentroidTracker))

    def test_legacy_events_shim(self):
        from events import EventEngine, EventType

        self.assertTrue(callable(EventEngine))
        self.assertEqual(EventType.RAPID_MOVEMENT.value, "rapid_movement")


if __name__ == "__main__":
    unittest.main()
