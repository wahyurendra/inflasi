"use client";

import { useMemo, useState } from "react";
import {
  useCrossRegionComparison,
  useVolatilityRanking,
  usePriceGap,
} from "@/hooks/use-intelligence";
import {
  BarChart3,
  ArrowUpDown,
  TrendingUp,
  TrendingDown,
  Activity,
  RefreshCw,
  Info,
  ChevronUp,
  ChevronDown,
  Search,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid,
} from "recharts";
import { MVP_COMMODITIES } from "@/lib/constants";

// ============================================================
// Types
// ============================================================

interface VolatilityRow {
  commodity?: string;
  namaDisplay?: string;
  nama?: string;
  kode?: string;
  cv?: number;
  volatility?: number;
  trend?: "up" | "down" | "stable";
}

interface PriceGapRow {
  commodity: string;
  highest: number;
  lowest: number;
  gap: number;
  gapPct: number;
  highRegion: string;
  lowRegion: string;
}

type ComparisonRow = Record<string, string | number | null> & {
  region: string;
  kode?: string;
};

// ============================================================
// Helpers
// ============================================================

function formatCurrency(val: number | null | undefined): string {
  if (val === null || val === undefined) return "—";
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(val);
}

function cvBucket(cv: number): "critical" | "high" | "low" {
  if (cv > 15) return "critical";
  if (cv > 8) return "high";
  return "low";
}

function cvColor(cv: number): string {
  const b = cvBucket(cv);
  return b === "critical"
    ? "hsl(var(--risk-critical))"
    : b === "high"
      ? "hsl(var(--risk-high))"
      : "hsl(var(--risk-low))";
}

function gapColor(pct: number): string {
  if (pct > 50) return "text-risk-critical";
  if (pct > 25) return "text-risk-high";
  return "text-risk-low";
}

// ============================================================
// Sub-components
// ============================================================

function SummaryCard({
  label,
  value,
  detail,
  Icon,
  tone,
  loading,
}: {
  label: string;
  value: string;
  detail?: string;
  Icon: typeof TrendingUp;
  tone: "critical" | "high" | "low";
  loading?: boolean;
}) {
  const toneClass =
    tone === "critical"
      ? "text-risk-critical"
      : tone === "high"
        ? "text-risk-high"
        : "text-risk-low";
  const bgClass =
    tone === "critical"
      ? "bg-risk-critical/5 border-risk-critical/30"
      : tone === "high"
        ? "bg-risk-high/5 border-risk-high/30"
        : "bg-risk-low/5 border-risk-low/30";
  return (
    <div className={`rounded-md border p-4 ${bgClass}`}>
      <div className={`flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide ${toneClass}`}>
        <Icon className="h-3 w-3" />
        {label}
      </div>
      {loading ? (
        <>
          <div className="mt-2 h-5 w-24 bg-muted rounded animate-pulse" />
          <div className="mt-1.5 h-3 w-20 bg-muted rounded animate-pulse" />
        </>
      ) : (
        <>
          <p className="mt-1.5 text-base font-semibold text-foreground truncate">{value}</p>
          {detail && (
            <p className={`text-[11px] mt-0.5 ${toneClass}`}>{detail}</p>
          )}
        </>
      )}
    </div>
  );
}

function VolatilityTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: { trend?: string; kode?: string } }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const cv = payload[0].value;
  const bucket = cvBucket(cv);
  const labelText = bucket === "critical" ? "Sangat Volatil" : bucket === "high" ? "Volatil" : "Stabil";
  return (
    <div className="rounded-md border bg-card px-3 py-2 shadow-sm">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold tabular-nums">CV {cv.toFixed(2)}%</p>
      <p className="text-[10px]" style={{ color: cvColor(cv) }}>
        {labelText}
      </p>
    </div>
  );
}

function VolatilityChart({ rows, loading }: { rows: VolatilityRow[]; loading: boolean }) {
  if (loading) {
    return <div className="h-72 bg-muted/30 rounded animate-pulse" />;
  }
  const data = rows
    .map((r) => ({
      commodity: r.commodity || r.namaDisplay || r.nama || "—",
      cv: r.cv ?? r.volatility ?? 0,
      kode: r.kode,
      trend: r.trend,
    }))
    .filter((r) => r.cv > 0);

  if (!data.length) {
    return (
      <div className="h-72 flex items-center justify-center border border-dashed rounded text-xs text-muted-foreground">
        Belum ada data volatilitas. Pastikan harga harian sudah ter-ingest minimal 5 hari.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(240, data.length * 32)}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="hsl(var(--border))" horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(v) => `${v}%`}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          tickLine={false}
          axisLine={{ stroke: "hsl(var(--border))" }}
        />
        <YAxis
          type="category"
          dataKey="commodity"
          tick={{ fontSize: 11, fill: "hsl(var(--foreground))" }}
          tickLine={false}
          axisLine={false}
          width={100}
        />
        <Tooltip
          content={<VolatilityTooltip />}
          cursor={{ fill: "hsl(var(--accent))", opacity: 0.4 }}
        />
        <Bar dataKey="cv" radius={[0, 3, 3, 0]} maxBarSize={20}>
          {data.map((entry, i) => (
            <Cell key={i} fill={cvColor(entry.cv)} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function PriceGapTable({ rows, loading }: { rows: PriceGapRow[]; loading: boolean }) {
  type SortKey = "gapPct" | "gap" | "commodity";
  const [sortKey, setSortKey] = useState<SortKey>("gapPct");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    const copy = [...rows];
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
  }, [rows, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir(key === "commodity" ? "asc" : "desc");
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
      <th className={`p-2 font-medium text-muted-foreground text-[11px] uppercase tracking-wide ${align === "right" ? "text-right" : "text-left"}`}>
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

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-8 bg-muted/40 rounded animate-pulse" />
        ))}
      </div>
    );
  }
  if (!rows.length) {
    return (
      <div className="py-10 text-center border border-dashed rounded">
        <p className="text-sm text-muted-foreground font-medium">Belum ada data price gap.</p>
        <p className="text-[11px] text-muted-foreground/80 mt-1">
          Diperlukan harga komoditas di minimal 2 wilayah berbeda.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-xs">
        <thead className="bg-muted/40 border-b">
          <tr>
            <SortHeader label="Komoditas" sortKeyName="commodity" />
            <th className="p-2 font-medium text-muted-foreground text-[11px] uppercase tracking-wide text-right">Terendah</th>
            <th className="p-2 font-medium text-muted-foreground text-[11px] uppercase tracking-wide">Wilayah</th>
            <th className="p-2 font-medium text-muted-foreground text-[11px] uppercase tracking-wide text-right">Tertinggi</th>
            <th className="p-2 font-medium text-muted-foreground text-[11px] uppercase tracking-wide">Wilayah</th>
            <SortHeader label="Gap" sortKeyName="gap" align="right" />
            <SortHeader label="Gap %" sortKeyName="gapPct" align="right" />
          </tr>
        </thead>
        <tbody>
          {sorted.map((item, i) => (
            <tr key={`${item.commodity}-${i}`} className="border-b last:border-0 hover:bg-accent/40 transition-colors">
              <td className="p-2 font-medium text-foreground">{item.commodity}</td>
              <td className="p-2 text-right font-mono text-risk-low tabular-nums">
                {formatCurrency(item.lowest)}
              </td>
              <td className="p-2 text-muted-foreground text-[11px]">{item.lowRegion}</td>
              <td className="p-2 text-right font-mono text-risk-critical tabular-nums">
                {formatCurrency(item.highest)}
              </td>
              <td className="p-2 text-muted-foreground text-[11px]">{item.highRegion}</td>
              <td className="p-2 text-right font-mono tabular-nums">{formatCurrency(item.gap)}</td>
              <td className="p-2 text-right">
                <span className={`font-bold tabular-nums ${gapColor(item.gapPct)}`}>
                  {item.gapPct.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ComparisonTable({
  rows,
  loading,
}: {
  rows: ComparisonRow[];
  loading: boolean;
}) {
  const [search, setSearch] = useState("");
  // Columns derive from MVP commodities + show only those that have ≥1 value
  const columns = useMemo(() => {
    return MVP_COMMODITIES.slice(0, 6).filter((c) => rows.some((r) => r[c.kode] !== null && r[c.kode] !== undefined));
  }, [rows]);

  const filteredRows = useMemo(() => {
    if (!search.trim()) return rows;
    const q = search.toLowerCase();
    return rows.filter((r) => r.region.toLowerCase().includes(q));
  }, [rows, search]);

  // Per-column min/max for cheapest/most-expensive highlight
  const stats = useMemo(() => {
    const result: Record<string, { min: number; max: number }> = {};
    for (const c of columns) {
      const values = rows
        .map((r) => r[c.kode])
        .filter((v): v is number => typeof v === "number");
      if (values.length) {
        result[c.kode] = { min: Math.min(...values), max: Math.max(...values) };
      }
    }
    return result;
  }, [rows, columns]);

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-7 bg-muted/40 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (!rows.length) {
    return (
      <div className="py-10 text-center border border-dashed rounded">
        <p className="text-sm text-muted-foreground font-medium">
          Belum ada data perbandingan harga.
        </p>
        <p className="text-[11px] text-muted-foreground/80 mt-1">
          Pastikan harga harian per provinsi sudah ter-ingest.
        </p>
      </div>
    );
  }

  if (!columns.length) {
    return (
      <div className="py-10 text-center border border-dashed rounded">
        <p className="text-sm text-muted-foreground font-medium">
          Belum ada komoditas dengan harga tersedia.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="relative max-w-xs">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Cari wilayah…"
          className="w-full h-8 pl-8 pr-3 text-xs bg-card border rounded-md placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-xs">
          <thead className="bg-muted/40 border-b sticky top-0">
            <tr>
              <th className="p-2 font-medium text-muted-foreground text-[11px] uppercase tracking-wide text-left sticky left-0 bg-muted/40">
                Wilayah
              </th>
              {columns.map((c) => (
                <th
                  key={c.kode}
                  className="p-2 font-medium text-muted-foreground text-[11px] uppercase tracking-wide text-right whitespace-nowrap"
                >
                  {c.display}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, i) => (
              <tr key={`${row.region}-${i}`} className="border-b last:border-0 hover:bg-accent/40">
                <td className="p-2 font-medium text-foreground sticky left-0 bg-card hover:bg-accent/40">
                  {row.region}
                </td>
                {columns.map((c) => {
                  const value = row[c.kode];
                  const isNum = typeof value === "number";
                  const stat = stats[c.kode];
                  const isMin = isNum && stat && value === stat.min;
                  const isMax = isNum && stat && value === stat.max;
                  return (
                    <td
                      key={c.kode}
                      className={`p-2 text-right font-mono tabular-nums whitespace-nowrap ${
                        isMin
                          ? "text-risk-low font-semibold"
                          : isMax
                            ? "text-risk-critical font-semibold"
                            : "text-foreground"
                      }`}
                    >
                      {isNum ? value.toLocaleString("id-ID") : "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded bg-risk-low" />
          Termurah per kolom
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded bg-risk-critical" />
          Termahal per kolom
        </span>
      </div>
    </div>
  );
}

// ============================================================
// Page
// ============================================================

export default function IntelligencePage() {
  const {
    data: comparisonData,
    isLoading: comparisonLoading,
    refetch: refetchComparison,
    dataUpdatedAt: comparisonUpdatedAt,
    isFetching: comparisonFetching,
  } = useCrossRegionComparison();
  const {
    data: volatilityData,
    isLoading: volatilityLoading,
    refetch: refetchVolatility,
    isFetching: volatilityFetching,
  } = useVolatilityRanking();
  const {
    data: priceGapData,
    isLoading: priceGapLoading,
    refetch: refetchPriceGap,
    isFetching: priceGapFetching,
  } = usePriceGap();

  const comparison = ((comparisonData as { data?: ComparisonRow[] })?.data ?? []) as ComparisonRow[];
  const volatility = ((volatilityData as { data?: VolatilityRow[] })?.data ?? []) as VolatilityRow[];
  const priceGaps = ((priceGapData as { data?: PriceGapRow[] })?.data ?? []) as PriceGapRow[];

  // Summary: most volatile, biggest gap, most stable
  const mostVolatile = useMemo(() => {
    if (!volatility.length) return null;
    return [...volatility].sort((a, b) => (b.cv ?? 0) - (a.cv ?? 0))[0];
  }, [volatility]);
  const mostStable = useMemo(() => {
    if (!volatility.length) return null;
    return [...volatility].sort((a, b) => (a.cv ?? Infinity) - (b.cv ?? Infinity))[0];
  }, [volatility]);
  const biggestGap = useMemo(() => {
    if (!priceGaps.length) return null;
    return [...priceGaps].sort((a, b) => b.gapPct - a.gapPct)[0];
  }, [priceGaps]);

  const lastUpdated = comparisonUpdatedAt
    ? new Date(comparisonUpdatedAt).toLocaleTimeString("id-ID", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  const refetchAll = () => {
    refetchComparison();
    refetchVolatility();
    refetchPriceGap();
  };
  const anyFetching = comparisonFetching || volatilityFetching || priceGapFetching;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-lg font-semibold tracking-tight flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-primary" />
            Price Intelligence
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Analisis volatilitas komoditas, gap harga antar wilayah, dan perbandingan lintas provinsi.
          </p>
        </div>
        <button
          type="button"
          onClick={refetchAll}
          disabled={anyFetching}
          className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground disabled:opacity-50 mt-1"
        >
          <RefreshCw className={`h-3 w-3 ${anyFetching ? "animate-spin" : ""}`} />
          {lastUpdated ? `Diperbarui ${lastUpdated}` : "Perbarui"}
        </button>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <SummaryCard
          label="Paling Volatil"
          Icon={TrendingUp}
          tone="critical"
          loading={volatilityLoading}
          value={mostVolatile?.commodity || mostVolatile?.namaDisplay || "—"}
          detail={mostVolatile ? `CV ${(mostVolatile.cv ?? 0).toFixed(2)}%` : "Belum ada data"}
        />
        <SummaryCard
          label="Gap Terbesar"
          Icon={ArrowUpDown}
          tone="high"
          loading={priceGapLoading}
          value={biggestGap?.commodity || "—"}
          detail={
            biggestGap
              ? `${biggestGap.gapPct.toFixed(1)}% · ${biggestGap.lowRegion} → ${biggestGap.highRegion}`
              : "Belum ada data"
          }
        />
        <SummaryCard
          label="Paling Stabil"
          Icon={TrendingDown}
          tone="low"
          loading={volatilityLoading}
          value={mostStable?.commodity || mostStable?.namaDisplay || "—"}
          detail={mostStable ? `CV ${(mostStable.cv ?? 0).toFixed(2)}%` : "Belum ada data"}
        />
      </div>

      {/* Volatility */}
      <section className="bg-card rounded-md border p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <h2 className="text-sm font-semibold flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-primary" />
              Volatilitas Komoditas
            </h2>
            <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-1">
              <Info className="h-3 w-3" />
              Coefficient of Variation 30 hari — semakin tinggi semakin tidak stabil
            </p>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground shrink-0">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded bg-risk-low" />
              &lt;8% Stabil
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded bg-risk-high" />
              8–15% Volatil
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded bg-risk-critical" />
              &gt;15% Sangat Volatil
            </span>
          </div>
        </div>
        <VolatilityChart rows={volatility} loading={volatilityLoading} />
      </section>

      {/* Price Gap */}
      <section className="bg-card rounded-md border p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <h2 className="text-sm font-semibold flex items-center gap-2">
              <ArrowUpDown className="h-3.5 w-3.5 text-primary" />
              Price Gap Antar Wilayah
            </h2>
            <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-1">
              <Info className="h-3 w-3" />
              Selisih harga komoditas antara wilayah termurah dan termahal
            </p>
          </div>
        </div>
        <PriceGapTable rows={priceGaps} loading={priceGapLoading} />
      </section>

      {/* Comparison */}
      <section className="bg-card rounded-md border p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <h2 className="text-sm font-semibold flex items-center gap-2">
              <BarChart3 className="h-3.5 w-3.5 text-primary" />
              Perbandingan Harga Antar Wilayah
            </h2>
            <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-1">
              <Info className="h-3 w-3" />
              Harga terkini per komoditas strategis di tiap provinsi
            </p>
          </div>
        </div>
        <ComparisonTable rows={comparison} loading={comparisonLoading} />
      </section>
    </div>
  );
}
