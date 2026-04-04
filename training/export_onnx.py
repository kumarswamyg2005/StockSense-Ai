from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from onnxsim import simplify

from model import StockSenseModel


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    train_dir = Path(__file__).resolve().parent
    backend_model_dir = train_dir.parent / "backend" / "model"
    ensure_dir(backend_model_dir)

    checkpoint_path = train_dir / "stocksense_best.pth"
    raw_onnx_path = train_dir / "stocksense_model_raw.onnx"
    final_onnx_train = train_dir / "stocksense_model.onnx"
    final_onnx_backend = backend_model_dir / "stocksense_model.onnx"

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model = StockSenseModel(input_size=11, horizon=7)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    dummy = torch.randn(1, 60, 11, dtype=torch.float32)

    torch.onnx.export(
        model,
        dummy,
        str(raw_onnx_path),
        input_names=["input"],
        output_names=["predictions", "confidence"],
        opset_version=11,
        do_constant_folding=True,
    )
    print(f"✅ Raw ONNX exported: {raw_onnx_path}")

    model_onnx = onnx.load(str(raw_onnx_path))
    simplified_model, check = simplify(model_onnx)
    if not check:
        raise RuntimeError("ONNX simplification failed.")

    onnx.save(simplified_model, str(final_onnx_train))
    shutil.copy2(final_onnx_train, final_onnx_backend)
    print(f"✅ Simplified ONNX saved: {final_onnx_train}")
    print(f"✅ ONNX copied to backend: {final_onnx_backend}")

    # Verify CPU inference
    session = ort.InferenceSession(str(final_onnx_train), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    sample = np.random.randn(1, 60, 11).astype(np.float32)
    pred, conf = session.run(None, {input_name: sample})

    print("✅ CPU inference verified with onnxruntime")
    print(f"Predictions shape: {pred.shape}")
    print(f"Confidence shape: {conf.shape}")

    size_mb = final_onnx_train.stat().st_size / (1024 * 1024)
    print(f"Model size: {size_mb:.2f} MB")
    if size_mb <= 15:
        print("✅ Target met: model under 15MB")
    else:
        print("⚠️ Model is above 15MB target")

    # Copy scalers to backend/model/scalers.json
    scaler_src = train_dir / "scalers" / "scalers.json"
    scaler_dst_backend = backend_model_dir / "scalers.json"
    scaler_dst_train = train_dir / "scalers.json"

    if scaler_src.exists():
        with scaler_src.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        with scaler_dst_backend.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        with scaler_dst_train.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        print(f"✅ Scalers exported to: {scaler_dst_backend}")
        print(f"✅ Scalers exported to: {scaler_dst_train}")
    else:
        print(f"⚠️ Scaler file not found at {scaler_src}. Train first.")


if __name__ == "__main__":
    main()
