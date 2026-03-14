import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

const mockPriceGap = [
  { commodity: "Cabai Rawit", highest: 70000, lowest: 35000, gap: 35000, gapPct: 100, highRegion: "Papua", lowRegion: "Jawa Tengah" },
  { commodity: "Cabai Merah", highest: 55000, lowest: 30000, gap: 25000, gapPct: 83, highRegion: "Papua", lowRegion: "Jawa Timur" },
  { commodity: "Bawang Merah", highest: 45000, lowest: 28000, gap: 17000, gapPct: 61, highRegion: "Kalimantan Timur", lowRegion: "Jawa Tengah" },
  { commodity: "Daging Sapi", highest: 140000, lowest: 110000, gap: 30000, gapPct: 27, highRegion: "Papua", lowRegion: "Jawa Timur" },
  { commodity: "Beras", highest: 18000, lowest: 12500, gap: 5500, gapPct: 44, highRegion: "Papua", lowRegion: "Jawa Tengah" },
  { commodity: "Telur Ayam", highest: 35000, lowest: 25000, gap: 10000, gapPct: 40, highRegion: "Papua", lowRegion: "Jawa Timur" },
  { commodity: "Daging Ayam", highest: 42000, lowest: 32000, gap: 10000, gapPct: 31, highRegion: "Bali", lowRegion: "Jawa Tengah" },
  { commodity: "Minyak Goreng", highest: 20000, lowest: 16000, gap: 4000, gapPct: 25, highRegion: "Papua", lowRegion: "Jawa Barat" },
  { commodity: "Gula Pasir", highest: 18000, lowest: 14500, gap: 3500, gapPct: 24, highRegion: "Maluku", lowRegion: "Jawa Timur" },
  { commodity: "Bawang Putih", highest: 38000, lowest: 28000, gap: 10000, gapPct: 36, highRegion: "Papua", lowRegion: "DKI Jakarta" },
];

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
  } catch {
    return NextResponse.json({ data: mockPriceGap, source: "mock" });
  }
}
