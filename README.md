# Sentinel AI 🚨

**Sentinel AI** is an AI-powered security and defense prototype for video analysis, object tracking, and behavior-driven event detection.

---

## Overview

Sentinel AI is a modern computer vision platform built to transform video footage into operational intelligence. It combines real-time object detection, centroid-based tracking, and event analysis to identify suspicious behavior and produce annotated output video for security-focused applications.

This project is designed as a defense-oriented prototype, emphasizing a clean, extensible pipeline for surveillance, monitoring, and situational awareness.

---

## Key Features

- **🎯 YOLOv8 Object Detection**
  - Human/object detection using YOLOv8
  - Confidence-based filtering for robust results

- **🧭 Centroid-Based Tracking**
  - Persistent track IDs across frames
  - Simple, stable multi-object tracking

- **⚠️ Behavior & Event Detection**
  - Loitering detection
  - Rapid movement and sudden stop detection
  - Object-level event association

- **🎥 Annotated Video Output**
  - Frame-by-frame annotation
  - Bounding boxes, IDs, and event labels
  - Saved processed video output

---

## System Architecture

```text
Video Input
     ↓
Frame Capture
     ↓
YOLOv8 Detection
     ↓
Centroid Tracking
     ↓
Event Engine Update
     ↓
Frame Annotation
     ↓
Annotated Video Output
```

---

## Tech Stack

- **Python**
- **PyTorch** via Ultralytics YOLOv8
- **YOLOv8**
- **OpenCV**
- **NumPy**
- **Streamlit** for demo visualization
- **Git**

---

## Project Structure

```text
sentinel-ai/
│
├── app/
│   └── streamlit_app.py
│
├── data/
│   ├── output/
│   └── videos/
│
├── src/
│   ├── core/
│   │   └── types.py
│   ├── detection/
│   │   └── yolo_detector.py
│   ├── events/
│   │   ├── event_engine.py
│   │   ├── event_detector.py
│   │   ├── models.py
│   │   └── __init__.py
│   ├── summary/
│   │   └── generator.py
│   ├── tracking/
│   │   └── centroid_tracker.py
│   └── video/
│       └── __init__.py
│
├── tests/
│   ├── test_event_detector.py
│   ├── test_event_engine.py
│   ├── test_imports.py
│   └── test_summary_generator.py
│
├── main.py
├── README.md
├── requirements.txt
└── yolov8n.pt
```

---

## How to Run

1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the video processing demo:

```bash
python main.py --video data/videos/test.mp4
```

4. View the annotated result:

```text
data/output/output.mp4
```

---

## Purpose & Vision

Sentinel AI aims to advance operational intelligence for defense and security systems by turning raw video into actionable alerts and event-aware visual output.

The vision is to evolve this prototype into a trusted situational awareness platform that supports intelligent monitoring, anomaly detection, and security decision support across defense, critical infrastructure, and public safety domains.
