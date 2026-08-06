import cv2

from events import EventEngine, EventType
from src.detection.yolo_detector import YOLODetector
from tracker import CentroidTracker

CONF_THRESHOLD = 0.5
EVENT_COLORS = {
    EventType.RAPID_MOVEMENT: (0, 0, 255),
    EventType.LOITERING: (255, 165, 0),
    EventType.SUDDEN_STOP: (255, 0, 255),
}

detector = YOLODetector("yolov8n.pt", CONF_THRESHOLD)
tracker = CentroidTracker(max_disappeared=50, max_distance=120)
event_engine = EventEngine()

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    rects = detector.detect(frame)

    tracks = tracker.update(rects)

    track_inputs = []
    for object_id, (x1, y1, x2, y2) in tracks:
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        track_inputs.append((object_id, (cx, cy), (x1, y1, x2, y2)))

    events = event_engine.update(track_inputs)
    active_event_types = {(event.object_id, event.event_type) for event in events}

    for object_id, (x1, y1, x2, y2) in tracks:
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        label = f"ID {object_id}"
        color = (0, 255, 0)
        for event_type in EventType:
            if (object_id, event_type) in active_event_types:
                label += f" | {event_type.value}"
                color = EVENT_COLORS[event_type]
                break

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.circle(frame, (cx, cy), 4, color, -1)
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    cv2.imshow("Sentinel AI", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
