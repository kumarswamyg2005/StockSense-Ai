export default function ConfidenceBar({ confidence = 0 }) {
  const value = Math.max(0, Math.min(100, confidence * 100));
  const level = value >= 70 ? "High" : value >= 50 ? "Medium" : "Low";

  let color =
    value >= 70
      ? "from-[var(--color-gain)] to-emerald-400"
      : value >= 50
        ? "from-amber-400 to-yellow-300"
        : "from-[var(--color-loss)] to-rose-400";

  return (
    <div className="card-strong">
      <div className="mb-4 flex flex-col md:flex-row md:items-center justify-between gap-2">
        <h4 className="text-sm font-bold uppercase tracking-widest text-[var(--color-text-secondary)] font-[Sora]">
          Model Convolution Confidence
        </h4>
        <span className="rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1 text-sm font-bold mono-font tracking-tight text-[var(--color-text-primary)]">
          {value.toFixed(1)}%
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--color-border)]">
        <div
          className={`h-full bg-gradient-to-r ${color} transition-all duration-700 ease-out`}
          style={{ width: `${value}%` }}
        />
      </div>
      <p className="mt-4 text-[0.7rem] uppercase tracking-widest text-[var(--color-text-secondary)] font-bold">
        Threshold:{" "}
        <span className="font-extrabold text-[var(--color-text-primary)]">
          {level}
        </span>
        .
        <span className="opacity-70 normal-case tracking-normal ml-1">
          Statistical certainty based on historical pattern recognition.
        </span>
      </p>
    </div>
  );
}
