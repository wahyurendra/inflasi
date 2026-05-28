"use client";

import { useState } from "react";
import { IndonesiaChoropleth } from "@/components/maps/indonesia-choropleth";
import { useRiskScores } from "@/hooks/use-risk-scores";
import { useQuery } from "@tanstack/react-query";

interface RegionHeatmapItem {
  kodeWilayah: string;
  namaProvinsi: string;
  avgPriceChange: number;
  alertCount: number;
  riskCategory: "rendah" | "sedang" | "tinggi";
}

function useRegionHeatmap() {
  return useQuery<{ data: RegionHeatmapItem[] }>({
    queryKey: ["regions", "heatmap"],
    queryFn: async () => {
      const res = await fetch("/api/regions/heatmap");
      if (!res.ok) throw new Error("Failed to fetch regions");
      return res.json();
    },
  });
}

const riskColors = {
  tinggi: "bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-300",
  sedang: "bg-orange-100 text-orange-700 dark:bg-orange-950/30 dark:text-orange-300",
  rendah: "bg-green-100 text-green-700 dark:bg-green-950/30 dark:text-green-300",
};

export default function WilayahPage() {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [mapMode, setMapMode] = useState<"price_change" | "risk">("price_change");

  const { data: heatmapData, isLoading } = useRegionHeatmap();
  const { data: riskScores } = useRiskScores();

  const regions = heatmapData?.data ?? [];

  const mapData = regions.map((r) => {
    const riskData = riskScores?.find((rs) => rs.kodeWilayah === r.kodeWilayah);
    return {
      kodeWilayah: r.kodeWilayah,
      namaProvinsi: r.namaProvinsi,
      avgPriceChange: r.avgPriceChange,
      riskCategory: (riskData?.riskCategory ?? r.riskCategory ?? "rendah") as "rendah" | "sedang" | "tinggi",
      hasAlert: r.alertCount > 0,
    };
  });

  const sorted = [...regions].sort((a, b) => b.avgPriceChange - a.avgPriceChange);
  const selectedInfo = selectedRegion
    ? regions.find((r) => r.kodeWilayah === selectedRegion)
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-foreground">Peta Tekanan Harga</h2>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Wilayah dengan tekanan harga pangan tertinggi
        </p>
      </div>

      {/* Map */}
      <div className="bg-card rounded-xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-foreground">
            Heatmap Tekanan Harga Indonesia
          </h3>
          <div className="flex rounded-lg bg-muted p-0.5">
            <button
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                mapMode === "price_change"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setMapMode("price_change")}
            >
              Perubahan Harga
            </button>
            <button
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                mapMode === "risk"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setMapMode("risk")}
            >
              Risiko
            </button>
          </div>
        </div>
        <IndonesiaChoropleth
          data={mapData}
          mode={mapMode}
          onRegionClick={(kode) =>
            setSelectedRegion(kode === selectedRegion ? null : kode)
          }
        />
        {selectedInfo && (
          <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-foreground">
                  {selectedInfo.namaProvinsi}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Rata-rata kenaikan: +{selectedInfo.avgPriceChange.toFixed(1)}% | Alert: {selectedInfo.alertCount}
                </p>
              </div>
              <span
                className={`text-xs font-medium px-2.5 py-1 rounded-full ${riskColors[selectedInfo.riskCategory] ?? riskColors.rendah}`}
              >
                {selectedInfo.riskCategory}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Ranking Table */}
      <div className="bg-card rounded-xl border overflow-hidden">
        <div className="px-5 py-4 border-b">
          <h3 className="text-sm font-semibold text-foreground">
            Ranking Provinsi — 10 Teratas
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/50">
                <th className="w-12 px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                  #
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                  Provinsi
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                  Rata-rata Kenaikan
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                  Risiko
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                  Alert
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {isLoading && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-sm text-muted-foreground">
                    Memuat data...
                  </td>
                </tr>
              )}
              {!isLoading && sorted.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-sm text-muted-foreground">
                    Belum ada data wilayah tersedia.
                  </td>
                </tr>
              )}
              {sorted.slice(0, 10).map((r, idx) => (
                <tr
                  key={r.kodeWilayah}
                  className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                    selectedRegion === r.kodeWilayah ? "bg-blue-50 dark:bg-blue-950/30" : ""
                  }`}
                  onClick={() =>
                    setSelectedRegion(r.kodeWilayah === selectedRegion ? null : r.kodeWilayah)
                  }
                >
                  <td className="px-4 py-3 text-sm font-medium text-muted-foreground">
                    {idx + 1}
                  </td>
                  <td className="px-4 py-3 text-sm font-medium text-foreground">
                    {r.namaProvinsi}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-sm font-semibold ${
                        r.avgPriceChange > 5
                          ? "text-red-600"
                          : r.avgPriceChange > 2
                            ? "text-orange-500"
                            : "text-muted-foreground"
                      }`}
                    >
                      +{r.avgPriceChange.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-medium px-2 py-1 rounded-full ${riskColors[r.riskCategory] ?? riskColors.rendah}`}
                    >
                      {r.riskCategory}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {r.alertCount > 0 ? (
                      <span className="text-orange-600 font-medium">{r.alertCount}</span>
                    ) : (
                      "-"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
