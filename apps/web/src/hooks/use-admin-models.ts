"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export interface ModelRegistryEntry {
  id: number;
  model_type: string;
  target_type: string;
  horizon: number;
  version: string;
  is_active: boolean;
  trained_at: string;
  metrics: Record<string, number> | null;
}

export function useAdminModels(filters?: {
  modelType?: string;
  targetType?: string;
  horizon?: number;
  activeOnly?: boolean;
}) {
  return useQuery<ModelRegistryEntry[]>({
    queryKey: ["admin", "models", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.modelType) params.set("model_type", filters.modelType);
      if (filters?.targetType) params.set("target_type", filters.targetType);
      if (filters?.horizon) params.set("horizon", String(filters.horizon));
      if (filters?.activeOnly !== undefined) params.set("active_only", String(filters.activeOnly));
      const qs = params.toString();
      const res = await fetch(`/api/admin/models${qs ? `?${qs}` : ""}`);
      if (!res.ok) throw new Error("Failed to fetch models");
      const json = await res.json();
      return Array.isArray(json) ? json : (json.data ?? []);
    },
  });
}

export function useActiveModels() {
  return useQuery<ModelRegistryEntry[]>({
    queryKey: ["admin", "models", "active"],
    queryFn: async () => {
      const res = await fetch("/api/admin/models/active");
      if (!res.ok) throw new Error("Failed to fetch active models");
      const json = await res.json();
      return Array.isArray(json) ? json : (json.data ?? []);
    },
  });
}

export function usePromoteModel() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: async (modelId) => {
      const res = await fetch(`/api/admin/models/${modelId}/promote`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to promote model");
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "models"] });
    },
  });
}
