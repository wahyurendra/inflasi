"use client";

import { useState } from "react";
import { IndonesiaChoropleth } from "@/components/maps/indonesia-choropleth";
import { useRiskScores } from "@/hooks/use-risk-scores";

const mockRegions = [
  { rank: 1, kode: "91", provinsi: "Papua", change: 8.2, risk: "tinggi" as const, alerts: 2 },
  { rank: 2, kode: "81", provinsi: "Maluku", change: 6.1, risk: "tinggi" as const, alerts: 1 },
  { rank: 3, kode: "53", provinsi: "Nusa Tenggara Timur", change: 5.3, risk: "sedang" as const, alerts: 1 },
  { rank: 4, kode: "71", provinsi: "Sulawesi Utara", change: 4.8, risk: "sedang" as const, alerts: 0 },
  { rank: 5, kode: "64", provinsi: "Kalimantan Timur", change: 4.0, risk: "sedang" as const, alerts: 0 },
  { rank: 6, kode: "18", provinsi: "Lampung", change: 3.5, risk: "rendah" as const, alerts: 0 },
  { rank: 7, kode: "32", provinsi: "Jawa Barat", change: 3.2, risk: "rendah" as const, alerts: 1 },
  { rank: 8, kode: "35", provinsi: "Jawa Timur", change: 2.8, risk: "rendah" as const, alerts: 0 },
  { rank: 9, kode: "12", provinsi: "Sumatera Utara", change: 2.5, risk: "rendah" as const, alerts: 0 },
  { rank: 10, kode: "31", provinsi: "DKI Jakarta", change: 1.1, risk: "rendah" as const, alerts: 0 },
  { rank: 11, kode: "11", provinsi: "Aceh", change: 2.0, risk: "rendah" as const, alerts: 0 },
  { rank: 12, kode: "13", provinsi: "Sumatera Barat", change: 1.8, risk: "rendah" as const, alerts: 0 },
  { rank: 13, kode: "14", provinsi: "Riau", change: 1.5, risk: "rendah" as const, alerts: 0 },
  { rank: 14, kode: "15", provinsi: "Jambi", change: 1.7, risk: "rendah" as const, alerts: 0 },
  { rank: 15, kode: "16", provinsi: "Sumatera Selatan", change: 2.2, risk: "rendah" as const, alerts: 0 },
  { rank: 16, kode: "17", provinsi: "Bengkulu", change: 1.9, risk: "rendah" as const, alerts: 0 },
  { rank: 17, kode: "19", provinsi: "Kep. Bangka Belitung", change: 1.3, risk: "rendah" as const, alerts: 0 },
  { rank: 18, kode: "21", provinsi: "Kepulauan Riau", change: 1.6, risk: "rendah" as const, alerts: 0 },
  { rank: 19, kode: "33", provinsi: "Jawa Tengah", change: 2.1, risk: "rendah" as const, alerts: 0 },
  { rank: 20, kode: "34", provinsi: "DI Yogyakarta", change: 1.4, risk: "rendah" as const, alerts: 0 },
  { rank: 21, kode: "36", provinsi: "Banten", change: 1.9, risk: "rendah" as const, alerts: 0 },
  { rank: 22, kode: "51", provinsi: "Bali", change: 1.7, risk: "rendah" as const, alerts: 0 },
  { rank: 23, kode: "52", provinsi: "NTB", change: 3.1, risk: "sedang" as const, alerts: 0 },
  { rank: 24, kode: "61", provinsi: "Kalimantan Barat", change: 2.5, risk: "rendah" as const, alerts: 0 },
  { rank: 25, kode: "62", provinsi: "Kalimantan Tengah", change: 2.3, risk: "rendah" as const, alerts: 0 },
  { rank: 26, kode: "63", provinsi: "Kalimantan Selatan", change: 2.0, risk: "rendah" as const, alerts: 0 },
  { rank: 27, kode: "65", provinsi: "Kalimantan Utara", change: 3.5, risk: "sedang" as const, alerts: 0 },
  { rank: 28, kode: "72", provinsi: "Sulawesi Tengah", change: 2.8, risk: "rendah" as const, alerts: 0 },
  { rank: 29, kode: "73", provinsi: "Sulawesi Selatan", change: 2.4, risk: "rendah" as const, alerts: 0 },
  { rank: 30, kode: "74", provinsi: "Sulawesi Tenggara", change: 3.2, risk: "sedang" as const, alerts: 0 },
  { rank: 31, kode: "75", provinsi: "Gorontalo", change: 2.7, risk: "rendah" as const, alerts: 0 },
  { rank: 32, kode: "76", provinsi: "Sulawesi Barat", change: 2.9, risk: "rendah" as const, alerts: 0 },
  { rank: 33, kode: "82", provinsi: "Maluku Utara", change: 4.5, risk: "sedang" as const, alerts: 0 },
  { rank: 34, kode: "92", provinsi: "Papua Barat", change: 5.8, risk: "tinggi" as const, alerts: 1 },
];

const riskColors = {
  tinggi: "bg-red-100 text-red-700",
  sedang: "bg-orange-100 text-orange-700",
  rendah: "bg-green-100 text-green-700",
};

export default function WilayahPage() {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [mapMode, setMapMode] = useState<"price_change" | "risk">("price_change");

  const { data: riskScores } = useRiskScores();

  const mapData = mockRegions.map((r) => {
    const riskData = riskScores?.find((rs) => rs.kodeWilayah === r.kode);
    return {
      kodeWilayah: r.kode,
      namaProvinsi: r.provinsi,
      avgPriceChange: r.change,
      riskCategory: riskData?.riskCategory ?? r.risk,
      hasAlert: r.alerts > 0,
    };
  });

  const sorted = [...mockRegions].sort((a, b) => b.change - a.change);
  const selectedInfo = selectedRegion
    ? mockRegions.find((r) => r.kode === selectedRegion)
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
                  {selectedInfo.provinsi}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Rata-rata kenaikan: +{selectedInfo.change.toFixed(1)}% | Alert: {selectedInfo.alerts}
                </p>
              </div>
              <span
                className={`text-xs font-medium px-2.5 py-1 rounded-full ${riskColors[selectedInfo.risk]}`}
              >
                {selectedInfo.risk}
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
              {sorted.slice(0, 10).map((r, idx) => (
                <tr
                  key={r.kode}
                  className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                    selectedRegion === r.kode ? "bg-blue-50" : ""
                  }`}
                  onClick={() =>
                    setSelectedRegion(r.kode === selectedRegion ? null : r.kode)
                  }
                >
                  <td className="px-4 py-3 text-sm text-gray-500 font-medium">
                    {idx + 1}
                  </td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {r.provinsi}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-sm font-semibold ${
                        r.change > 5
                          ? "text-red-600"
                          : r.change > 2
                            ? "text-orange-500"
                            : "text-gray-600"
                      }`}
                    >
                      +{r.change.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-medium px-2 py-1 rounded-full ${riskColors[r.risk]}`}
                    >
                      {r.risk}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {r.alerts > 0 ? (
                      <span className="text-orange-600 font-medium">{r.alerts}</span>
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
