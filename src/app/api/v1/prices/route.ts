import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const commodityId = searchParams.get("commodityId");
    const regionId = searchParams.get("regionId");
    const days = parseInt(searchParams.get("days") || "7");
    const limit = Math.min(parseInt(searchParams.get("limit") || "100"), 500);

    const where: Record<string, unknown> = {
      tanggal: { gte: new Date(Date.now() - days * 24 * 60 * 60 * 1000) },
    };
    if (commodityId) where.commodityId = parseInt(commodityId);
    if (regionId) where.regionId = parseInt(regionId);

    const prices = await prisma.factPriceDaily.findMany({
      where,
      include: {
        commodity: { select: { namaDisplay: true, satuan: true } },
        region: { select: { namaProvinsi: true, kodeWilayah: true } },
      },
      orderBy: { tanggal: "desc" },
      take: limit,
    });

    const data = prices.map((p) => ({
      date: p.tanggal.toISOString().slice(0, 10),
      commodity: p.commodity.namaDisplay,
      unit: p.commodity.satuan,
      region: p.region.namaProvinsi,
      regionCode: p.region.kodeWilayah,
      price: Number(p.harga),
      changePercent: p.perubahanHarian ? Number(p.perubahanHarian) : null,
    }));

    return NextResponse.json({
      data,
      meta: { count: data.length, days, limit },
    });
  } catch {
    return NextResponse.json(
      { error: "Service unavailable", data: [], meta: { count: 0 } },
      { status: 503 }
    );
  }
}
