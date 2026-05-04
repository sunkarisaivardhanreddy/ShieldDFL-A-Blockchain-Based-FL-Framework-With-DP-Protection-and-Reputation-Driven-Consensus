import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
from typing import List, Dict
import logging

logger = logging.getLogger('shielddfl')


class SimpleCNN(nn.Module):
    """Simple CNN for IIoT Data Classification"""
    def __init__(self, input_dim=28*28, num_classes=10):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 64 * 7 * 7)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)
        return x


class FederatedAveraging:
    """FedAvg Algorithm Implementation"""
    
    def __init__(self, model_architecture='SimpleCNN'):
        self.model_architecture = model_architecture
        self.global_model = self._initialize_model()
    
    def _initialize_model(self):
        """Initialize global model"""
        if self.model_architecture == 'SimpleCNN':
            return SimpleCNN()
        # Add more architectures as needed
        return SimpleCNN()
    
    def get_model_weights(self):
        """Get current global model weights"""
        return {k: v.cpu().numpy().tolist() for k, v in self.global_model.state_dict().items()}
    
    def set_model_weights(self, weights_dict):
        """Set global model weights"""
        state_dict = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights_dict.items()}
        self.global_model.load_state_dict(state_dict, strict=False)
    
    def aggregate_weights(self, local_updates: List[Dict], aggregation_weights=None):
        """
        Federated Averaging
        Args:
            local_updates: List of dictionaries containing model weights
            aggregation_weights: Optional weights for each client (based on data size)
        Returns:
            Aggregated global weights
        """
        if not local_updates:
            return self.get_model_weights()
        
        # If no aggregation weights provided, use equal weights
        if aggregation_weights is None:
            aggregation_weights = [1.0 / len(local_updates)] * len(local_updates)
        else:
            # Normalize weights
            total = sum(aggregation_weights)
            aggregation_weights = [w / total for w in aggregation_weights]
        
        # Initialize aggregated weights
        aggregated_weights = {}
        
        # Get all parameter names from first update
        param_names = local_updates[0].keys()
        
        # Aggregate each parameter
        for param_name in param_names:
            # Stack all client weights for this parameter
            stacked_weights = np.array([
                local_updates[i][param_name] for i in range(len(local_updates))
            ])
            
            # Weighted average
            weighted_sum = np.zeros_like(stacked_weights[0])
            for i, weight in enumerate(aggregation_weights):
                weighted_sum += weight * stacked_weights[i]
            
            aggregated_weights[param_name] = weighted_sum.tolist()
        
        # Update global model
        self.set_model_weights(aggregated_weights)
        
        return aggregated_weights
    
    def evaluate_model(self, test_loader):
        """Evaluate global model"""
        self.global_model.eval()
        correct = 0
        total = 0
        total_loss = 0
        criterion = nn.CrossEntropyLoss()
        
        with torch.no_grad():
            for data, target in test_loader:
                output = self.global_model(data)
                loss = criterion(output, target)
                total_loss += loss.item()
                _, predicted = torch.max(output.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()
        
        accuracy = 100 * correct / total if total > 0 else 0
        avg_loss = total_loss / len(test_loader) if len(test_loader) > 0 else 0
        
        return accuracy, avg_loss


class LocalTrainer:
    """Local training on device"""
    
    def __init__(self, model_weights, device_id, learning_rate=0.01):
        self.model = SimpleCNN()
        self.set_weights(model_weights)
        self.device_id = device_id
        self.learning_rate = learning_rate
        self.optimizer = optim.SGD(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()
    
    def set_weights(self, weights_dict):
        """Load weights into local model"""
        state_dict = {k: torch.tensor(v) for k, v in weights_dict.items()}
        self.model.load_state_dict(state_dict)
    
    def get_weights(self):
        """Get local model weights"""
        return {k: v.cpu().numpy().tolist() for k, v in self.model.state_dict().items()}
    
    def train(self, train_loader, epochs=3):
        """Train local model"""
        self.model.train()
        metrics = []
        
        for epoch in range(epochs):
            epoch_loss = 0
            correct = 0
            total = 0
            
            for batch_idx, (data, target) in enumerate(train_loader):
                self.optimizer.zero_grad()
                output = self.model(data)
                loss = self.criterion(output, target)
                loss.backward()
                self.optimizer.step()
                
                epoch_loss += loss.item()
                _, predicted = torch.max(output.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()
            
            accuracy = 100 * correct / total if total > 0 else 0
            avg_loss = epoch_loss / len(train_loader) if len(train_loader) > 0 else 0
            
            metrics.append({
                'epoch': epoch + 1,
                'accuracy': accuracy,
                'loss': avg_loss
            })
            
            logger.info(f"Device {self.device_id} - Epoch {epoch+1}: Acc={accuracy:.2f}%, Loss={avg_loss:.4f}")
        
        return self.get_weights(), metrics


def calculate_gradient_norm(model_weights):
    """Calculate L2 norm of model weights"""
    total_norm = 0.0
    for param_values in model_weights.values():
        param_array = np.array(param_values)
        total_norm += np.sum(param_array ** 2)
    return np.sqrt(total_norm)
