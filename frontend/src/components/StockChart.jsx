import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function StockChart({ data = [] }) {
  const formatDate = (value) => {
    if (!value) return "";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
  };

  return (
    <div className="h-[420px] relative">
      <h3 className="mb-4 text-lg font-bold font-[Sora] text-[var(--color-text-primary)]">
        Trading Volume & Price Action
        <p className="text-[0.65rem] font-bold text-[var(--color-text-secondary)] uppercase tracking-[0.2em] mt-1">
          6-Month historical analysis
        </p>
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 8, right: 12, left: 0, bottom: 28 }}
        >
          <CartesianGrid
            stroke="var(--chart-grid)"
            strokeDasharray="3 3"
            strokeOpacity={0.5}
          />
          <XAxis
            dataKey="date"
            minTickGap={28}
            interval="preserveStartEnd"
            tickFormatter={formatDate}
            tick={{ fill: "var(--chart-axis)", fontSize: 12 }}
            axisLine={{ stroke: "var(--chart-grid)" }}
            tickLine={false}
            height={42}
            tickMargin={8}
          />
          <YAxis
            yAxisId="price"
            domain={["auto", "auto"]}
            tick={{ fill: "var(--chart-axis)", fontSize: 12 }}
            axisLine={{ stroke: "var(--chart-grid)" }}
            tickLine={{ stroke: "var(--chart-grid)" }}
            width={42}
          />
          <YAxis yAxisId="volume" orientation="right" hide />
          <Tooltip
            contentStyle={{
              background: "var(--chart-tooltip-bg)",
              border: "1px solid var(--chart-tooltip-border)",
              borderRadius: "12px",
            }}
            labelStyle={{ color: "var(--chart-tooltip-text)", fontWeight: 600 }}
            itemStyle={{ color: "var(--chart-tooltip-text)" }}
          />
          <Area
            yAxisId="price"
            type="monotone"
            dataKey="close"
            stroke="var(--color-chart)"
            fill="var(--chart-area-fill)"
            name="Close"
            strokeWidth={3}
            activeDot={{
              r: 6,
              fill: "var(--color-bg)",
              stroke: "var(--color-chart)",
              strokeWidth: 3,
            }}
          />
          <Bar
            yAxisId="volume"
            dataKey="volume"
            fill="var(--color-border)"
            name="Volume"
            maxBarSize={7}
            radius={[2, 2, 0, 0]}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
