"use client";

import { useQuery } from "@tanstack/react-query";

export interface Region {
  id: number;
  kodeWilayah: string;
  namaProvinsi: string;
  namaKabKota: string | null;
  levelWilayah: string;
}

export function useRegions(level?: string) {
  return useQuery<Region[]>({
    queryKey: ["regions", level],
    queryFn: async () => {
      const qs = level ? `?level=${level}` : "";
      const res = await fetch(`/api/regions${qs}`);
      if (!res.ok) throw new Error("Failed to fetch regions");
      const json = await res.json();
      return Array.isArray(json) ? json : (json.data ?? []);
    },
    staleTime: 30 * 60 * 1000,
  });
}

export function useRegionRanking(sort: "pressure" | "risk_score" = "pressure", limit = 10) {
  return useQuery<Array<Record<string, unknown>>>({
    queryKey: ["regions", "ranking", sort, limit],
    queryFn: async () => {
      const res = await fetch(`/api/regions/ranking?sort=${sort}&limit=${limit}`);
      if (!res.ok) throw new Error("Failed to fetch region ranking");
      const json = await res.json();
      return Array.isArray(json) ? json : (json.data ?? []);
    },
  });
}

export function useRegionHeatmap() {
  return useQuery<Array<Record<string, unknown>>>({
    queryKey: ["regions", "heatmap"],
    queryFn: async () => {
      const res = await fetch("/api/regions/heatmap");
      if (!res.ok) throw new Error("Failed to fetch heatmap");
      const json = await res.json();
      return Array.isArray(json) ? json : (json.data ?? []);
    },
  });
}
