import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const windowDays = searchParams.get("window_days") || "30";
  const targetType = searchParams.get("target_type") || "price";
  return runBff(() =>
    apiClient.get("/analytics/model-performance", { window_days: windowDays, target_type: targetType }),
  );
}
