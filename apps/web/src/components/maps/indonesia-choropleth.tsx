"use client";

import { useMemo, useState } from "react";
import { PROVINCE_PATHS } from "./province-paths";
import { AlertTriangle, Info } from "lucide-react";

interface RegionData {
  kodeWilayah: string;
  namaProvinsi: string;
  avgPriceChange: number;
  riskCategory: "rendah" | "sedang" | "tinggi";
  alertCount?: number;
  hasAlert?: boolean;
}

interface IndonesiaChoroplethProps {
  data: RegionData[];
  mode?: "price_change" | "risk";
  selectedKode?: string | null;
  onRegionClick?: (kodeWilayah: string) => void;
}

// Theme-token based colors. "No data" stays clearly distinct from the data
// scale so users can tell missing observations apart from low pressure.
const NO_DATA_COLOR = "hsl(var(--muted))";
const NO_DATA_STROKE = "hsl(var(--border))";

// Sequential pressure scale. Negative or near-zero changes use cool muted
// tones — they signal "no inflationary pressure" without alarming. Positive
// changes ramp into the risk traffic-light at thresholds matching the legend.
function getPriceColor(change: number): { fill: string; bucket: number } {
  if (change > 10) return { fill: "hsl(var(--risk-critical))", bucket: 4 };
  if (change > 5) return { fill: "hsl(var(--risk-high))", bucket: 3 };
  if (change > 2) return { fill: "hsl(var(--risk-medium))", bucket: 2 };
  if (change > 0) return { fill: "hsl(var(--risk-low))", bucket: 1 };
  // Decreases or zero — cool teal/slate. Looks distinct from "low pressure"
  // without competing for attention.
  return { fill: "hsl(195 40% 70%)", bucket: 0 };
}

function getRiskColor(risk: string): string {
  if (risk === "tinggi") return "hsl(var(--risk-critical))";
  if (risk === "sedang") return "hsl(var(--risk-high))";
  return "hsl(var(--risk-low))";
}

export function IndonesiaChoropleth({
  data,
  mode = "price_change",
  selectedKode = null,
  onRegionClick,
}: IndonesiaChoroplethProps) {
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const dataMap = useMemo(() => {
    const map = new Map<string, RegionData>();
    data.forEach((d) => map.set(d.kodeWilayah, d));
    return map;
  }, [data]);

  const stats = useMemo(() => {
    const tinggi = data.filter((d) => d.avgPriceChange > 5).length;
    const sedang = data.filter(
      (d) => d.avgPriceChange > 2 && d.avgPriceChange <= 5,
    ).length;
    const rendah = data.filter(
      (d) => d.avgPriceChange > 0 && d.avgPriceChange <= 2,
    ).length;
    const turun = data.filter((d) => d.avgPriceChange <= 0).length;
    const noData =
      Object.keys(PROVINCE_PATHS).length - data.filter((d) => dataMap.has(d.kodeWilayah)).length;
    const alertCount = data.reduce((sum, d) => sum + (d.alertCount ?? 0), 0);
    return { tinggi, sedang, rendah, turun, noData, alertCount };
  }, [data, dataMap]);

  const hoveredData = hoveredRegion ? dataMap.get(hoveredRegion) : null;

  return (
    <div className="w-full relative">
      {/* Quick stats strip */}
      <div className="flex items-center justify-between gap-3 mb-2 px-1 flex-wrap">
        <div className="flex items-center gap-3 text-[11px]">
          {mode === "price_change" ? (
            <>
              <StatChip color="hsl(var(--risk-critical))" label="Tinggi" value={stats.tinggi} />
              <StatChip color="hsl(var(--risk-high))" label="Naik 5–10%" value={stats.sedang} />
              <StatChip color="hsl(var(--risk-medium))" label="Naik 2–5%" value={stats.rendah} />
              <StatChip color="hsl(195 40% 70%)" label="Stabil/turun" value={stats.turun} />
            </>
          ) : (
            <>
              <StatChip
                color="hsl(var(--risk-critical))"
                label="Risiko Tinggi"
                value={data.filter((d) => d.riskCategory === "tinggi").length}
              />
              <StatChip
                color="hsl(var(--risk-high))"
                label="Sedang"
                value={data.filter((d) => d.riskCategory === "sedang").length}
              />
              <StatChip
                color="hsl(var(--risk-low))"
                label="Rendah"
                value={data.filter((d) => d.riskCategory === "rendah").length}
              />
            </>
          )}
        </div>
        {stats.alertCount > 0 && (
          <span className="inline-flex items-center gap-1 text-[10px] text-risk-high">
            <AlertTriangle className="h-2.5 w-2.5" />
            {stats.alertCount} alert aktif
          </span>
        )}
      </div>

      <svg
        viewBox="-5 -5 710 300"
        className="w-full h-auto"
        style={{ minHeight: 260 }}
      >
        {/* Ocean / water backdrop — subtle cool tint so land masses pop */}
        <defs>
          <linearGradient id="ocean" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(210 30% 97%)" />
            <stop offset="100%" stopColor="hsl(210 25% 95%)" />
          </linearGradient>
          <filter id="province-shadow" x="-2%" y="-2%" width="104%" height="104%">
            <feDropShadow
              dx="0"
              dy="0.5"
              stdDeviation="0.4"
              floodColor="hsl(var(--foreground))"
              floodOpacity="0.15"
            />
          </filter>
        </defs>
        <rect
          x="-5"
          y="-5"
          width="710"
          height="300"
          fill="url(#ocean)"
          rx={8}
        />

        {/* Province paths */}
        {Object.entries(PROVINCE_PATHS).map(([kode, { d }]) => {
          const regionData = dataMap.get(kode);
          const hasData = !!regionData;
          const change = regionData?.avgPriceChange ?? 0;
          const risk = regionData?.riskCategory ?? "rendah";
          const colorInfo =
            mode === "risk"
              ? { fill: getRiskColor(risk), bucket: -1 }
              : getPriceColor(change);
          const fill = !hasData ? NO_DATA_COLOR : colorInfo.fill;
          const alertCount = regionData?.alertCount ?? 0;
          // Only "critical" alert count (≥3) warrants the attention-grabbing
          // pulsing outline — otherwise the map looks chaotic when most
          // provinces have at least one alert.
          const criticalAlert = alertCount >= 3;
          const isSelected = selectedKode === kode;
          const isHovered = hoveredRegion === kode;

          return (
            <g key={kode}>
              {criticalAlert && (
                <path
                  d={d}
                  fill="none"
                  stroke="hsl(var(--risk-critical))"
                  strokeWidth={2.5}
                  opacity={0.45}
                  className="animate-pulse"
                  style={{ animationDuration: "2s" }}
                />
              )}
              <path
                d={d}
                fill={fill}
                stroke={
                  isSelected
                    ? "hsl(var(--primary))"
                    : !hasData
                      ? NO_DATA_STROKE
                      : "hsl(var(--card))"
                }
                strokeWidth={isSelected ? 1.5 : 0.5}
                fillOpacity={!hasData ? 0.55 : isHovered ? 1 : 0.92}
                filter={hasData ? "url(#province-shadow)" : undefined}
                className="cursor-pointer transition-all duration-150"
                onClick={() => onRegionClick?.(kode)}
                onMouseEnter={(e) => {
                  setHoveredRegion(kode);
                  const svg = e.currentTarget.ownerSVGElement;
                  if (svg) {
                    const pt = svg.createSVGPoint();
                    pt.x = e.clientX;
                    pt.y = e.clientY;
                    const svgP = pt.matrixTransform(svg.getScreenCTM()?.inverse());
                    setTooltipPos({ x: svgP.x, y: svgP.y });
                  }
                }}
                onMouseLeave={() => setHoveredRegion(null)}
              />
              {alertCount > 0 && !criticalAlert && (
                <PathCentroidBadge d={d} count={alertCount} />
              )}
            </g>
          );
        })}

        {/* Tooltip */}
        {hoveredRegion && (
          <g
            transform={`translate(${tooltipPos.x + 10}, ${tooltipPos.y - 36})`}
            pointerEvents="none"
          >
            {(() => {
              const name = hoveredData?.namaProvinsi ?? "Wilayah";
              const change = hoveredData?.avgPriceChange ?? 0;
              const detail = hoveredData
                ? mode === "risk"
                  ? `Risiko: ${hoveredData.riskCategory}`
                  : `${change > 0 ? "+" : ""}${change.toFixed(1)}% rata-rata 7H`
                : "Belum ada data";
              const alertText =
                hoveredData?.alertCount && hoveredData.alertCount > 0
                  ? `${hoveredData.alertCount} alert aktif`
                  : null;
              const width = Math.max(
                name.length * 6.5 + 24,
                Math.max(detail.length * 5.5, alertText ? alertText.length * 5.5 : 0) + 24,
                150,
              );
              const height = alertText ? 44 : 32;
              return (
                <>
                  <rect
                    x={0}
                    y={0}
                    width={width}
                    height={height}
                    fill="hsl(var(--card))"
                    stroke="hsl(var(--border))"
                    strokeWidth={0.5}
                    rx={4}
                  />
                  <text
                    x={8}
                    y={12}
                    fill="hsl(var(--foreground))"
                    fontSize={9}
                    fontWeight="600"
                  >
                    {name}
                  </text>
                  <text
                    x={8}
                    y={24}
                    fill="hsl(var(--muted-foreground))"
                    fontSize={8}
                  >
                    {detail}
                  </text>
                  {alertText && (
                    <text
                      x={8}
                      y={36}
                      fill="hsl(var(--risk-high))"
                      fontSize={7.5}
                      fontWeight="500"
                    >
                      ⚠ {alertText}
                    </text>
                  )}
                </>
              );
            })()}
          </g>
        )}
      </svg>

      {/* Legend */}
      <div className="mt-2 flex items-center justify-between gap-3 flex-wrap px-1">
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <Info className="h-3 w-3" />
          {mode === "price_change"
            ? "Rata-rata perubahan harga 7 hari per provinsi"
            : "Kategori risiko inflasi berdasar skor multi-faktor"}
        </div>
        <div className="flex items-center gap-1">
          {mode === "risk" ? (
            <>
              <ScaleStop color="hsl(var(--risk-low))" label="Rendah" />
              <ScaleStop color="hsl(var(--risk-high))" label="Sedang" />
              <ScaleStop color="hsl(var(--risk-critical))" label="Tinggi" />
            </>
          ) : (
            <>
              <ScaleStop color="hsl(195 40% 70%)" label="≤ 0%" />
              <ScaleStop color="hsl(var(--risk-low))" label="0–2%" />
              <ScaleStop color="hsl(var(--risk-medium))" label="2–5%" />
              <ScaleStop color="hsl(var(--risk-high))" label="5–10%" />
              <ScaleStop color="hsl(var(--risk-critical))" label="> 10%" />
            </>
          )}
          {stats.noData > 0 && (
            <ScaleStop color={NO_DATA_COLOR} label={`N/A (${stats.noData})`} outline />
          )}
        </div>
      </div>
    </div>
  );
}

function StatChip({
  color,
  label,
  value,
}: {
  color: string;
  label: string;
  value: number;
}) {
  return (
    <span className="inline-flex items-center gap-1 text-muted-foreground">
      <span
        className="h-2 w-2 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="tabular-nums font-semibold text-foreground">{value}</span>
      <span>{label}</span>
    </span>
  );
}

function ScaleStop({
  color,
  label,
  outline,
}: {
  color: string;
  label: string;
  outline?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
      <span
        className={`h-3 w-3 rounded-sm ${outline ? "border border-border" : ""}`}
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  );
}

/**
 * Tiny inline badge for non-critical alerts. We don't have province centroids
 * pre-computed, so instead of rendering at the visual center we anchor at the
 * first M-command coordinate of the path — visually close enough for a marker
 * and avoids the cost of a bounding-box calculation per path on every render.
 */
function PathCentroidBadge({ d, count }: { d: string; count: number }) {
  const match = /M\s*(-?\d+\.?\d*)\s*[,\s]\s*(-?\d+\.?\d*)/.exec(d);
  if (!match) return null;
  const cx = parseFloat(match[1]);
  const cy = parseFloat(match[2]);
  return (
    <g transform={`translate(${cx}, ${cy})`} pointerEvents="none">
      <circle r={3} fill="hsl(var(--risk-high))" stroke="hsl(var(--card))" strokeWidth={0.6} />
      <text
        x={0}
        y={1.6}
        fill="white"
        fontSize={4}
        fontWeight="700"
        textAnchor="middle"
      >
        {count > 9 ? "9+" : count}
      </text>
    </g>
  );
}
