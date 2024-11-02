# real_time_emotion_detection.py
import cv2
import torch
import numpy as np
from torchvision import transforms
from model import CNNModel
from data_loader import train_dataset

# Load trained model and move to device
num_classes = len(train_dataset.classes)
model = CNNModel(num_classes)
model.load_state_dict(torch.load(r"C:\Users\droha\Downloads\COLLEGE\4\FYP\FYP_C21315413\kaggle.py in parts\models\emotion_cnn_model_20241102_225020_10epochs.pth"))
model.eval()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

# Class labels from dataset
emotion_mapping = train_dataset.classes

# Transformation for real-time input
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Grayscale(),
    transforms.Resize((48, 48)),
    transforms.ToTensor()
])


# Real-time emotion detection function
def real_time_emotion_detection(model, emotion_mapping):
    cap = cv2.VideoCapture(0)  # Access the webcam

    while True:
        ret, frame = cap.read()  # Capture frame-by-frame
        if not ret:
            break

        # Preprocess the image for the model
        face = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_resized = cv2.resize(face, (48, 48))
        face_tensor = transform(face_resized).unsqueeze(0).to(device)

        # Get prediction from model
        with torch.no_grad():
            output = model(face_tensor)
            probabilities = torch.softmax(output, dim=1)[0].cpu().numpy()
            predicted_class = np.argmax(probabilities)
            emotion = emotion_mapping[predicted_class]  # Predicted emotion label

        # Display the emotion on the screen
        cv2.putText(frame, f'Emotion: {emotion}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        for i, (emotion_name, prob) in enumerate(zip(emotion_mapping, probabilities)):
            cv2.putText(frame, f'{emotion_name}: {prob * 100:.2f}%', (50, 100 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 0, 0), 1)

        cv2.imshow('Real-time Emotion Detection', frame)

        # Break loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()  # Release the webcam
    cv2.destroyAllWindows()  # Close all OpenCV windows


# Run real-time emotion detection
real_time_emotion_detection(model, emotion_mapping)
