"use client";

import { useMemo, useState, useEffect } from "react";
import {
  Newspaper,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  TrendingDown,
  TrendingUp,
  Minus,
} from "lucide-react";

export interface NewsItem {
  tanggal: string;
  kategori: string;
  judul: string;
  sumber: string;
  url: string | null;
  sentimen: string | null;
  relevansi: number | null;
}

interface NewsIntelligenceProps {
  news: NewsItem[];
  source?: string; // e.g. "GDELT"
  pageSize?: number;
}

const PAGE_SIZE_DEFAULT = 5;

const CATEGORY_LABEL: Record<string, string> = {
  food_supply: "Pangan",
  energy: "Energi",
  geopolitics: "Geopolitik",
  climate: "Iklim",
  agriculture: "Pertanian",
  indonesia: "Indonesia",
};

const CATEGORY_STYLE: Record<string, string> = {
  food_supply: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/30 dark:text-orange-300 dark:border-orange-900",
  energy: "bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-950/30 dark:text-yellow-300 dark:border-yellow-900",
  geopolitics: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900",
  climate: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-300 dark:border-blue-900",
  agriculture: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-900",
  indonesia: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/30 dark:text-purple-300 dark:border-purple-900",
};

const SENTIMENT_STYLE: Record<string, { color: string; label: string; Icon: typeof TrendingDown }> = {
  positive: { color: "text-emerald-600 dark:text-emerald-400", label: "Positif", Icon: TrendingUp },
  negative: { color: "text-red-600 dark:text-red-400", label: "Negatif", Icon: TrendingDown },
  neutral: { color: "text-muted-foreground", label: "Netral", Icon: Minus },
};

function formatDate(date: string): string {
  try {
    return new Date(date).toLocaleDateString("id-ID", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return date;
  }
}

export function NewsIntelligence({
  news,
  source = "GDELT",
  pageSize = PAGE_SIZE_DEFAULT,
}: NewsIntelligenceProps) {
  const [category, setCategory] = useState<string>("all");
  const [page, setPage] = useState(1);

  // Build category list from real data + show counts
  const categories = useMemo(() => {
    const counts = new Map<string, number>();
    for (const n of news) {
      counts.set(n.kategori, (counts.get(n.kategori) ?? 0) + 1);
    }
    const list = Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([key, count]) => ({
        key,
        label: CATEGORY_LABEL[key] || key.replace(/_/g, " "),
        count,
      }));
    return [{ key: "all", label: "Semua", count: news.length }, ...list];
  }, [news]);

  const filtered = useMemo(
    () => (category === "all" ? news : news.filter((n) => n.kategori === category)),
    [news, category]
  );

  useEffect(() => {
    setPage(1);
  }, [category]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  const pageButtons = useMemo(() => {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
      .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
      .reduce<(number | "…")[]>((acc, p, idx, arr) => {
        if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push("…");
        acc.push(p);
        return acc;
      }, []);
  }, [page, totalPages]);

  return (
    <div className="bg-card rounded-md border">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Newspaper className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">News Intelligence</h3>
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
            {source}
          </span>
        </div>
        <span className="text-[11px] text-muted-foreground">
          {filtered.length} artikel
        </span>
      </div>

      {/* Category filter */}
      <div className="px-4 py-2.5 border-b overflow-x-auto">
        <div className="flex items-center gap-1.5 min-w-max">
          {categories.map((c) => (
            <button
              key={c.key}
              type="button"
              onClick={() => setCategory(c.key)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border transition-colors ${
                category === c.key
                  ? "bg-primary text-primary-foreground border-primary shadow-sm"
                  : "bg-card text-muted-foreground border-border hover:text-foreground hover:border-primary/40"
              }`}
            >
              {c.label}
              <span
                className={`text-[10px] font-semibold rounded-full px-1.5 ${
                  category === c.key
                    ? "bg-primary-foreground/20 text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {c.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* News list */}
      <div className="divide-y">
        {paginated.length === 0 ? (
          <div className="p-8 text-center">
            <Newspaper className="h-7 w-7 text-muted-foreground/30 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              Tidak ada berita untuk kategori ini.
            </p>
            {category !== "all" && (
              <button
                type="button"
                onClick={() => setCategory("all")}
                className="mt-2 text-xs text-primary hover:underline"
              >
                Tampilkan semua kategori
              </button>
            )}
          </div>
        ) : (
          paginated.map((n, i) => {
            const catStyle = CATEGORY_STYLE[n.kategori] ?? "bg-muted text-muted-foreground border-border";
            const sentiment = n.sentimen ? SENTIMENT_STYLE[n.sentimen] : null;
            const SentIcon = sentiment?.Icon;
            return (
              <div key={`${n.tanggal}-${i}`} className="px-4 py-3 hover:bg-accent/40 transition-colors">
                <div className="flex items-start gap-3">
                  <span
                    className={`shrink-0 mt-0.5 text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded border ${catStyle}`}
                  >
                    {CATEGORY_LABEL[n.kategori] || n.kategori}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium leading-snug">
                      {n.url ? (
                        <a
                          href={n.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-primary hover:underline inline-flex items-start gap-1"
                        >
                          <span>{n.judul}</span>
                          <ExternalLink className="h-3 w-3 mt-0.5 shrink-0 opacity-60" />
                        </a>
                      ) : (
                        n.judul
                      )}
                    </p>
                    <div className="mt-1 flex items-center gap-x-2 gap-y-0.5 text-[11px] text-muted-foreground flex-wrap">
                      <span className="font-medium">{n.sumber}</span>
                      <span className="text-muted-foreground/40">·</span>
                      <span>{formatDate(n.tanggal)}</span>
                      {sentiment && SentIcon && (
                        <>
                          <span className="text-muted-foreground/40">·</span>
                          <span className={`inline-flex items-center gap-0.5 ${sentiment.color}`}>
                            <SentIcon className="h-2.5 w-2.5" />
                            {sentiment.label}
                          </span>
                        </>
                      )}
                      {typeof n.relevansi === "number" && (
                        <>
                          <span className="text-muted-foreground/40">·</span>
                          <span>Relevansi {(n.relevansi * 100).toFixed(0)}%</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      {filtered.length > pageSize && (
        <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-t bg-muted/30">
          <p className="text-[11px] text-muted-foreground hidden sm:block">
            Halaman <span className="font-semibold text-foreground">{page}</span> /{" "}
            <span className="font-semibold text-foreground">{totalPages}</span>
            <span className="mx-1.5 text-muted-foreground/40">·</span>
            {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, filtered.length)} dari{" "}
            {filtered.length}
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
  );
}
