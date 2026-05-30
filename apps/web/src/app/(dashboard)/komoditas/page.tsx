"use client";

import { useState, useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  LineChart as LineChartIcon,
  Package,
  MapPin,
  Calendar,
  Search,
  ArrowUpDown,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { PriceLineChart } from "@/components/charts/price-line-chart";
import { DriverPanel } from "@/components/dashboard/driver-panel";
import { usePrices, useCommodityRanking } from "@/hooks/use-prices";
import { useForecast } from "@/hooks/use-forecast";
import { useDrivers } from "@/hooks/use-drivers";
import { MVP_COMMODITIES, REGIONS } from "@/lib/constants";

// ============================================================
// Helpers
// ============================================================

function formatRupiah(val: number | null | undefined): string {
  if (val === null || val === undefined) return "—";
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(val);
}

function changeTone(value: number | null | undefined) {
  if (value === null || value === undefined || Math.abs(value) < 0.05) {
    return { color: "text-muted-foreground", Icon: Minus };
  }
  return value > 0
    ? { color: "text-risk-critical", Icon: TrendingUp }
    : { color: "text-risk-low", Icon: TrendingDown };
}

// ============================================================
// Sub-components
// ============================================================

function ChangeBadge({ value, size = "sm" }: { value: number | null; size?: "sm" | "lg" }) {
  if (value === null) {
    return <span className="text-muted-foreground">—</span>;
  }
  const { color, Icon } = changeTone(value);
  const sizes =
    size === "lg"
      ? { icon: "h-4 w-4", text: "text-lg font-bold" }
      : { icon: "h-3 w-3", text: "text-sm font-medium" };
  return (
    <span className={`inline-flex items-center gap-1 tabular-nums ${color}`}>
      <Icon className={sizes.icon} />
      <span className={sizes.text}>
        {value > 0 ? "+" : ""}
        {value.toFixed(1)}%
      </span>
    </span>
  );
}

function HeroStat({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
        {label}
      </p>
      <div className="mt-1">{children}</div>
    </div>
  );
}

// ============================================================
// Page
// ============================================================

export default function KomoditasPage() {
  // Filter state — initialise from MVP list so the value always matches an option
  const [selected, setSelected] = useState<string>(MVP_COMMODITIES[1].kode); // CABAI_MERAH
  const [region, setRegion] = useState<string>("00");
  const [days, setDays] = useState(30);
  const [showForecast, setShowForecast] = useState(true);
  const [tableSearch, setTableSearch] = useState("");

  // Data queries
  const {
    data: rankingData,
    isLoading: rankingLoading,
    refetch: refetchRanking,
    isFetching: rankingFetching,
    dataUpdatedAt,
  } = useCommodityRanking("weekly_change", 20);
  const {
    data: priceData,
    isLoading: priceLoading,
    refetch: refetchPrice,
    isFetching: priceFetching,
  } = usePrices(selected, region, days);
  const {
    data: forecastData,
    isFetching: forecastFetching,
  } = useForecast(selected, region, 14);
  const { data: driverData } = useDrivers(selected, region);

  // Ranking rows for the table — fallback to MVP_COMMODITIES so the dropdown
  // always lists known commodities even when ranking endpoint returns partial data
  const rankingByKode = useMemo(() => {
    const map = new Map<string, {
      kode: string; nama: string; harga: number;
      harian: number; mingguan: number; bulanan: number;
    }>();
    for (const c of rankingData?.data ?? []) {
      map.set(c.kodeKomoditas, {
        kode: c.kodeKomoditas,
        nama: c.namaDisplay,
        harga: c.hargaTerakhir ?? 0,
        harian: c.perubahanHarian ?? 0,
        mingguan: c.perubahanMingguan ?? 0,
        bulanan: c.perubahanBulanan ?? 0,
      });
    }
    return map;
  }, [rankingData]);

  const commodities = useMemo(() => {
    return MVP_COMMODITIES.map((mvp) => {
      const ranked = rankingByKode.get(mvp.kode);
      return {
        kode: mvp.kode,
        nama: mvp.display,
        satuan: mvp.satuan,
        harga: ranked?.harga ?? 0,
        harian: ranked?.harian ?? null,
        mingguan: ranked?.mingguan ?? null,
        bulanan: ranked?.bulanan ?? null,
      };
    });
  }, [rankingByKode]);

  const selectedCommodity = commodities.find((c) => c.kode === selected);
  const selectedRegion = REGIONS.find((r) => r.kode === region);

  // Latest price prefers price-daily response (most accurate per region) and
  // falls back to ranking (which is national-only) if nothing returned.
  const latestPrice = priceData?.data?.[0]?.harga ?? selectedCommodity?.harga ?? null;

  // Chart data — reverse so oldest is on left
  const chartData = useMemo(() => {
    if (!priceData?.data?.length) return [];
    return priceData.data
      .map((d) => ({ tanggal: d.tanggal, harga: d.harga }))
      .reverse();
  }, [priceData]);

  // Table sorting + filtering
  type SortKey = "nama" | "harga" | "harian" | "mingguan" | "bulanan";
  const [sortKey, setSortKey] = useState<SortKey>("mingguan");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sortedCommodities = useMemo(() => {
    const filtered = tableSearch.trim()
      ? commodities.filter((c) => c.nama.toLowerCase().includes(tableSearch.toLowerCase()))
      : commodities;
    const copy = [...filtered];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "string" && typeof bv === "string") {
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      const an = (av as number) ?? -Infinity;
      const bn = (bv as number) ?? -Infinity;
      return sortDir === "asc" ? an - bn : bn - an;
    });
    return copy;
  }, [commodities, tableSearch, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir(key === "nama" ? "asc" : "desc");
    }
  }

  function SortHeader({ label, sortKeyName, align = "left" }: { label: string; sortKeyName: SortKey; align?: "left" | "right" }) {
    const active = sortKey === sortKeyName;
    const SortIcon = active && sortDir === "asc" ? ChevronUp : ChevronDown;
    return (
      <th className={`p-2.5 font-medium text-muted-foreground text-[11px] uppercase tracking-wide ${align === "right" ? "text-right" : "text-left"}`}>
        <button
          type="button"
          onClick={() => toggleSort(sortKeyName)}
          className={`inline-flex items-center gap-0.5 hover:text-foreground ${active ? "text-foreground" : ""}`}
        >
          {label}
          <SortIcon className={`h-3 w-3 ${active ? "" : "opacity-30"}`} />
        </button>
      </th>
    );
  }

  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("id-ID", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;
  const anyFetching = rankingFetching || priceFetching || forecastFetching;

  const refetchAll = () => {
    refetchRanking();
    refetchPrice();
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Harga Komoditas</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Tren harga harian komoditas pangan strategis nasional & per provinsi
          </p>
        </div>
        <button
          type="button"
          onClick={refetchAll}
          disabled={anyFetching}
          className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${anyFetching ? "animate-spin" : ""}`} />
          {lastUpdated ? `Diperbarui ${lastUpdated}` : "Perbarui"}
        </button>
      </div>

      {/* Filter bar */}
      <div className="bg-card rounded-md border p-3 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[180px]">
          <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1 mb-1">
            <Package className="h-3 w-3" /> Komoditas
          </label>
          <select
            className="w-full h-9 px-2.5 text-[13px] bg-background border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            {MVP_COMMODITIES.map((c) => (
              <option key={c.kode} value={c.kode}>
                {c.display}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[180px]">
          <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1 mb-1">
            <MapPin className="h-3 w-3" /> Wilayah
          </label>
          <select
            className="w-full h-9 px-2.5 text-[13px] bg-background border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            {REGIONS.map((r) => (
              <option key={r.kode} value={r.kode}>
                {r.provinsi}
              </option>
            ))}
          </select>
        </div>
        <div className="min-w-[110px]">
          <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1 mb-1">
            <Calendar className="h-3 w-3" /> Periode
          </label>
          <select
            className="w-full h-9 px-2.5 text-[13px] bg-background border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          >
            <option value={7}>7 Hari</option>
            <option value={14}>14 Hari</option>
            <option value={30}>30 Hari</option>
            <option value={90}>90 Hari</option>
          </select>
        </div>
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground h-9 px-3 border rounded-md bg-background cursor-pointer hover:bg-accent">
          <input
            type="checkbox"
            checked={showForecast}
            onChange={(e) => setShowForecast(e.target.checked)}
            className="rounded border-input"
          />
          Tampilkan Forecast 14 Hari
        </label>
      </div>

      {/* Hero stats card */}
      <div className="bg-card rounded-md border p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
              <span className="font-semibold">{selectedCommodity?.nama ?? "—"}</span>
              <span className="text-muted-foreground/40">·</span>
              <span>{selectedRegion?.provinsi ?? "—"}</span>
            </div>
            <p className="text-2xl font-bold tabular-nums mt-1">
              {priceLoading && !latestPrice ? (
                <span className="inline-block h-7 w-32 bg-muted rounded animate-pulse" />
              ) : (
                <>
                  {formatRupiah(latestPrice)}
                  <span className="text-sm text-muted-foreground font-normal ml-1">
                    /{selectedCommodity?.satuan ?? "kg"}
                  </span>
                </>
              )}
            </p>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <HeroStat label="Harian">
              <ChangeBadge value={selectedCommodity?.harian ?? null} size="lg" />
            </HeroStat>
            <HeroStat label="Mingguan">
              <ChangeBadge value={selectedCommodity?.mingguan ?? null} size="lg" />
            </HeroStat>
            <HeroStat label="Bulanan">
              <ChangeBadge value={selectedCommodity?.bulanan ?? null} size="lg" />
            </HeroStat>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-card rounded-md border p-4">
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <LineChartIcon className="h-3.5 w-3.5 text-primary" />
            Tren Harga {days} Hari
          </h3>
          {showForecast && (
            <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1">
                <span className="h-0.5 w-3 bg-primary rounded" />
                Historis
              </span>
              <span className="flex items-center gap-1">
                <span className="h-0.5 w-3 border-t border-dashed border-risk-high rounded" />
                Forecast
              </span>
            </div>
          )}
        </div>
        {priceLoading ? (
          <div className="h-[280px] bg-muted/30 rounded animate-pulse" />
        ) : chartData.length > 0 ? (
          <PriceLineChart
            data={chartData}
            forecastData={forecastData?.data}
            showForecast={showForecast}
          />
        ) : (
          <div className="h-[280px] flex flex-col items-center justify-center border border-dashed rounded text-center">
            <p className="text-sm text-muted-foreground font-medium">
              Belum ada data harga untuk kombinasi ini
            </p>
            <p className="text-[11px] text-muted-foreground/80 mt-1">
              {selectedCommodity?.nama} · {selectedRegion?.provinsi} · {days} hari terakhir
            </p>
            {region !== "00" && (
              <button
                type="button"
                onClick={() => setRegion("00")}
                className="mt-2 text-xs text-primary hover:underline"
              >
                Coba wilayah Nasional
              </button>
            )}
          </div>
        )}
      </div>

      {/* Driver Panel */}
      <DriverPanel
        drivers={driverData?.drivers ?? []}
        commodity={selectedCommodity?.nama}
      />

      {/* Ranking Table */}
      <div className="bg-card rounded-md border">
        <div className="flex items-center justify-between gap-3 px-4 py-3 border-b">
          <div>
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <ArrowUpDown className="h-3.5 w-3.5 text-primary" />
              Perubahan Harga Semua Komoditas
            </h3>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Klik baris untuk pilih komoditas pada grafik di atas
            </p>
          </div>
          <div className="relative max-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={tableSearch}
              onChange={(e) => setTableSearch(e.target.value)}
              placeholder="Cari komoditas…"
              className="w-full h-8 pl-8 pr-3 text-xs bg-background border rounded-md placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 border-b">
              <tr>
                <SortHeader label="Komoditas" sortKeyName="nama" />
                <SortHeader label="Harga" sortKeyName="harga" align="right" />
                <SortHeader label="Harian" sortKeyName="harian" align="right" />
                <SortHeader label="Mingguan" sortKeyName="mingguan" align="right" />
                <SortHeader label="Bulanan" sortKeyName="bulanan" align="right" />
              </tr>
            </thead>
            <tbody>
              {rankingLoading && commodities.every((c) => c.harga === 0) ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td colSpan={5} className="p-3">
                      <div className="h-4 w-full bg-muted/40 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : sortedCommodities.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    {tableSearch ? `Tidak ada komoditas cocok dengan "${tableSearch}"` : "Belum ada data komoditas tersedia."}
                  </td>
                </tr>
              ) : (
                sortedCommodities.map((c) => {
                  const isSelected = selected === c.kode;
                  return (
                    <tr
                      key={c.kode}
                      onClick={() => setSelected(c.kode)}
                      className={`border-b last:border-0 cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-primary/10 hover:bg-primary/15"
                          : "hover:bg-accent/40"
                      }`}
                    >
                      <td className="p-2.5">
                        <div className="flex items-center gap-2">
                          {isSelected && (
                            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                          )}
                          <span className={`font-medium ${isSelected ? "text-primary" : "text-foreground"}`}>
                            {c.nama}
                          </span>
                        </div>
                      </td>
                      <td className="p-2.5 text-right font-mono tabular-nums text-foreground">
                        {c.harga > 0 ? formatRupiah(c.harga) : <span className="text-muted-foreground">—</span>}
                      </td>
                      <td className="p-2.5 text-right">
                        <ChangeBadge value={c.harian} />
                      </td>
                      <td className="p-2.5 text-right">
                        <ChangeBadge value={c.mingguan} />
                      </td>
                      <td className="p-2.5 text-right">
                        <ChangeBadge value={c.bulanan} />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
