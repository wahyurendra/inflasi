"use client";

import Link from "next/link";
import { AnalystHome } from "./analyst-home";
import { useActiveModels } from "@/hooks/use-admin-models";
import { useReportStats } from "@/hooks/use-reports";
import { useQuery } from "@tanstack/react-query";
import { Database, FileCheck2, ServerCog } from "lucide-react";

function useDbStats() {
  return useQuery<Record<string, unknown>>({
    queryKey: ["health", "db-stats"],
    queryFn: async () => {
      const res = await fetch("/api/health");
      if (!res.ok) throw new Error("Failed to fetch health");
      return res.json();
    },
    refetchInterval: 60_000,
  });
}

export function AdminHome() {
  const { data: activeModels } = useActiveModels();
  const { data: reportStats } = useReportStats();
  const { data: health } = useDbStats();

  const dbConnected = ((health?.database as { connected?: boolean })?.connected) ?? false;
  const totalReports = (reportStats as { total?: number })?.total ?? 0;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Link
          href="/admin/models"
          className="bg-card rounded-md border p-4 hover:border-primary transition-colors"
        >
          <div className="flex items-center gap-2 text-muted-foreground text-[11px]">
            <Database className="h-3.5 w-3.5 text-primary" />
            Model Aktif
          </div>
          <p className="text-2xl font-semibold mt-1">{activeModels?.length ?? 0}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            slot (model × target × horizon)
          </p>
        </Link>
        <Link
          href="/admin"
          className="bg-card rounded-md border p-4 hover:border-primary transition-colors"
        >
          <div className="flex items-center gap-2 text-muted-foreground text-[11px]">
            <FileCheck2 className="h-3.5 w-3.5 text-primary" />
            Total Laporan
          </div>
          <p className="text-2xl font-semibold mt-1">{totalReports}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            sejak sistem berjalan
          </p>
        </Link>
        <div className="bg-card rounded-md border p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-[11px]">
            <ServerCog className="h-3.5 w-3.5 text-primary" />
            Sistem
          </div>
          <p className={`text-2xl font-semibold mt-1 ${dbConnected ? "text-risk-low" : "text-risk-critical"}`}>
            {dbConnected ? "OK" : "Degraded"}
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            Database & analytics
          </p>
        </div>
      </div>

      <AnalystHome />
    </div>
  );
}
