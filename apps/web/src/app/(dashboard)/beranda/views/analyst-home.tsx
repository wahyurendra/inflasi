"use client";

import { HeadlineCards } from "@/components/dashboard/headline-cards";
import { CommodityRanking } from "@/components/dashboard/commodity-ranking";
import { RegionRanking } from "@/components/dashboard/region-ranking";
import { InsightCard } from "@/components/dashboard/insight-card";
import { AlertBanner } from "@/components/dashboard/alert-banner";
import { InflationTrendChart } from "@/components/charts/inflation-trend-chart";
import { useHeadlineInflation, useInflationSeries } from "@/hooks/use-inflation";
import { useCommodityRanking } from "@/hooks/use-prices";
import { useAlerts } from "@/hooks/use-alerts";
import { useForecast } from "@/hooks/use-forecast";
import { useVolatilityRanking } from "@/hooks/use-intelligence";
import { useModelPerformance } from "@/hooks/use-model-performance";
import { useRegionHeatmap } from "@/hooks/use-regions";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  LineChart as LineChartIcon,
  Crosshair,
  Lightbulb,
} from "lucide-react";
import { MVP_COMMODITIES } from "@/lib/constants";

function useLatestInsight() {
  return useQuery<{
    data: { tanggal: string; judul: string; konten: string } | null;
  }>({
    queryKey: ["insights", "latest"],
    queryFn: async () => {
      const res = await fetch("/api/insights/latest");
      if (!res.ok) throw new Error("Failed to fetch insight");
      return res.json();
    },
  });
}

interface ForecastCardProps {
  kode: string;
  nama: string;
  hargaSekarang: number;
}

function ForecastCard({ kode, nama, hargaSekarang }: ForecastCardProps) {
  const { data, isLoading } = useForecast(kode, "00", 7);
  const lastForecast = data?.data?.[data.data.length - 1];
  const prediksi = lastForecast?.yhat;

  const changePct =
    prediksi !== undefined && hargaSekarang > 0
      ? ((prediksi - hargaSekarang) / hargaSekarang) * 100
      : null;

  const tone =
    changePct === null
      ? { bg: "bg-muted/40", text: "text-muted-foreground", border: "border-border" }
      : changePct > 3
        ? { bg: "bg-risk-critical/5", text: "text-risk-critical", border: "border-risk-critical/30" }
        : changePct > 1
          ? { bg: "bg-risk-high/5", text: "text-risk-high", border: "border-risk-high/30" }
          : changePct < -1
            ? { bg: "bg-risk-low/5", text: "text-risk-low", border: "border-risk-low/30" }
            : { bg: "bg-muted/40", text: "text-muted-foreground", border: "border-border" };

  const Icon =
    changePct === null || Math.abs(changePct) < 0.5
      ? Minus
      : changePct > 0
        ? TrendingUp
        : TrendingDown;

  return (
    <div className={`rounded-md px-3 py-2.5 border ${tone.bg} ${tone.border}`}>
      <p className="text-[11px] text-muted-foreground truncate">{nama}</p>
      <div className="flex items-center justify-between mt-1">
        <div className="min-w-0">
          {isLoading ? (
            <div className="h-4 w-16 bg-muted rounded animate-pulse" />
          ) : prediksi !== undefined ? (
            <p className="text-sm font-semibold tabular-nums">
              Rp {Math.round(prediksi).toLocaleString("id-ID")}
            </p>
          ) : (
            <p className="text-xs text-muted-foreground italic">N/A</p>
          )}
        </div>
        <div className={`flex items-center gap-0.5 ${tone.text}`}>
          <Icon className="h-3.5 w-3.5" />
          <span className="text-sm font-bold tabular-nums">
            {changePct === null
              ? "—"
              : `${changePct > 0 ? "+" : ""}${changePct.toFixed(1)}%`}
          </span>
        </div>
      </div>
    </div>
  );
}

interface VolatilityRow {
  commodity?: string;
  namaDisplay?: string;
  nama?: string;
  kode?: string;
  cv?: number;
  volatility?: number;
  trend?: string;
}

function VolatilityList({ rows }: { rows: VolatilityRow[] }) {
  if (!rows.length) {
    return (
      <div className="py-6 text-center text-xs text-muted-foreground">
        Belum ada data volatilitas.
      </div>
    );
  }
  const max = Math.max(...rows.map((r) => r.cv ?? r.volatility ?? 0), 1);
  return (
    <ul className="space-y-2">
      {rows.map((v, i) => {
        const name = v.commodity || v.namaDisplay || v.nama || "—";
        const cv = v.cv ?? v.volatility ?? 0;
        const pct = (cv / max) * 100;
        const trendIcon = v.trend === "up" ? TrendingUp : v.trend === "down" ? TrendingDown : Minus;
        const TrendIcon = trendIcon;
        return (
          <li key={i} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 text-foreground truncate">
                <TrendIcon
                  className={`h-3 w-3 shrink-0 ${
                    v.trend === "up"
                      ? "text-risk-critical"
                      : v.trend === "down"
                        ? "text-risk-low"
                        : "text-muted-foreground"
                  }`}
                />
                {name}
              </span>
              <span className="font-semibold tabular-nums text-foreground">
                {cv.toFixed(2)}%
              </span>
            </div>
            <div className="h-1 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  cv > 15 ? "bg-risk-critical" : cv > 8 ? "bg-risk-high" : "bg-risk-low"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export function AnalystHome() {
  const { data: headlineData } = useHeadlineInflation();
  const { data: seriesData, isLoading: seriesLoading } = useInflationSeries(12);
  const { data: rankingData } = useCommodityRanking("weekly_change", 8);
  const { data: regionData } = useRegionHeatmap();
  const { data: alertData } = useAlerts(true, undefined, 5);
  const { data: insightData } = useLatestInsight();
  const { data: volatility } = useVolatilityRanking();
  const { data: perf } = useModelPerformance(30, "price");

  const headline = headlineData?.inflasi ?? null;
  const periode = headline?.periode
    ? new Date(headline.periode).toLocaleDateString("id-ID", { month: "long", year: "numeric" })
    : "-";

  const trendSeries = seriesData?.data ?? [];

  const commodities = (rankingData?.data ?? []).slice(0, 5).map((c) => ({
    namaDisplay: c.namaDisplay,
    hargaTerakhir: c.hargaTerakhir ?? 0,
    perubahanMingguan: c.perubahanMingguan ?? 0,
    kategori: c.kategori,
  }));

  const regions = (regionData ?? [])
    .map((r) => r as { kodeWilayah: string; namaProvinsi: string; avgPriceChange: number; alertCount: number; riskCategory: string })
    .sort((a, b) => (b.avgPriceChange ?? 0) - (a.avgPriceChange ?? 0))
    .slice(0, 5);

  const alerts = (alertData?.data ?? []).map((a) => ({ id: a.id, severity: a.severity, judul: a.judul }));
  const insight = insightData?.data ?? null;

  // Pull current prices once from ranking, then pass down — avoids re-fetching the
  // same ranking query inside each ForecastCard.
  const forecastTargets = MVP_COMMODITIES.slice(0, 4).map((c) => {
    const ranked = rankingData?.data?.find((r) => r.kodeKomoditas === c.kode);
    return {
      kode: c.kode,
      nama: c.display,
      hargaSekarang: ranked?.hargaTerakhir ?? 0,
    };
  });

  const volatilityTop = ((volatility as { data?: VolatilityRow[] })?.data ?? []).slice(0, 5);
  const perfRows = (perf?.data ?? []).slice(0, 4);

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Ringkasan Analis</h2>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            Data terakhir diperbarui:{" "}
            <span className="font-medium text-foreground">
              {headline?.periode
                ? new Date(headline.periode).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" })
                : "-"}
            </span>
          </p>
        </div>
      </div>

      <HeadlineCards
        mtm={headline?.mtm ?? null}
        ytd={headline?.ytd ?? null}
        yoy={headline?.yoy ?? null}
        ihk={headline?.ihk ?? null}
        periode={periode}
      />

      {/* Inflation trend chart */}
      <div className="bg-card rounded-md border p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <LineChartIcon className="h-3.5 w-3.5 text-primary" />
            <h3 className="text-sm font-semibold">Tren Inflasi Bulanan (MtM)</h3>
          </div>
          <span className="text-[10px] text-muted-foreground">
            {trendSeries.length > 0 ? `${trendSeries.length} bulan` : ""}
          </span>
        </div>
        <InflationTrendChart data={trendSeries} height={200} loading={seriesLoading} />
      </div>

      {/* Forecast strip */}
      <div className="bg-card rounded-md border p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Crosshair className="h-3.5 w-3.5 text-primary" />
              Forecast Harga 7 Hari
            </h3>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Prediksi perubahan harga H+7 dibanding hari ini
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
          {forecastTargets.map((c) => (
            <ForecastCard key={c.kode} {...c} />
          ))}
        </div>
      </div>

      {/* Ranking row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CommodityRanking data={commodities} title="Komoditas Paling Naik Minggu Ini" />
        <RegionRanking data={regions} title="Wilayah Paling Tertekan Minggu Ini" />
      </div>

      {/* Volatility + Model perf */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-card rounded-md border p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-primary" /> Top Volatilitas
            </h3>
            <span className="text-[10px] text-muted-foreground">CV 30 hari</span>
          </div>
          <VolatilityList rows={volatilityTop} />
        </div>

        <div className="bg-card rounded-md border p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-primary" /> Performa Model (30 hari)
            </h3>
          </div>
          {perfRows.length === 0 ? (
            <div className="py-6 text-center text-xs text-muted-foreground">
              Belum ada evaluasi model.
            </div>
          ) : (
            <table className="w-full text-[11px]">
              <thead className="text-muted-foreground border-b">
                <tr className="text-left">
                  <th className="pb-1.5 font-medium">Model</th>
                  <th className="pb-1.5 font-medium">Horizon</th>
                  <th className="pb-1.5 font-medium text-right">MAPE</th>
                  <th className="pb-1.5 font-medium text-right">Coverage</th>
                </tr>
              </thead>
              <tbody>
                {perfRows.map((r, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-1.5 font-medium truncate max-w-[100px]">
                      {r.model_version}
                    </td>
                    <td className="py-1.5 text-muted-foreground">{r.horizon}d</td>
                    <td className="py-1.5 text-right tabular-nums">
                      {(r.mape * 100).toFixed(1)}%
                    </td>
                    <td className="py-1.5 text-right tabular-nums">
                      {(r.coverage_p10_p90 * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Insight + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {insight ? (
          <InsightCard judul={insight.judul} konten={insight.konten} tanggal={insight.tanggal} />
        ) : (
          <div className="bg-card rounded-md border p-4">
            <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
              <Lightbulb className="h-3.5 w-3.5 text-primary" /> Insight Hari Ini
            </h3>
            <div className="py-6 text-center text-xs text-muted-foreground">
              Belum ada insight tersedia.
            </div>
          </div>
        )}
        <AlertBanner alerts={alerts} />
      </div>
    </div>
  );
}
