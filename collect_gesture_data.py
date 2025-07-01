import cv2
from cvzone.HandTrackingModule import HandDetector
import pandas as pd
import os

# Create or append to a CSV file
CSV_FILENAME = "gesture_data.csv"
columns = [f"x{i},y{i},z{i}" for i in range(21)] + ["label"]

if not os.path.exists(CSV_FILENAME):
    df = pd.DataFrame(columns=columns)
    df.to_csv(CSV_FILENAME, index=False)

# Initialize camera and hand detector
cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1, detectionCon=0.8)

# Ask the user what gesture to collect
label = input("Enter label name for the gesture you want to record (e.g., 'thumbs_up'): ")

print("\nStarting gesture capture. Press 's' to save a frame, 'q' to quit.\n")

while True:
    success, img = cap.read()
    hands, img = detector.findHands(img)

    if hands:
        hand = hands[0]
        lmList = hand["lmList"]  # List of 21 landmarks (x, y, z)
        bbox = hand["bbox"]

        # Show a bounding box
        x, y, w, h = bbox
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Show label
        cv2.putText(img, f"Gesture: {label}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        key = cv2.waitKey(1)
        if key == ord('s'):
            # Save this frame's landmarks into the CSV
            row = []
            for point in lmList:
                row.extend([round(point[0], 2), round(point[1], 2), round(point[2], 2)])
            row.append(label)

            # Append to CSV
            df = pd.DataFrame([row], columns=columns)
            df.to_csv(CSV_FILENAME, mode='a', index=False, header=False)
            print(f"✅ Frame saved for label: {label}")

        elif key == ord('q'):
            break
    else:
        cv2.putText(img, "Hand Not Detected", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)

    cv2.imshow("Gesture Capture", img)

cap.release()
cv2.destroyAllWindows()
