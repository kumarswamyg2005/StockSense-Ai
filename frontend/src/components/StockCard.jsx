export default function StockCard({ stock, onClick }) {
  const hasChange = typeof stock.daily_change_pct === "number";
  const up = hasChange ? stock.daily_change_pct >= 0 : null;
  const signal = stock.signal?.signal;
  const hasPrice = typeof stock.price === "number";
  const hasDailyChange = typeof stock.daily_change === "number";

  const signalTone = {
    BUY: "bg-[var(--color-chart)]/20 text-[var(--color-chart)]",
    HOLD: "bg-[var(--color-text-secondary)]/20 text-[var(--color-text-secondary)]",
    SELL: "bg-[#FF3366]/20 text-[#FF3366]",
  };

  return (
    <button
      onClick={onClick}
      className="card-strong w-full text-left transition-all hover:-translate-y-1 hover:shadow-[var(--shadow-hover)] hover:border-[var(--color-chart)]/50 group relative overflow-hidden"
    >
      <div className="absolute top-[-50px] right-[-50px] w-32 h-32 bg-[var(--color-chart)] opacity-[0.03] rounded-full blur-2xl pointer-events-none group-hover:opacity-[0.08] transition-opacity duration-500"></div>

      <div className="flex items-start justify-between relative z-10">
        <div>
          <p className="text-[0.65rem] font-bold uppercase tracking-widest text-[var(--color-text-secondary)] mb-1">
            {stock.symbol}
          </p>
          <h3 className="text-lg font-bold font-[Sora] text-[var(--color-text-primary)] leading-tight">
            {stock.name}
          </h3>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          {signal ? (
            <span
              className={`rounded-[var(--radius-sm)] px-2 py-0.5 text-[0.6rem] font-bold uppercase tracking-widest ${signalTone[signal] || "bg-[var(--color-border)] text-[var(--color-text-secondary)]"}`}
            >
              {signal}
            </span>
          ) : null}
          <span
            className={`rounded-[var(--radius-sm)] px-2 py-0.5 text-xs font-semibold mono-font tracking-tight ${!hasChange ? "bg-[var(--color-border)] text-[var(--color-text-secondary)]" : up ? "bg-gain text-gain" : "bg-loss text-loss"}`}
          >
            {!hasChange
              ? "Unavailable"
              : `${up ? "+" : ""}${stock.daily_change_pct}%`}
          </span>
        </div>
      </div>

      <p className="mt-6 text-[1.75rem] font-extrabold mono-font tracking-tighter text-[var(--color-text-primary)] relative z-10">
        {hasPrice ? stock.price : "—"}
      </p>
      <p
        className={`text-sm font-semibold mono-font tracking-tight mt-1 relative z-10 ${!hasDailyChange ? "text-[var(--color-text-secondary)]" : up ? "text-gain" : "text-loss"}`}
      >
        {!hasDailyChange
          ? "Connecting..."
          : `${up ? "+" : ""}${stock.daily_change}`}
      </p>
    </button>
  );
}
