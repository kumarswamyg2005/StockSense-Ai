import { Activity, Droplet, Hash, TrendingUp, DollarSign } from "lucide-react";

export default function StockStats({ stock }) {
  if (!stock || !stock.technical_indicators) return null;

  const {
    sma_20,
    sma_50,
    rsi,
    macd,
    macd_signal,
    volatility,
  } = stock.technical_indicators;

  const stats = [
    {
      label: "SMA 20 Day",
      value: sma_20 ? sma_20.toFixed(2) : "N/A",
      icon: TrendingUp,
    },
    {
      label: "SMA 50 Day",
      value: sma_50 ? sma_50.toFixed(2) : "N/A",
      icon: TrendingUp,
    },
    {
      label: "React Strength Index",
      value: rsi ? rsi.toFixed(2) : "N/A",
      icon: Activity,
    },
    {
      label: "MACD Delta",
      value: macd && macd_signal ? (macd - macd_signal).toFixed(3) : "N/A",
      icon: Hash,
    },
    {
      label: "Realized Volatility",
      value: volatility ? volatility.toFixed(4) : "N/A",
      icon: Droplet,
    },
    {
      label: "Market Phase",
      value: rsi ? (rsi > 70 ? "Overbought" : rsi < 30 ? "Oversold" : "Neutral") : "N/A",
      icon: DollarSign,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.label}
            className="flex items-center gap-4 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-[var(--shadow-subtle)] transition-all hover:shadow-[var(--shadow-hover)] hover:-translate-y-1"
          >
            <div className="rounded-full bg-[var(--color-bg)] text-[var(--color-text-primary)] p-2">
              <Icon size={18} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-text-secondary)]">{stat.label}</p>
              <p className="text-lg font-bold mono-font text-[var(--color-text-primary)] mt-1 tracking-tight">{stat.value}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
