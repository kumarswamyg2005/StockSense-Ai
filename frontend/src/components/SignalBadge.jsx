import {
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  XCircle,
} from "lucide-react";

const styleMap = {
  BUY: "border-[var(--color-chart)] bg-[var(--color-chart)]/10 text-[var(--color-chart)]",
  HOLD: "border-amber-500/50 bg-amber-500/10 text-amber-500",
  SELL: "border-[#FF3366]/50 bg-[#FF3366]/10 text-[#FF3366]",
};

const iconMap = {
  BUY: CheckCircle2,
  HOLD: AlertTriangle,
  SELL: XCircle,
};

const plainMeaning = {
  BUY: "Algorithmic edge detected. Consider systematic scaling strategies.",
  HOLD: "Statistical edge absent. Capital preservation favored.",
  SELL: "Downside distribution likely. Strict risk management advised.",
};

export default function SignalBadge({ signal }) {
  const signalValue = signal?.signal;
  const tone = styleMap[signalValue] || "border-[var(--color-border)] bg-[var(--color-border)]/20 text-[var(--color-text-secondary)]";
  const Icon = iconMap[signalValue] || ShieldAlert;
  const meaning = plainMeaning[signalValue] || "Insufficient data to generate a signal. Open for full analysis.";

  return (
    <div
      className={`card-strong border ${tone} bg-transparent backdrop-blur-md relative overflow-hidden`}
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-current opacity-[0.05] rounded-full blur-2xl pointer-events-none mix-blend-screen"></div>
      <div className="mb-4 flex items-start gap-4">
        <Icon size={32} className="opacity-90 mt-1" />
        <div>
          <p className="text-[0.65rem] uppercase tracking-[0.2em] font-bold opacity-70 mb-1">
            Algorithmic Signal
          </p>
          <h3 className="text-[2.5rem] font-extrabold font-[Sora] leading-none tracking-tight">
            {signalValue || "N/A"}
          </h3>
          <p className="text-sm font-semibold mono-font mt-2 tracking-tight">
            Conviction Scale:{" "}
            <span className="opacity-100 uppercase tracking-wider text-xs ml-1 bg-none border border-current px-2 py-0.5 rounded-[var(--radius-sm)]">
              {signal?.strength || "—"}
            </span>
          </p>
          <p className="mt-3 text-[0.8rem] font-medium leading-relaxed opacity-90 border-l-2 border-current pl-3">
            {meaning}
          </p>
        </div>
      </div>
    </div>
  );
}
