from ultralytics import YOLO
import cv2

# modeli yükle
model = YOLO("yolov8n.pt")

# kamera aç
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # nesne tespiti
    results = model(frame)

    # tespitleri görüntüye çiz
    annotated_frame = results[0].plot()

    cv2.imshow("Sentinel AI", annotated_frame)

    # ESC ile çıkış
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()