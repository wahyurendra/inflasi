"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";

interface InflationDataPoint {
  periode: string;
  mtm: number | null;
}

interface InflationTrendChartProps {
  data: InflationDataPoint[];
  height?: number;
  loading?: boolean;
}

function formatMonth(periode: string): string {
  try {
    const d = new Date(periode);
    return d.toLocaleDateString("id-ID", { month: "short", year: "2-digit" });
  } catch {
    return periode;
  }
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: { periode: string } }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  const value = payload[0].value;
  return (
    <div className="rounded-md border bg-card px-3 py-1.5 shadow-sm">
      <p className="text-[10px] text-muted-foreground uppercase">{label}</p>
      <p
        className={`text-sm font-semibold ${
          value >= 0 ? "text-risk-critical" : "text-risk-low"
        }`}
      >
        {value > 0 ? "+" : ""}
        {value.toFixed(2)}%
      </p>
    </div>
  );
}

export function InflationTrendChart({
  data,
  height = 200,
  loading = false,
}: InflationTrendChartProps) {
  if (loading) {
    return (
      <div
        className="w-full bg-muted/30 rounded animate-pulse"
        style={{ height }}
      />
    );
  }

  const validData = data.filter((d) => d.mtm !== null) as Array<{
    periode: string;
    mtm: number;
  }>;

  if (!validData.length) {
    return (
      <div
        style={{ height }}
        className="w-full flex items-center justify-center text-xs text-muted-foreground border border-dashed rounded"
      >
        Belum ada data inflasi tersedia.
      </div>
    );
  }

  const chartData = validData.map((d) => ({
    ...d,
    periodeLabel: formatMonth(d.periode),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
        <CartesianGrid
          strokeDasharray="2 4"
          stroke="hsl(var(--border))"
          vertical={false}
        />
        <XAxis
          dataKey="periodeLabel"
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          tickLine={false}
          axisLine={{ stroke: "hsl(var(--border))" }}
        />
        <YAxis
          tickFormatter={(v) => `${v}%`}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          tickLine={false}
          axisLine={false}
          width={42}
        />
        <ReferenceLine y={0} stroke="hsl(var(--border))" strokeWidth={1} />
        <Tooltip
          content={<CustomTooltip />}
          cursor={{ fill: "hsl(var(--accent))", opacity: 0.4 }}
        />
        <Bar dataKey="mtm" radius={[3, 3, 0, 0]} maxBarSize={32}>
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={
                entry.mtm >= 0
                  ? "hsl(var(--risk-critical))"
                  : "hsl(var(--risk-low))"
              }
              fillOpacity={0.85}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
