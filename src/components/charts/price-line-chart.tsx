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
} from "recharts";

interface PriceDataPoint {
  tanggal: string;
  harga: number;
}

interface PriceLineChartProps {
  data: PriceDataPoint[];
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
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length || !label) return null;

  return (
    <div className="bg-white border rounded-lg shadow-lg px-3 py-2">
      <p className="text-xs text-gray-500">{formatDate(label)}</p>
      <p className="text-sm font-semibold text-gray-900">
        {formatRupiah(payload[0].value)}
      </p>
    </div>
  );
}

export function PriceLineChart({
  data,
  color = "#2563eb",
  height = 280,
  showGrid = true,
}: PriceLineChartProps) {
  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center text-gray-400 border rounded-lg bg-gray-50"
        style={{ height }}
      >
        Tidak ada data untuk ditampilkan
      </div>
    );
  }

  const prices = data.map((d) => d.harga);
  const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1 || 500;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
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
          domain={[minPrice - padding, maxPrice + padding]}
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
        <Line
          type="monotone"
          dataKey="harga"
          stroke={color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, stroke: color, strokeWidth: 2, fill: "white" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
