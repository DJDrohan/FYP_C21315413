import cv2
import dlib
import numpy as np

# Load the dlib face detector and facial landmarks predictor
detector = dlib.get_frontal_face_detector()
predictor_path =r'shape_predictor_68_face_landmarks.dat'
predictor = dlib.shape_predictor(predictor_path)

# Start capturing video from the webcam
cap = cv2.VideoCapture(0)

while True:
    # Read a frame from the video
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to grayscale for processing
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = detector(gray_frame)

    # Loop through detected faces
    for face in faces:
        # Get the facial landmarks
        landmarks = predictor(gray_frame, face)

        # Extract eyebrow positions
        left_eyebrow = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(17, 22)]
        right_eyebrow = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(22, 27)]

        # Draw the eyebrows on the frame
        for point in left_eyebrow:
            cv2.circle(frame, point, 3, (0, 255, 0), -1)  # Green for left eyebrow

        for point in right_eyebrow:
            cv2.circle(frame, point, 3, (0, 255, 0), -1)  # Green for right eyebrow

        # Optionally draw a rectangle around the detected face
        cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (255, 0, 0), 2)  # Draw rectangle in blue

    # Display the processed video feed
    cv2.imshow('Eyebrow Position Detection', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
