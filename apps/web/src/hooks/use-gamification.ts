"use client";

import { useQuery } from "@tanstack/react-query";

export function useUserPoints() {
  return useQuery({
    queryKey: ["gamification", "user-points"],
    queryFn: async () => {
      const res = await fetch("/api/gamification/user-points");
      if (!res.ok) throw new Error("Failed to fetch points");
      return res.json();
    },
  });
}

export function useUserBadges() {
  return useQuery({
    queryKey: ["gamification", "user-badges"],
    queryFn: async () => {
      const res = await fetch("/api/gamification/user-badges");
      if (!res.ok) throw new Error("Failed to fetch badges");
      return res.json();
    },
  });
}
