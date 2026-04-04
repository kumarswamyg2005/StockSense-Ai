import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function PredictionChart({ historical = [], predictions = [] }) {
  const formatDate = (value) => {
    if (!value) return "";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
  };

  const hist30 = historical.slice(-30).map((d) => ({
    date: d.date,
    historical: d.close,
    predicted: null,
    lower_bound: null,
    upper_bound: null,
  }));

  const pred = predictions.map((d) => ({
    date: d.date,
    historical: null,
    predicted: d.predicted_price,
    lower_bound: d.lower_bound,
    upper_bound: d.upper_bound,
  }));

  const data = [...hist30, ...pred];

  return (
    <div className="h-[420px] relative">
      <h3 className="mb-4 text-lg font-bold font-[Sora] text-[var(--color-text-primary)]">
        Algorithmic 7-Day Forecast
        <p className="text-[0.65rem] font-bold text-[var(--color-text-secondary)] uppercase tracking-[0.2em] mt-1">
          Deep learning projection band
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
            minTickGap={30}
            interval="preserveStartEnd"
            tickFormatter={formatDate}
            tick={{ fill: "var(--chart-axis)", fontSize: 12 }}
            axisLine={{ stroke: "var(--chart-grid)" }}
            tickLine={false}
            height={42}
            tickMargin={8}
          />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fill: "var(--chart-axis)", fontSize: 12 }}
            axisLine={{ stroke: "var(--chart-grid)" }}
            tickLine={{ stroke: "var(--chart-grid)" }}
            width={42}
          />
          <Tooltip
            contentStyle={{
              background: "var(--chart-tooltip-bg)",
              border: "1px solid var(--chart-tooltip-border)",
              borderRadius: "12px",
            }}
            labelStyle={{ color: "var(--chart-tooltip-text)", fontWeight: 600 }}
            itemStyle={{ color: "var(--chart-tooltip-text)" }}
          />
          <Legend />

          <Area
            type="monotone"
            dataKey="upper_bound"
            stroke="none"
            fill="var(--color-chart)"
            fillOpacity={0.1}
            name="Estimate Range"
            baseLine={(entry) =>
              entry.lower_bound || entry.predicted || entry.historical
            }
          />

          <Line
            type="monotone"
            dataKey="historical"
            stroke="var(--color-text-secondary)"
            strokeWidth={3}
            dot={false}
            name="Past Price"
          />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="var(--color-chart)"
            strokeWidth={3}
            strokeDasharray="6 4"
            dot={{
              r: 4,
              fill: "var(--color-bg)",
              stroke: "var(--color-chart)",
              strokeWidth: 2,
            }}
            name="AI Estimate"
          />
          <Line
            type="monotone"
            dataKey="lower_bound"
            stroke="var(--color-chart)"
            strokeOpacity={0.4}
            dot={false}
            name="Lower"
          />
          <Line
            type="monotone"
            dataKey="upper_bound"
            stroke="var(--color-chart)"
            strokeOpacity={0.4}
            dot={false}
            name="Upper"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
