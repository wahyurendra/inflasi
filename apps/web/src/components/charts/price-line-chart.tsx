"use client";

import { useMemo } from "react";
import {
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
  /** Batas jumlah hari proyeksi yang digambar (sinkron dengan label UI). */
  forecastDays?: number;
  color?: string;
  height?: number;
  showGrid?: boolean;
}

const HISTORY_COLOR = "hsl(var(--chart-history))";
const FORECAST_COLOR = "hsl(var(--chart-forecast))";

function formatRupiah(value: number): string {
  return `Rp ${value.toLocaleString("id-ID")}`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("id-ID", { day: "numeric", month: "short" });
}

function formatRibu(value: number): string {
  return `${(value / 1000).toLocaleString("id-ID", { maximumFractionDigits: 1 })}rb`;
}

/* Skala "nice": domain dibulatkan ke kelipatan step yang enak dibaca
   (1 / 2 / 2.5 / 5 × 10^n) sehingga tick sumbu Y berjarak seragam —
   menggantikan domain mentah yang menghasilkan tick 44/49/55/60/64. */
function niceScale(min: number, max: number, tickCount = 5): { domain: [number, number]; ticks: number[] } {
  if (min === max) {
    min -= 500;
    max += 500;
  }
  const rawStep = (max - min) / (tickCount - 1);
  const mag = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const norm = rawStep / mag;
  const step = norm > 5 ? 10 * mag : norm > 2.5 ? 5 * mag : norm > 2 ? 2.5 * mag : norm > 1 ? 2 * mag : mag;
  const lo = Math.floor(min / step) * step;
  const hi = Math.ceil(max / step) * step;
  const ticks: number[] = [];
  for (let t = lo; t <= hi + step / 2; t += step) ticks.push(t);
  return { domain: [lo, hi], ticks };
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ dataKey: unknown; value: number; color: string }>;
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
            <p key="forecast" className="text-sm font-semibold" style={{ color: FORECAST_COLOR }}>
              Proyeksi: {formatRupiah(p.value)}
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
  forecastDays,
  color = HISTORY_COLOR,
  height = 280,
  showGrid = true,
}: PriceLineChartProps) {
  // Proyeksi yang sah hanyalah titik SETELAH data historis terakhir. Respons
  // API bisa menyertakan prediksi in-sample (tanggal yang tumpang tindih
  // dengan historis) — kalau ikut digambar, sumbu kategori mengulang tanggal
  // dan garis proyeksi "melompat" di sambungan.
  const cleanForecast = useMemo(() => {
    if (!forecastData?.length || !data.length) return [];
    const lastHistorical = new Date(data[data.length - 1].tanggal).getTime();
    const future = forecastData
      .filter((f) => new Date(f.tanggal).getTime() > lastHistorical)
      .sort((a, b) => new Date(a.tanggal).getTime() - new Date(b.tanggal).getTime());
    return forecastDays ? future.slice(0, forecastDays) : future;
  }, [forecastData, data, forecastDays]);

  const hasForecast = showForecast && cleanForecast.length > 0;
  const lastHistoricalDate = data[data.length - 1]?.tanggal;

  const mergedData = useMemo(() => {
    const merged: Array<Record<string, unknown>> = data.map((d) => ({
      tanggal: d.tanggal,
      harga: d.harga,
    }));

    if (hasForecast) {
      // Titik jembatan: garis proyeksi menyambung mulus dari harga terakhir.
      const lastPrice = data[data.length - 1].harga;
      merged[merged.length - 1] = {
        ...merged[merged.length - 1],
        yhat: lastPrice,
        band: [lastPrice, lastPrice],
      };
      for (const f of cleanForecast) {
        merged.push({
          tanggal: f.tanggal,
          yhat: f.yhat,
          band: [f.yhatLower, f.yhatUpper],
        });
      }
    }
    return merged;
  }, [data, cleanForecast, hasForecast]);

  const { domain, ticks, avgPrice } = useMemo(() => {
    const allValues = [
      ...data.map((d) => d.harga),
      ...cleanForecast.flatMap((f) => [f.yhatLower, f.yhatUpper]),
    ];
    const scale = niceScale(Math.min(...allValues), Math.max(...allValues));
    const prices = data.map((d) => d.harga);
    return {
      ...scale,
      avgPrice: prices.reduce((a, b) => a + b, 0) / prices.length,
    };
  }, [data, cleanForecast]);

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

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={mergedData} margin={{ top: 16, right: 12, left: 4, bottom: 5 }}>
        {showGrid && (
          <CartesianGrid strokeDasharray="2 4" stroke="hsl(var(--border))" vertical={false} />
        )}
        <XAxis
          dataKey="tanggal"
          tickFormatter={formatDate}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          tickLine={false}
          tickMargin={6}
          axisLine={{ stroke: "hsl(var(--border))" }}
          minTickGap={28}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={formatRibu}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          tickLine={false}
          axisLine={false}
          domain={domain}
          ticks={ticks}
          width={48}
        />
        <Tooltip
          content={<CustomTooltip />}
          cursor={{ stroke: "hsl(var(--accent))", strokeWidth: 1 }}
        />
        <ReferenceLine
          y={avgPrice}
          stroke="hsl(var(--muted-foreground))"
          strokeOpacity={0.4}
          strokeDasharray="4 4"
          label={{
            value: `Rata-rata ${formatRibu(Math.round(avgPrice))}`,
            position: "insideBottomRight",
            fontSize: 9,
            fill: "hsl(var(--muted-foreground))",
          }}
        />

        {/* Batas historis → proyeksi */}
        {hasForecast && (
          <ReferenceLine
            x={lastHistoricalDate}
            stroke={FORECAST_COLOR}
            strokeDasharray="4 4"
            strokeOpacity={0.5}
            label={{
              value: "Proyeksi →",
              position: "insideTopLeft",
              fontSize: 9,
              fill: FORECAST_COLOR,
            }}
          />
        )}

        {/* Pita interval keyakinan — range area [lower, upper], bukan dua
            area bertumpuk yang menutupi grid di belakangnya */}
        {hasForecast && (
          <Area
            type="monotone"
            dataKey="band"
            stroke="none"
            fill={FORECAST_COLOR}
            fillOpacity={0.12}
            activeDot={false}
            connectNulls={false}
          />
        )}

        {/* Garis harga historis */}
        <Line
          type="monotone"
          dataKey="harga"
          stroke={color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, stroke: color, strokeWidth: 2, fill: "hsl(var(--card))" }}
          connectNulls={false}
        />

        {/* Garis proyeksi */}
        {hasForecast && (
          <Line
            type="monotone"
            dataKey="yhat"
            stroke={FORECAST_COLOR}
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={false}
            activeDot={{
              r: 4,
              stroke: FORECAST_COLOR,
              strokeWidth: 2,
              fill: "hsl(var(--card))",
            }}
            connectNulls={false}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
