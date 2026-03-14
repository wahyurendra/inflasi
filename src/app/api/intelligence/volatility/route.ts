import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

const mockVolatility = [
  { commodity: "Cabai Rawit", kode: "CABAI_RAWIT", cv: 18.5, trend: "up" },
  { commodity: "Cabai Merah", kode: "CABAI_MERAH", cv: 15.2, trend: "up" },
  { commodity: "Bawang Merah", kode: "BAWANG_MERAH", cv: 12.8, trend: "stable" },
  { commodity: "Bawang Putih", kode: "BAWANG_PUTIH", cv: 9.4, trend: "down" },
  { commodity: "Telur Ayam", kode: "TELUR_AYAM", cv: 7.1, trend: "stable" },
  { commodity: "Daging Ayam", kode: "DAGING_AYAM", cv: 6.8, trend: "up" },
  { commodity: "Minyak Goreng", kode: "MINYAK_GORENG", cv: 4.2, trend: "stable" },
  { commodity: "Gula Pasir", kode: "GULA_PASIR", cv: 3.5, trend: "stable" },
  { commodity: "Beras", kode: "BERAS", cv: 2.8, trend: "stable" },
  { commodity: "Daging Sapi", kode: "DAGING_SAPI", cv: 5.1, trend: "up" },
];

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
  } catch {
    return NextResponse.json({ data: mockVolatility, source: "mock" });
  }
}
