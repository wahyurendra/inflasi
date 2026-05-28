"use client";

import { useState } from "react";
import Link from "next/link";
import { useMyReports } from "@/hooks/use-reports";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PlusCircle, ChevronLeft, ChevronRight } from "lucide-react";

const statusBadge: Record<string, { label: string; variant: "success" | "warning" | "danger" | "info" }> = {
  PENDING: { label: "Menunggu", variant: "warning" },
  APPROVED: { label: "Disetujui", variant: "success" },
  REJECTED: { label: "Ditolak", variant: "danger" },
  FLAGGED: { label: "Ditandai", variant: "info" },
};

export default function LaporanSayaPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useMyReports(page);

  const reports = data?.data || [];
  const totalPages = data?.totalPages || 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-foreground">Laporan Saya</h1>
          <p className="text-sm text-muted-foreground">
            Riwayat laporan harga yang Anda kirim
          </p>
        </div>
        <Link href="/lapor">
          <Button size="sm">
            <PlusCircle className="h-4 w-4 mr-2" />
            Lapor Harga Baru
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Memuat...</div>
      ) : reports.length === 0 ? (
        <div className="text-center py-12 bg-card rounded-xl border">
          <p className="text-muted-foreground mb-4">
            Anda belum memiliki laporan harga
          </p>
          <Link href="/lapor">
            <Button>
              <PlusCircle className="h-4 w-4 mr-2" />
              Buat Laporan Pertama
            </Button>
          </Link>
        </div>
      ) : (
        <>
          <div className="bg-card rounded-xl border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-3 font-medium text-muted-foreground">Tanggal</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Komoditas</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Pasar</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Harga</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Wilayah</th>
                    <th className="text-center p-3 font-medium text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((report: Record<string, unknown>) => {
                    const commodity = report.commodity as Record<string, string>;
                    const region = report.region as Record<string, string>;
                    const status = statusBadge[report.status as string] || statusBadge.PENDING;
                    return (
                      <tr key={report.id as string} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                        <td className="p-3">
                          {new Date(report.tanggal as string).toLocaleDateString("id-ID", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                          })}
                        </td>
                        <td className="p-3 font-medium">{commodity?.namaDisplay}</td>
                        <td className="p-3">{report.namaPasar as string}</td>
                        <td className="p-3 text-right font-mono">
                          Rp {Number(report.harga).toLocaleString("id-ID")}
                        </td>
                        <td className="p-3">{region?.namaProvinsi}</td>
                        <td className="p-3 text-center">
                          <Badge variant={status.variant}>{status.label}</Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground">
                Halaman {page} dari {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
