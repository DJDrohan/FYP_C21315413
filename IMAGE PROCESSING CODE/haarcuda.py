import cv2
import os
import datetime

save_directory = 'Face screenshots'

# Ensure the save directory exists
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

# Load the pre-trained Haar Cascade classifiers for face detection (use CUDA version)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Check if CUDA is available
if not cv2.cuda.getCudaEnabledDeviceCount():
    print("CUDA is not available on this machine. Make sure you have a CUDA-compatible GPU and drivers installed.")
    exit()

# Create CUDA Haar cascade detector
gpu_face_cascade = cv2.cuda.CascadeClassifier.create(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

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

    # Upload frame to the GPU
    gpu_frame = cv2.cuda_GpuMat()
    gpu_frame.upload(frame)

    # Convert to grayscale on GPU
    gpu_gray = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2GRAY)

    # Detect faces on GPU
    faces = gpu_face_cascade.detectMultiScale(gpu_gray)

    # Draw rectangles around detected faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Display the frame with face rectangles
    cv2.imshow('Face Detection with CUDA', frame)

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
