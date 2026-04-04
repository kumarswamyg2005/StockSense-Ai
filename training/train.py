from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
import torch
from torch.nn.utils import clip_grad_norm_
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from dataset import load_all_datasets, save_scalers
from model import StockSenseModel, combined_loss


def _to_device(batch, device: torch.device):
    x, y = batch
    return x.to(device), y.to(device)


def _denorm(arr: np.ndarray, cmin: float, cmax: float) -> np.ndarray:
    return arr * (cmax - cmin) + cmin


def evaluate_model(
    model: StockSenseModel,
    loader: DataLoader,
    device: torch.device,
) -> tuple[float, float]:
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    n = 0

    with torch.no_grad():
        for batch in loader:
            x, y = _to_device(batch, device)
            pred, conf = model(x)
            loss, _, _ = combined_loss(pred, conf, y)
            mae = torch.mean(torch.abs(pred - y))

            bs = x.size(0)
            total_loss += loss.item() * bs
            total_mae += mae.item() * bs
            n += bs

    return total_loss / max(n, 1), total_mae / max(n, 1)


def main() -> None:
    data_root = os.getenv("DATA_ROOT", "/content/data/stocks")
    epochs = int(os.getenv("EPOCHS", "100"))
    batch_size = int(os.getenv("BATCH_SIZE", "64"))
    lr = float(os.getenv("LR", "0.001"))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    ds = load_all_datasets(data_root=data_root, seq_len=60, horizon=7)
    scaler_path = save_scalers(ds.scalers, Path("scalers"))
    print(f"Saved scalers to: {scaler_path}")

    train_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(ds.x_train).float(),
            torch.from_numpy(ds.y_train).float(),
        ),
        batch_size=batch_size,
        shuffle=True,
        drop_last=False,
    )
    val_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(ds.x_val).float(),
            torch.from_numpy(ds.y_val).float(),
        ),
        batch_size=batch_size,
        shuffle=False,
        drop_last=False,
    )

    model = StockSenseModel(input_size=11, horizon=7).to(device)
    optimizer = Adam(model.parameters(), lr=lr)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", patience=5, factor=0.5)

    best_val = float("inf")
    no_improve = 0
    early_stop_patience = 10

    log_rows = []

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        sample_count = 0

        progress = tqdm(train_loader, desc=f"Epoch {epoch}/{epochs}", leave=False)
        for batch in progress:
            x, y = _to_device(batch, device)

            optimizer.zero_grad(set_to_none=True)
            pred, conf = model(x)
            loss, mse, conf_loss = combined_loss(pred, conf, y)

            loss.backward()
            clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            bs = x.size(0)
            running_loss += loss.item() * bs
            sample_count += bs

            progress.set_postfix(
                loss=f"{loss.item():.5f}",
                mse=f"{mse.item():.5f}",
                conf=f"{conf_loss.item():.5f}",
            )

        train_loss = running_loss / max(sample_count, 1)
        val_loss, val_mae = evaluate_model(model, val_loader, device)

        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]

        if epoch % 10 == 0 and torch.cuda.is_available():
            print("\n=== GPU MEMORY SUMMARY ===")
            print(torch.cuda.memory_summary())

        print(
            f"Epoch {epoch:03d} | train_loss={train_loss:.6f} "
            f"| val_loss={val_loss:.6f} | val_mae={val_mae:.6f} | lr={current_lr:.6g}"
        )

        log_rows.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_mae": val_mae,
                "learning_rate": current_lr,
            }
        )

        if val_loss < best_val:
            best_val = val_loss
            no_improve = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "best_val_loss": best_val,
                    "input_size": 11,
                    "horizon": 7,
                },
                "stocksense_best.pth",
            )
            print("✅ Saved new best model -> stocksense_best.pth")
        else:
            no_improve += 1

        if no_improve >= early_stop_patience:
            print(f"⏹️ Early stopping triggered at epoch {epoch}.")
            break

    with open("training_log.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["epoch", "train_loss", "val_loss", "val_mae", "learning_rate"]
        )
        writer.writeheader()
        writer.writerows(log_rows)

    print("\nSaved training log -> training_log.csv")

    # Evaluate final per-stock MAE and directional accuracy on test splits
    ckpt = torch.load("stocksense_best.pth", map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    per_stock_mae = {}
    per_stock_acc = {}

    with torch.no_grad():
        for symbol, payload in ds.stock_test_map.items():
            x_test = torch.from_numpy(payload["x_test"]).float().to(device)
            y_test = payload["y_test"]
            cmin = float(payload["close_min"][0])
            cmax = float(payload["close_max"][0])

            pred_scaled, _ = model(x_test)
            pred_scaled = pred_scaled.cpu().numpy()

            pred_real = _denorm(pred_scaled, cmin, cmax)
            true_real = _denorm(y_test, cmin, cmax)

            mae = float(np.mean(np.abs(pred_real - true_real)))
            mape = float(
                np.mean(np.abs((pred_real - true_real) / np.clip(np.abs(true_real), 1e-6, None)))
            )
            accuracy = max(0.0, 100.0 * (1.0 - mape))

            per_stock_mae[symbol] = mae
            per_stock_acc[symbol] = accuracy

    print("\n=== Final MAE Per Stock ===")
    for symbol in sorted(per_stock_mae):
        print(f"{symbol:12s} -> MAE: {per_stock_mae[symbol]:.4f}")

    avg_acc = float(np.mean(list(per_stock_acc.values()))) if per_stock_acc else 0.0
    print(f"\nAverage prediction accuracy: {avg_acc:.2f}%")


if __name__ == "__main__":
    main()
