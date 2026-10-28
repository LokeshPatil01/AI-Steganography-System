"""Lightweight PyTorch CNN Steganalyzer with Spatial Rich Model (SRM) Preprocessing.

Phase 16: Deep Learning Steganalyzer Architecture
- SRM Preprocessing Layer: Fixed 5x5 High-Pass Filter residual bank (KV, Laplacian, Edge).
- Content suppression & residual truncation: Clamped to [-3.0, 3.0].
- Feature Extraction: 4 Convolutional blocks with BatchNorm & LeakyReLU.
- Global Pooling: AdaptiveAvgPool2d to support arbitrary image dimensions.
- Classification Head: Dense layers with Dropout producing P(stego) in [0.0, 1.0].
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional


class SpatialRichModelLayer(nn.Module):
    """Fixed Spatial Rich Model (SRM) High-Pass Filtering preprocessing layer.

    Suppresses image semantic content (textures, colors, structures) and exposes
    micro-scale noise residuals where LSB steganographic modifications reside.
    Uses 3 standard steganalyzer kernels:
    1. Ker-Van (KV) 5x5 kernel (Fridrich & Kodovsky, 2012)
    2. 5x5 Laplacian high-pass curvature kernel
    3. 5x5 Horizontal second-order difference edge kernel
    """

    def __init__(self, truncation_threshold: float = 3.0):
        super().__init__()
        self.truncation_threshold = truncation_threshold

        # Define the 3 SRM 5x5 high-pass kernels
        # 1. KV filter (5x5)
        kv = torch.tensor([
            [-1.0,  2.0,  -2.0,  2.0, -1.0],
            [ 2.0, -6.0,   8.0, -6.0,  2.0],
            [-2.0,  8.0, -12.0,  8.0, -2.0],
            [ 2.0, -6.0,   8.0, -6.0,  2.0],
            [-1.0,  2.0,  -2.0,  2.0, -1.0],
        ], dtype=torch.float32) / 12.0

        # 2. Laplacian filter (5x5)
        lap = torch.tensor([
            [ 0.0,  0.0, -1.0,  0.0,  0.0],
            [ 0.0, -1.0, -2.0, -1.0,  0.0],
            [-1.0, -2.0, 16.0, -2.0, -1.0],
            [ 0.0, -1.0, -2.0, -1.0,  0.0],
            [ 0.0,  0.0, -1.0,  0.0,  0.0],
        ], dtype=torch.float32) / 16.0

        # 3. Horizontal edge second-order difference (5x5)
        edge = torch.tensor([
            [ 0.0,  0.0,  0.0,  0.0,  0.0],
            [ 0.0, -1.0,  2.0, -1.0,  0.0],
            [ 0.0, -2.0,  4.0, -2.0,  0.0],
            [ 0.0, -1.0,  2.0, -1.0,  0.0],
            [ 0.0,  0.0,  0.0,  0.0,  0.0],
        ], dtype=torch.float32) / 4.0

        # Stack into [3, 1, 5, 5] weight tensor
        weights = torch.stack([kv, lap, edge], dim=0).unsqueeze(1)

        self.conv = nn.Conv2d(
            in_channels=1,
            out_channels=3,
            kernel_size=5,
            stride=1,
            padding=2,
            bias=False,
        )
        self.conv.weight = nn.Parameter(weights, requires_grad=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Applies SRM high-pass filtering and clamps noise residuals.

        Args:
            x: Input grayscale tensor of shape [B, 1, H, W] in range [0, 255] or [0, 1].

        Returns:
            Residual tensor of shape [B, 3, H, W] clamped to [-T, T].
        """
        # If input is in [0, 1], scale to [0, 255] for standard SRM filter response
        if x.max() <= 1.0 + 1e-5:
            x = x * 255.0

        residuals = self.conv(x)
        # Non-linear truncation function T(x) = max(-T, min(T, x))
        truncated = torch.clamp(
            residuals,
            min=-self.truncation_threshold,
            max=self.truncation_threshold,
        )
        return truncated


class SteganalyzerCNN(nn.Module):
    """Deep Learning Convolutional Steganalyzer.

    Extracts high-order noise statistics via Spatial Rich Model (SRM) residuals
    and classifies images into Cover (0) vs. Stego (1).
    """

    def __init__(self, srm_truncation: float = 3.0, dropout_rate: float = 0.4):
        super().__init__()
        self.srm = SpatialRichModelLayer(truncation_threshold=srm_truncation)

        # Block 1: 3 -> 32
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(32)
        self.act1 = nn.LeakyReLU(0.2, inplace=True)
        self.pool1 = nn.AvgPool2d(kernel_size=2, stride=2)

        # Block 2: 32 -> 64
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(64)
        self.act2 = nn.LeakyReLU(0.2, inplace=True)
        self.pool2 = nn.AvgPool2d(kernel_size=2, stride=2)

        # Block 3: 64 -> 128
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1, bias=False)
        self.bn3 = nn.BatchNorm2d(128)
        self.act3 = nn.LeakyReLU(0.2, inplace=True)
        self.pool3 = nn.AvgPool2d(kernel_size=2, stride=2)

        # Block 4: 128 -> 128
        self.conv4 = nn.Conv2d(128, 128, kernel_size=3, padding=1, bias=False)
        self.bn4 = nn.BatchNorm2d(128)
        self.act4 = nn.LeakyReLU(0.2, inplace=True)

        # Global Average Pooling ensures dimension-independence
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))

        # Classification Head
        self.fc1 = nn.Linear(128, 64)
        self.act_fc = nn.LeakyReLU(0.2, inplace=True)
        self.dropout = nn.Dropout(p=dropout_rate)
        self.fc2 = nn.Linear(64, 1)

    def extract_residuals(self, x: torch.Tensor) -> torch.Tensor:
        """Exposes SRM noise residuals for inspection and explainability."""
        return self.srm(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning raw unnormalized logits [B, 1]."""
        # Preprocessing: SRM Residuals
        res = self.srm(x)

        # Feature extraction
        h = self.pool1(self.act1(self.bn1(self.conv1(res))))
        h = self.pool2(self.act2(self.bn2(self.conv2(h))))
        h = self.pool3(self.act3(self.bn3(self.conv3(h))))
        h = self.act4(self.bn4(self.conv4(h)))

        # Global pooling & classification
        h = self.global_pool(h)
        h = torch.flatten(h, 1)
        h = self.dropout(self.act_fc(self.fc1(h)))
        logits = self.fc2(h)
        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Returns stego probability P(stego) in [0.0, 1.0]."""
        logits = self.forward(x)
        return torch.sigmoid(logits)


def count_parameters(model: nn.Module) -> Dict[str, int]:
    """Returns total and trainable parameter counts."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    fixed = total - trainable
    return {"total": total, "trainable": trainable, "fixed_srm": fixed}
