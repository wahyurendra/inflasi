"use client";

import Link from "next/link";
import { AlertBanner } from "@/components/dashboard/alert-banner";
import { useAlerts } from "@/hooks/use-alerts";
import { useAllReports, useReportStats } from "@/hooks/use-reports";
import { useAuth } from "@/hooks/use-auth";
import { CheckSquare, AlertTriangle, PlusCircle, MapPin } from "lucide-react";

export function OfficerHome() {
  const { user } = useAuth();
  const { data: pending } = useAllReports({ status: "PENDING", limit: 1 });
  const { data: alertData } = useAlerts(true, undefined, 5);
  const { data: stats } = useReportStats();

  const pendingCount = (pending as { total?: number })?.total ?? 0;
  const alerts = (alertData?.data ?? []).map((a) => ({
    id: a.id,
    severity: a.severity,
    judul: a.judul,
  }));
  const approvalRate = (stats as { approvalRate?: number })?.approvalRate ?? 0;

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">
          Beranda Petugas{user?.name ? ` — ${user.name.split(" ")[0]}` : ""}
        </h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Validasi laporan masuk dan pantau alert wilayah Anda.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Link
          href="/validasi"
          className="block bg-card rounded-md border p-4 hover:border-primary transition-colors"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <CheckSquare className="h-3.5 w-3.5 text-primary" />
                Validation Queue
              </p>
              <p className="text-2xl font-semibold mt-1">{pendingCount}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                laporan menunggu review
              </p>
            </div>
            <span className="text-[11px] text-primary">Buka →</span>
          </div>
        </Link>
        <Link
          href="/alerts"
          className="block bg-card rounded-md border p-4 hover:border-primary transition-colors"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 text-risk-high" />
                Alert Aktif
              </p>
              <p className="text-2xl font-semibold mt-1">{alerts.length}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                peringatan harga & supply
              </p>
            </div>
            <span className="text-[11px] text-primary">Buka →</span>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-card rounded-md border p-4">
          <h3 className="text-sm font-semibold mb-3">Ringkasan Validasi</h3>
          <div className="space-y-2 text-xs">
            <Row label="Approved" value={(stats as { approved?: number })?.approved ?? 0} />
            <Row label="Pending" value={(stats as { pending?: number })?.pending ?? 0} />
            <Row label="Flagged" value={(stats as { flagged?: number })?.flagged ?? 0} />
            <Row label="Rejected" value={(stats as { rejected?: number })?.rejected ?? 0} />
            <div className="border-t pt-2 flex items-center justify-between">
              <span className="text-muted-foreground">Approval Rate</span>
              <span className="text-primary font-semibold">
                {(approvalRate * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
        <AlertBanner alerts={alerts} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Link
          href="/lapor"
          className="bg-card rounded-md border p-4 hover:border-primary transition-colors flex items-center gap-3"
        >
          <PlusCircle className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-medium">Lapor Harga</p>
            <p className="text-[11px] text-muted-foreground">Kirim laporan dari lapangan</p>
          </div>
        </Link>
        <Link
          href="/wilayah"
          className="bg-card rounded-md border p-4 hover:border-primary transition-colors flex items-center gap-3"
        >
          <MapPin className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-medium">Peta Wilayah</p>
            <p className="text-[11px] text-muted-foreground">Heatmap tekanan harga</p>
          </div>
        </Link>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground font-medium">{value}</span>
    </div>
  );
}
