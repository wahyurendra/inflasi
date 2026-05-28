import { useQuery } from "@tanstack/react-query";

interface RiskScore {
  kodeWilayah: string;
  namaProvinsi: string;
  kodeKomoditas: string;
  namaDisplay: string;
  riskScoreTotal: number;
  riskCategory: "rendah" | "sedang" | "tinggi";
}

export function useRiskScores() {
  return useQuery<RiskScore[]>({
    queryKey: ["risk-scores"],
    queryFn: async () => {
      const res = await fetch("/api/risk-scores");
      if (!res.ok) throw new Error("Failed to fetch risk scores");
      const json = await res.json();
      const items = Array.isArray(json) ? json : json.data || json.scores || [];
      if (!Array.isArray(items)) return [];
      return items.map((s: Record<string, unknown>) => ({
        kodeWilayah: (s.region as { kode?: string })?.kode ?? (s as { kodeWilayah?: string }).kodeWilayah ?? "",
        namaProvinsi: (s.region as { nama?: string })?.nama ?? (s as { namaProvinsi?: string }).namaProvinsi ?? "",
        kodeKomoditas: (s.commodity as { kode?: string })?.kode ?? (s as { kodeKomoditas?: string }).kodeKomoditas ?? "",
        namaDisplay: (s.commodity as { nama?: string })?.nama ?? (s as { namaDisplay?: string }).namaDisplay ?? "",
        riskScoreTotal: Number(s.riskScoreTotal) || 0,
        riskCategory: (s.riskCategory as string) || "rendah",
      })) as RiskScore[];
    },
    staleTime: 5 * 60 * 1000,
  });
}
