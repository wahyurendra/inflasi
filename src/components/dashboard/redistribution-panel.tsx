"use client";

import { ArrowRight, Truck } from "lucide-react";

interface Recommendation {
  commodity: string;
  from_region: string;
  to_region: string;
  from_harga: number;
  to_harga: number;
  price_gap: number;
  distance_km: number;
  estimated_tonnage: number;
  urgency: "tinggi" | "sedang";
}

interface RedistributionPanelProps {
  recommendations: Recommendation[];
}

function formatRupiah(value: number): string {
  return `Rp ${value.toLocaleString("id-ID")}`;
}

const urgencyColors = {
  tinggi: "bg-red-100 text-red-700",
  sedang: "bg-orange-100 text-orange-700",
};

export function RedistributionPanel({ recommendations }: RedistributionPanelProps) {
  if (!recommendations?.length) {
    return (
      <div className="bg-white rounded-xl border p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">
          Rekomendasi Redistribusi
        </h3>
        <p className="text-sm text-gray-400">Tidak ada rekomendasi saat ini</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="px-5 py-4 border-b flex items-center gap-2">
        <Truck className="h-4 w-4 text-blue-600" />
        <h3 className="text-sm font-semibold text-gray-900">
          Rekomendasi Redistribusi Pangan
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Komoditas
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Dari → Ke
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Gap Harga
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Est. Tonase
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Jarak
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Urgensi
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {recommendations.map((r, idx) => (
              <tr key={idx} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {r.commodity}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 text-sm">
                    <span className="text-green-700 font-medium">{r.from_region}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-gray-400" />
                    <span className="text-red-700 font-medium">{r.to_region}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-0.5">
                    <span>{formatRupiah(r.from_harga)}</span>
                    <ArrowRight className="h-2.5 w-2.5" />
                    <span>{formatRupiah(r.to_harga)}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm font-semibold text-orange-600">
                    {formatRupiah(r.price_gap)}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {r.estimated_tonnage} ton
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {r.distance_km.toLocaleString("id-ID")} km
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`text-xs font-medium px-2 py-1 rounded-full ${urgencyColors[r.urgency]}`}
                  >
                    {r.urgency}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
