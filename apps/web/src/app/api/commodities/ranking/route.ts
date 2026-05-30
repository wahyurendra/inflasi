import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";
import { toFrontendCommodity } from "@/lib/region-mapping";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

interface BackendRankingRow {
  kodeKomoditas: string;
  [key: string]: unknown;
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sort = searchParams.get("sort") || "weekly_change";
  const limit = searchParams.get("limit") || "8";
  return runBff(async () => {
    const result = await apiClient.get<{ data: BackendRankingRow[] }>(
      "/commodities/ranking",
      { sort, limit },
    );
    return {
      ...result,
      data: (result.data ?? []).map((row) => ({
        ...row,
        kodeKomoditas: toFrontendCommodity(row.kodeKomoditas),
      })),
    };
  });
}
