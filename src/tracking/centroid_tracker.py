import numpy as np


class CentroidTracker:
    """Centroid + hız tahmini + IoU ile çoklu nesne takibi."""

    def __init__(self, max_disappeared=50, max_distance=120, min_iou=0.15):
        self.next_object_id = 0
        self.tracks = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.min_iou = min_iou

    def register(self, centroid, rect):
        self.tracks[self.next_object_id] = {
            "centroid": centroid,
            "rect": rect,
            "velocity": (0.0, 0.0),
            "disappeared": 0,
        }
        self.next_object_id += 1

    def deregister(self, object_id):
        del self.tracks[object_id]

    @staticmethod
    def _centroid(rect):
        x1, y1, x2, y2 = rect
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    @staticmethod
    def _rect_diagonal(rect):
        x1, y1, x2, y2 = rect
        return float(np.hypot(x2 - x1, y2 - y1))

    @staticmethod
    def _distance(a, b):
        return float(np.hypot(a[0] - b[0], a[1] - b[1]))

    @staticmethod
    def _iou(a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0

        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        union = area_a + area_b - inter_area

        if union <= 0:
            return 0.0
        return inter_area / union

    def _match_threshold(self, track_rect, input_rect):
        avg_diag = (self._rect_diagonal(track_rect) + self._rect_diagonal(input_rect)) / 2
        return max(self.max_distance, avg_diag * 0.75)

    def _predicted_centroid(self, track):
        cx, cy = track["centroid"]
        vx, vy = track["velocity"]
        return (cx + vx, cy + vy)

    def _update_track(self, object_id, centroid, rect):
        track = self.tracks[object_id]
        old_cx, old_cy = track["centroid"]
        vx, vy = track["velocity"]

        track["velocity"] = (
            0.6 * vx + 0.4 * (centroid[0] - old_cx),
            0.6 * vy + 0.4 * (centroid[1] - old_cy),
        )
        track["centroid"] = centroid
        track["rect"] = rect
        track["disappeared"] = 0

    def _is_match(self, track, input_centroid, input_rect):
        predicted = self._predicted_centroid(track)
        distance = self._distance(predicted, input_centroid)
        threshold = self._match_threshold(track["rect"], input_rect)
        iou = self._iou(track["rect"], input_rect)
        return distance <= threshold or iou >= self.min_iou

    def _match_cost(self, track, input_centroid, input_rect):
        predicted = self._predicted_centroid(track)
        distance = self._distance(predicted, input_centroid)
        threshold = self._match_threshold(track["rect"], input_rect)
        iou = self._iou(track["rect"], input_rect)
        return distance / max(threshold, 1.0) - iou

    def _find_reusable_track(self, input_centroid, input_rect):
        best_id = None
        best_cost = float("inf")

        for object_id, track in self.tracks.items():
            if track["disappeared"] == 0:
                continue
            if not self._is_match(track, input_centroid, input_rect):
                continue

            cost = self._match_cost(track, input_centroid, input_rect)
            cost += track["disappeared"] * 0.05
            if cost < best_cost:
                best_cost = cost
                best_id = object_id

        return best_id

    def update(self, rects):
        """
        rects: [(x1, y1, x2, y2), ...]
        Returns: [(object_id, (x1, y1, x2, y2)), ...]
        """
        if len(rects) == 0:
            for object_id in list(self.tracks):
                self.tracks[object_id]["disappeared"] += 1
                if self.tracks[object_id]["disappeared"] > self.max_disappeared:
                    self.deregister(object_id)
            return []

        input_centroids = [self._centroid(rect) for rect in rects]

        if not self.tracks:
            for centroid, rect in zip(input_centroids, rects):
                self.register(centroid, rect)
            return list(enumerate(rects))

        object_ids = list(self.tracks.keys())
        cost_matrix = np.zeros((len(object_ids), len(rects)), dtype=np.float32)

        for row, object_id in enumerate(object_ids):
            track = self.tracks[object_id]
            for col, (centroid, rect) in enumerate(zip(input_centroids, rects)):
                if self._is_match(track, centroid, rect):
                    cost_matrix[row, col] = self._match_cost(track, centroid, rect)
                else:
                    cost_matrix[row, col] = np.inf

        rows = cost_matrix.min(axis=1).argsort()
        cols = cost_matrix.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()
        assignments = []

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if not np.isfinite(cost_matrix[row, col]):
                continue

            object_id = object_ids[row]
            self._update_track(object_id, input_centroids[col], rects[col])
            assignments.append((object_id, rects[col]))
            used_rows.add(row)
            used_cols.add(col)

        unused_rows = set(range(len(object_ids))) - used_rows
        unused_cols = set(range(len(rects))) - used_cols

        for row in unused_rows:
            object_id = object_ids[row]
            self.tracks[object_id]["disappeared"] += 1
            if self.tracks[object_id]["disappeared"] > self.max_disappeared:
                self.deregister(object_id)

        for col in unused_cols:
            centroid = input_centroids[col]
            rect = rects[col]
            reusable_id = self._find_reusable_track(centroid, rect)

            if reusable_id is not None:
                self._update_track(reusable_id, centroid, rect)
                assignments.append((reusable_id, rect))
            else:
                self.register(centroid, rect)
                assignments.append((self.next_object_id - 1, rect))

        return assignments
