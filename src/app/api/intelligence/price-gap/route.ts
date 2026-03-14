import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const commodities = await prisma.dimCommodity.findMany({
      where: { isMvp: true },
      include: {
        priceDaily: {
          where: { tanggal: { gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } },
          include: { region: { select: { namaProvinsi: true } } },
        },
      },
    });

    const data = commodities
      .map((c) => {
        if (c.priceDaily.length === 0) return null;

        const sorted = [...c.priceDaily].sort((a, b) => Number(a.harga) - Number(b.harga));
        const lowest = sorted[0];
        const highest = sorted[sorted.length - 1];
        const gap = Number(highest.harga) - Number(lowest.harga);
        const gapPct = Number(lowest.harga) > 0 ? Math.round((gap / Number(lowest.harga)) * 100) : 0;

        return {
          commodity: c.namaDisplay,
          highest: Number(highest.harga),
          lowest: Number(lowest.harga),
          gap,
          gapPct,
          highRegion: highest.region.namaProvinsi,
          lowRegion: lowest.region.namaProvinsi,
        };
      })
      .filter(Boolean);

    data.sort((a, b) => (b?.gapPct || 0) - (a?.gapPct || 0));
    return NextResponse.json({ data });
  } catch (error) {
    console.error("Price gap error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
