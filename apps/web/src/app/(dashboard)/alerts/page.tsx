"use client";

import { useState, useMemo, useEffect } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useAlerts } from "@/hooks/use-alerts";
import {
  AlertTriangle,
  Info,
  AlertCircle,
  MapPin,
  Package,
  TrendingUp,
  TrendingDown,
  Clock,
  RefreshCw,
} from "lucide-react";

const PAGE_SIZE = 5;

type Severity = "critical" | "warning" | "info";
type FilterTab = "all" | Severity;

const SEVERITY_CONFIG = {
  critical: {
    label: "Critical",
    icon: AlertCircle,
    bar: "bg-risk-critical",
    badge: "bg-red-50 text-red-700 border border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900",
    count: "text-risk-critical",
    ring: "ring-red-200",
    pulse: true,
  },
  warning: {
    label: "Warning",
    icon: AlertTriangle,
    bar: "bg-risk-high",
    badge: "bg-orange-50 text-orange-700 border border-orange-200 dark:bg-orange-950/30 dark:text-orange-300 dark:border-orange-900",
    count: "text-risk-high",
    ring: "ring-orange-200",
    pulse: false,
  },
  info: {
    label: "Info",
    icon: Info,
    bar: "bg-blue-500",
    badge: "bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/30 dark:text-blue-300 dark:border-blue-900",
    count: "text-blue-600",
    ring: "ring-blue-200",
    pulse: false,
  },
} as const;

const ALERT_TYPE_LABELS: Record<string, string> = {
  PRICE_SPIKE: "Lonjakan Harga",
  PRICE_DROP: "Penurunan Harga",
  SUPPLY_SHORTAGE: "Defisit Pasokan",
  VOLATILITY: "Volatilitas Tinggi",
  ANOMALY: "Anomali Terdeteksi",
  FORECAST_BREACH: "Proyeksi Melewati Batas",
};

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("id-ID", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function formatCurrency(val: number | null): string {
  if (val === null) return "—";
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(val);
}

function DeltaBadge({
  actual,
  threshold,
}: {
  actual: number | null;
  threshold: number | null;
}) {
  if (actual === null || threshold === null) return null;
  const delta = actual - threshold;
  const pct = ((Math.abs(delta) / threshold) * 100).toFixed(1);
  const up = delta > 0;
  return (
    <span
      className={`inline-flex items-center gap-0.5 text-[11px] font-semibold px-1.5 py-0.5 rounded ${
        up
          ? "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400"
          : "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400"
      }`}
    >
      {up ? (
        <TrendingUp className="h-2.5 w-2.5" />
      ) : (
        <TrendingDown className="h-2.5 w-2.5" />
      )}
      {up ? "+" : "-"}
      {pct}%
    </span>
  );
}

function AlertCard({
  alert,
}: {
  alert: {
    id: number;
    tanggal: string;
    alertType: string;
    severity: string;
    judul: string;
    deskripsi: string;
    nilaiAktual: number | null;
    nilaiThreshold: number | null;
    region: { kode: string; nama: string };
    commodity: { kode: string; nama: string };
  };
}) {
  const sev = (alert.severity as Severity) in SEVERITY_CONFIG
    ? (alert.severity as Severity)
    : "info";
  const cfg = SEVERITY_CONFIG[sev];
  const Icon = cfg.icon;
  const typeLabel =
    ALERT_TYPE_LABELS[alert.alertType] || alert.alertType?.replace(/_/g, " ");

  return (
    <div className="group flex bg-card border rounded-md overflow-hidden hover:shadow-sm transition-shadow">
      {/* Severity bar */}
      <div className={`w-1 shrink-0 ${cfg.bar}`} />

      <div className="flex-1 min-w-0 p-3">
        {/* Top row: badges + date */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 flex-wrap min-w-0">
            <span
              className={`inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${cfg.badge}`}
            >
              {cfg.pulse && (
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-risk-critical" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-risk-critical" />
                </span>
              )}
              <Icon className="h-2.5 w-2.5" />
              {cfg.label}
            </span>
            {typeLabel && (
              <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
                {typeLabel}
              </span>
            )}
            <DeltaBadge
              actual={alert.nilaiAktual}
              threshold={alert.nilaiThreshold}
            />
          </div>
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground whitespace-nowrap shrink-0">
            <Clock className="h-3 w-3" />
            {formatDate(alert.tanggal)}
          </div>
        </div>

        {/* Title */}
        <h4 className="mt-1.5 text-[13px] font-semibold text-foreground leading-snug line-clamp-1">
          {alert.judul}
        </h4>

        {/* Description */}
        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-1">
          {alert.deskripsi}
        </p>

        {/* Meta row — compact single line */}
        <div className="mt-1.5 flex items-center gap-x-3 gap-y-1 flex-wrap text-[10px] text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Package className="h-3 w-3 text-primary" />
            <span className="font-medium text-foreground">{alert.commodity.nama}</span>
          </span>
          <span className="inline-flex items-center gap-1">
            <MapPin className="h-3 w-3 text-primary" />
            <span className="font-medium text-foreground">{alert.region.nama}</span>
          </span>
          {alert.nilaiAktual !== null && (
            <span>
              Aktual{" "}
              <span className="font-medium text-foreground">
                {formatCurrency(alert.nilaiAktual)}
              </span>
            </span>
          )}
          {alert.nilaiThreshold !== null && (
            <span>
              Threshold{" "}
              <span className="font-medium text-foreground">
                {formatCurrency(alert.nilaiThreshold)}
              </span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="flex bg-card border rounded-md overflow-hidden">
      <div className="w-1 shrink-0 bg-muted" />
      <div className="flex-1 p-3 space-y-1.5 animate-pulse">
        <div className="flex gap-1.5">
          <div className="h-3.5 w-14 bg-muted rounded-full" />
          <div className="h-3.5 w-20 bg-muted rounded-full" />
        </div>
        <div className="h-3.5 w-3/4 bg-muted rounded" />
        <div className="h-3 w-full bg-muted rounded" />
        <div className="flex gap-3 pt-0.5">
          <div className="h-3 w-20 bg-muted rounded" />
          <div className="h-3 w-24 bg-muted rounded" />
        </div>
      </div>
    </div>
  );
}

export default function AlertsPage() {
  const [activeTab, setActiveTab] = useState<FilterTab>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data: alertResponse, isLoading, dataUpdatedAt, refetch, isFetching } =
    useAlerts(true, undefined, 50);

  const allAlerts = alertResponse?.data ?? [];

  const counts = useMemo(
    () => ({
      all: allAlerts.length,
      critical: allAlerts.filter((a) => a.severity === "critical").length,
      warning: allAlerts.filter((a) => a.severity === "warning").length,
      info: allAlerts.filter((a) => a.severity === "info").length,
    }),
    [allAlerts]
  );

  const filtered = useMemo(() => {
    let list = activeTab === "all" ? allAlerts : allAlerts.filter((a) => a.severity === activeTab);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (a) =>
          a.judul.toLowerCase().includes(q) ||
          a.commodity.nama.toLowerCase().includes(q) ||
          a.region.nama.toLowerCase().includes(q)
      );
    }
    return list;
  }, [allAlerts, activeTab, search]);

  // Reset to page 1 whenever filter/search changes
  useEffect(() => { setPage(1); }, [activeTab, search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("id-ID", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  const TABS: { key: FilterTab; label: string; count: number }[] = [
    { key: "all", label: "Semua", count: counts.all },
    { key: "critical", label: "Critical", count: counts.critical },
    { key: "warning", label: "Warning", count: counts.warning },
    { key: "info", label: "Info", count: counts.info },
  ];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-foreground">
            Alert Center
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Komoditas dan wilayah yang memerlukan perhatian segera
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50 mt-1"
        >
          <RefreshCw className={`h-3 w-3 ${isFetching ? "animate-spin" : ""}`} />
          {lastUpdated ? `Diperbarui ${lastUpdated}` : "Perbarui"}
        </button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-card border rounded-md p-3">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
            Total Alert
          </p>
          <p className="text-2xl font-bold text-foreground mt-0.5">
            {isLoading ? <span className="animate-pulse">—</span> : counts.all}
          </p>
        </div>
        {(["critical", "warning", "info"] as const).map((sev) => {
          const cfg = SEVERITY_CONFIG[sev];
          const Icon = cfg.icon;
          return (
            <div key={sev} className="bg-card border rounded-md p-3">
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1">
                <Icon className={`h-3 w-3 ${cfg.count}`} />
                {cfg.label}
              </p>
              <p className={`text-2xl font-bold mt-0.5 ${cfg.count}`}>
                {isLoading ? (
                  <span className="animate-pulse text-muted-foreground">—</span>
                ) : (
                  counts[sev]
                )}
              </p>
            </div>
          );
        })}
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1 bg-muted rounded-md p-0.5">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-1 rounded text-[12px] font-medium transition-colors flex items-center gap-1.5 ${
                activeTab === tab.key
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
              <span
                className={`text-[10px] font-semibold px-1 rounded-full ${
                  activeTab === tab.key
                    ? tab.key === "critical"
                      ? "bg-red-100 text-red-700"
                      : tab.key === "warning"
                      ? "bg-orange-100 text-orange-700"
                      : tab.key === "info"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-secondary text-secondary-foreground"
                    : "bg-background/60 text-muted-foreground"
                }`}
              >
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Cari komoditas atau wilayah…"
          className="flex-1 min-w-[180px] max-w-xs h-8 px-3 text-[12px] bg-card border rounded-md placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Alert list */}
      <div className="space-y-2">
        {isLoading &&
          Array.from({ length: PAGE_SIZE }).map((_, i) => <SkeletonCard key={i} />)}

        {!isLoading && filtered.length === 0 && (
          <div className="bg-card border rounded-md p-10 text-center">
            <AlertTriangle className="h-8 w-8 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-sm font-medium text-muted-foreground">
              {search
                ? `Tidak ada alert untuk "${search}"`
                : "Tidak ada alert aktif saat ini"}
            </p>
            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                className="mt-2 text-xs text-primary hover:underline"
              >
                Hapus filter
              </button>
            )}
          </div>
        )}

        {!isLoading &&
          paginated.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
      </div>

      {/* Pagination — sticky bottom, prominent, large touch targets */}
      {!isLoading && filtered.length > 0 && (
        <div className="sticky bottom-0 -mx-2 px-2 pt-3 pb-2 bg-gradient-to-t from-background via-background to-background/0">
          <div className="flex items-center justify-between gap-3 bg-card border rounded-md shadow-sm px-3 py-2">
            <p className="text-xs text-muted-foreground hidden sm:block">
              Halaman <span className="font-semibold text-foreground">{page}</span> dari{" "}
              <span className="font-semibold text-foreground">{totalPages}</span>
              <span className="mx-1.5 text-muted-foreground/40">·</span>
              {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)} dari{" "}
              {filtered.length}
            </p>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center gap-1 h-9 px-3 rounded-md border bg-card text-xs font-medium text-foreground hover:bg-accent hover:border-primary/40 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-card disabled:hover:border-border transition-colors"
                aria-label="Halaman sebelumnya"
              >
                <ChevronLeft className="h-4 w-4" />
                <span className="hidden sm:inline">Sebelumnya</span>
              </button>

              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
                  .reduce<(number | "…")[]>((acc, p, idx, arr) => {
                    if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push("…");
                    acc.push(p);
                    return acc;
                  }, [])
                  .map((item, idx) =>
                    item === "…" ? (
                      <span
                        key={`ellipsis-${idx}`}
                        className="h-9 w-7 flex items-center justify-center text-xs text-muted-foreground"
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
                        className={`h-9 min-w-9 px-2.5 rounded-md text-xs font-semibold transition-colors ${
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
                className="flex items-center gap-1 h-9 px-3 rounded-md border bg-card text-xs font-medium text-foreground hover:bg-accent hover:border-primary/40 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-card disabled:hover:border-border transition-colors"
                aria-label="Halaman berikutnya"
              >
                <span className="hidden sm:inline">Berikutnya</span>
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
