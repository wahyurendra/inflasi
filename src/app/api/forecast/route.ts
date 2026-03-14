import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "CABAI_RAWIT";
  const region = searchParams.get("region") || "00";
  const horizon = parseInt(searchParams.get("horizon") || "14");

  try {
    const commodityRow = await prisma.dimCommodity.findFirst({
      where: { kodeKomoditas: commodity },
    });
    const regionRow = await prisma.dimRegion.findFirst({
      where: { kodeWilayah: region },
    });

    if (!commodityRow || !regionRow) {
      return NextResponse.json({
        data: [],
        commodity,
        region,
        message: "Komoditas atau wilayah tidak ditemukan",
      });
    }

    const forecasts = await prisma.analyticsForecast.findMany({
      where: {
        commodityId: commodityRow.id,
        regionId: regionRow.id,
        horizon,
        tanggal: { gte: new Date() },
      },
      orderBy: { tanggal: "asc" },
      take: horizon,
    });

    return NextResponse.json({
      data: forecasts.map((f) => ({
        tanggal: f.tanggal.toISOString().slice(0, 10),
        yhat: Number(f.yhat),
        yhatLower: Number(f.yhatLower),
        yhatUpper: Number(f.yhatUpper),
      })),
      commodity,
      region,
      modelVersion: forecasts[0]?.modelVersion || null,
    });
  } catch (error) {
    console.error("Forecast error:", error);
    return NextResponse.json({ data: [], commodity, region, error: "Database error" }, { status: 500 });
  }
}
