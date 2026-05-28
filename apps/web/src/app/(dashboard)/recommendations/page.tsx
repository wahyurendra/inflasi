"use client";

import { useRecommendations } from "@/hooks/use-recommendations";
import { RedistributionPanel } from "@/components/dashboard/redistribution-panel";

export default function RecommendationsPage() {
  const { data: recommendations, isLoading } = useRecommendations();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-foreground">
          Rekomendasi Redistribusi Supply Chain
        </h2>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Analisis surplus/defisit antar wilayah dan rekomendasi pengiriman
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card rounded-xl border p-5">
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Total Rekomendasi
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {isLoading ? "..." : recommendations?.length || 0}
          </p>
        </div>
        <div className="bg-card rounded-xl border p-5">
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Urgensi Tinggi
          </p>
          <p className="mt-1 text-2xl font-bold text-red-600">
            {isLoading
              ? "..."
              : recommendations?.filter((r) => r.urgency === "tinggi").length || 0}
          </p>
        </div>
        <div className="bg-card rounded-xl border p-5">
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Est. Total Tonase
          </p>
          <p className="mt-1 text-2xl font-bold text-blue-600">
            {isLoading
              ? "..."
              : `${recommendations?.reduce((sum, r) => sum + r.estimated_tonnage, 0) || 0} ton`}
          </p>
        </div>
      </div>

      {/* Main Table */}
      {isLoading ? (
        <div className="bg-card rounded-xl border p-8 text-center text-muted-foreground">
          Memuat data rekomendasi...
        </div>
      ) : (
        <RedistributionPanel recommendations={recommendations || []} />
      )}

      {/* Info */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950/30">
        <p className="text-xs text-blue-700 dark:text-blue-300">
          Rekomendasi dihasilkan berdasarkan analisis price-spread antar wilayah,
          status stok pangan (Bapanas), dan jarak geografis. Estimasi tonase bersifat
          indikatif dan perlu disesuaikan dengan kapasitas logistik aktual.
        </p>
      </div>
    </div>
  );
}
