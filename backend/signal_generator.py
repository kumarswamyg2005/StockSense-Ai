from __future__ import annotations

from typing import Any


def generate_signal(
    prediction: dict[str, Any],
    technicals: dict[str, float],
    current_price: float,
) -> dict[str, Any]:
    predicted_change_pct = float(prediction.get("predicted_change_pct", 0.0))
    confidence = float(prediction.get("overall_confidence", 0.5))

    rsi = float(technicals.get("rsi", 50.0))
    macd = float(technicals.get("macd", 0.0))
    macd_signal = float(technicals.get("macd_signal", 0.0))
    ma_50 = float(technicals.get("ma_50", current_price))

    score = 0
    reasons: list[str] = []

    if predicted_change_pct > 1.0:
        score += 2
        reasons.append(f"Price predicted to rise {predicted_change_pct:.2f}% in 7 days")
    elif predicted_change_pct < -1.0:
        score -= 2
        reasons.append(f"Price predicted to fall {abs(predicted_change_pct):.2f}% in 7 days")
    else:
        reasons.append("Short-term trend appears range-bound")

    if rsi < 30:
        score += 1
        reasons.append(f"RSI shows oversold condition at {rsi:.1f}")
    elif rsi > 70:
        score -= 1
        reasons.append(f"RSI shows overbought condition at {rsi:.1f}")

    if macd > macd_signal:
        score += 1
        reasons.append("MACD bullish crossover detected")
    elif macd < macd_signal:
        score -= 1
        reasons.append("MACD bearish crossover detected")

    if current_price > ma_50:
        score += 1
        reasons.append("Price above 50-day moving average")
    else:
        score -= 1
        reasons.append("Price below 50-day moving average")

    if confidence > 0.75:
        score += 1
    elif confidence < 0.45:
        score -= 1

    if score >= 2:
        signal = "BUY"
    elif score <= -2:
        signal = "SELL"
    else:
        signal = "HOLD"

    abs_score = abs(score)
    if abs_score >= 4:
        strength = "Strong"
    elif abs_score >= 2:
        strength = "Moderate"
    else:
        strength = "Weak"

    if confidence >= 0.75:
        risk_level = "Low"
    elif confidence >= 0.55:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "signal": signal,
        "strength": strength,
        "confidence": round(confidence, 4),
        "reasons": reasons,
        "risk_level": risk_level,
        "disclaimer": "This is not financial advice. Always do your own research.",
    }
