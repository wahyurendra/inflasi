"use client";

import { useQuery } from "@tanstack/react-query";

export function useLeaderboard(period: string = "all", limit: number = 20) {
  return useQuery({
    queryKey: ["leaderboard", period, limit],
    queryFn: async () => {
      const res = await fetch(`/api/leaderboard?period=${period}&limit=${limit}`);
      if (!res.ok) throw new Error("Failed to fetch leaderboard");
      return res.json();
    },
  });
}
