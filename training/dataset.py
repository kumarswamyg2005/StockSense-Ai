from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

FEATURE_COLUMNS = [
    "close",
    "volume",
    "daily_return",
    "ma_5",
    "ma_20",
    "ma_50",
    "rsi_14",
    "macd",
    "bb_upper",
    "bb_lower",
    "momentum_10",
]


@dataclass
class DatasetBundle:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    scalers: dict[str, dict[str, Any]]
    stock_test_map: dict[str, dict[str, np.ndarray]]


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    return a / (b.replace(0, np.nan))


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]

    def _find_col(target: str, allow_adj_close: bool = False) -> str | None:
        if target in out.columns:
            return target

        for col in out.columns:
            base = col.split(".")[0].strip().lower()
            if base == target:
                if target == "close" and ("adj" in col) and not allow_adj_close:
                    continue
                return col

        for col in out.columns:
            lc = col.lower()
            if lc.startswith(target):
                if target == "close" and ("adj" in lc) and not allow_adj_close:
                    continue
                return col
        return None

    open_col = _find_col("open")
    high_col = _find_col("high")
    low_col = _find_col("low")
    close_col = _find_col("close") or _find_col("adj close", allow_adj_close=True)
    volume_col = _find_col("volume")

    required_map = {
        "open": open_col,
        "high": high_col,
        "low": low_col,
        "close": close_col,
        "volume": volume_col,
    }
    missing = [k for k, v in required_map.items() if v is None]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available columns: {list(out.columns)}")

    out = out[[open_col, high_col, low_col, close_col, volume_col]].rename(
        columns={
            open_col: "open",
            high_col: "high",
            low_col: "low",
            close_col: "close",
            volume_col: "volume",
        }
    )

    # yfinance CSVs can include extra header/ticker rows (e.g., 'AAPL') as data.
    # Coerce numerics and drop invalid rows safely.
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["open", "high", "low", "close", "volume"])

    out["daily_return"] = out["close"].pct_change().fillna(0.0)
    out["ma_5"] = out["close"].rolling(5).mean()
    out["ma_20"] = out["close"].rolling(20).mean()
    out["ma_50"] = out["close"].rolling(50).mean()

    rsi = RSIIndicator(close=out["close"], window=14)
    out["rsi_14"] = rsi.rsi()

    macd = MACD(close=out["close"], window_slow=26, window_fast=12, window_sign=9)
    out["macd"] = macd.macd()

    bb = BollingerBands(close=out["close"], window=20, window_dev=2)
    out["bb_upper"] = bb.bollinger_hband()
    out["bb_middle"] = bb.bollinger_mavg()
    out["bb_lower"] = bb.bollinger_lband()

    out["momentum_10"] = out["close"] - out["close"].shift(10)

    out = out.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    return out


def _build_scaler(train_feat: np.ndarray, train_close: np.ndarray) -> dict[str, Any]:
    feat_min = train_feat.min(axis=0)
    feat_max = train_feat.max(axis=0)

    close_min = float(train_close.min())
    close_max = float(train_close.max())

    return {
        "feature_columns": FEATURE_COLUMNS,
        "feature_min": feat_min.tolist(),
        "feature_max": feat_max.tolist(),
        "close_min": close_min,
        "close_max": close_max,
    }


def _scale_features(features: np.ndarray, scaler: dict[str, Any]) -> np.ndarray:
    fmin = np.array(scaler["feature_min"], dtype=np.float32)
    fmax = np.array(scaler["feature_max"], dtype=np.float32)
    denom = np.clip(fmax - fmin, 1e-8, None)
    return (features - fmin) / denom


def _scale_close(close_vals: np.ndarray, scaler: dict[str, Any]) -> np.ndarray:
    cmin = scaler["close_min"]
    cmax = scaler["close_max"]
    denom = max(cmax - cmin, 1e-8)
    return (close_vals - cmin) / denom


def _create_sequences_for_range(
    features: np.ndarray,
    scaled_close: np.ndarray,
    start_idx: int,
    end_idx: int,
    seq_len: int,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []

    effective_start = max(start_idx, seq_len)
    effective_end = end_idx - horizon + 1

    for i in range(effective_start, effective_end):
        x = features[i - seq_len : i]
        y = scaled_close[i : i + horizon]

        if x.shape[0] != seq_len or y.shape[0] != horizon:
            continue

        xs.append(x)
        ys.append(y)

    if not xs:
        return (
            np.empty((0, seq_len, features.shape[1]), dtype=np.float32),
            np.empty((0, horizon), dtype=np.float32),
        )

    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32)


def save_scalers(scalers: dict[str, dict[str, Any]], out_dir: str | Path) -> str:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    combined = out_path / "scalers.json"
    with combined.open("w", encoding="utf-8") as f:
        json.dump(scalers, f, indent=2)

    for symbol, payload in scalers.items():
        symbol_file = out_path / f"{symbol.replace('.', '_')}.json"
        with symbol_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    return str(combined)


def load_all_datasets(
    data_root: str,
    seq_len: int = 60,
    horizon: int = 7,
) -> DatasetBundle:
    data_path = Path(data_root)
    if not data_path.exists():
        raise FileNotFoundError(f"Data folder not found: {data_path}")

    train_x_all: list[np.ndarray] = []
    train_y_all: list[np.ndarray] = []
    val_x_all: list[np.ndarray] = []
    val_y_all: list[np.ndarray] = []
    test_x_all: list[np.ndarray] = []
    test_y_all: list[np.ndarray] = []

    scalers: dict[str, dict[str, Any]] = {}
    stock_test_map: dict[str, dict[str, np.ndarray]] = {}

    csv_files = sorted(data_path.glob("*.csv"))
    if not csv_files:
        raise RuntimeError(f"No CSV files found in {data_path}")

    for csv_file in csv_files:
        symbol = csv_file.stem

        raw = pd.read_csv(csv_file)
        if len(raw) < (seq_len + horizon + 100):
            continue

        feat_df = engineer_features(raw)
        if len(feat_df) < (seq_len + horizon + 100):
            continue

        features = feat_df[FEATURE_COLUMNS].values.astype(np.float32)
        close_values = feat_df["close"].values.astype(np.float32)

        n = len(feat_df)
        train_end = int(n * 0.8)
        val_end = int(n * 0.9)

        if train_end <= seq_len or val_end <= train_end:
            continue

        train_features = features[:train_end]
        train_close = close_values[:train_end]

        scaler = _build_scaler(train_features, train_close)
        scalers[symbol] = scaler

        scaled_features = _scale_features(features, scaler)
        scaled_close = _scale_close(close_values, scaler)

        x_train, y_train = _create_sequences_for_range(
            scaled_features, scaled_close, 0, train_end, seq_len, horizon
        )
        x_val, y_val = _create_sequences_for_range(
            scaled_features, scaled_close, train_end, val_end, seq_len, horizon
        )
        x_test, y_test = _create_sequences_for_range(
            scaled_features, scaled_close, val_end, n, seq_len, horizon
        )

        if len(x_train) == 0 or len(x_val) == 0 or len(x_test) == 0:
            continue

        train_x_all.append(x_train)
        train_y_all.append(y_train)
        val_x_all.append(x_val)
        val_y_all.append(y_val)
        test_x_all.append(x_test)
        test_y_all.append(y_test)

        stock_test_map[symbol] = {
            "x_test": x_test,
            "y_test": y_test,
            "close_min": np.array([scaler["close_min"]], dtype=np.float32),
            "close_max": np.array([scaler["close_max"]], dtype=np.float32),
        }

    if not train_x_all:
        raise RuntimeError("No valid stock datasets produced. Check your CSV files.")

    x_train = np.concatenate(train_x_all, axis=0)
    y_train = np.concatenate(train_y_all, axis=0)
    x_val = np.concatenate(val_x_all, axis=0)
    y_val = np.concatenate(val_y_all, axis=0)
    x_test = np.concatenate(test_x_all, axis=0)
    y_test = np.concatenate(test_y_all, axis=0)

    return DatasetBundle(
        x_train=x_train,
        y_train=y_train,
        x_val=x_val,
        y_val=y_val,
        x_test=x_test,
        y_test=y_test,
        scalers=scalers,
        stock_test_map=stock_test_map,
    )


if __name__ == "__main__":
    data_root = os.getenv("DATA_ROOT", "/content/data/stocks")
    ds = load_all_datasets(data_root=data_root)
    print("Train:", ds.x_train.shape, ds.y_train.shape)
    print("Val:", ds.x_val.shape, ds.y_val.shape)
    print("Test:", ds.x_test.shape, ds.y_test.shape)
    print("Stocks:", len(ds.scalers))
