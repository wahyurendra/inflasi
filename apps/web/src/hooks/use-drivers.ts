import { useQuery } from "@tanstack/react-query";

interface Driver {
  name: string;
  contribution_pct: number;
  magnitude: number;
  direction: "naik" | "turun" | "neutral";
  detail: string;
}

interface DriverResponse {
  commodity: string;
  tanggal: string;
  drivers: Driver[];
}

export function useDrivers(commodity?: string, region: string = "00") {
  return useQuery<DriverResponse>({
    queryKey: ["drivers", commodity, region],
    queryFn: async () => {
      const params = new URLSearchParams({
        commodity: commodity || "",
        region,
      });
      const res = await fetch(`/api/drivers?${params}`);
      if (!res.ok) throw new Error("Failed to fetch drivers");
      return res.json();
    },
    enabled: !!commodity,
    staleTime: 5 * 60 * 1000,
  });
}
