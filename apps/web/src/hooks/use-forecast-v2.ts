"use client";

import { useMutation } from "@tanstack/react-query";

export interface ForecastPointV2 {
  target_date: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
  p10: number;
  p50: number;
  p90: number;
  risk_level: "low" | "medium" | "high" | string;
  confidence_score: number;
  top_drivers: Array<{ name: string; weight: number }>;
  model_contribution: Record<string, number>;
  components: Array<Record<string, unknown>>;
}

export interface ForecastPriceV2Response {
  commodity_id: number;
  region_id: number;
  horizon: number;
  model_version: string;
  points: ForecastPointV2[];
}

export function useForecastPriceV2() {
  return useMutation<
    ForecastPriceV2Response,
    Error,
    { commodity_id: number; region_id: number; horizon: number }
  >({
    mutationFn: async (body) => {
      const res = await fetch("/api/forecast/price", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error("Failed to get forecast");
      return res.json();
    },
  });
}

export interface InflationForecastPoint {
  target_date: string;
  horizon_months: number;
  yhat: number;
  p10: number;
  p50: number;
  p90: number;
  risk_level: string;
  confidence_score: number;
  top_drivers: Array<{ name: string; weight: number }>;
  model_contribution: Record<string, number>;
  components: Array<Record<string, unknown>>;
}

export interface InflationForecastResponse {
  region_id: number;
  horizons: number[];
  model_version: string;
  points: InflationForecastPoint[];
}

export function useForecastInflation() {
  return useMutation<InflationForecastResponse, Error, { region_id: number; horizons: number[] }>({
    mutationFn: async (body) => {
      const res = await fetch("/api/forecast/inflation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error("Failed to forecast inflation");
      return res.json();
    },
  });
}
