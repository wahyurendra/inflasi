"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export interface Market {
  id: number;
  region_id: number;
  kode_pasar: string | null;
  nama_pasar: string;
  tipe_pasar: string | null;
  alamat: string | null;
  latitude: number | null;
  longitude: number | null;
  is_active: boolean;
}

export function useMarkets(regionId: number | null, activeOnly = true) {
  return useQuery<Market[]>({
    queryKey: ["markets", regionId, activeOnly],
    queryFn: async () => {
      const res = await fetch(
        `/api/markets?region_id=${regionId}&active_only=${activeOnly}`,
      );
      if (!res.ok) throw new Error("Failed to fetch markets");
      return res.json();
    },
    enabled: regionId != null,
    staleTime: 5 * 60 * 1000,
  });
}

export interface MarketResolveResult {
  match: Market | null;
  score?: number;
  method?: string;
}

export function useResolveMarket() {
  return useMutation<MarketResolveResult, Error, { regionId: number; namaPasar: string }>({
    mutationFn: async ({ regionId, namaPasar }) => {
      const params = new URLSearchParams({
        region_id: String(regionId),
        nama_pasar: namaPasar,
      });
      const res = await fetch(`/api/markets/resolve?${params}`);
      if (!res.ok) throw new Error("Failed to resolve market");
      return res.json();
    },
  });
}

export function useCreateMarket() {
  const qc = useQueryClient();
  return useMutation<Market, Error, Partial<Market> & { region_id: number; nama_pasar: string }>({
    mutationFn: async (body) => {
      const res = await fetch("/api/markets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error("Failed to create market");
      return res.json();
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["markets", variables.region_id] });
    },
  });
}
