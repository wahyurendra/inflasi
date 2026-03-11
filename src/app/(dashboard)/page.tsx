"use client";

import { HeadlineCards } from "@/components/dashboard/headline-cards";
import { CommodityRanking } from "@/components/dashboard/commodity-ranking";
import { RegionRanking } from "@/components/dashboard/region-ranking";
import { InsightCard } from "@/components/dashboard/insight-card";
import { AlertBanner } from "@/components/dashboard/alert-banner";
import { InflationTrendChart } from "@/components/charts/inflation-trend-chart";
import { useHeadlineInflation } from "@/hooks/use-inflation";

// Mock data — digunakan saat DB belum terisi
const mockHeadline = {
  mtm: 0.42,
  ytd: 1.23,
  yoy: 5.21,
  ihk: 118.35,
  periode: "Februari 2026",
};

const mockInflationTrend = [
  { periode: "Sep", mtm: 0.18 },
  { periode: "Okt", mtm: 0.12 },
  { periode: "Nov", mtm: -0.05 },
  { periode: "Des", mtm: 0.55 },
  { periode: "Jan", mtm: 0.65 },
  { periode: "Feb", mtm: 0.42 },
];

const mockCommodities = [
  { namaDisplay: "Cabai Rawit", hargaTerakhir: 85000, perubahanMingguan: 12.0, kategori: "bumbu" },
  { namaDisplay: "Bawang Merah", hargaTerakhir: 42000, perubahanMingguan: 7.0, kategori: "bumbu" },
  { namaDisplay: "Telur Ayam", hargaTerakhir: 28500, perubahanMingguan: 4.0, kategori: "protein" },
  { namaDisplay: "Gula Pasir", hargaTerakhir: 17200, perubahanMingguan: 2.0, kategori: "minyak_gula" },
  { namaDisplay: "Beras", hargaTerakhir: 14850, perubahanMingguan: 1.2, kategori: "bahan_pokok" },
];

const mockRegions = [
  { namaProvinsi: "Papua", avgPriceChange: 8.2, alertCount: 2 },
  { namaProvinsi: "Maluku", avgPriceChange: 6.1, alertCount: 1 },
  { namaProvinsi: "Nusa Tenggara Timur", avgPriceChange: 5.3, alertCount: 1 },
  { namaProvinsi: "Sulawesi Utara", avgPriceChange: 4.8, alertCount: 0 },
  { namaProvinsi: "Kalimantan Timur", avgPriceChange: 4.0, alertCount: 0 },
];

const mockAlerts = [
  { id: 1, severity: "critical" as const, judul: "Cabai rawit: spike +12% / 7 hari (5 provinsi)" },
  { id: 2, severity: "warning" as const, judul: "Bawang merah: volatilitas tinggi 2 minggu" },
  { id: 3, severity: "warning" as const, judul: "Papua: 3 komoditas naik bersamaan" },
];

const mockInsight = {
  judul: "Insight Harian 10 Maret 2026",
  tanggal: "10 Mar 2026",
  konten:
    "Cabai rawit mengalami kenaikan 12% dalam 7 hari terakhir, terutama di wilayah Jawa Barat dan Jawa Timur. Kenaikan ini bertepatan dengan curah hujan tinggi dan mendekati periode Ramadan.\n\nBawang merah menunjukkan volatilitas tinggi selama 2 minggu berturut-turut dengan CV 18.3%.\n\nWilayah Papua mencatat 3 komoditas naik bersamaan — perlu perhatian khusus.",
};

export default function OverviewPage() {
  const { data: headlineData } = useHeadlineInflation();

  const headline = headlineData?.inflasi ?? mockHeadline;
  const periode =
    headlineData?.inflasi?.periode
      ? new Date(headlineData.inflasi.periode).toLocaleDateString("id-ID", {
          month: "long",
          year: "numeric",
        })
      : mockHeadline.periode;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-gray-900">
          Pemantauan Inflasi Pangan Indonesia
        </h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Data terakhir diperbarui: 10 Maret 2026 11:30 WIB
        </p>
      </div>

      {/* Headline Cards */}
      <HeadlineCards
        mtm={headline.mtm}
        ytd={headline.ytd}
        yoy={headline.yoy}
        ihk={headline.ihk}
        periode={periode}
      />

      {/* Inflation Trend Chart */}
      <div className="bg-white rounded-xl border p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">
          Tren Inflasi Bulanan (MtM)
        </h3>
        <InflationTrendChart data={mockInflationTrend} height={180} />
      </div>

      {/* Two Column: Commodities + Regions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CommodityRanking data={mockCommodities} title="Komoditas Paling Naik Minggu Ini" />
        <RegionRanking data={mockRegions} title="Wilayah Paling Tertekan Minggu Ini" />
      </div>

      {/* Insight + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <InsightCard {...mockInsight} />
        <AlertBanner alerts={mockAlerts} />
      </div>
    </div>
  );
}
