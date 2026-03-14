"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { PriceLineChart } from "@/components/charts/price-line-chart";
import { DriverPanel } from "@/components/dashboard/driver-panel";
import { usePrices, useCommodityRanking } from "@/hooks/use-prices";
import { useForecast } from "@/hooks/use-forecast";
import { useDrivers } from "@/hooks/use-drivers";

function ChangeCell({ value }: { value: number | null }) {
  if (value === null) return <td className="px-4 py-3 text-sm text-gray-400">-</td>;
  const color = value > 0 ? "text-red-600" : value < 0 ? "text-green-600" : "text-gray-500";
  const Icon = value > 0 ? TrendingUp : value < 0 ? TrendingDown : Minus;

  return (
    <td className="px-4 py-3">
      <div className={`flex items-center gap-1 ${color}`}>
        <Icon className="h-3.5 w-3.5" />
        <span className="text-sm font-medium">
          {value > 0 ? "+" : ""}
          {value.toFixed(1)}%
        </span>
      </div>
    </td>
  );
}

export default function KomoditasPage() {
  const [selected, setSelected] = useState<string>("CABAI_RAWIT");
  const [days, setDays] = useState(30);
  const [showForecast, setShowForecast] = useState(true);

  const { data: rankingData, isLoading: rankingLoading } = useCommodityRanking("weekly_change", 10);
  const commodities = (rankingData?.data ?? []).map((c) => ({
    kode: c.kodeKomoditas,
    nama: c.namaDisplay,
    harga: c.hargaTerakhir ?? 0,
    harian: c.perubahanHarian ?? 0,
    mingguan: c.perubahanMingguan ?? 0,
    bulanan: c.perubahanBulanan ?? 0,
  }));

  const { data: apiData } = usePrices(selected, "00", days);
  const { data: forecastData } = useForecast(selected, "00", 14);
  const { data: driverData } = useDrivers(selected, "00");

  const chartData =
    apiData?.data?.length
      ? apiData.data
          .map((d) => ({ tanggal: d.tanggal, harga: d.harga }))
          .reverse()
      : [];

  const selectedCommodity = commodities.find((c) => c.kode === selected);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Harga Komoditas</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Tren harga harian komoditas pangan strategis
        </p>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              Tren Harga {selectedCommodity?.nama ?? "—"}
            </h3>
            {selectedCommodity && selectedCommodity.harga > 0 && (
              <p className="text-xs text-gray-500 mt-0.5">
                Harga terakhir: Rp{" "}
                {selectedCommodity.harga.toLocaleString("id-ID")} | Mingguan:{" "}
                <span
                  className={
                    selectedCommodity.mingguan > 0
                      ? "text-red-600"
                      : "text-green-600"
                  }
                >
                  {selectedCommodity.mingguan > 0 ? "+" : ""}
                  {selectedCommodity.mingguan}%
                </span>
              </p>
            )}
          </div>
          <div className="flex gap-2 items-center">
            <label className="flex items-center gap-1.5 text-xs text-gray-600">
              <input
                type="checkbox"
                checked={showForecast}
                onChange={(e) => setShowForecast(e.target.checked)}
                className="rounded border-gray-300"
              />
              Forecast
            </label>
            {commodities.length > 0 ? (
              <select
                className="text-sm border rounded-lg px-3 py-1.5 bg-white"
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
              >
                {commodities.map((c) => (
                  <option key={c.kode} value={c.kode}>
                    {c.nama}
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-sm text-gray-400">Memuat komoditas...</span>
            )}
            <select
              className="text-sm border rounded-lg px-3 py-1.5 bg-white"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
            >
              <option value={7}>7 Hari</option>
              <option value={14}>14 Hari</option>
              <option value={30}>30 Hari</option>
              <option value={90}>90 Hari</option>
            </select>
          </div>
        </div>
        {chartData.length > 0 ? (
          <PriceLineChart
            data={chartData}
            forecastData={forecastData?.data}
            showForecast={showForecast}
          />
        ) : (
          <div className="h-[200px] flex items-center justify-center text-sm text-gray-400">
            {rankingLoading ? "Memuat data..." : "Belum ada data harga tersedia."}
          </div>
        )}
      </div>

      {/* Driver Panel */}
      <DriverPanel
        drivers={driverData?.drivers ?? []}
        commodity={selectedCommodity?.nama}
      />

      {/* Summary Cards */}
      {selectedCommodity && selectedCommodity.harga > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white rounded-xl border px-4 py-3">
            <p className="text-xs text-gray-500">Harga Terakhir</p>
            <p className="text-lg font-bold text-gray-900">
              Rp {selectedCommodity.harga.toLocaleString("id-ID")}
            </p>
          </div>
          <div className="bg-white rounded-xl border px-4 py-3">
            <p className="text-xs text-gray-500">Harian</p>
            <p
              className={`text-lg font-bold ${
                selectedCommodity.harian > 0 ? "text-red-600" : selectedCommodity.harian < 0 ? "text-green-600" : "text-gray-600"
              }`}
            >
              {selectedCommodity.harian > 0 ? "+" : ""}
              {selectedCommodity.harian}%
            </p>
          </div>
          <div className="bg-white rounded-xl border px-4 py-3">
            <p className="text-xs text-gray-500">Mingguan</p>
            <p
              className={`text-lg font-bold ${
                selectedCommodity.mingguan > 0 ? "text-red-600" : selectedCommodity.mingguan < 0 ? "text-green-600" : "text-gray-600"
              }`}
            >
              {selectedCommodity.mingguan > 0 ? "+" : ""}
              {selectedCommodity.mingguan}%
            </p>
          </div>
          <div className="bg-white rounded-xl border px-4 py-3">
            <p className="text-xs text-gray-500">Bulanan</p>
            <p
              className={`text-lg font-bold ${
                selectedCommodity.bulanan > 0 ? "text-red-600" : selectedCommodity.bulanan < 0 ? "text-green-600" : "text-gray-600"
              }`}
            >
              {selectedCommodity.bulanan > 0 ? "+" : ""}
              {selectedCommodity.bulanan}%
            </p>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-5 py-4 border-b">
          <h3 className="text-sm font-semibold text-gray-900">
            Perubahan Harga Semua Komoditas
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Komoditas
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Harga
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Harian
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Mingguan
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Bulanan
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {commodities.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-400">
                    {rankingLoading ? "Memuat data..." : "Belum ada data komoditas tersedia."}
                  </td>
                </tr>
              )}
              {commodities.map((c) => (
                <tr
                  key={c.kode}
                  className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                    selected === c.kode ? "bg-blue-50" : ""
                  }`}
                  onClick={() => setSelected(c.kode)}
                >
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-gray-900">
                      {c.nama}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {c.harga > 0 ? `Rp ${c.harga.toLocaleString("id-ID")}` : "-"}
                  </td>
                  <ChangeCell value={c.harian} />
                  <ChangeCell value={c.mingguan} />
                  <ChangeCell value={c.bulanan} />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
