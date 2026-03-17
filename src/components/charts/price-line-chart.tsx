"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from "recharts";

interface PriceDataPoint {
  tanggal: string;
  harga: number;
}

interface ForecastDataPoint {
  tanggal: string;
  yhat: number;
  yhatLower: number;
  yhatUpper: number;
}

interface PriceLineChartProps {
  data: PriceDataPoint[];
  forecastData?: ForecastDataPoint[];
  showForecast?: boolean;
  color?: string;
  height?: number;
  showGrid?: boolean;
}

function formatRupiah(value: number): string {
  return `Rp ${value.toLocaleString("id-ID")}`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("id-ID", { day: "numeric", month: "short" });
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ dataKey: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length || !label) return null;

  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-lg">
      <p className="text-xs text-muted-foreground">{formatDate(label)}</p>
      {payload.map((p) => {
        if (p.dataKey === "harga" && p.value) {
          return (
            <p key="harga" className="text-sm font-semibold text-foreground">
              {formatRupiah(p.value)}
            </p>
          );
        }
        if (p.dataKey === "yhat" && p.value) {
          return (
            <p key="forecast" className="text-sm font-semibold text-orange-600">
              Forecast: {formatRupiah(p.value)}
            </p>
          );
        }
        return null;
      })}
    </div>
  );
}

export function PriceLineChart({
  data,
  forecastData,
  showForecast = true,
  color = "#2563eb",
  height = 280,
  showGrid = true,
}: PriceLineChartProps) {
  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border bg-muted/50 text-muted-foreground"
        style={{ height }}
      >
        Tidak ada data untuk ditampilkan
      </div>
    );
  }

  // Merge historical + forecast data
  const mergedData: Array<Record<string, unknown>> = data.map((d) => ({
    tanggal: d.tanggal,
    harga: d.harga,
  }));

  const hasForecast = showForecast && forecastData && forecastData.length > 0;
  const lastHistoricalDate = data[data.length - 1]?.tanggal;

  if (hasForecast) {
    // Add bridge point (last historical + first forecast)
    mergedData[mergedData.length - 1] = {
      ...mergedData[mergedData.length - 1],
      yhat: data[data.length - 1].harga,
      yhatLower: data[data.length - 1].harga,
      yhatUpper: data[data.length - 1].harga,
    };

    for (const f of forecastData!) {
      mergedData.push({
        tanggal: f.tanggal,
        yhat: f.yhat,
        yhatLower: f.yhatLower,
        yhatUpper: f.yhatUpper,
      });
    }
  }

  // Calculate Y axis domain from all values
  const allValues = [
    ...data.map((d) => d.harga),
    ...(hasForecast ? forecastData!.map((f) => f.yhatUpper) : []),
    ...(hasForecast ? forecastData!.map((f) => f.yhatLower) : []),
  ];
  const minVal = Math.min(...allValues);
  const maxVal = Math.max(...allValues);
  const padding = (maxVal - minVal) * 0.1 || 500;

  const prices = data.map((d) => d.harga);
  const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={mergedData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
        <XAxis
          dataKey="tanggal"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}rb`}
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          tickLine={false}
          axisLine={false}
          domain={[minVal - padding, maxVal + padding]}
          width={50}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine
          y={avgPrice}
          stroke="#d1d5db"
          strokeDasharray="4 4"
          label={{
            value: `Rata-rata: ${formatRupiah(Math.round(avgPrice))}`,
            position: "right",
            fontSize: 10,
            fill: "#9ca3af",
          }}
        />

        {/* Forecast/Historical boundary */}
        {hasForecast && (
          <ReferenceLine
            x={lastHistoricalDate}
            stroke="#f97316"
            strokeDasharray="4 4"
            label={{
              value: "Forecast →",
              position: "top",
              fontSize: 10,
              fill: "#f97316",
            }}
          />
        )}

        {/* Confidence interval band */}
        {hasForecast && (
          <Area
            type="monotone"
            dataKey="yhatUpper"
            stroke="none"
            fill="#fed7aa"
            fillOpacity={0.4}
          />
        )}
        {hasForecast && (
          <Area
            type="monotone"
            dataKey="yhatLower"
            stroke="none"
            fill="hsl(var(--card))"
            fillOpacity={1}
          />
        )}

        {/* Historical price line */}
        <Line
          type="monotone"
          dataKey="harga"
          stroke={color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, stroke: color, strokeWidth: 2, fill: "hsl(var(--card))" }}
          connectNulls={false}
        />

        {/* Forecast line */}
        {hasForecast && (
          <Line
            type="monotone"
            dataKey="yhat"
            stroke="#f97316"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={false}
            activeDot={{ r: 4, stroke: "#f97316", strokeWidth: 2, fill: "hsl(var(--card))" }}
            connectNulls={false}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
