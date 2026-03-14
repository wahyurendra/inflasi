import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

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

    // No commodity specified: get cross-commodity comparison per region
    const commodities = await prisma.dimCommodity.findMany({ where: { isMvp: true } });
    const regions = await prisma.dimRegion.findMany({
      where: { levelWilayah: "provinsi" },
    });

    const prices = await prisma.factPriceDaily.findMany({
      where: { tanggal: { gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } },
      select: { regionId: true, commodityId: true, harga: true },
    });

    const priceMap = new Map<string, number[]>();
    for (const p of prices) {
      const key = `${p.regionId}-${p.commodityId}`;
      const arr = priceMap.get(key) || [];
      arr.push(Number(p.harga));
      priceMap.set(key, arr);
    }

    const data = regions.slice(0, 10).map((r) => {
      const row: Record<string, unknown> = { region: r.namaProvinsi, kode: r.kodeWilayah };
      for (const c of commodities) {
        const key = `${r.id}-${c.id}`;
        const arr = priceMap.get(key);
        row[c.kodeKomoditas.toLowerCase()] = arr ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : null;
      }
      return row;
    });

    return NextResponse.json({ data });
  } catch (error) {
    console.error("Comparison error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
