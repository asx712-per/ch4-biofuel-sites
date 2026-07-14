import argparse
import os
import numpy as np
import torch
import pytorch_lightning as pl
from torch.utils.data import DataLoader
from src.dataio.datasets import DemoCH4Dataset
from src.models.unet import MethaneUNet
from src.models.losses import focal_loss, wind_alignment_penalty

class CH4Module(pl.LightningModule):
    def __init__(self, in_channels=12, lr=1e-3, use_wind=True):
        super().__init__()
        self.model = MethaneUNet(in_channels=in_channels, classes=1)
        self.lr = lr
        self.use_wind = use_wind

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y, wind = batch["image"], batch["mask"], batch["wind"]
        logits = self(x)
        loss = focal_loss(logits, y)
        if self.use_wind:
            prob = torch.sigmoid(logits)
            loss = loss + 0.1 * wind_alignment_penalty(prob, wind[:, 0], wind[:, 1])
        self.log("train_loss", loss, prog_bar=False, on_step=True, on_epoch=True)
        return loss

    def configure_optimizers(self):
        return torch.optim.AdamW(self.parameters(), lr=self.lr)

def make_loader(n=16, in_channels=12, size=256, batch_size=4, workers=0):
    ds = DemoCH4Dataset(n=n, in_channels=in_channels, size=size)
    return DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=workers, pin_memory=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()

    train_loader = make_loader(workers=0)
    mod = CH4Module(in_channels=12, lr=1e-3, use_wind=True)

    trainer = pl.Trainer(
        max_epochs=args.epochs,
        accelerator="cpu",
        devices=1,
        logger=False,
        enable_checkpointing=False,
        enable_model_summary=False,
        enable_progress_bar=False,
        default_root_dir="data/lightning"
    )

    trainer.fit(mod, train_loader)

    if args.demo:
        outdir = "data/outputs"
        os.makedirs(outdir, exist_ok=True)
        batch = next(iter(train_loader))
        with torch.no_grad():
            prob = torch.sigmoid(mod(batch["image"]))
        np.save(f"{outdir}/demo_prob.npy", prob.cpu().numpy())
        print(f"Saved {outdir}/demo_prob.npy")

if __name__ == "__main__":
    main()
