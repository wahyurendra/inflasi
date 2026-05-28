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
