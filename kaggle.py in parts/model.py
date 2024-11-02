# model.py
import torch.nn as nn
import torch


class CNNModel(nn.Module):
    def __init__(self, num_classes):
        super(CNNModel, self).__init__()

        # Convolutional layers with batch normalization
        self.conv1 = nn.Conv2d(1, 64, kernel_size=3, padding=1)  # Input: (1, 48, 48), Output: (64, 48, 48)
        self.bn1 = nn.BatchNorm2d(64)

        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)  # Output: (128, 24, 24)
        self.bn2 = nn.BatchNorm2d(128)

        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, padding=1)  # Output: (256, 12, 12)
        self.bn3 = nn.BatchNorm2d(256)

        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)  # Reduce spatial dimensions by half

        # Fully connected layers with dropout to reduce overfitting
        self.fc1 = nn.Linear(256 * 6 * 6, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, num_classes)
        self.dropout = nn.Dropout(0.5)  # Dropout layer with 50% dropout rate

    def forward(self, x):
        # Apply convolutional layers with ReLU, batch norm, and max pooling
        x = self.pool(torch.relu(self.bn1(self.conv1(x))))
        x = self.pool(torch.relu(self.bn2(self.conv2(x))))
        x = self.pool(torch.relu(self.bn3(self.conv3(x))))

        # Flatten tensor for fully connected layers
        x = x.view(-1, 256 * 6 * 6)

        # Apply fully connected layers with ReLU and dropout
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)  # Dropout applied before final layers
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x


# Initialize weights for convolutional and linear layers
def init_weights(m):
    if isinstance(m, nn.Conv2d):
        nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
    elif isinstance(m, nn.Linear):
        nn.init.xavier_normal_(m.weight)
