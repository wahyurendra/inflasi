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
  tinggi: "bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-300",
  sedang: "bg-orange-100 text-orange-700 dark:bg-orange-950/30 dark:text-orange-300",
};

export function RedistributionPanel({ recommendations }: RedistributionPanelProps) {
  if (!recommendations?.length) {
    return (
      <div className="bg-card rounded-xl border p-5">
        <h3 className="mb-3 text-sm font-semibold text-foreground">
          Rekomendasi Redistribusi
        </h3>
        <p className="text-sm text-muted-foreground">Tidak ada rekomendasi saat ini</p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-xl border overflow-hidden">
      <div className="px-5 py-4 border-b flex items-center gap-2">
        <Truck className="h-4 w-4 text-blue-600" />
        <h3 className="text-sm font-semibold text-foreground">
          Rekomendasi Redistribusi Pangan
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                Komoditas
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                Dari → Ke
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                Gap Harga
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                Est. Tonase
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                Jarak
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                Urgensi
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {recommendations.map((r, idx) => (
              <tr key={idx} className="transition-colors hover:bg-muted/50">
                <td className="px-4 py-3 text-sm font-medium text-foreground">
                  {r.commodity}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 text-sm">
                    <span className="text-green-700 font-medium">{r.from_region}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-red-700 font-medium">{r.to_region}</span>
                  </div>
                  <div className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
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
                <td className="px-4 py-3 text-sm text-muted-foreground">
                  {r.estimated_tonnage} ton
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">
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
