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
  tinggi: "bg-red-100 text-red-700",
  sedang: "bg-orange-100 text-orange-700",
  rendah: "bg-green-100 text-green-700",
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
        <h2 className="text-lg font-bold text-gray-900">Peta Tekanan Harga</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Wilayah dengan tekanan harga pangan tertinggi
        </p>
      </div>

      {/* Map */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-900">
            Heatmap Tekanan Harga Indonesia
          </h3>
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            <button
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                mapMode === "price_change"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
              onClick={() => setMapMode("price_change")}
            >
              Perubahan Harga
            </button>
            <button
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                mapMode === "risk"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
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
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-gray-900">
                  {selectedInfo.namaProvinsi}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
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
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-5 py-4 border-b">
          <h3 className="text-sm font-semibold text-gray-900">
            Ranking Provinsi — 10 Teratas
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase w-12">
                  #
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Provinsi
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Rata-rata Kenaikan
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Risiko
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Alert
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {isLoading && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-400">
                    Memuat data...
                  </td>
                </tr>
              )}
              {!isLoading && sorted.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-400">
                    Belum ada data wilayah tersedia.
                  </td>
                </tr>
              )}
              {sorted.slice(0, 10).map((r, idx) => (
                <tr
                  key={r.kodeWilayah}
                  className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                    selectedRegion === r.kodeWilayah ? "bg-blue-50" : ""
                  }`}
                  onClick={() =>
                    setSelectedRegion(r.kodeWilayah === selectedRegion ? null : r.kodeWilayah)
                  }
                >
                  <td className="px-4 py-3 text-sm text-gray-500 font-medium">
                    {idx + 1}
                  </td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {r.namaProvinsi}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-sm font-semibold ${
                        r.avgPriceChange > 5
                          ? "text-red-600"
                          : r.avgPriceChange > 2
                            ? "text-orange-500"
                            : "text-gray-600"
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
                  <td className="px-4 py-3 text-sm text-gray-500">
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
