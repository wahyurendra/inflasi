"use client";

import { useQuery } from "@tanstack/react-query";

interface PriceDataPoint {
  tanggal: string;
  harga: number;
  perubahanHarian: number | null;
  perubahanMingguan: number | null;
  perubahanBulanan: number | null;
  commodity: { kode: string; nama: string };
  region: { kode: string; nama: string };
}

export function usePrices(
  commodity?: string,
  region: string = "00",
  days: number = 30
) {
  return useQuery<{ data: PriceDataPoint[]; count: number }>({
    queryKey: ["prices", commodity, region, days],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (commodity) params.set("commodity", commodity);
      params.set("region", region);
      params.set("days", String(days));
      const res = await fetch(`/api/prices/daily?${params}`);
      if (!res.ok) throw new Error("Failed to fetch prices");
      return res.json();
    },
    enabled: !!commodity,
  });
}

export function useCommodityRanking(sort = "weekly_change", limit = 8) {
  return useQuery<{ data: Array<{
    kodeKomoditas: string;
    namaDisplay: string;
    kategori: string;
    satuan: string;
    hargaTerakhir: number | null;
    perubahanHarian: number | null;
    perubahanMingguan: number | null;
    perubahanBulanan: number | null;
  }> }>({
    queryKey: ["commodityRanking", sort, limit],
    queryFn: async () => {
      const res = await fetch(
        `/api/commodities/ranking?sort=${sort}&limit=${limit}`
      );
      if (!res.ok) throw new Error("Failed to fetch ranking");
      return res.json();
    },
  });
}
