"""
Model Architectures & Wrappers Module.
Implements focused model suite:
- M1: Support Vector Machine (SVM)
- M2: Random Forest (RF)
- M3: XGBoost (Primary SHAP model)
- M4: Compact 1D Temporal CNN (PyTorch)
"""

import numpy as np
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

def build_svm_model(C_val: float = 1.0, kernel: str = 'rbf', gamma: str = 'scale'):
    return SVC(C=C_val, kernel=kernel, gamma=gamma, probability=False, random_state=20260728)

def build_rf_model(n_estimators: int = 100, max_depth: int = 15, min_samples_leaf: int = 2):
    return RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        n_jobs=-1,
        random_state=20260728
    )

def build_xgboost_model(n_estimators: int = 150, max_depth: int = 6, learning_rate: float = 0.05, subsample: float = 0.8, colsample_bytree: float = 0.8, device: str = 'cuda'):
    return xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        tree_method='hist',
        device=device,
        random_state=20260728,
        eval_metric='mlogloss'
    )

class Compact1DCNN(nn.Module):
    """
    Compact 1D Convolutional Neural Network for Raw sEMG Tensors (Batch, Channels, Time).
    """
    def __init__(self, in_channels: int, n_samples: int, num_classes: int, hidden_dim: int = 64, dropout_rate: float = 0.3):
        super(Compact1DCNN, self).__init__()
        self.conv1 = nn.Conv1d(in_channels, hidden_dim, kernel_size=9, stride=1, padding=4)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.relu1 = nn.GELU()
        
        self.conv2 = nn.Conv1d(hidden_dim, hidden_dim * 2, kernel_size=5, stride=1, padding=2)
        self.bn2 = nn.BatchNorm1d(hidden_dim * 2)
        self.relu2 = nn.GELU()
        
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.dropout = nn.Dropout(dropout_rate)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (B, C, T)
        out = self.relu1(self.bn1(self.conv1(x)))
        out = self.relu2(self.bn2(self.conv2(out)))
        out = self.pool(out).squeeze(-1) # (B, hidden_dim * 2)
        out = self.dropout(out)
        out = self.fc(out) # (B, num_classes)
        return out

class CNNWrapper:
    """
    Scikit-learn compatible wrapper for Compact1DCNN.
    """
    def __init__(self, in_channels: int, n_samples: int, num_classes: int, lr: float = 1e-3, epochs: int = 25, batch_size: int = 128, device: str = None):
        self.in_channels = in_channels
        self.n_samples = n_samples
        self.num_classes = num_classes
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = Compact1DCNN(in_channels, n_samples, num_classes).to(self.device)

    def fit(self, X: np.ndarray, y: np.ndarray):
        # X shape: (N, C, T)
        self.model.train()
        X_t = torch.tensor(X, dtype=torch.float32)
        y_t = torch.tensor(y, dtype=torch.long)
        dataset = TensorDataset(X_t, y_t)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=1e-4)

        for epoch in range(self.epochs):
            for bx, by in loader:
                bx, by = bx.to(self.device), by.to(self.device)
                optimizer.zero_grad()
                out = self.model(bx)
                loss = criterion(out, by)
                loss.backward()
                optimizer.step()

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            out = self.model(X_t)
            preds = torch.argmax(out, dim=1).cpu().numpy()
        return preds

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            out = self.model(X_t)
            probs = torch.softmax(out, dim=1).cpu().numpy()
        return probs
