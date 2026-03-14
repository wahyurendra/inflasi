import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

const mockComparison = [
  { region: "DKI Jakarta", kode: "31", beras: 14500, cabaiMerah: 42000, cabaiRawit: 55000, bawangMerah: 35000, telurAyam: 28000 },
  { region: "Jawa Barat", kode: "32", beras: 13800, cabaiMerah: 38000, cabaiRawit: 48000, bawangMerah: 32000, telurAyam: 27000 },
  { region: "Jawa Tengah", kode: "33", beras: 13200, cabaiMerah: 35000, cabaiRawit: 45000, bawangMerah: 30000, telurAyam: 26500 },
  { region: "Jawa Timur", kode: "35", beras: 13500, cabaiMerah: 36000, cabaiRawit: 46000, bawangMerah: 31000, telurAyam: 26000 },
  { region: "Sumatera Utara", kode: "12", beras: 14800, cabaiMerah: 44000, cabaiRawit: 58000, bawangMerah: 38000, telurAyam: 29000 },
  { region: "Sulawesi Selatan", kode: "73", beras: 13000, cabaiMerah: 40000, cabaiRawit: 52000, bawangMerah: 34000, telurAyam: 27500 },
  { region: "Bali", kode: "51", beras: 14200, cabaiMerah: 45000, cabaiRawit: 60000, bawangMerah: 36000, telurAyam: 28500 },
  { region: "Kalimantan Timur", kode: "64", beras: 15000, cabaiMerah: 48000, cabaiRawit: 62000, bawangMerah: 40000, telurAyam: 30000 },
  { region: "Papua", kode: "91", beras: 18000, cabaiMerah: 55000, cabaiRawit: 70000, bawangMerah: 45000, telurAyam: 35000 },
];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity");

  try {
    if (commodity) {
      const prices = await prisma.factPriceDaily.findMany({
        where: {
          commodity: { kodeKomoditas: commodity },
          tanggal: { gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) },
        },
        include: { region: { select: { namaProvinsi: true, kodeWilayah: true } } },
        orderBy: { harga: "desc" },
      });

      const regionMap = new Map<string, { total: number; count: number; name: string }>();
      for (const p of prices) {
        const key = p.region.kodeWilayah;
        const existing = regionMap.get(key) || { total: 0, count: 0, name: p.region.namaProvinsi };
        existing.total += Number(p.harga);
        existing.count += 1;
        regionMap.set(key, existing);
      }

      const data = Array.from(regionMap.entries()).map(([kode, v]) => ({
        region: v.name,
        kode,
        avgPrice: Math.round(v.total / v.count),
      }));

      return NextResponse.json({ data });
    }

    return NextResponse.json({ data: mockComparison });
  } catch {
    return NextResponse.json({ data: mockComparison, source: "mock" });
  }
}
