import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";
import {
  toBackendCommodity,
  toBackendRegion,
  toFrontendCommodity,
  toBpsCode,
} from "@/lib/region-mapping";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

interface BackendPriceRow {
  tanggal: string;
  harga: number;
  perubahanHarian: number | null;
  perubahanMingguan: number | null;
  perubahanBulanan: number | null;
  commodity: { kode: string; nama: string };
  region: { kode: string; nama: string };
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const commodity = searchParams.get("commodity");
  const region = searchParams.get("region") || "00";
  const days = searchParams.get("days") || "30";

  if (!commodity) {
    return NextResponse.json(
      { detail: "commodity parameter required" },
      { status: 400 },
    );
  }

  return runBff(async () => {
    const result = await apiClient.get<{ data: BackendPriceRow[] }>(
      "/prices/trends",
      {
        commodity: toBackendCommodity(commodity),
        region: toBackendRegion(region),
        days,
      },
    );
    return {
      ...result,
      data: (result.data ?? []).map((row) => ({
        ...row,
        commodity: {
          ...row.commodity,
          kode: toFrontendCommodity(row.commodity.kode),
        },
        region: {
          ...row.region,
          kode: toBpsCode(row.region.kode, row.region.nama),
        },
      })),
    };
  });
}
