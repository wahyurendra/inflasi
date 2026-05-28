import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

interface RawAlert {
  id: number;
  tanggal: string;
  alert_type: string;
  severity: string;
  judul: string;
  deskripsi: string;
  nilai_aktual: number | null;
  nilai_threshold: number | null;
  nama_provinsi: string;
  kode_wilayah: string;
  nama_display: string;
  kode_komoditas: string;
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const active = searchParams.get("active") !== "false" ? "true" : "false";
  const severity = searchParams.get("severity");
  const limit = searchParams.get("limit") || "20";

  try {
    const params: Record<string, string> = { active, limit };
    if (severity) params.severity = severity;

    const result = await apiClient.get<RawAlert[]>("/alerts/active", params);

    const alerts = (Array.isArray(result) ? result : []).map((a) => ({
      id: a.id,
      tanggal: a.tanggal,
      alertType: a.alert_type,
      severity: a.severity,
      judul: a.judul,
      deskripsi: a.deskripsi,
      nilaiAktual: a.nilai_aktual,
      nilaiThreshold: a.nilai_threshold,
      isActive: true,
      region: { kode: a.kode_wilayah, nama: a.nama_provinsi },
      commodity: { kode: a.kode_komoditas, nama: a.nama_display },
    }));

    return NextResponse.json({ data: alerts, count: alerts.length });
  } catch (error) {
    console.error("Alerts error:", error);
    return NextResponse.json({ data: [], count: 0, error: "Database error" }, { status: 500 });
  }
}
