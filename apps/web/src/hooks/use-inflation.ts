"use client";

import { useQuery } from "@tanstack/react-query";

interface HeadlineData {
  inflasi: {
    mtm: number;
    ytd: number;
    yoy: number;
    ihk: number;
    periode: string;
  };
  source: string;
}

export function useHeadlineInflation() {
  return useQuery<HeadlineData>({
    queryKey: ["inflation", "headline"],
    queryFn: async () => {
      const res = await fetch("/api/inflation/headline");
      if (!res.ok) throw new Error("Failed to fetch headline");
      return res.json();
    },
  });
}

export interface InflationSeriesPoint {
  periode: string;
  mtm: number | null;
  ytd: number | null;
  yoy: number | null;
  ihk: number | null;
}

export function useInflationSeries(months = 12) {
  return useQuery<{ data: InflationSeriesPoint[] }>({
    queryKey: ["inflation", "series", months],
    queryFn: async () => {
      const res = await fetch(`/api/inflation/series?months=${months}`);
      if (!res.ok) throw new Error("Failed to fetch inflation series");
      return res.json();
    },
    staleTime: 10 * 60 * 1000,
  });
}
