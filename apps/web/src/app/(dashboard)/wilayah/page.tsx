"use client";

import { useMemo, useState, useEffect } from "react";
import { IndonesiaChoropleth } from "@/components/maps/indonesia-choropleth";
import { useRiskScores } from "@/hooks/use-risk-scores";
import { useRegionHeatmap } from "@/hooks/use-regions";
import {
  Map as MapIcon,
  MapPin,
  AlertTriangle,
  TrendingUp,
  Activity,
  RefreshCw,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";

const PAGE_SIZE = 8;

interface RegionHeatmapItem {
  kodeWilayah: string;
  namaProvinsi: string;
  avgPriceChange: number;
  alertCount: number;
  riskCategory: "rendah" | "sedang" | "tinggi";
}

const riskBadge: Record<string, string> = {
  tinggi: "bg-risk-critical/10 text-risk-critical border-risk-critical/30",
  sedang: "bg-risk-high/10 text-risk-high border-risk-high/30",
  rendah: "bg-risk-low/10 text-risk-low border-risk-low/30",
};

const riskLabel: Record<string, string> = {
  tinggi: "Tinggi",
  sedang: "Sedang",
  rendah: "Rendah",
};

function changeColor(value: number): string {
  if (value > 10) return "text-risk-critical";
  if (value > 5) return "text-risk-high";
  if (value > 2) return "text-risk-medium";
  return "text-risk-low";
}

export default function WilayahPage() {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [mapMode, setMapMode] = useState<"price_change" | "risk">("price_change");
  const [search, setSearch] = useState("");

  type SortKey = "namaProvinsi" | "avgPriceChange" | "alertCount" | "riskCategory";
  const [sortKey, setSortKey] = useState<SortKey>("avgPriceChange");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  const {
    data: heatmapData,
    isLoading,
    isFetching,
    refetch,
    dataUpdatedAt,
  } = useRegionHeatmap();
  const { data: riskScores } = useRiskScores();

  const regions = useMemo(() => {
    const list = (heatmapData ?? []) as unknown as RegionHeatmapItem[];
    return list.map((r) => {
      const rs = riskScores?.find((s) => s.kodeWilayah === r.kodeWilayah);
      return {
        ...r,
        riskCategory: (rs?.riskCategory ?? r.riskCategory ?? "rendah") as
          | "rendah"
          | "sedang"
          | "tinggi",
      };
    });
  }, [heatmapData, riskScores]);

  const mapData = useMemo(
    () =>
      regions.map((r) => ({
        kodeWilayah: r.kodeWilayah,
        namaProvinsi: r.namaProvinsi,
        avgPriceChange: r.avgPriceChange,
        riskCategory: r.riskCategory,
        hasAlert: r.alertCount > 0,
      })),
    [regions]
  );

  // KPI counts
  const kpis = useMemo(() => {
    const tinggi = regions.filter((r) => r.riskCategory === "tinggi").length;
    const sedang = regions.filter((r) => r.riskCategory === "sedang").length;
    const rendah = regions.filter((r) => r.riskCategory === "rendah").length;
    const totalAlerts = regions.reduce((sum, r) => sum + (r.alertCount ?? 0), 0);
    const maxRegion = [...regions].sort((a, b) => b.avgPriceChange - a.avgPriceChange)[0] ?? null;
    return { tinggi, sedang, rendah, totalAlerts, maxRegion, tracked: regions.length };
  }, [regions]);

  const top10 = useMemo(
    () =>
      [...regions]
        .sort((a, b) => b.avgPriceChange - a.avgPriceChange)
        .slice(0, 10),
    [regions]
  );

  const filteredSorted = useMemo(() => {
    const filtered = search.trim()
      ? regions.filter((r) =>
          r.namaProvinsi.toLowerCase().includes(search.toLowerCase())
        )
      : regions;
    const copy = [...filtered];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "string" && typeof bv === "string") {
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sortDir === "asc"
        ? (av as number) - (bv as number)
        : (bv as number) - (av as number);
    });
    return copy;
  }, [regions, search, sortKey, sortDir]);

  // Reset to page 1 whenever filter/sort changes
  useEffect(() => {
    setPage(1);
  }, [search, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filteredSorted.length / PAGE_SIZE));
  const paginatedRegions = filteredSorted.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );

  const pageButtons = useMemo(() => {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
      .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
      .reduce<(number | "…")[]>((acc, p, idx, arr) => {
        if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push("…");
        acc.push(p);
        return acc;
      }, []);
  }, [page, totalPages]);

  const selectedInfo = selectedRegion
    ? regions.find((r) => r.kodeWilayah === selectedRegion)
    : null;

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir(key === "namaProvinsi" ? "asc" : "desc");
    }
  }

  function SortHeader({
    label,
    sortKeyName,
    align = "left",
  }: {
    label: string;
    sortKeyName: SortKey;
    align?: "left" | "right";
  }) {
    const active = sortKey === sortKeyName;
    const SortIcon = active && sortDir === "asc" ? ChevronUp : ChevronDown;
    return (
      <th
        className={`p-2.5 font-medium text-muted-foreground text-[11px] uppercase tracking-wide ${align === "right" ? "text-right" : "text-left"}`}
      >
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

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
            <MapIcon className="h-4 w-4 text-primary" />
            Peta Tekanan Harga
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Distribusi geografis tekanan harga pangan & ranking provinsi
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${isFetching ? "animate-spin" : ""}`} />
          {lastUpdated ? `Diperbarui ${lastUpdated}` : "Perbarui"}
        </button>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          label="Risiko Tinggi"
          value={kpis.tinggi}
          detail={`dari ${kpis.tracked} provinsi`}
          Icon={AlertTriangle}
          tone="critical"
          loading={isLoading}
        />
        <KpiCard
          label="Risiko Sedang"
          value={kpis.sedang}
          detail={`dari ${kpis.tracked} provinsi`}
          Icon={Activity}
          tone="high"
          loading={isLoading}
        />
        <KpiCard
          label="Alert Aktif"
          value={kpis.totalAlerts}
          detail="seluruh provinsi"
          Icon={AlertTriangle}
          tone="medium"
          loading={isLoading}
        />
        <KpiCard
          label="Provinsi Tertekan"
          value={kpis.maxRegion?.namaProvinsi ?? "—"}
          detail={
            kpis.maxRegion
              ? `+${kpis.maxRegion.avgPriceChange.toFixed(1)}%`
              : "Belum ada data"
          }
          Icon={TrendingUp}
          tone="critical"
          loading={isLoading}
          isText
        />
      </div>

      {/* Map + side panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Map */}
        <div className="lg:col-span-2 bg-card rounded-md border p-4">
          <div className="flex items-center justify-between gap-3 mb-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <MapIcon className="h-3.5 w-3.5 text-primary" />
              Heatmap Indonesia
            </h3>
            <div className="flex rounded-md bg-muted p-0.5">
              <button
                type="button"
                onClick={() => setMapMode("price_change")}
                className={`text-[11px] px-2.5 py-1 rounded font-medium transition-colors ${
                  mapMode === "price_change"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Perubahan Harga
              </button>
              <button
                type="button"
                onClick={() => setMapMode("risk")}
                className={`text-[11px] px-2.5 py-1 rounded font-medium transition-colors ${
                  mapMode === "risk"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Kategori Risiko
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="h-[260px] bg-muted/30 rounded animate-pulse" />
          ) : (
            <IndonesiaChoropleth
              data={mapData}
              mode={mapMode}
              selectedKode={selectedRegion}
              onRegionClick={(kode) =>
                setSelectedRegion(kode === selectedRegion ? null : kode)
              }
            />
          )}

          {selectedInfo && (
            <div className="mt-4 rounded-md border bg-accent/40 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <MapPin className="h-3 w-3" /> Provinsi
                  </p>
                  <p className="text-sm font-semibold text-foreground mt-0.5">
                    {selectedInfo.namaProvinsi}
                  </p>
                  <div className="mt-2 flex items-center gap-4 text-[11px]">
                    <span className="text-muted-foreground">
                      Rata-rata kenaikan:{" "}
                      <span
                        className={`font-semibold tabular-nums ${changeColor(selectedInfo.avgPriceChange)}`}
                      >
                        {selectedInfo.avgPriceChange > 0 ? "+" : ""}
                        {selectedInfo.avgPriceChange.toFixed(1)}%
                      </span>
                    </span>
                    <span className="text-muted-foreground">
                      Alert aktif:{" "}
                      <span className="font-semibold text-foreground">
                        {selectedInfo.alertCount}
                      </span>
                    </span>
                  </div>
                </div>
                <span
                  className={`text-[10px] font-semibold uppercase tracking-wide px-2 py-1 rounded-full border ${riskBadge[selectedInfo.riskCategory] ?? riskBadge.rendah}`}
                >
                  {riskLabel[selectedInfo.riskCategory]}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Top-10 side panel */}
        <div className="bg-card rounded-md border p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <TrendingUp className="h-3.5 w-3.5 text-primary" />
              Top 10 Tertekan
            </h3>
            <span className="text-[10px] text-muted-foreground">avg kenaikan</span>
          </div>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-7 bg-muted/40 rounded animate-pulse" />
              ))}
            </div>
          ) : top10.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground">
              Belum ada data wilayah.
            </div>
          ) : (
            <ul className="space-y-1.5">
              {top10.map((r, i) => {
                const isSelected = selectedRegion === r.kodeWilayah;
                return (
                  <li key={r.kodeWilayah}>
                    <button
                      type="button"
                      onClick={() =>
                        setSelectedRegion(
                          r.kodeWilayah === selectedRegion ? null : r.kodeWilayah
                        )
                      }
                      className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left transition-colors ${
                        isSelected
                          ? "bg-primary/10 text-primary"
                          : "hover:bg-accent/40"
                      }`}
                    >
                      <span
                        className={`text-[10px] font-semibold tabular-nums w-4 text-right ${
                          i < 3 ? "text-risk-critical" : "text-muted-foreground"
                        }`}
                      >
                        {i + 1}
                      </span>
                      <span className="text-xs font-medium flex-1 truncate">
                        {r.namaProvinsi}
                      </span>
                      {r.alertCount > 0 && (
                        <span className="inline-flex items-center gap-0.5 text-[10px] text-risk-high">
                          <AlertTriangle className="h-2.5 w-2.5" />
                          {r.alertCount}
                        </span>
                      )}
                      <span
                        className={`text-xs font-semibold tabular-nums ${changeColor(r.avgPriceChange)}`}
                      >
                        +{r.avgPriceChange.toFixed(1)}%
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>

      {/* Full ranking table */}
      <div className="bg-card rounded-md border">
        <div className="flex items-center justify-between gap-3 px-4 py-3 border-b">
          <div>
            <h3 className="text-sm font-semibold">Semua Provinsi</h3>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Klik baris untuk menyorot wilayah pada peta
            </p>
          </div>
          <div className="relative max-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari provinsi…"
              className="w-full h-8 pl-8 pr-3 text-xs bg-background border rounded-md placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 border-b">
              <tr>
                <th className="w-10 p-2.5 text-[11px] text-muted-foreground uppercase tracking-wide text-left font-medium">
                  #
                </th>
                <SortHeader label="Provinsi" sortKeyName="namaProvinsi" />
                <SortHeader label="Rata-rata Kenaikan" sortKeyName="avgPriceChange" align="right" />
                <SortHeader label="Risiko" sortKeyName="riskCategory" />
                <SortHeader label="Alert" sortKeyName="alertCount" align="right" />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td colSpan={5} className="p-3">
                      <div className="h-4 w-full bg-muted/40 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : filteredSorted.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    {search
                      ? `Tidak ada provinsi cocok dengan "${search}"`
                      : "Belum ada data wilayah."}
                  </td>
                </tr>
              ) : (
                paginatedRegions.map((r, idx) => {
                  const isSelected = selectedRegion === r.kodeWilayah;
                  const rowNumber = (page - 1) * PAGE_SIZE + idx + 1;
                  return (
                    <tr
                      key={r.kodeWilayah}
                      onClick={() =>
                        setSelectedRegion(
                          r.kodeWilayah === selectedRegion ? null : r.kodeWilayah
                        )
                      }
                      className={`border-b last:border-0 cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-primary/10 hover:bg-primary/15"
                          : "hover:bg-accent/40"
                      }`}
                    >
                      <td className="p-2.5 text-muted-foreground tabular-nums">
                        {rowNumber}
                      </td>
                      <td className="p-2.5 font-medium text-foreground">
                        <div className="flex items-center gap-2">
                          {isSelected && (
                            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                          )}
                          {r.namaProvinsi}
                        </div>
                      </td>
                      <td
                        className={`p-2.5 text-right font-semibold tabular-nums ${changeColor(r.avgPriceChange)}`}
                      >
                        {r.avgPriceChange > 0 ? "+" : ""}
                        {r.avgPriceChange.toFixed(1)}%
                      </td>
                      <td className="p-2.5">
                        <span
                          className={`text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full border ${riskBadge[r.riskCategory] ?? riskBadge.rendah}`}
                        >
                          {riskLabel[r.riskCategory]}
                        </span>
                      </td>
                      <td className="p-2.5 text-right">
                        {r.alertCount > 0 ? (
                          <span className="inline-flex items-center gap-0.5 text-risk-high font-semibold">
                            <AlertTriangle className="h-3 w-3" />
                            {r.alertCount}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!isLoading && filteredSorted.length > 0 && (
          <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-t bg-muted/30">
            <p className="text-[11px] text-muted-foreground hidden sm:block">
              Halaman <span className="font-semibold text-foreground">{page}</span> /{" "}
              <span className="font-semibold text-foreground">{totalPages}</span>
              <span className="mx-1.5 text-muted-foreground/40">·</span>
              {(page - 1) * PAGE_SIZE + 1}–
              {Math.min(page * PAGE_SIZE, filteredSorted.length)} dari{" "}
              {filteredSorted.length} provinsi
            </p>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                aria-label="Halaman sebelumnya"
                className="flex items-center gap-1 h-8 px-2.5 rounded-md border bg-card text-[11px] font-medium text-foreground hover:bg-accent hover:border-primary/40 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-card disabled:hover:border-border transition-colors"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Prev</span>
              </button>

              <div className="flex items-center gap-1">
                {pageButtons.map((item, idx) =>
                  item === "…" ? (
                    <span
                      key={`e-${idx}`}
                      className="h-8 w-6 flex items-center justify-center text-[11px] text-muted-foreground"
                    >
                      …
                    </span>
                  ) : (
                    <button
                      key={item}
                      type="button"
                      onClick={() => setPage(item as number)}
                      aria-current={page === item ? "page" : undefined}
                      aria-label={`Halaman ${item}`}
                      className={`h-8 min-w-8 px-2 rounded-md text-[11px] font-semibold transition-colors ${
                        page === item
                          ? "bg-primary text-primary-foreground shadow-sm"
                          : "bg-card border text-foreground hover:bg-accent hover:border-primary/40"
                      }`}
                    >
                      {item}
                    </button>
                  )
                )}
              </div>

              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                aria-label="Halaman berikutnya"
                className="flex items-center gap-1 h-8 px-2.5 rounded-md border bg-card text-[11px] font-medium text-foreground hover:bg-accent hover:border-primary/40 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-card disabled:hover:border-border transition-colors"
              >
                <span className="hidden sm:inline">Next</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function KpiCard({
  label,
  value,
  detail,
  Icon,
  tone,
  loading,
  isText,
}: {
  label: string;
  value: number | string;
  detail: string;
  Icon: typeof TrendingUp;
  tone: "critical" | "high" | "medium" | "low";
  loading?: boolean;
  isText?: boolean;
}) {
  const toneClass =
    tone === "critical"
      ? "text-risk-critical"
      : tone === "high"
        ? "text-risk-high"
        : tone === "medium"
          ? "text-risk-medium"
          : "text-risk-low";
  return (
    <div className="bg-card rounded-md border p-3">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
        <Icon className={`h-3 w-3 ${toneClass}`} />
        {label}
      </div>
      {loading ? (
        <>
          <div className="mt-2 h-6 w-16 bg-muted rounded animate-pulse" />
          <div className="mt-1 h-3 w-20 bg-muted rounded animate-pulse" />
        </>
      ) : (
        <>
          <p
            className={`mt-1 font-bold tabular-nums truncate ${isText ? "text-base" : `text-2xl ${toneClass}`}`}
          >
            {value}
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">{detail}</p>
        </>
      )}
    </div>
  );
}
