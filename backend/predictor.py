from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
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


class ONNXPredictor:
    def __init__(self, model_path: str | Path, scaler_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.session: ort.InferenceSession | None = None
        self.input_name: str | None = None
        self.scalers: dict[str, dict[str, Any]] = {}
        self.model_load_error: str | None = None

        self._load_scalers()
        self._load_model()

    @property
    def is_ready(self) -> bool:
        return self.session is not None

    def _load_scalers(self) -> None:
        if self.scaler_path.exists():
            with self.scaler_path.open("r", encoding="utf-8") as f:
                self.scalers = json.load(f)

    def _load_model(self) -> None:
        if not self.model_path.exists():
            self.model_load_error = (
                f"Model file not found at {self.model_path}. "
                "Run training/export or copy stocksense_model.onnx to backend/model/."
            )
            return
        try:
            self.session = ort.InferenceSession(
                str(self.model_path), providers=["CPUExecutionProvider"]
            )
            self.input_name = self.session.get_inputs()[0].name
            self.model_load_error = None
        except Exception as exc:
            self.session = None
            self.input_name = None
            self.model_load_error = (
                "Failed to load ONNX model. "
                f"Ensure backend/model/stocksense_model.onnx is a valid exported model. Error: {exc}"
            )

    @staticmethod
    def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if "Close" not in out.columns or "Volume" not in out.columns:
            raise ValueError("Input dataframe missing required Close/Volume columns.")

        out["daily_return"] = out["Close"].pct_change().fillna(0.0)
        out["ma_5"] = out["Close"].rolling(5).mean()
        out["ma_20"] = out["Close"].rolling(20).mean()
        out["ma_50"] = out["Close"].rolling(50).mean()

        rsi = RSIIndicator(close=out["Close"], window=14)
        out["rsi_14"] = rsi.rsi()

        macd = MACD(close=out["Close"], window_slow=26, window_fast=12, window_sign=9)
        out["macd"] = macd.macd()

        bb = BollingerBands(close=out["Close"], window=20, window_dev=2)
        out["bb_upper"] = bb.bollinger_hband()
        out["bb_lower"] = bb.bollinger_lband()

        out["momentum_10"] = out["Close"] - out["Close"].shift(10)

        out = out.rename(columns={"Close": "close", "Volume": "volume"})
        out = out.replace([np.inf, -np.inf], np.nan)
        out = out.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
        return out

    @staticmethod
    def _scale(values: np.ndarray, mins: np.ndarray, maxs: np.ndarray) -> np.ndarray:
        denom = np.clip(maxs - mins, 1e-8, None)
        return (values - mins) / denom

    @staticmethod
    def _denorm(values: np.ndarray, cmin: float, cmax: float) -> np.ndarray:
        return values * (cmax - cmin) + cmin

    def _get_symbol_scaler(self, symbol: str, feature_values: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, float]:
        payload = self.scalers.get(symbol)
        if payload:
            fmin = np.array(payload["feature_min"], dtype=np.float32)
            fmax = np.array(payload["feature_max"], dtype=np.float32)
            cmin = float(payload["close_min"])
            cmax = float(payload["close_max"])
            return fmin, fmax, cmin, cmax

        # fallback for unseen symbol/scaler file not present
        fmin = feature_values.min(axis=0)
        fmax = feature_values.max(axis=0)
        close_series = feature_values[:, 0]
        cmin = float(close_series.min())
        cmax = float(close_series.max())
        return fmin, fmax, cmin, cmax

    def predict(self, symbol: str, df: pd.DataFrame) -> dict[str, Any]:
        if not self.session or not self.input_name:
            raise RuntimeError(self.model_load_error or "Model not loaded. Place stocksense_model.onnx in backend/model/")

        feat_df = self._engineer_features(df)
        if len(feat_df) < 60:
            raise ValueError("Not enough history to produce a 60-day model input.")

        features = feat_df[FEATURE_COLUMNS].values.astype(np.float32)
        fmin, fmax, cmin, cmax = self._get_symbol_scaler(symbol, features)
        scaled = self._scale(features, fmin, fmax)

        model_input = scaled[-60:]
        model_input = np.expand_dims(model_input.astype(np.float32), axis=0)

        pred_scaled, conf = self.session.run(None, {self.input_name: model_input})
        pred_scaled = pred_scaled[0]
        conf = np.clip(conf[0], 0.0, 1.0)

        pred_prices = self._denorm(pred_scaled, cmin, cmax)

        last_date = pd.to_datetime(df["Date"].iloc[-1]).to_pydatetime()
        future_dates = []
        cursor = last_date
        while len(future_dates) < 7:
            cursor += timedelta(days=1)
            if cursor.weekday() < 5:
                future_dates.append(cursor)

        recent_close = float(df["Close"].iloc[-1])
        predicted_change_pct = ((float(pred_prices[-1]) - recent_close) / recent_close) * 100.0 if recent_close else 0.0
        trend = "BULLISH" if predicted_change_pct >= 0 else "BEARISH"

        # uncertainty band based on confidence and recent volatility
        vol = df["Close"].pct_change().tail(30).std()
        vol = float(0.01 if pd.isna(vol) else max(vol, 0.005))

        days = []
        for i in range(7):
            confidence_i = float(conf[i])
            p = float(pred_prices[i])
            margin_pct = (1.0 - confidence_i) * 0.04 + vol
            margin = p * margin_pct
            days.append(
                {
                    "date": future_dates[i].strftime("%Y-%m-%d"),
                    "predicted_price": round(p, 4),
                    "confidence": round(confidence_i, 4),
                    "lower_bound": round(p - margin, 4),
                    "upper_bound": round(p + margin, 4),
                }
            )

        return {
            "days": days,
            "trend": trend,
            "predicted_change_pct": round(predicted_change_pct, 4),
            "overall_confidence": round(float(np.mean(conf)), 4),
        }
