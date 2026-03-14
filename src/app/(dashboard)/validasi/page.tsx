"use client";

import { useState } from "react";
import { useAllReports, useUpdateReportStatus } from "@/hooks/use-reports";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { CheckCircle, XCircle, Flag, Eye } from "lucide-react";

export default function ValidasiPage() {
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const [page] = useState(1);
  const { data, isLoading } = useAllReports({ status: statusFilter, page });
  const updateStatus = useUpdateReportStatus();
  const { toast } = useToast();

  const [rejectDialog, setRejectDialog] = useState<string | null>(null);
  const [rejectionNote, setRejectionNote] = useState("");
  const [detailDialog, setDetailDialog] = useState<Record<string, unknown> | null>(null);

  const reports = data?.data || [];

  const handleApprove = async (id: string) => {
    try {
      await updateStatus.mutateAsync({ id, status: "APPROVED" });
      toast({ title: "Laporan disetujui", variant: "success" });
    } catch {
      toast({ title: "Gagal menyetujui", variant: "destructive" });
    }
  };

  const handleReject = async () => {
    if (!rejectDialog) return;
    try {
      await updateStatus.mutateAsync({
        id: rejectDialog,
        status: "REJECTED",
        rejectionNote,
      });
      toast({ title: "Laporan ditolak" });
      setRejectDialog(null);
      setRejectionNote("");
    } catch {
      toast({ title: "Gagal menolak", variant: "destructive" });
    }
  };

  const handleFlag = async (id: string) => {
    try {
      await updateStatus.mutateAsync({ id, status: "FLAGGED" });
      toast({ title: "Laporan ditandai untuk review" });
    } catch {
      toast({ title: "Gagal menandai", variant: "destructive" });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground">Validasi Laporan</h1>
        <p className="text-sm text-muted-foreground">
          Tinjau dan validasi laporan harga dari masyarakat
        </p>
      </div>

      <Tabs value={statusFilter} onValueChange={setStatusFilter}>
        <TabsList>
          <TabsTrigger value="PENDING">Menunggu</TabsTrigger>
          <TabsTrigger value="FLAGGED">Ditandai</TabsTrigger>
          <TabsTrigger value="APPROVED">Disetujui</TabsTrigger>
          <TabsTrigger value="REJECTED">Ditolak</TabsTrigger>
        </TabsList>

        <TabsContent value={statusFilter} className="mt-4">
          {isLoading ? (
            <div className="text-center py-12 text-muted-foreground">Memuat...</div>
          ) : reports.length === 0 ? (
            <div className="text-center py-12 bg-card rounded-xl border">
              <p className="text-muted-foreground">Tidak ada laporan dengan status ini</p>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((report: Record<string, unknown>) => {
                const commodity = report.commodity as Record<string, string>;
                const region = report.region as Record<string, string>;
                const user = report.user as Record<string, string>;
                const confidence = Number(report.confidenceScore || 0);

                return (
                  <div
                    key={report.id as string}
                    className="bg-card rounded-xl border p-4 space-y-3"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm">
                            {commodity?.namaDisplay}
                          </span>
                          <Badge variant="outline" className="text-xs">
                            {report.satuan as string}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          oleh {user?.name} &middot;{" "}
                          {new Date(report.tanggal as string).toLocaleDateString("id-ID")}
                        </p>
                      </div>
                      <span className="text-lg font-bold text-foreground">
                        Rp {Number(report.harga).toLocaleString("id-ID")}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                      <span>Pasar: {report.namaPasar as string}</span>
                      <span>Wilayah: {region?.namaProvinsi}</span>
                      {confidence > 0 && (
                        <span>
                          Skor kepercayaan:{" "}
                          <span
                            className={
                              confidence >= 70
                                ? "text-green-600"
                                : confidence >= 40
                                ? "text-orange-600"
                                : "text-red-600"
                            }
                          >
                            {confidence}%
                          </span>
                        </span>
                      )}
                    </div>

                    {statusFilter === "PENDING" || statusFilter === "FLAGGED" ? (
                      <div className="flex items-center gap-2 pt-1">
                        <Button
                          size="sm"
                          onClick={() => handleApprove(report.id as string)}
                          disabled={updateStatus.isPending}
                        >
                          <CheckCircle className="h-3.5 w-3.5 mr-1" />
                          Setujui
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => setRejectDialog(report.id as string)}
                          disabled={updateStatus.isPending}
                        >
                          <XCircle className="h-3.5 w-3.5 mr-1" />
                          Tolak
                        </Button>
                        {statusFilter !== "FLAGGED" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleFlag(report.id as string)}
                            disabled={updateStatus.isPending}
                          >
                            <Flag className="h-3.5 w-3.5 mr-1" />
                            Tandai
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setDetailDialog(report)}
                        >
                          <Eye className="h-3.5 w-3.5 mr-1" />
                          Detail
                        </Button>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Reject Dialog */}
      <Dialog open={!!rejectDialog} onOpenChange={() => setRejectDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Tolak Laporan</DialogTitle>
            <DialogDescription>
              Berikan alasan penolakan untuk reporter
            </DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="Alasan penolakan..."
            value={rejectionNote}
            onChange={(e) => setRejectionNote(e.target.value)}
            rows={3}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectDialog(null)}>
              Batal
            </Button>
            <Button variant="destructive" onClick={handleReject}>
              Tolak Laporan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={!!detailDialog} onOpenChange={() => setDetailDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Detail Laporan</DialogTitle>
          </DialogHeader>
          {detailDialog && (
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-muted-foreground">Komoditas:</span>{" "}
                  {(detailDialog.commodity as Record<string, string>)?.namaDisplay}
                </div>
                <div>
                  <span className="text-muted-foreground">Harga:</span>{" "}
                  Rp {Number(detailDialog.harga).toLocaleString("id-ID")}/{detailDialog.satuan as string}
                </div>
                <div>
                  <span className="text-muted-foreground">Pasar:</span>{" "}
                  {detailDialog.namaPasar as string}
                </div>
                <div>
                  <span className="text-muted-foreground">Wilayah:</span>{" "}
                  {(detailDialog.region as Record<string, string>)?.namaProvinsi}
                </div>
                <div>
                  <span className="text-muted-foreground">Kota:</span>{" "}
                  {(detailDialog.kota as string) || "-"}
                </div>
                <div>
                  <span className="text-muted-foreground">Tanggal:</span>{" "}
                  {new Date(detailDialog.tanggal as string).toLocaleDateString("id-ID")}
                </div>
              </div>
              {detailDialog.catatan ? (
                <div>
                  <span className="text-muted-foreground">Catatan:</span>{" "}
                  {String(detailDialog.catatan)}
                </div>
              ) : null}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
