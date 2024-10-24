import cv2
import os
import datetime

save_directory = 'Face screenshots'

# Ensure the save directory exists
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

# Load the pre-trained Haar Cascade classifiers for face and eye detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Capture video from the webcam (0 for the default webcam)
cap = cv2.VideoCapture(0)

# Initialize recording state
is_recording = False
output_video = None

while True:
    # Read frame-by-frame from the video capture
    ret, frame = cap.read()

    # If the frame was not captured properly, break the loop
    if not ret:
        print("Failed to grab frame")
        break

    # Convert the frame to grayscale (Haar Cascades require grayscale images)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Draw rectangles around detected faces and detect eyes within the face region
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Region of interest for detecting eyes within the face
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]

        # Detect eyes in the face region
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

    # Display the frame with face and eye rectangles
    cv2.imshow('Face and Eye Detection', frame)

    # Check for key presses
    key = cv2.waitKey(1)  # Use a small delay for smoother operation
    if key == 27:  # Exit on ESC
        break
    elif key == ord('s'):  # Save a screenshot
        timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        screenshot_filename = f"screenshot_{timestamp}.png"
        screenshot_path = os.path.join(save_directory, screenshot_filename)
        cv2.imwrite(screenshot_path, frame)  # Save the current frame
        print(f"Screenshot saved as {screenshot_filename}")
    elif key == ord('r'):  # Start/stop recording
        if not is_recording:
            # Start recording
            timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            video_filename = f"video_{timestamp}.avi"
            video_path = os.path.join(save_directory, video_filename)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec
            fps = 30.0  # Frames per second
            height, width, _ = frame.shape
            output_video = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
            is_recording = True
            print(f"Recording started: {video_filename}")
        else:
            # Stop recording
            output_video.release()
            output_video = None
            is_recording = False
            print("Recording stopped.")

    # If recording, write the frame to the video file
    if is_recording:
        output_video.write(frame)

# Release the capture and close the window
cap.release()
if output_video is not None:
    output_video.release()
cv2.destroyAllWindows()
