"use client";

import { useQuery } from "@tanstack/react-query";

interface AlertData {
  id: number;
  tanggal: string;
  alertType: string;
  severity: "info" | "warning" | "critical";
  judul: string;
  deskripsi: string;
  nilaiAktual: number | null;
  nilaiThreshold: number | null;
  isActive: boolean;
  region: { kode: string; nama: string };
  commodity: { kode: string; nama: string };
}

export function useAlerts(active = true, severity?: string, limit = 20) {
  return useQuery<{ data: AlertData[]; count: number }>({
    queryKey: ["alerts", active, severity, limit],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("active", String(active));
      if (severity) params.set("severity", severity);
      params.set("limit", String(limit));
      const res = await fetch(`/api/alerts?${params}`);
      if (!res.ok) throw new Error("Failed to fetch alerts");
      return res.json();
    },
  });
}
