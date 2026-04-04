import os

detail_content = """import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "react-query";
import axios from "axios";
import { ArrowLeft, Sparkles, Activity } from "lucide-react";
import ConfidenceBar from "../components/ConfidenceBar";
import PredictionChart from "../components/PredictionChart";
import SignalBadge from "../components/SignalBadge";
import StockChart from "../components/StockChart";
import StockStats from "../components/StockStats";

const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
const protocol = typeof window !== "undefined" ? window.location.protocol : "http:";
const API_BASE = import.meta.env.VITE_API_BASE_URL || `${protocol}//${host}:8000`;

const fetchStock = async (symbol) => {
  let normalized = symbol;
  try {
    normalized = decodeURIComponent(symbol);
  } catch {
    normalized = symbol;
  }
  const { data } = await axios.get(
    `${API_BASE}/stock/${encodeURIComponent(normalized)}`,
  );
  return data;
};

export default function StockDetail() {
  const navigate = useNavigate();
  const { symbol } = useParams();
  const [tab, setTab] = useState("historical");

  const {
    data: stock,
    isLoading,
    error,
  } = useQuery(["stock", symbol], () => fetchStock(symbol), {
    retry: 1,
  });

  const trendUp = (stock?.daily_change_pct || 0) >= 0;
  const confidence = useMemo(() => stock?.signal?.confidence || 0, [stock]);

  const beginnerSummary = useMemo(() => {
    if (!stock) return [];

    const lines = [];
    const action = stock.signal?.signal || "HOLD";
    const strength = stock.signal?.strength || "Moderate";
    const rsi = Number(stock?.technical_indicators?.rsi);
    const predictions = stock?.predictions?.days || [];

    if (action === "BUY") {
      lines.push(
        `AI currently leans positive (${strength.toLowerCase()} strength), indicating potential upside accumulation.`
      );
    } else if (action === "SELL") {
      lines.push(
        `AI observes downside risk (${strength.toLowerCase()} strength), suggesting potential correction ahead.`
      );
    } else {
      lines.push(
        "AI does not detect a firm statistical edge right now. Neutral stance recommended."
      );
    }

    if (predictions.length >= 2) {
      const first = Number(predictions[0]?.predicted_price || 0);
      const last = Number(
        predictions[predictions.length - 1]?.predicted_price || 0,
      );
      if (first > 0) {
        const pct = ((last - first) / first) * 100;
        lines.push(
          `7-day automated projection: ${pct >= 0 ? "up" : "down"} ${Math.abs(pct).toFixed(2)}% variance.`
        );
      }
    }

    if (Number.isFinite(rsi)) {
      if (rsi < 30)
        lines.push(
          "RSI sits in oversold territory, possible reversion zone spotted."
        );
      else if (rsi > 70)
        lines.push(
          "RSI signifies overbought momentum, increasing the probability of a structural pullback."
        );
      else lines.push("RSI indicates neutral relative momentum.");
    }

    return lines.slice(0, 3);
  }, [stock]);

  if (isLoading)
    return (
      <div className="space-y-6 animate-pulse max-w-7xl mx-auto z-10 relative mt-8">
        <div className="h-[200px] rounded-[var(--radius-lg)] bg-[var(--color-border)]/50" />
        <div className="h-[400px] rounded-[var(--radius-lg)] bg-[var(--color-border)]/50" />
      </div>
    );
    
  if (error || !stock)
    return (
      <div className="card-strong max-w-2xl mx-auto mt-16 text-center shadow-[var(--shadow-hover)]">
        <p className="text-[1.5rem] font-extrabold font-[Sora]">Failed to load asset data</p>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          The requested ticker symbol could not be resolved or the server is unavailable.
        </p>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="mt-6 bg-[var(--color-text-primary)] text-white px-6 py-3 rounded-full font-semibold font-[Sora] transition-all hover:bg-[var(--color-chart)] shadow-[var(--shadow-subtle)]"
        >
          Return to Hub
        </button>
      </div>
    );

  return (
    <div className="space-y-8 relative z-10 pt-4 pb-12 max-w-[1400px] mx-auto px-4 md:px-8">
      {/* Background elements inherited from root wrapper */}
      
      <section className="card-strong backdrop-blur-xl bg-[var(--color-surface)]/80 relative overflow-hidden">
        {/* Subtle mesh background for the header card */}
        <div className="absolute top-[-50px] right-[-50px] w-64 h-64 bg-[var(--color-chart)] opacity-[0.04] rounded-full blur-3xl pointer-events-none"></div>
        
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-8 inline-flex items-center gap-2 text-sm text-[var(--color-text-secondary)] transition hover:text-[var(--color-chart)] font-semibold"
        >
          <ArrowLeft size={16} />
          Back to Overview
        </button>

        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
                <p className="px-2 py-1 rounded bg-[var(--color-border)] text-[var(--color-text-primary)] text-sm font-bold mono-font">{stock.symbol}</p>
                <div className="h-4 w-[1px] bg-[var(--color-border)]"></div>
                <p className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-widest">Equity</p>
            </div>
            <h1 className="text-[clamp(2.5rem,4vw,3.5rem)] font-extrabold font-[Sora] tracking-tight leading-tight">{stock.name}</h1>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-[3rem] font-medium mono-font tracking-tighter leading-none">{stock.current_price}</span>
              <span className="text-[1.25rem] font-semibold text-[var(--color-text-secondary)] mono-font">{stock.currency}</span>
            </div>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className={`px-6 py-4 rounded-[var(--radius-md)] text-2xl font-medium mono-font tracking-tight ${trendUp ? 'bg-gain text-gain' : 'bg-loss text-loss'}`}>
                {trendUp ? "+" : ""}{stock.daily_change} 
                <span className="opacity-80 ml-2">({trendUp ? "+" : ""}{stock.daily_change_pct}%)</span>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          <div className="flex rounded-full border border-[var(--color-border)] bg-[var(--color-bg)] p-1.5 shadow-[var(--shadow-subtle)]">
            <button
              className={`flex-1 rounded-full px-4 py-2.5 text-sm font-semibold transition-all ${tab === "historical" ? "bg-[var(--color-surface)] shadow-[var(--shadow-card)] text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"}`}
              onClick={() => setTab("historical")}
            >
              Historical Volume
            </button>
            <button
              className={`flex-1 rounded-full px-4 py-2.5 text-sm font-semibold transition-all ${tab === "prediction" ? "bg-[var(--color-surface)] shadow-[var(--shadow-card)] text-[var(--color-chart)]" : "text-[var(--color-text-secondary)] hover:text-[var(--color-chart)]"}`}
              onClick={() => setTab("prediction")}
            >
              AI Forecast (7d)
            </button>
          </div>

          <div className="card p-6 border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
            {tab === "historical" ? (
              <StockChart data={stock.historical_prices || []} />
            ) : (
              <PredictionChart
                historical={stock.historical_prices || []}
                predictions={stock.predictions?.days || []}
              />
            )}
          </div>

          <StockStats stock={stock} />
        </div>

        <div className="space-y-6">
          <div className="card-strong">
            <SignalBadge signal={stock.signal} />
            <div className="mt-8">
              <ConfidenceBar confidence={confidence} />
            </div>
          </div>

          <section className="card border-l-4 border-l-[var(--color-chart)] bg-[var(--color-surface)] text-[var(--color-text-primary)]">
            <h2 className="text-lg font-bold font-[Sora] flex items-center gap-2 mb-3">
              <Sparkles size={18} className="text-[var(--color-chart)]" /> 
              Algorithmic Summary
            </h2>
            <ul className="mt-2 space-y-3">
              {beginnerSummary.map((item, idx) => (
                <li key={idx} className="flex gap-3 text-sm text-[var(--color-text-secondary)] leading-relaxed relative pl-4 before:content-[''] before:absolute before:left-0 before:top-[8px] before:w-1.5 before:h-1.5 before:rounded-full before:bg-[var(--color-chart)]">
                  {item}
                </li>
              ))}
            </ul>
          </section>

          <div className="card-strong bg-[var(--color-bg)] border-[var(--color-border)]">
            <h3 className="mb-4 text-sm font-bold uppercase tracking-widest text-[var(--color-text-secondary)]">Decision Factors</h3>
            <ul className="space-y-3 text-sm text-[var(--color-text-primary)] font-medium leading-relaxed">
              {(
                stock.signal?.reasons || [
                  "Insufficient historical data to derive deep statistical reasoning.",
                ]
              ).map((reason, idx) => (
                <li key={idx} className="flex align-start gap-2">
                  <span className="text-[var(--color-text-secondary)] opacity-50 mt-0.5">•</span> 
                  {reason}
                </li>
              ))}
            </ul>
          </div>

          <div className="card bg-[var(--color-surface)] border-[var(--color-border)] text-xs text-[var(--color-text-secondary)] opacity-80 hover:opacity-100 transition-opacity">
            <p className="font-bold uppercase tracking-widest mb-2 font-[Sora]">Notice</p>
            <p className="leading-relaxed">
              {stock.signal?.disclaimer ||
                "Models are predictive mechanisms, not guarantees. Outputs are generated computationally without factoring in qualitative macro events. Verify allocations per standard institutional metrics."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
"""

with open("src/pages/StockDetail.jsx", "w") as f:
    f.write(detail_content)

print("Updated StockDetail.jsx via python")
