import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    // Get latest inflation data (national level)
    const latest = await prisma.factInflationMonthly.findFirst({
      where: {
        region: { kodeWilayah: "00" },
      },
      orderBy: { periode: "desc" },
      include: { region: true },
    });

    if (!latest) {
      // Return mock data if no data in DB yet
      return NextResponse.json({
        inflasi: {
          mtm: 0.42,
          ytd: 1.23,
          yoy: 5.21,
          ihk: 118.35,
          periode: "2026-02-01",
        },
        source: "mock",
      });
    }

    return NextResponse.json({
      inflasi: {
        mtm: latest.inflasiMtm ? Number(latest.inflasiMtm) : null,
        ytd: latest.inflasiYtd ? Number(latest.inflasiYtd) : null,
        yoy: latest.inflasiYoy ? Number(latest.inflasiYoy) : null,
        ihk: latest.ihk ? Number(latest.ihk) : null,
        periode: latest.periode.toISOString().slice(0, 10),
      },
      source: "database",
    });
  } catch {
    // DB not connected — return mock data
    return NextResponse.json({
      inflasi: {
        mtm: 0.42,
        ytd: 1.23,
        yoy: 5.21,
        ihk: 118.35,
        periode: "2026-02-01",
      },
      source: "mock",
    });
  }
}
