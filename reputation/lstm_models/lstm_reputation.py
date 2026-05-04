import torch
import torch.nn as nn


class ReputationLSTM(nn.Module):
    """
    LSTM model that predicts next reputation score
    based on sequence of behaviors (accuracy, loss, gradient norm, flags).
    """
    def __init__(self, input_size=4, hidden_size=32, num_layers=2):
        super(ReputationLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)  # Predict scalar reputation score in [0,1]
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        # x: (batch, seq_len, input_size)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        out, _ = self.lstm(x, (h0, c0))
        out = out[:, -1, :]  # Last time step
        out = self.fc(out)
        out = self.sigmoid(out)
        return out
