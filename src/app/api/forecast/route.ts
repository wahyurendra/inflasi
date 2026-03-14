import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

const MOCK_FORECAST = [
  { tanggal: "2026-03-14", yhat: 87000, yhatLower: 82000, yhatUpper: 92000 },
  { tanggal: "2026-03-15", yhat: 88500, yhatLower: 83000, yhatUpper: 94000 },
  { tanggal: "2026-03-16", yhat: 89200, yhatLower: 83500, yhatUpper: 95000 },
  { tanggal: "2026-03-17", yhat: 88800, yhatLower: 83000, yhatUpper: 94500 },
  { tanggal: "2026-03-18", yhat: 89500, yhatLower: 84000, yhatUpper: 95000 },
  { tanggal: "2026-03-19", yhat: 90200, yhatLower: 84500, yhatUpper: 96000 },
  { tanggal: "2026-03-20", yhat: 91000, yhatLower: 85000, yhatUpper: 97000 },
  { tanggal: "2026-03-21", yhat: 90500, yhatLower: 84500, yhatUpper: 96500 },
  { tanggal: "2026-03-22", yhat: 91200, yhatLower: 85000, yhatUpper: 97500 },
  { tanggal: "2026-03-23", yhat: 92000, yhatLower: 85500, yhatUpper: 98500 },
  { tanggal: "2026-03-24", yhat: 92800, yhatLower: 86000, yhatUpper: 99500 },
  { tanggal: "2026-03-25", yhat: 93500, yhatLower: 86500, yhatUpper: 100500 },
  { tanggal: "2026-03-26", yhat: 94000, yhatLower: 87000, yhatUpper: 101000 },
  { tanggal: "2026-03-27", yhat: 94500, yhatLower: 87500, yhatUpper: 101500 },
];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "CABAI_RAWIT";
  const region = searchParams.get("region") || "00";
  const horizon = parseInt(searchParams.get("horizon") || "14");

  try {
    // Get commodity & region IDs
    const commodityRow = await prisma.dimCommodity.findFirst({
      where: { kodeKomoditas: commodity },
    });
    const regionRow = await prisma.dimRegion.findFirst({
      where: { kodeWilayah: region },
    });

    if (!commodityRow || !regionRow) {
      return NextResponse.json({
        data: MOCK_FORECAST.slice(0, horizon),
        commodity,
        region,
        modelVersion: "mock",
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

    if (!forecasts.length) {
      return NextResponse.json({
        data: MOCK_FORECAST.slice(0, horizon),
        commodity,
        region,
        modelVersion: "mock",
      });
    }

    return NextResponse.json({
      data: forecasts.map((f) => ({
        tanggal: f.tanggal.toISOString().slice(0, 10),
        yhat: Number(f.yhat),
        yhatLower: Number(f.yhatLower),
        yhatUpper: Number(f.yhatUpper),
      })),
      commodity,
      region,
      modelVersion: forecasts[0].modelVersion,
    });
  } catch {
    return NextResponse.json({
      data: MOCK_FORECAST.slice(0, horizon),
      commodity,
      region,
      modelVersion: "mock",
    });
  }
}
