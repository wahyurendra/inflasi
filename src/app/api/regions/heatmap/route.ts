import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const regions = await prisma.dimRegion.findMany({
      where: { levelWilayah: "provinsi" },
      include: {
        priceDaily: {
          orderBy: { tanggal: "desc" },
          take: 8, // 1 per commodity
        },
        alerts: {
          where: { isActive: true },
        },
        riskScores: {
          orderBy: { tanggal: "desc" },
          take: 1,
        },
      },
    });

    const data = regions.map((r) => {
      const avgChange =
        r.priceDaily.length > 0
          ? r.priceDaily.reduce(
              (sum, p) => sum + (p.perubahanMingguan ? Number(p.perubahanMingguan) : 0),
              0
            ) / r.priceDaily.length
          : 0;

      const riskScore = r.riskScores[0];

      return {
        kodeWilayah: r.kodeWilayah,
        namaProvinsi: r.namaProvinsi,
        avgPriceChange: Math.round(avgChange * 100) / 100,
        alertCount: r.alerts.length,
        riskCategory: riskScore?.riskCategory ?? "rendah",
      };
    });

    return NextResponse.json({ data });
  } catch {
    return NextResponse.json({ data: [], source: "mock" });
  }
}
