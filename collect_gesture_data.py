"""
Gesture Data Collection Tool

This script captures hand gesture data for machine learning training.
It saves hand landmark coordinates (x, y, z) to a CSV file for later model training.

Usage:
    1. Run the script
    2. Enter a gesture label (e.g., 'thumbs_up', 'peace_sign')
    3. Press 's' to save the current hand pose
    4. Press 'q' to quit
"""

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
    print(f"✅ Created new CSV file: {CSV_FILENAME}")
else:
    print(f"📂 Using existing CSV file: {CSV_FILENAME}")

# Initialize camera and hand detector
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Error: Could not open webcam. Please check your camera connection.")
    exit()

detector = HandDetector(maxHands=1, detectionCon=0.8)

# Ask the user what gesture to collect
label = input("Enter label name for the gesture you want to record (e.g., 'thumbs_up'): ")

print("\n✅ Gesture capture started!")
print("👉 Press 's' to save a frame")
print("👉 Press 'q' to quit\n")

frame_count = 0

while True:
    success, img = cap.read()
    if not success:
        print("⚠️ Warning: Failed to read frame from webcam")
        break
    
    hands, img = detector.findHands(img)

    if hands:
        hand = hands[0]
        lmList = hand["lmList"]  # List of 21 landmarks (x, y, z)
        bbox = hand["bbox"]

        # Show a bounding box
        x, y, w, h = bbox
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Show label and instructions
        cv2.putText(img, f"Gesture: {label}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        cv2.putText(img, f"Frames saved: {frame_count}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.putText(img, "Press 's' to save, 'q' to quit", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        key = cv2.waitKey(1)
        if key == ord('s'):
            # Save this frame's landmarks into the CSV
            row = []
            for point in lmList:
                row.extend([round(point[0], 2), round(point[1], 2), round(point[2], 2)])
            row.append(label)

            # Append to CSV
            try:
                df = pd.DataFrame([row], columns=columns)
                df.to_csv(CSV_FILENAME, mode='a', index=False, header=False)
                frame_count += 1
                print(f"✅ Frame {frame_count} saved for label: {label}")
            except Exception as e:
                print(f"❌ Error saving data: {e}")

        elif key == ord('q'):
            print(f"\n👋 Quitting. Total frames saved: {frame_count}")
            break
    else:
        cv2.putText(img, "Hand Not Detected", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
        cv2.putText(img, "Show your hand to the camera", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    cv2.imshow("Gesture Capture", img)
    
    # Also check for 'q' when no hand is detected
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(f"\n👋 Quitting. Total frames saved: {frame_count}")
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Gesture capture session completed!")
