# Sentinel AI 🚨

AI-Powered Video Surveillance & Event Detection System

---

## Overview

Sentinel AI is an AI-based computer vision system designed for real-time video analysis, object tracking, and behavior-driven event detection.

The system processes video streams (live or recorded) and transforms raw visual data into actionable insights by identifying human activity, tracking movement patterns, and detecting security-relevant events.

This project is developed as a defense-oriented prototype focusing on scalable, modular, and real-time AI systems.

---

## Key Features

### 🎯 Real-Time Detection & Tracking
- Human detection using YOLOv8
- Multi-object tracking with persistent IDs
- Confidence-based filtering
- Stable tracking across frames

### 🧠 Event Detection Engine
- Loitering detection
- Movement-based anomaly detection
- Sudden behavior changes
- Event triggering with object-level association

### 🎥 Video Processing Pipeline
- Works with recorded video files
- Frame-by-frame processing
- Annotated output video generation
- Bounding boxes + object IDs + event labels

### 📊 Intelligent Output
- Real-time statistics (object count, events)
- Event-aware visual annotations
- Structured event signals for future reporting systems

---

## System Architecture
Video Input
↓
Frame Processing
↓
YOLOv8 Detection
↓
Object Tracking (Centroid-based)
↓
Event Detection Engine
↓
Annotated Video Output

The system is modular, allowing independent improvements in detection, tracking, or event analysis without redesigning the entire pipeline.

---

## Demo

The system processes input video and generates an annotated output including:

- Bounding boxes
- Object IDs
- Event labels
- Real-time object count

Example capabilities observed:

- Multi-person tracking (5–10 individuals)
- Stable ID assignment across frames
- Event triggering in dynamic crowd scenarios

---

## Technology Stack

- Python
- PyTorch
- YOLOv8 (Ultralytics)
- OpenCV
- Custom Centroid-Based Tracking
- Streamlit (for visualization)
- Git

---

## Project Structure
sentinel-ai/
│
├── src/
│ ├── detection/ # YOLO-based detection
│ ├── tracking/ # Object tracking logic
│ ├── events/ # Event detection engine
│ ├── summary/ # Event summarization
│ └── video/ # Video processing utilities
│
├── app/ # Streamlit demo
├── tests/ # Unit tests
├── main.py # Entry point
├── requirements.txt
└── README.md

---

## How to Run

```bash
python main.py --video data/videos/test.mp4

Output will be saved to:
data/output/output.mp4

## Purpose

Sentinel AI explores how modern AI and computer vision can transform raw surveillance footage into meaningful operational intelligence.

The long-term vision is to build intelligent monitoring systems capable of supporting security, defense, and situational awareness applications.