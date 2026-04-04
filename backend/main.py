from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from predictor import ONNXPredictor
from signal_generator import generate_signal
from stock_data import StockDataService

app = FastAPI(title="StockSense AI API", version="1.0.0")

_extra = os.environ.get("ALLOWED_ORIGINS", "")
_allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://[::1]:5173",
] + [o.strip() for o in _extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = Path(__file__).resolve().parent
model_path = base_dir / "model" / "stocksense_model.onnx"
scaler_path = base_dir / "model" / "scalers.json"

stock_service = StockDataService()
predictor = ONNXPredictor(model_path=model_path, scaler_path=scaler_path)
signal_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=256, ttl=600)


def _heuristic_signal_from_quote(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("data_unavailable"):
        return {
            "signal": None,
            "strength": "N/A",
            "confidence": 0.0,
            "reasons": ["Live market data is currently unavailable for this symbol."],
            "risk_level": "Unknown",
            "disclaimer": "Signal unavailable until live data is reachable.",
        }

    try:
        pct = float(item.get("daily_change_pct", 0.0))
    except Exception:
        pct = 0.0

    if pct >= 1.2:
        signal = "BUY"
    elif pct <= -1.2:
        signal = "SELL"
    else:
        signal = "HOLD"

    abs_pct = abs(pct)
    if abs_pct >= 2.5:
        strength = "Strong"
    elif abs_pct >= 1.2:
        strength = "Moderate"
    else:
        strength = "Weak"

    confidence = min(0.8, max(0.45, 0.45 + abs_pct / 10.0))

    if signal == "BUY":
        reasons = [f"Price momentum positive today ({pct:.2f}%)"]
    elif signal == "SELL":
        reasons = [f"Price momentum negative today ({pct:.2f}%)"]
    else:
        reasons = [f"Price move is range-bound today ({pct:.2f}%)"]

    return {
        "signal": signal,
        "strength": strength,
        "confidence": round(confidence, 4),
        "reasons": reasons,
        "risk_level": "Medium",
        "disclaimer": "This is a quick signal for filtering. Open stock details for full AI signal.",
    }


def _attach_signals_to_stocks(stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []

    for item in stocks:
        symbol = str(item.get("symbol", "")).upper()
        out = dict(item)
        if not symbol:
            out["signal"] = None
            enriched.append(out)
            continue

        cached_signal = signal_cache.get(symbol)
        if cached_signal:
            out["signal"] = dict(cached_signal)
            enriched.append(out)
            continue

        out["signal"] = _heuristic_signal_from_quote(out)

        enriched.append(out)

    return enriched


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_loaded": predictor.is_ready,
        "model_error": predictor.model_load_error,
        "model_path": str(model_path),
        "scalers_loaded": len(predictor.scalers),
        "disclaimer": "Not financial advice",
    }


@app.get("/search")
def search(q: str = Query("", description="Stock search query")) -> dict:
    return {"query": q, "results": stock_service.search_stocks(q)}


@app.get("/trending")
def trending(
    include_signals: bool = Query(False, description="Include BUY/HOLD/SELL signal per stock"),
    signal: str | None = Query(None, description="Optional filter: BUY, HOLD, or SELL"),
    limit: int = Query(10, ge=1, le=500),
) -> dict:
    requested_signal = signal.upper() if signal else None
    needs_signals = include_signals or requested_signal in {"BUY", "HOLD", "SELL"}

    fetch_limit = max(200 if requested_signal in {"BUY", "HOLD", "SELL"} else limit, 20 if needs_signals else limit)
    stocks = stock_service.get_trending(limit=fetch_limit)

    if needs_signals:
        stocks = _attach_signals_to_stocks(stocks)

    if requested_signal in {"BUY", "HOLD", "SELL"}:
        stocks = [
            item
            for item in stocks
            if (item.get("signal") or {}).get("signal") == requested_signal
        ]

    return {
        "stocks": stocks[:limit],
        "filter": requested_signal or "ALL",
        "include_signals": needs_signals,
    }


@app.get("/market-overview")
def market_overview() -> dict:
    return {"indices": stock_service.get_market_overview()}


@app.get("/stock/{symbol}/history")
def stock_history(symbol: str) -> dict:
    try:
        history = stock_service.get_history(symbol, period="1y")
        return {"symbol": symbol.upper(), "history": history}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch history: {e}")


@app.get("/stock/{symbol}")
def stock(symbol: str) -> dict:
    try:
        snapshot = stock_service.get_stock_snapshot(symbol)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch stock data: {e}")

    try:
        predictions = predictor.predict(snapshot.symbol, snapshot.dataframe)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Prediction unavailable. Ensure ONNX model/scalers are present. Error: {e}",
        )

    signal = generate_signal(
        prediction=predictions,
        technicals=snapshot.technical_indicators,
        current_price=snapshot.current_price,
    )
    signal_cache[snapshot.symbol] = signal

    return {
        "symbol": snapshot.symbol,
        "name": snapshot.name,
        "current_price": snapshot.current_price,
        "currency": snapshot.currency,
        "daily_change": snapshot.daily_change,
        "daily_change_pct": snapshot.daily_change_pct,
        "week_52_high": snapshot.week_52_high,
        "week_52_low": snapshot.week_52_low,
        "market_cap": snapshot.market_cap,
        "volume": snapshot.volume,
        "technical_indicators": {
            "rsi": snapshot.technical_indicators["rsi"],
            "macd": snapshot.technical_indicators["macd"],
            "ma_50": snapshot.technical_indicators["ma_50"],
            "ma_200": snapshot.technical_indicators["ma_200"],
            "bollinger_upper": snapshot.technical_indicators["bollinger_upper"],
            "bollinger_lower": snapshot.technical_indicators["bollinger_lower"],
        },
        "historical_prices": snapshot.historical_prices,
        "predictions": {
            "days": predictions["days"],
            "trend": predictions["trend"],
            "predicted_change_pct": predictions["predicted_change_pct"],
        },
        "signal": signal,
        "disclaimer": "Not financial advice",
    }
