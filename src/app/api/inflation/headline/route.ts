import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const latest = await prisma.factInflationMonthly.findFirst({
      where: {
        region: { kodeWilayah: "00" },
      },
      orderBy: { periode: "desc" },
      include: { region: true },
    });

    if (!latest) {
      return NextResponse.json({
        inflasi: null,
        message: "Belum ada data inflasi",
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
    });
  } catch (error) {
    console.error("Inflation headline error:", error);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}
