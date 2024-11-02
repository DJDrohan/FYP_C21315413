# main.py
import torch
import os
from datetime import datetime
from train_eval import model, criterion, optimizer, scheduler, train_model, evaluate_model
from data_loader import train_loader, test_loader

# Set the number of epochs for training
num_epochs = 10

# Train the model with early stopping and validation
train_model(model, train_loader, val_loader=test_loader, epochs=num_epochs, patience=3)

# Evaluate the model on the test set
evaluate_model(model, test_loader)

# Get current timestamp in a readable format
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create filename based on timestamp and number of epochs
model_filename = f'emotion_cnn_model_{current_time}_{num_epochs}epochs.pth'

# Define the directory to save the model
model_dir = 'models'

# Create the models directory if it doesn't exist
os.makedirs(model_dir, exist_ok=True)

# Full path to save the model
model_path = os.path.join(model_dir, model_filename)

# Save the trained model in the specified directory
torch.save(model.state_dict(), model_path)
print(f"Model saved to '{model_path}'")
