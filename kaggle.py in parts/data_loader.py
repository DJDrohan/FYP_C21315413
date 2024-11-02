# data_loader.py
import os
from torch.utils.data import DataLoader
from torchvision import datasets
from transform import transform

# Define the path to the dataset directory
dataset_dir = r"C:\Users\droha\Downloads\COLLEGE\4\FYP\kaggle emotion data"

# Load the train and test datasets
# 1. ImageFolder automatically assigns labels based on subfolder names
# 2. Apply transformations to each dataset
train_dataset = datasets.ImageFolder(root=os.path.join(dataset_dir, 'train'), transform=transform)
test_dataset = datasets.ImageFolder(root=os.path.join(dataset_dir, 'test'), transform=transform)

# Create DataLoaders for batching and shuffling data
# 1. Shuffle the training data to improve model generalization
# 2. No shuffling for test data to keep evaluation consistent
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)
