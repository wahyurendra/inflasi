"use client";

import { useQuery } from "@tanstack/react-query";

export function useCrossRegionComparison(commodity?: string) {
  return useQuery({
    queryKey: ["intelligence-comparison", commodity],
    queryFn: async () => {
      const params = commodity ? `?commodity=${commodity}` : "";
      const res = await fetch(`/api/intelligence/comparison${params}`);
      if (!res.ok) throw new Error("Failed to fetch comparison");
      return res.json();
    },
  });
}

export function useVolatilityRanking() {
  return useQuery({
    queryKey: ["intelligence-volatility"],
    queryFn: async () => {
      const res = await fetch("/api/intelligence/volatility");
      if (!res.ok) throw new Error("Failed to fetch volatility");
      return res.json();
    },
  });
}

export function usePriceGap() {
  return useQuery({
    queryKey: ["intelligence-price-gap"],
    queryFn: async () => {
      const res = await fetch("/api/intelligence/price-gap");
      if (!res.ok) throw new Error("Failed to fetch price gap");
      return res.json();
    },
  });
}
