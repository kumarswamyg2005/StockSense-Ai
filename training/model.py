from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class AttentionBlock(nn.Module):
    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.score = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # x: (batch, seq_len, hidden)
        weights = self.score(x).squeeze(-1)  # (batch, seq_len)
        weights = torch.softmax(weights, dim=1)
        context = torch.sum(x * weights.unsqueeze(-1), dim=1)  # (batch, hidden)
        return context, weights


class StockSenseModel(nn.Module):
    """
    Input:  (batch, 60, 11)
    Output: (batch, 7) predictions + (batch, 7) confidence
    """

    def __init__(self, input_size: int = 11, horizon: int = 7) -> None:
        super().__init__()
        self.horizon = horizon

        self.lstm_1 = nn.LSTM(
            input_size=input_size,
            hidden_size=256,
            num_layers=3,
            dropout=0.2,
            batch_first=True,
        )
        self.lstm_2 = nn.LSTM(
            input_size=256,
            hidden_size=128,
            num_layers=1,
            batch_first=True,
        )

        self.attention = AttentionBlock(hidden_size=128)

        self.fc1 = nn.Linear(128, 64)
        self.drop = nn.Dropout(0.3)
        self.fc2 = nn.Linear(64, 32)

        self.price_head = nn.Linear(32, horizon)
        self.confidence_head = nn.Linear(32, horizon)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x, _ = self.lstm_1(x)
        x, _ = self.lstm_2(x)

        context, _ = self.attention(x)

        x = F.relu(self.fc1(context))
        x = self.drop(x)
        x = F.relu(self.fc2(x))

        price_pred = self.price_head(x)
        confidence = torch.sigmoid(self.confidence_head(x))
        return price_pred, confidence


def combined_loss(
    prediction: torch.Tensor,
    confidence: torch.Tensor,
    target: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    mse = F.mse_loss(prediction, target)

    # Confidence target: high confidence for low normalized error.
    normalized_error = torch.abs(prediction - target) / (torch.abs(target) + 1e-6)
    confidence_target = torch.exp(-normalized_error).detach().clamp(0.0, 1.0)
    confidence_loss = F.mse_loss(confidence, confidence_target)

    total = mse + 0.1 * confidence_loss
    return total, mse, confidence_loss
