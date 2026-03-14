"use client";

import { HeadlineCards } from "@/components/dashboard/headline-cards";
import { CommodityRanking } from "@/components/dashboard/commodity-ranking";
import { RegionRanking } from "@/components/dashboard/region-ranking";
import { InsightCard } from "@/components/dashboard/insight-card";
import { AlertBanner } from "@/components/dashboard/alert-banner";
import { InflationTrendChart } from "@/components/charts/inflation-trend-chart";
import { useHeadlineInflation } from "@/hooks/use-inflation";
import { useCommodityRanking } from "@/hooks/use-prices";
import { useAlerts } from "@/hooks/use-alerts";
import { useForecast } from "@/hooks/use-forecast";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { MVP_COMMODITIES } from "@/lib/constants";

function useRegionHeatmap() {
  return useQuery<{
    data: Array<{
      kodeWilayah: string;
      namaProvinsi: string;
      avgPriceChange: number;
      alertCount: number;
      riskCategory: string;
    }>;
  }>({
    queryKey: ["regions", "heatmap"],
    queryFn: async () => {
      const res = await fetch("/api/regions/heatmap");
      if (!res.ok) throw new Error("Failed to fetch regions");
      return res.json();
    },
  });
}

function useLatestInsight() {
  return useQuery<{
    data: {
      tanggal: string;
      judul: string;
      konten: string;
    } | null;
  }>({
    queryKey: ["insights", "latest"],
    queryFn: async () => {
      const res = await fetch("/api/insights/latest");
      if (!res.ok) throw new Error("Failed to fetch insight");
      return res.json();
    },
  });
}

function ForecastTrafficLight({ kode, nama }: { kode: string; nama: string }) {
  const { data: rankingData } = useCommodityRanking("weekly_change", 10);
  const commodity = rankingData?.data?.find((c) => c.kodeKomoditas === kode);
  const hargaSekarang = commodity?.hargaTerakhir ?? 0;

  const { data } = useForecast(kode, "00", 7);
  const lastForecast = data?.data?.[data.data.length - 1];
  const prediksi = lastForecast?.yhat ?? hargaSekarang;
  const changePct = hargaSekarang > 0 ? ((prediksi - hargaSekarang) / hargaSekarang) * 100 : 0;

  const color = changePct > 3 ? "text-red-600" : changePct > 1 ? "text-orange-500" : changePct < -1 ? "text-green-600" : "text-muted-foreground";
  const bg = changePct > 3 ? "bg-red-50" : changePct > 1 ? "bg-orange-50" : changePct < -1 ? "bg-green-50" : "bg-muted";
  const Icon = changePct > 0.5 ? TrendingUp : changePct < -0.5 ? TrendingDown : Minus;

  if (!hargaSekarang) return null;

  return (
    <div className={`${bg} rounded-lg px-4 py-3 border`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">{nama}</p>
          <p className="text-sm font-semibold text-foreground">
            Rp {Math.round(prediksi).toLocaleString("id-ID")}
          </p>
        </div>
        <div className={`flex items-center gap-1 ${color}`}>
          <Icon className="h-4 w-4" />
          <span className="text-sm font-bold">
            {changePct > 0 ? "+" : ""}{changePct.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const { data: headlineData } = useHeadlineInflation();
  const { data: rankingData } = useCommodityRanking("weekly_change", 5);
  const { data: regionData } = useRegionHeatmap();
  const { data: alertData } = useAlerts(true, undefined, 5);
  const { data: insightData } = useLatestInsight();

  const headline = headlineData?.inflasi ?? null;
  const periode = headline?.periode
    ? new Date(headline.periode).toLocaleDateString("id-ID", {
        month: "long",
        year: "numeric",
      })
    : "-";

  const commodities = (rankingData?.data ?? []).map((c) => ({
    namaDisplay: c.namaDisplay,
    hargaTerakhir: c.hargaTerakhir ?? 0,
    perubahanMingguan: c.perubahanMingguan ?? 0,
    kategori: c.kategori,
  }));

  const regions = (regionData?.data ?? [])
    .sort((a, b) => b.avgPriceChange - a.avgPriceChange)
    .slice(0, 5);

  const alerts = (alertData?.data ?? []).map((a) => ({
    id: a.id,
    severity: a.severity,
    judul: a.judul,
  }));

  const insight = insightData?.data ?? null;

  const forecastCommodities = MVP_COMMODITIES.slice(0, 4).map((c) => ({
    kode: c.kode,
    nama: c.display,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-foreground">
          Pemantauan Inflasi Pangan Indonesia
        </h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Data terakhir diperbarui: {headline?.periode ? new Date(headline.periode).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" }) : "-"}
        </p>
      </div>

      {/* Headline Cards */}
      <HeadlineCards
        mtm={headline?.mtm ?? null}
        ytd={headline?.ytd ?? null}
        yoy={headline?.yoy ?? null}
        ihk={headline?.ihk ?? null}
        periode={periode}
      />

      {/* Inflation Trend Chart */}
      <div className="bg-card rounded-xl border p-5">
        <h3 className="text-sm font-semibold text-foreground mb-3">
          Tren Inflasi Bulanan (MtM)
        </h3>
        <InflationTrendChart data={[]} height={180} />
      </div>

      {/* Forecast 7 Hari */}
      {forecastCommodities.length > 0 && (
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-semibold text-foreground mb-3">
            Forecast Harga 7 Hari
          </h3>
          <p className="text-xs text-muted-foreground mb-4">
            Prediksi perubahan harga H+7 dibanding hari ini
          </p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {forecastCommodities.map((c) => (
              <ForecastTrafficLight key={c.kode} {...c} />
            ))}
          </div>
        </div>
      )}

      {/* Two Column: Commodities + Regions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CommodityRanking data={commodities} title="Komoditas Paling Naik Minggu Ini" />
        <RegionRanking data={regions} title="Wilayah Paling Tertekan Minggu Ini" />
      </div>

      {/* Insight + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {insight ? (
          <InsightCard
            judul={insight.judul}
            konten={insight.konten}
            tanggal={insight.tanggal}
          />
        ) : (
          <div className="bg-card rounded-xl border p-5">
            <h3 className="text-sm font-semibold text-foreground mb-3">Insight Hari Ini</h3>
            <p className="text-sm text-muted-foreground">Belum ada insight tersedia.</p>
          </div>
        )}
        <AlertBanner alerts={alerts} />
      </div>
    </div>
  );
}
