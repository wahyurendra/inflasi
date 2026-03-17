"use client";

import { useMemo, useState } from "react";
import { PROVINCE_PATHS } from "./province-paths";

interface RegionData {
  kodeWilayah: string;
  namaProvinsi: string;
  avgPriceChange: number;
  riskCategory: "rendah" | "sedang" | "tinggi";
  hasAlert?: boolean;
}

interface IndonesiaChoroplethProps {
  data: RegionData[];
  mode?: "price_change" | "risk";
  onRegionClick?: (kodeWilayah: string) => void;
}

function getPriceColor(change: number): string {
  if (change > 10) return "#dc2626"; // red-600
  if (change > 5) return "#f97316"; // orange-500
  if (change > 2) return "#eab308"; // yellow-500
  if (change > 0) return "#22c55e"; // green-500
  return "#6b7280"; // gray-500
}

function getRiskColor(risk: string): string {
  if (risk === "tinggi") return "#dc2626";
  if (risk === "sedang") return "#f97316";
  return "#22c55e";
}

export function IndonesiaChoropleth({
  data,
  mode = "price_change",
  onRegionClick,
}: IndonesiaChoroplethProps) {
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const dataMap = useMemo(() => {
    const map = new Map<string, RegionData>();
    data.forEach((d) => map.set(d.kodeWilayah, d));
    return map;
  }, [data]);

  const hoveredData = hoveredRegion ? dataMap.get(hoveredRegion) : null;

  return (
    <div className="w-full relative">
      <svg
        viewBox="-5 -5 710 300"
        className="w-full h-auto"
        style={{ minHeight: 220 }}
      >
        {/* Background */}
        <rect x="-5" y="-5" width="710" height="300" fill="hsl(var(--muted))" rx="8" />

        {/* Province paths */}
        {Object.entries(PROVINCE_PATHS).map(([kode, { d }]) => {
          const regionData = dataMap.get(kode);
          const change = regionData?.avgPriceChange ?? 0;
          const risk = regionData?.riskCategory ?? "rendah";
          const color =
            mode === "risk" ? getRiskColor(risk) : getPriceColor(change);
          const hasAlert = regionData?.hasAlert;

          return (
            <g key={kode}>
              {/* Alert glow outline — rendered behind the main path */}
              {hasAlert && (
                <path
                  d={d}
                  fill="none"
                  stroke="#dc2626"
                  strokeWidth={3}
                  opacity={0.6}
                  className="animate-pulse"
                  style={{ animationDuration: "1.5s" }}
                />
              )}
              <path
                d={d}
                fill={color}
                stroke={hasAlert ? "#dc2626" : "hsl(var(--background))"}
                strokeWidth={hasAlert ? 1.5 : 0.8}
                opacity={
                  hoveredRegion === null || hoveredRegion === kode ? 0.9 : 0.5
                }
                className="cursor-pointer transition-opacity duration-150"
                onClick={() => onRegionClick?.(kode)}
                onMouseEnter={(e) => {
                  setHoveredRegion(kode);
                  const svg = e.currentTarget.ownerSVGElement;
                  if (svg) {
                    const pt = svg.createSVGPoint();
                    pt.x = e.clientX;
                    pt.y = e.clientY;
                    const svgP = pt.matrixTransform(
                      svg.getScreenCTM()?.inverse()
                    );
                    setTooltipPos({ x: svgP.x, y: svgP.y });
                  }
                }}
                onMouseLeave={() => setHoveredRegion(null)}
              />
            </g>
          );
        })}

        {/* Tooltip */}
        {hoveredData && (
          <g
            transform={`translate(${tooltipPos.x + 8}, ${tooltipPos.y - 12})`}
            pointerEvents="none"
          >
            <rect
              x={0}
              y={-14}
              width={Math.max(hoveredData.namaProvinsi.length * 6 + 60, 130)}
              height={34}
              fill="rgba(0,0,0,0.85)"
              rx={4}
            />
            <text x={6} y={0} fill="white" fontSize={9} fontWeight="600">
              {hoveredData.namaProvinsi}
            </text>
            <text x={6} y={13} fill="#d1d5db" fontSize={8}>
              {mode === "risk"
                ? `Risiko: ${hoveredData.riskCategory}`
                : `${hoveredData.avgPriceChange > 0 ? "+" : ""}${hoveredData.avgPriceChange.toFixed(1)}%`}
              {" · "}
              {hoveredData.riskCategory}
            </text>
          </g>
        )}
      </svg>

      {/* Legend */}
      <div className="flex gap-4 mt-3 justify-center">
        {mode === "risk" ? (
          <>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-3 w-3 rounded" style={{ backgroundColor: "#22c55e" }} />
              Rendah
            </span>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-3 w-3 rounded" style={{ backgroundColor: "#f97316" }} />
              Sedang
            </span>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-3 w-3 rounded" style={{ backgroundColor: "#dc2626" }} />
              Tinggi
            </span>
          </>
        ) : (
          <>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-3 w-3 rounded" style={{ backgroundColor: "#22c55e" }} />
              Rendah (&lt;2%)
            </span>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-3 w-3 rounded" style={{ backgroundColor: "#eab308" }} />
              Sedang (2-5%)
            </span>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-3 w-3 rounded" style={{ backgroundColor: "#f97316" }} />
              Tinggi (5-10%)
            </span>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-3 w-3 rounded" style={{ backgroundColor: "#dc2626" }} />
              Sangat Tinggi (&gt;10%)
            </span>
          </>
        )}
      </div>
    </div>
  );
}
