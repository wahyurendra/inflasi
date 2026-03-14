import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const active = searchParams.get("active") !== "false";
  const severity = searchParams.get("severity");
  const limit = parseInt(searchParams.get("limit") || "20");

  try {
    const alerts = await prisma.analyticsAlert.findMany({
      where: {
        isActive: active ? true : undefined,
        severity: severity || undefined,
      },
      include: {
        region: true,
        commodity: true,
      },
      orderBy: [{ severity: "asc" }, { tanggal: "desc" }],
      take: limit,
    });

    return NextResponse.json({
      data: alerts.map((a) => ({
        id: a.id,
        tanggal: a.tanggal.toISOString().slice(0, 10),
        alertType: a.alertType,
        severity: a.severity,
        judul: a.judul,
        deskripsi: a.deskripsi,
        nilaiAktual: a.nilaiAktual ? Number(a.nilaiAktual) : null,
        nilaiThreshold: a.nilaiThreshold ? Number(a.nilaiThreshold) : null,
        isActive: a.isActive,
        region: {
          kode: a.region.kodeWilayah,
          nama: a.region.namaProvinsi,
        },
        commodity: {
          kode: a.commodity.kodeKomoditas,
          nama: a.commodity.namaDisplay,
        },
      })),
      count: alerts.length,
    });
  } catch (error) {
    console.error("Alerts error:", error);
    return NextResponse.json({ data: [], count: 0, error: "Database error" }, { status: 500 });
  }
}
