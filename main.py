import argparse
import cv2

from src.detection.yolo_detector import YOLODetector
from src.events import EventEngine
from src.tracking import CentroidTracker

CONF_THRESHOLD = 0.3
MODEL_PATH = "yolov8n.pt"
OUTPUT_PATH = "data/output/output.mp4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sentinel AI video demo")
    parser.add_argument("--video", required=True, help="Path to input video file")
    return parser.parse_args()


def normalize_rects(detections):
    rects = []

    for det in detections:
        # Case 1: (x1,y1,x2,y2)
        if isinstance(det, tuple) and len(det) == 4:
            rects.append(tuple(map(int, det)))

        # Case 2: (class_id, conf, bbox)
        elif isinstance(det, tuple) and len(det) == 3:
            rect = det[2]
            if isinstance(rect, tuple) and len(rect) == 4:
                rects.append(tuple(map(int, rect)))

    return rects


def draw_annotations(frame, tracks, events):
    event_labels = {}

    for event in events:
        if hasattr(event, "object_id"):
            event_labels.setdefault(event.object_id, []).append(
                str(event.event_type)
            )

    for object_id, rect in tracks:
        x1, y1, x2, y2 = rect

        label_parts = [f"ID {object_id}"]
        color = (0, 255, 0)

        if object_id in event_labels:
            label_parts.extend(event_labels[object_id])
            color = (0, 0, 255)

        label_text = " | ".join(label_parts)
        text_y = y1 - 10 if y1 > 20 else y1 + 20

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            label_text,
            (x1, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )


def main() -> None:
    args = parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video file: {args.video}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps is None or fps <= 0:
        fps = 30.0

    writer = cv2.VideoWriter(
        OUTPUT_PATH,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Unable to open output file: {OUTPUT_PATH}")

    detector = YOLODetector(MODEL_PATH, CONF_THRESHOLD)
    tracker = CentroidTracker(max_disappeared=50, max_distance=120)
    event_engine = EventEngine()

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        detections = detector.detect(frame)
        rects = normalize_rects(detections)
        tracks = tracker.update(rects)

        track_inputs = []
        for object_id, rect in tracks:
            x1, y1, x2, y2 = rect
            centroid = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
            track_inputs.append((object_id, centroid, rect))

        events = event_engine.update(track_inputs)

        # ✅ Terminal log (her 10 frame'de bir)
        if frame_count % 10 == 0:
            print(
                f"Frame {frame_count} | "
                f"Detections: {len(detections)} | "
                f"Tracks: {len(tracks)} | "
                f"Events: {len(events)}"
            )

        draw_annotations(frame, tracks, events)
        writer.write(frame)

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    print("\n✅ Processing complete.")
    print(f"📁 Output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()