from __future__ import annotations

from typing import List, Tuple
from ultralytics import YOLO


class YOLODetector:
    def __init__(self, model_path: str, confidence_threshold: float) -> None:
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = YOLO(model_path)

    def detect(self, frame) -> List[Tuple[int, int, int, int]]:
        results = self.model(frame, verbose=False)[0]

        boxes: List[Tuple[int, int, int, int]] = []

        if results.boxes is None:
            return []

        for box in results.boxes:
            confidence = float(box.conf[0])
            cls_id = int(box.cls[0])

            
            if confidence < self.confidence_threshold:
                continue

            
            if cls_id != 0:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            boxes.append((x1, y1, x2, y2))

        return boxes