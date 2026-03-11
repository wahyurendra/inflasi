"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { PriceLineChart } from "@/components/charts/price-line-chart";
import { usePrices } from "@/hooks/use-prices";

const commodities = [
  { kode: "CABAI_RAWIT", nama: "Cabai Rawit", harga: 85000, harian: 2.1, mingguan: 12.0, bulanan: 18.5 },
  { kode: "BAWANG_MERAH", nama: "Bawang Merah", harga: 42000, harian: 0.5, mingguan: 7.0, bulanan: 11.2 },
  { kode: "TELUR_AYAM", nama: "Telur Ayam", harga: 28500, harian: 0.8, mingguan: 4.0, bulanan: 6.1 },
  { kode: "GULA_PASIR", nama: "Gula Pasir", harga: 17200, harian: 0.2, mingguan: 2.0, bulanan: 3.5 },
  { kode: "BERAS", nama: "Beras", harga: 14850, harian: 0.3, mingguan: 1.2, bulanan: 3.8 },
  { kode: "MINYAK_GORENG", nama: "Minyak Goreng", harga: 18100, harian: -0.1, mingguan: 0.5, bulanan: 1.2 },
  { kode: "BAWANG_PUTIH", nama: "Bawang Putih", harga: 38000, harian: 0.0, mingguan: -0.3, bulanan: 2.1 },
  { kode: "CABAI_MERAH", nama: "Cabai Merah", harga: 55000, harian: -0.5, mingguan: -1.2, bulanan: 5.3 },
];

// Mock chart data — akan diganti saat DB terisi
function generateMockChartData(kode: string, days: number = 30) {
  const basePrice = commodities.find((c) => c.kode === kode)?.harga ?? 15000;
  const data = [];
  const today = new Date();
  for (let i = days; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const noise = (Math.random() - 0.4) * basePrice * 0.03;
    const trend = ((days - i) / days) * basePrice * 0.05;
    data.push({
      tanggal: date.toISOString().slice(0, 10),
      harga: Math.round(basePrice + trend + noise),
    });
  }
  return data;
}

function ChangeCell({ value }: { value: number }) {
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

  // Try fetching from API
  const { data: apiData } = usePrices(selected, "00", days);

  // Use API data if available, otherwise mock
  const chartData =
    apiData?.data?.length
      ? apiData.data
          .map((d) => ({ tanggal: d.tanggal, harga: d.harga }))
          .reverse()
      : generateMockChartData(selected, days);

  const selectedCommodity = commodities.find((c) => c.kode === selected);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Harga Komoditas</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Tren harga harian 8 komoditas pangan strategis
        </p>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              Tren Harga {selectedCommodity?.nama ?? "—"}
            </h3>
            {selectedCommodity && (
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
          <div className="flex gap-2">
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
        <PriceLineChart data={chartData} />
      </div>

      {/* Summary Cards */}
      {selectedCommodity && (
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
                    Rp {c.harga.toLocaleString("id-ID")}
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
