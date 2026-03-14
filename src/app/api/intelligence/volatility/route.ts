import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const commodities = await prisma.dimCommodity.findMany({
      where: { isMvp: true },
      include: {
        priceDaily: {
          where: { tanggal: { gte: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000) } },
          select: { harga: true },
        },
      },
    });

    const data = commodities.map((c) => {
      const prices = c.priceDaily.map((p) => Number(p.harga));
      const mean = prices.reduce((a, b) => a + b, 0) / (prices.length || 1);
      const variance = prices.reduce((a, b) => a + (b - mean) ** 2, 0) / (prices.length || 1);
      const std = Math.sqrt(variance);
      const cv = mean > 0 ? (std / mean) * 100 : 0;

      return {
        commodity: c.namaDisplay,
        kode: c.kodeKomoditas,
        cv: Math.round(cv * 10) / 10,
        trend: cv > 10 ? "up" : cv > 5 ? "stable" : "down",
      };
    });

    data.sort((a, b) => b.cv - a.cv);
    return NextResponse.json({ data });
  } catch (error) {
    console.error("Volatility error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
