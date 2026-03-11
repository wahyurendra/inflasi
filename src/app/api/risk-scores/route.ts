import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const tanggal = request.nextUrl.searchParams.get("tanggal");

  try {
    const scores = await prisma.analyticsRiskScore.findMany({
      where: tanggal ? { tanggal: new Date(tanggal) } : undefined,
      include: { region: true, commodity: true },
      orderBy: { riskScoreTotal: "desc" },
      take: 50,
    });

    return NextResponse.json({
      data: scores.map((s) => ({
        tanggal: s.tanggal.toISOString().slice(0, 10),
        region: { kode: s.region.kodeWilayah, nama: s.region.namaProvinsi },
        commodity: { kode: s.commodity.kodeKomoditas, nama: s.commodity.namaDisplay },
        riskScoreTotal: s.riskScoreTotal ? Number(s.riskScoreTotal) : 0,
        riskCategory: s.riskCategory,
        scores: {
          kenaikan7d: s.skorKenaikan7d ? Number(s.skorKenaikan7d) : 0,
          kenaikan30d: s.skorKenaikan30d ? Number(s.skorKenaikan30d) : 0,
          volatilitas: s.skorVolatilitas ? Number(s.skorVolatilitas) : 0,
          deviasiWilayah: s.skorDeviasiWilayah ? Number(s.skorDeviasiWilayah) : 0,
          cuaca: s.skorCuaca ? Number(s.skorCuaca) : 0,
          stok: s.skorStok ? Number(s.skorStok) : 0,
        },
      })),
    });
  } catch {
    return NextResponse.json({ data: [], source: "mock" });
  }
}
