"use client";

import { useMemo } from "react";

interface RegionData {
  kodeWilayah: string;
  namaProvinsi: string;
  avgPriceChange: number;
  riskCategory: "rendah" | "sedang" | "tinggi";
}

interface IndonesiaChoroplethProps {
  data: RegionData[];
  onRegionClick?: (kodeWilayah: string) => void;
}

function getColor(change: number): string {
  if (change > 10) return "#dc2626"; // red-600
  if (change > 5) return "#f97316"; // orange-500
  if (change > 2) return "#eab308"; // yellow-500
  if (change > 0) return "#22c55e"; // green-500
  return "#6b7280"; // gray-500
}

// Simplified province positions for a schematic map
// Using approximate relative positions of Indonesian provinces
const PROVINCE_POSITIONS: Record<string, { x: number; y: number; w: number; h: number }> = {
  "11": { x: 30, y: 40, w: 50, h: 30 },    // Aceh
  "12": { x: 40, y: 70, w: 55, h: 30 },    // Sumut
  "13": { x: 30, y: 100, w: 40, h: 30 },   // Sumbar
  "14": { x: 70, y: 80, w: 50, h: 25 },    // Riau
  "15": { x: 60, y: 105, w: 40, h: 25 },   // Jambi
  "16": { x: 70, y: 130, w: 55, h: 25 },   // Sumsel
  "17": { x: 50, y: 140, w: 35, h: 20 },   // Bengkulu
  "18": { x: 85, y: 155, w: 45, h: 25 },   // Lampung
  "19": { x: 120, y: 120, w: 30, h: 20 },  // Babel
  "21": { x: 110, y: 60, w: 35, h: 20 },   // Kepri
  "31": { x: 160, y: 170, w: 25, h: 20 },  // DKI Jakarta
  "32": { x: 170, y: 190, w: 50, h: 25 },  // Jabar
  "33": { x: 220, y: 195, w: 50, h: 22 },  // Jateng
  "34": { x: 235, y: 218, w: 30, h: 18 },  // DIY
  "35": { x: 270, y: 195, w: 55, h: 25 },  // Jatim
  "36": { x: 140, y: 175, w: 35, h: 20 },  // Banten
  "51": { x: 310, y: 220, w: 30, h: 18 },  // Bali
  "52": { x: 340, y: 225, w: 45, h: 18 },  // NTB
  "53": { x: 385, y: 230, w: 55, h: 20 },  // NTT
  "61": { x: 170, y: 100, w: 55, h: 40 },  // Kalbar
  "62": { x: 225, y: 100, w: 55, h: 40 },  // Kalteng
  "63": { x: 245, y: 140, w: 45, h: 30 },  // Kalsel
  "64": { x: 275, y: 80, w: 50, h: 40 },   // Kaltim
  "65": { x: 280, y: 50, w: 40, h: 30 },   // Kaltara
  "71": { x: 350, y: 80, w: 35, h: 25 },   // Sulut
  "72": { x: 340, y: 110, w: 45, h: 30 },  // Sulteng
  "73": { x: 330, y: 145, w: 40, h: 35 },  // Sulsel
  "74": { x: 370, y: 150, w: 35, h: 30 },  // Sultra
  "75": { x: 345, y: 90, w: 30, h: 20 },   // Gorontalo
  "76": { x: 315, y: 135, w: 30, h: 25 },  // Sulbar
  "81": { x: 440, y: 120, w: 35, h: 30 },  // Maluku
  "82": { x: 430, y: 80, w: 35, h: 25 },   // Malut
  "91": { x: 500, y: 110, w: 80, h: 50 },  // Papua
  "92": { x: 470, y: 120, w: 40, h: 35 },  // Papua Barat
};

export function IndonesiaChoropleth({ data, onRegionClick }: IndonesiaChoroplethProps) {
  const dataMap = useMemo(() => {
    const map = new Map<string, RegionData>();
    data.forEach((d) => map.set(d.kodeWilayah, d));
    return map;
  }, [data]);

  return (
    <div className="w-full">
      <svg
        viewBox="0 0 620 280"
        className="w-full h-auto"
        style={{ minHeight: 200 }}
      >
        {/* Background */}
        <rect width="620" height="280" fill="#f8fafc" rx="8" />

        {/* Province blocks */}
        {Object.entries(PROVINCE_POSITIONS).map(([kode, pos]) => {
          const regionData = dataMap.get(kode);
          const change = regionData?.avgPriceChange ?? 0;
          const color = getColor(change);
          const name = regionData?.namaProvinsi ?? kode;

          return (
            <g
              key={kode}
              className="cursor-pointer transition-opacity hover:opacity-80"
              onClick={() => onRegionClick?.(kode)}
            >
              <rect
                x={pos.x}
                y={pos.y}
                width={pos.w}
                height={pos.h}
                fill={color}
                rx={3}
                stroke="white"
                strokeWidth={1}
                opacity={0.85}
              />
              <text
                x={pos.x + pos.w / 2}
                y={pos.y + pos.h / 2 - 3}
                textAnchor="middle"
                fill="white"
                fontSize={7}
                fontWeight="600"
              >
                {name.length > 12 ? name.slice(0, 10) + ".." : name}
              </text>
              <text
                x={pos.x + pos.w / 2}
                y={pos.y + pos.h / 2 + 7}
                textAnchor="middle"
                fill="white"
                fontSize={6}
                opacity={0.9}
              >
                {change > 0 ? "+" : ""}
                {change.toFixed(1)}%
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex gap-4 mt-3 justify-center">
        <span className="flex items-center gap-1.5 text-xs text-gray-600">
          <span className="h-3 w-3 rounded" style={{ backgroundColor: "#22c55e" }} />
          Rendah (&lt;2%)
        </span>
        <span className="flex items-center gap-1.5 text-xs text-gray-600">
          <span className="h-3 w-3 rounded" style={{ backgroundColor: "#eab308" }} />
          Sedang (2-5%)
        </span>
        <span className="flex items-center gap-1.5 text-xs text-gray-600">
          <span className="h-3 w-3 rounded" style={{ backgroundColor: "#f97316" }} />
          Tinggi (5-10%)
        </span>
        <span className="flex items-center gap-1.5 text-xs text-gray-600">
          <span className="h-3 w-3 rounded" style={{ backgroundColor: "#dc2626" }} />
          Sangat Tinggi (&gt;10%)
        </span>
      </div>
    </div>
  );
}
