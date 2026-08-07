from __future__ import annotations

from src.events.models import Event, EventSeverity, EventType


class EventSummaryGenerator:
    def generate(self, event: Event) -> str:
        descriptions = {
            EventType.RAPID_MOVEMENT: "rapid movement detected",
            EventType.LOITERING: "loitering detected",
            EventType.SUDDEN_STOP: "sudden stop detected",
            EventType.RESTRICTED_AREA_ENTRY: "restricted area entry detected",
            EventType.RESTRICTED_AREA_EXIT: "restricted area exit detected",
        }

        actions = {
            EventType.RAPID_MOVEMENT: "inspect the subject and verify the movement context",
            EventType.LOITERING: "monitor the area and confirm whether the subject is stationary",
            EventType.SUDDEN_STOP: "check for a possible incident or obstruction",
            EventType.RESTRICTED_AREA_ENTRY: "alert security and secure the restricted zone",
            EventType.RESTRICTED_AREA_EXIT: "review the exit path and verify perimeter control",
        }

        description = descriptions.get(event.event_type, event.event_type.value)
        action = actions.get(event.event_type, "review the event context")
        severity = event.severity.value if isinstance(event.severity, EventSeverity) else str(event.severity)

        return (
            f"{description} for object {event.object_id}; "
            f"severity: {severity}; action: {action}"
        )
