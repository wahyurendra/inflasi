"use client";

import { useQuery } from "@tanstack/react-query";

export interface ModelPerformanceRow {
  model_version: string;
  horizon: number;
  mae: number;
  mape: number;
  coverage_p10_p90: number;
  n_samples: number;
}

export function useModelPerformance(windowDays = 30, targetType: "price" | "inflation" = "price") {
  return useQuery<{ data: ModelPerformanceRow[] }>({
    queryKey: ["model-performance", windowDays, targetType],
    queryFn: async () => {
      const res = await fetch(
        `/api/analytics/model-performance?window_days=${windowDays}&target_type=${targetType}`,
      );
      if (!res.ok) throw new Error("Failed to fetch model performance");
      const json = await res.json();
      const data = Array.isArray(json) ? json : (json.data ?? []);
      return { data };
    },
    staleTime: 10 * 60 * 1000,
  });
}
