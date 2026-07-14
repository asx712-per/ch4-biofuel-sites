from typing import Dict
import torch
from torch.utils.data import Dataset
import numpy as np

class DemoCH4Dataset(Dataset):
    def __init__(self, n: int = 32, in_channels: int = 12, size: int = 256):
        self.n = n
        self.in_channels = in_channels
        self.size = size

    def __len__(self) -> int:
        return self.n

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        H = W = self.size
        x = np.random.randn(self.in_channels, H, W).astype("float32")
        mask = np.zeros((1, H, W), dtype="float32")
        cy, cx = np.random.randint(H//4, 3*H//4), np.random.randint(W//4, 3*W//4)
        rr, cc = np.ogrid[:H, :W]
        circle = (rr - cy)**2 + (cc - cx)**2 <= (H//8)**2
        mask[0, circle] = 1.0
        wind = np.zeros((2, H, W), dtype="float32")
        wind[0, :, :] = 1.0
        wind[1, :, :] = 0.0
        return {"image": torch.from_numpy(x),
                "mask": torch.from_numpy(mask),
                "wind": torch.from_numpy(wind)}