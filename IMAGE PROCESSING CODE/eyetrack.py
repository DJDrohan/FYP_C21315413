import cv2
import numpy as np
import dlib
import time

# Load Dlib's face detector and facial landmarks predictor
cap = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

def midpoint(p1, p2):
    return int((p1.x + p2.x) / 2), int((p1.y + p2.y) / 2)

# Define constants for EAR threshold
EAR_THRESHOLD = 0.2

# Variables to track time
total_time = 0.0
eyes_open_time = 0.0
start_time = time.time()

# State variables for eye tracking
eyes_open = False
last_change_time = time.time()  # Time when the last state change occurred

# Gaze tracking thresholds
gaze_threshold = 30  # Pixels, adjust for sensitivity

while True:
    ret, frame = cap.read()

    # Check if the frame was captured successfully
    if not ret:
        print("Error: Could not read frame.")
        break

    # Resize the frame for better performance (optional)
    frame = cv2.resize(frame, (640, 480))

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector(gray)
    for face in faces:
        landmarks = predictor(gray, face)

        # Get the eye points
        left_point = (landmarks.part(36).x, landmarks.part(36).y)
        right_point = (landmarks.part(39).x, landmarks.part(39).y)
        center_top = midpoint(landmarks.part(37), landmarks.part(38))
        center_bottom = midpoint(landmarks.part(41), landmarks.part(40))

        # Draw lines for eye tracking
        cv2.line(frame, left_point, right_point, (0, 255, 0), 2)  # Horizontal line between eyes
        cv2.line(frame, center_top, center_bottom, (0, 255, 0), 2)  # Vertical line between eyes

        # Calculate the Eye Aspect Ratio (EAR) for eye openness detection
        ear = (np.linalg.norm(np.array(left_point) - np.array(center_top)) +
               np.linalg.norm(np.array(right_point) - np.array(center_bottom))) / (2.0 *
               np.linalg.norm(np.array(left_point) - np.array(right_point)))

        # Check if eyes are open
        if ear >= EAR_THRESHOLD:
            cv2.putText(frame, "Eyes Open", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if not eyes_open:
                eyes_open = True
                last_change_time = time.time()  # Start the timer
        else:
            cv2.putText(frame, "Eyes Closed", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if eyes_open:
                eyes_open_time += time.time() - last_change_time  # Increment eyes open time
                eyes_open = False  # Set the state to closed

        # Gaze direction estimation based on eye position
        eye_center = midpoint(landmarks.part(36), landmarks.part(39))  # Center between the two eye points
        gaze_direction = eye_center[0] - (frame.shape[1] // 2)  # X-axis difference from the center of the frame

        # Check if gaze direction indicates eye contact
        if abs(gaze_direction) < gaze_threshold:
            cv2.putText(frame, "Making Eye Contact", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            cv2.putText(frame, "Not Making Eye Contact", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Calculate total runtime in seconds
    total_time = time.time() - start_time

    # Calculate the percentage of time eyes were open
    if total_time > 0:
        percentage_open = (eyes_open_time / total_time) * 100
    else:
        percentage_open = 0

    # Display the percentage of time eyes were open
    cv2.putText(frame, f"Eyes Open Time: {percentage_open:.2f}%", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Display total run time in seconds
    cv2.putText(frame, f"Total Time: {total_time:.2f} s", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Display time eyes open in seconds
    cv2.putText(frame, f"Time Eyes Open: {eyes_open_time:.2f} s", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Display the frame
    cv2.imshow("Eye Contact Tracker", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close windows
cap.release()
cv2.destroyAllWindows()
