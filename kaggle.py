import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# 1. Define Transforms for the Dataset
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),  # Convert to grayscale
    transforms.Resize((48, 48)),  # Resize to 48x48 pixels
    transforms.ToTensor()  # Convert to a tensor
])

# 2. Load Data Using ImageFolder
dataset_dir = r"C:\Users\droha\Downloads\COLLEGE\4\FYP\kaggle emotion data"

# Load train and test datasets separately
train_dataset = datasets.ImageFolder(root=os.path.join(dataset_dir, 'train'), transform=transform)
test_dataset = datasets.ImageFolder(root=os.path.join(dataset_dir, 'test'), transform=transform)

# DataLoader for batching and shuffling
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# 3. CNN Model Definition
class CNNModel(nn.Module):
    def __init__(self, num_classes):
        super(CNNModel, self).__init__()
        self.conv1 = nn.Conv2d(1, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(256 * 6 * 6, 256)  # Adjust based on input size after pooling
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, num_classes)  # Number of output classes (e.g., 7 emotions)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = self.pool(torch.relu(self.conv3(x)))
        x = x.view(-1, 256 * 6 * 6)  # Flatten the tensor
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x


# 4. Initialize the model, optimizer, and loss function
num_classes = len(train_dataset.classes)  # Automatically detected from the subfolders
model = CNNModel(num_classes)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)


print(f"Number of training samples: {len(train_dataset)}")
print(f"Number of test samples: {len(test_dataset)}")


# Check if a GPU is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')

# Move model to the device
model = CNNModel(num_classes).to(device)

# 5. Train the model
def train_model(model, train_loader, criterion, optimizer, epochs=10):
    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)  # Move data to GPU/CPU

            optimizer.zero_grad()  # Zero gradients

            outputs = model(images)  # Forward pass
            loss = criterion(outputs, labels)  # Compute loss

            loss.backward()  # Backpropagation
            optimizer.step()  # Optimization step

            running_loss += loss.item()

        print(f'Epoch [{epoch + 1}/{epochs}], Loss: {running_loss / len(train_loader):.4f}')
    print("Training complete.")
# Train the model for 10 epochs
train_model(model, train_loader, criterion, optimizer, epochs=10)

# 6. Evaluate the model
def evaluate_model(model, test_loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    print(f'Accuracy of the model on the test set: {accuracy:.2f}%')

# Evaluate the model
evaluate_model(model, test_loader)

# 7. Save the Model
torch.save(model.state_dict(), 'emotion_cnn_model.pth')

# 8. Real-time Emotion Detection with Webcam
def real_time_emotion_detection(model, emotion_mapping):
    cap = cv2.VideoCapture(0)  # Initialize webcam

    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Grayscale(),
        transforms.Resize((48, 48)),
        transforms.ToTensor()
    ])

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        face = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_resized = cv2.resize(face, (48, 48))
        face_tensor = transform(face_resized).unsqueeze(0)

        with torch.no_grad():
            output = model(face_tensor)
            probabilities = torch.softmax(output, dim=1)[0].numpy()
            predicted_class = np.argmax(probabilities)
            emotion = emotion_mapping[predicted_class]  # Class label from ImageFolder

        cv2.putText(frame, f'Emotion: {emotion}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        for i, (emotion_name, prob) in enumerate(zip(emotion_mapping, probabilities)):
            cv2.putText(frame, f'{emotion_name}: {prob * 100:.2f}%', (50, 100 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 0, 0), 1)
        cv2.imshow('Real-time Emotion Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Run real-time emotion detection
real_time_emotion_detection(model, train_dataset.classes)
