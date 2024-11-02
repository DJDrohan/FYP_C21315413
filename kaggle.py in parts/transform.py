# transforms.py
from torchvision import transforms

# Define transformations for the dataset
# 1. Convert images to grayscale (1 color channel)
# 2. Resize to 48x48 pixels (input size for the model)
# 3. Apply random horizontal flip with 50% probability to add variety
# 4. Apply random rotation of up to 10 degrees to add robustness
# 5. Convert the image to a tensor format
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((48, 48)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(10),
    transforms.ToTensor()
])
