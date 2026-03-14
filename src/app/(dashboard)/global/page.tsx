"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Globe,
  Fuel,
  Wheat,
  DollarSign,
  Newspaper,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";

interface GlobalSignals {
  fao: Array<{
    periode: string;
    overall: number | null;
    cereals: number | null;
    vegOil: number | null;
    dairy: number | null;
    meat: number | null;
    sugar: number | null;
  }>;
  commodities: Record<
    string,
    { price: number; changePct: number | null; unit: string; periode: string }
  >;
  kurs: Array<{
    tanggal: string;
    kursTengah: number | null;
    changePct: number | null;
  }>;
  energy: Array<{
    tanggal: string;
    commodity: string;
    price: number;
    changePct: number | null;
  }>;
  supplyChain: Array<{ periode: string; gscpi: number }>;
  news: Array<{
    tanggal: string;
    kategori: string;
    judul: string;
    sumber: string;
    url: string | null;
    sentimen: string | null;
    relevansi: number | null;
  }>;
}

const COMMODITY_LABELS: Record<string, string> = {
  rice: "Beras (Thai 5%)",
  wheat: "Gandum (US HRW)",
  palm_oil: "Minyak Sawit",
  sugar: "Gula",
  urea: "Urea (Pupuk)",
  crude_oil_brent: "Minyak Brent",
};

const CATEGORY_COLORS: Record<string, string> = {
  food_supply: "bg-orange-100 text-orange-700",
  energy: "bg-yellow-100 text-yellow-700",
  geopolitics: "bg-red-100 text-red-700",
  climate: "bg-blue-100 text-blue-700",
  agriculture: "bg-green-100 text-green-700",
  indonesia: "bg-purple-100 text-purple-700",
};

const SENTIMENT_COLORS: Record<string, string> = {
  negative: "text-red-600",
  neutral: "text-gray-500",
  positive: "text-green-600",
};

export default function GlobalSignalsPage() {
  const { data, isLoading } = useQuery<GlobalSignals>({
    queryKey: ["global-signals"],
    queryFn: () => fetch("/api/global-signals").then((r) => r.json()),
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  const fao = data?.fao || [];
  const commodities = data?.commodities || {};
  const kurs = data?.kurs || [];
  const energy = data?.energy || [];
  const supplyChain = data?.supplyChain || [];
  const news = data?.news || [];

  const latestFao = fao[0];
  const latestKurs = kurs[0];
  const latestEnergy = energy[0];
  const latestGscpi = supplyChain[0];

  // FAO chart data (reversed for chronological order)
  const faoChartData = [...fao].reverse().map((f) => ({
    bulan: f.periode.slice(0, 7),
    overall: f.overall,
    cereals: f.cereals,
    vegOil: f.vegOil,
  }));

  // GSCPI chart data
  const gscpiChartData = [...supplyChain].reverse().map((s) => ({
    bulan: s.periode.slice(0, 7),
    gscpi: s.gscpi,
  }));

  // Kurs chart data
  const kursChartData = [...kurs].reverse().map((k) => ({
    tanggal: k.tanggal.slice(5),
    kurs: k.kursTengah,
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Globe className="h-7 w-7 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold">Global Signals</h1>
          <p className="text-sm text-gray-500">
            Sinyal pasar global yang mempengaruhi inflasi pangan domestik
          </p>
        </div>
      </div>

      {/* Key Indicators Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* FAO Food Price Index */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Wheat className="h-4 w-4" />
              FAO Food Price Index
            </div>
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold">
              {latestFao?.overall?.toFixed(1) || "-"}
            </span>
            <span className="text-sm text-gray-400 ml-2">
              {latestFao?.periode?.slice(0, 7)}
            </span>
          </div>
          <div className="mt-1 text-xs text-gray-500">
            Cereals: {latestFao?.cereals} | Oil: {latestFao?.vegOil} | Sugar:{" "}
            {latestFao?.sugar}
          </div>
        </div>

        {/* USD/IDR */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <DollarSign className="h-4 w-4" />
            Kurs USD/IDR
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold">
              {latestKurs?.kursTengah
                ? `Rp ${latestKurs.kursTengah.toLocaleString("id-ID")}`
                : "-"}
            </span>
            {latestKurs?.changePct && (
              <span
                className={`text-sm flex items-center ${latestKurs.changePct > 0 ? "text-red-600" : "text-green-600"}`}
              >
                {latestKurs.changePct > 0 ? (
                  <ArrowUpRight className="h-3 w-3" />
                ) : (
                  <ArrowDownRight className="h-3 w-3" />
                )}
                {Math.abs(latestKurs.changePct).toFixed(2)}%
              </span>
            )}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {latestKurs?.tanggal}
          </div>
        </div>

        {/* Brent Crude */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Fuel className="h-4 w-4" />
            Minyak Brent
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold">
              ${latestEnergy?.price?.toFixed(1) || "-"}
            </span>
            <span className="text-sm text-gray-400 ml-1">/bbl</span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {latestEnergy?.tanggal}
          </div>
        </div>

        {/* Supply Chain Pressure */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <BarChart3 className="h-4 w-4" />
            Supply Chain Pressure
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold">
              {latestGscpi?.gscpi?.toFixed(2) || "-"}
            </span>
            {latestGscpi && (
              <span
                className={`text-sm ${latestGscpi.gscpi > 0.5 ? "text-red-600" : latestGscpi.gscpi > 0 ? "text-yellow-600" : "text-green-600"}`}
              >
                {latestGscpi.gscpi > 0.5
                  ? "Tekanan Tinggi"
                  : latestGscpi.gscpi > 0
                    ? "Normal"
                    : "Rendah"}
              </span>
            )}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            GSCPI (Fed NY) — {latestGscpi?.periode?.slice(0, 7)}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* FAO Index Trend */}
        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-semibold mb-3">
            FAO Food Price Index — 12 Bulan Terakhir
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={faoChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bulan" tick={{ fontSize: 11 }} />
              <YAxis domain={["dataMin - 5", "dataMax + 5"]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="overall"
                name="Overall"
                stroke="#2563eb"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="cereals"
                name="Cereals"
                stroke="#16a34a"
                strokeWidth={1}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="vegOil"
                name="Veg Oil"
                stroke="#ea580c"
                strokeWidth={1}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Kurs Trend */}
        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-semibold mb-3">Kurs USD/IDR — 30 Hari</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={kursChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tanggal" tick={{ fontSize: 11 }} />
              <YAxis
                domain={["dataMin - 50", "dataMax + 50"]}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
              />
              <Tooltip
                formatter={(v) => [
                  `Rp ${Number(v).toLocaleString("id-ID")}`,
                  "Kurs",
                ]}
              />
              <Line
                type="monotone"
                dataKey="kurs"
                stroke="#7c3aed"
                strokeWidth={2}
                dot={{ r: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Commodity Prices + GSCPI */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Commodity Prices Table */}
        <div className="lg:col-span-2 bg-white rounded-lg border p-4">
          <h3 className="font-semibold mb-3">Harga Komoditas Global</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2">Komoditas</th>
                  <th className="pb-2 text-right">Harga</th>
                  <th className="pb-2 text-right">Satuan</th>
                  <th className="pb-2 text-right">Periode</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(commodities).map(([key, val]) => (
                  <tr key={key} className="border-b last:border-0">
                    <td className="py-2 font-medium">
                      {COMMODITY_LABELS[key] || key}
                    </td>
                    <td className="py-2 text-right font-mono">
                      ${val.price.toLocaleString("en-US", { maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-2 text-right text-gray-500">
                      {val.unit}
                    </td>
                    <td className="py-2 text-right text-gray-400">
                      {val.periode.slice(0, 7)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* GSCPI Chart */}
        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-semibold mb-3">Supply Chain Pressure</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={gscpiChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="bulan"
                tick={{ fontSize: 10 }}
                tickFormatter={(v) => v.slice(5)}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="gscpi" name="GSCPI">
                {gscpiChartData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={
                      entry.gscpi > 0.5
                        ? "#ef4444"
                        : entry.gscpi > 0
                          ? "#f59e0b"
                          : "#22c55e"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-gray-400 mt-2">
            Fed NY Global Supply Chain Pressure Index. &gt;0.5 = tekanan tinggi
          </p>
        </div>
      </div>

      {/* News Intelligence */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center gap-2 mb-4">
          <Newspaper className="h-5 w-5 text-gray-600" />
          <h3 className="font-semibold">News Intelligence</h3>
          <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full text-gray-500">
            GDELT
          </span>
        </div>
        <div className="space-y-3">
          {news.length === 0 ? (
            <p className="text-sm text-gray-400">Tidak ada berita terbaru.</p>
          ) : (
            news.slice(0, 10).map((n, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition"
              >
                <div className="flex-shrink-0 mt-0.5">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${CATEGORY_COLORS[n.kategori] || "bg-gray-100 text-gray-600"}`}
                  >
                    {n.kategori}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {n.url ? (
                      <a
                        href={n.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-blue-600 hover:underline"
                      >
                        {n.judul}
                      </a>
                    ) : (
                      n.judul
                    )}
                  </p>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                    <span>{n.sumber}</span>
                    <span>·</span>
                    <span>{n.tanggal}</span>
                    {n.sentimen && (
                      <>
                        <span>·</span>
                        <span
                          className={
                            SENTIMENT_COLORS[n.sentimen] || "text-gray-500"
                          }
                        >
                          {n.sentimen}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
