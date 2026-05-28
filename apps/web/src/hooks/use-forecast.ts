import { useQuery } from "@tanstack/react-query";

interface ForecastPoint {
  tanggal: string;
  yhat: number;
  yhatLower: number;
  yhatUpper: number;
}

interface ForecastResponse {
  data: ForecastPoint[];
  commodity: string;
  region: string;
  modelVersion: string;
}

export function useForecast(
  commodity?: string,
  region: string = "00",
  horizon: number = 14
) {
  return useQuery<ForecastResponse>({
    queryKey: ["forecast", commodity, region, horizon],
    queryFn: async () => {
      const params = new URLSearchParams({
        commodity: commodity || "CABAI_RAWIT",
        region,
        horizon: String(horizon),
      });
      const res = await fetch(`/api/forecast?${params}`);
      if (!res.ok) throw new Error("Failed to fetch forecast");
      return res.json();
    },
    enabled: !!commodity,
    staleTime: 5 * 60 * 1000,
  });
}
