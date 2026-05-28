import { useQuery } from "@tanstack/react-query";

interface Recommendation {
  commodity: string;
  from_region: string;
  from_kode: string;
  from_harga: number;
  to_region: string;
  to_kode: string;
  to_harga: number;
  price_gap: number;
  distance_km: number;
  estimated_tonnage: number;
  urgency: "tinggi" | "sedang";
}

export function useRecommendations() {
  return useQuery<Recommendation[]>({
    queryKey: ["recommendations"],
    queryFn: async () => {
      const res = await fetch("/api/recommendations");
      if (!res.ok) throw new Error("Failed to fetch recommendations");
      const data = await res.json();
      return data.recommendations || [];
    },
    staleTime: 10 * 60 * 1000,
  });
}
