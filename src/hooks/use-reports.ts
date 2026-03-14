"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface ReportFilters {
  status?: string;
  commodityId?: number;
  regionId?: number;
  page?: number;
  limit?: number;
}

export function useMyReports(page = 1) {
  return useQuery({
    queryKey: ["my-reports", page],
    queryFn: async () => {
      const res = await fetch(`/api/reports/my?page=${page}`);
      if (!res.ok) throw new Error("Failed to fetch reports");
      return res.json();
    },
  });
}

export function useAllReports(filters: ReportFilters = {}) {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.commodityId) params.set("commodityId", filters.commodityId.toString());
  if (filters.regionId) params.set("regionId", filters.regionId.toString());
  if (filters.page) params.set("page", filters.page.toString());
  if (filters.limit) params.set("limit", filters.limit.toString());

  return useQuery({
    queryKey: ["reports", filters],
    queryFn: async () => {
      const res = await fetch(`/api/reports?${params}`);
      if (!res.ok) throw new Error("Failed to fetch reports");
      return res.json();
    },
  });
}

export function useReportStats() {
  return useQuery({
    queryKey: ["report-stats"],
    queryFn: async () => {
      const res = await fetch("/api/reports/stats");
      if (!res.ok) throw new Error("Failed to fetch stats");
      return res.json();
    },
  });
}

export function useSubmitReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await fetch("/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Gagal mengirim laporan");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-reports"] });
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      queryClient.invalidateQueries({ queryKey: ["report-stats"] });
    },
  });
}

export function useUpdateReportStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      status,
      rejectionNote,
    }: {
      id: string;
      status: string;
      rejectionNote?: string;
    }) => {
      const res = await fetch(`/api/reports/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, rejectionNote }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Gagal memperbarui status");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      queryClient.invalidateQueries({ queryKey: ["report-stats"] });
    },
  });
}
