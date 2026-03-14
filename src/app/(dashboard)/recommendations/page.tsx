"use client";

import { useRecommendations } from "@/hooks/use-recommendations";
import { RedistributionPanel } from "@/components/dashboard/redistribution-panel";

export default function RecommendationsPage() {
  const { data: recommendations, isLoading } = useRecommendations();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-gray-900">
          Rekomendasi Redistribusi Supply Chain
        </h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Analisis surplus/defisit antar wilayah dan rekomendasi pengiriman
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs text-gray-500 uppercase font-medium">
            Total Rekomendasi
          </p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {isLoading ? "..." : recommendations?.length || 0}
          </p>
        </div>
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs text-gray-500 uppercase font-medium">
            Urgensi Tinggi
          </p>
          <p className="text-2xl font-bold text-red-600 mt-1">
            {isLoading
              ? "..."
              : recommendations?.filter((r) => r.urgency === "tinggi").length || 0}
          </p>
        </div>
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs text-gray-500 uppercase font-medium">
            Est. Total Tonase
          </p>
          <p className="text-2xl font-bold text-blue-600 mt-1">
            {isLoading
              ? "..."
              : `${recommendations?.reduce((sum, r) => sum + r.estimated_tonnage, 0) || 0} ton`}
          </p>
        </div>
      </div>

      {/* Main Table */}
      {isLoading ? (
        <div className="bg-white rounded-xl border p-8 text-center text-gray-400">
          Memuat data rekomendasi...
        </div>
      ) : (
        <RedistributionPanel recommendations={recommendations || []} />
      )}

      {/* Info */}
      <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
        <p className="text-xs text-blue-700">
          Rekomendasi dihasilkan berdasarkan analisis price-spread antar wilayah,
          status stok pangan (Bapanas), dan jarak geografis. Estimasi tonase bersifat
          indikatif dan perlu disesuaikan dengan kapasitas logistik aktual.
        </p>
      </div>
    </div>
  );
}
