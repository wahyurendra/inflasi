import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";
import { toBackendCommodity, toBackendRegion } from "@/lib/region-mapping";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "CABAI_RAWIT";
  const region = searchParams.get("region") || "00";
  const horizon = searchParams.get("horizon") || "14";
  return runBff(() =>
    apiClient.get("/forecast/prices", {
      commodity: toBackendCommodity(commodity),
      region: toBackendRegion(region),
      horizon,
    }),
  );
}
