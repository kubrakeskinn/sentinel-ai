import unittest

from src.events.models import Event, EventSeverity, EventType
from src.summary.generator import EventSummaryGenerator


class TestEventSummaryGenerator(unittest.TestCase):
    def test_generates_summary_for_restricted_area_entry(self):
        generator = EventSummaryGenerator()
        event = Event(
            event_type=EventType.RESTRICTED_AREA_ENTRY,
            object_id=7,
            frame=10,
            speed=0.0,
            centroid=(1.0, 1.0),
            severity=EventSeverity.HIGH,
        )

        summary = generator.generate(event)

        self.assertIn("restricted area entry detected", summary)
        self.assertIn("object 7", summary)
        self.assertIn("severity: high", summary)
        self.assertIn("alert security", summary)

    def test_supports_other_event_types(self):
        generator = EventSummaryGenerator()
        event = Event(
            event_type=EventType.SUDDEN_STOP,
            object_id=2,
            frame=4,
            speed=0.0,
            centroid=(0.0, 0.0),
            severity=EventSeverity.HIGH,
        )

        summary = generator.generate(event)

        self.assertIn("sudden stop detected", summary)
        self.assertIn("object 2", summary)
        self.assertIn("severity: high", summary)


if __name__ == "__main__":
    unittest.main()
