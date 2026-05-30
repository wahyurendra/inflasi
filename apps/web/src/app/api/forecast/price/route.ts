import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

// POST /forecast/price (v2) — quantile p10/p50/p90 + driver + components.
export async function POST(request: NextRequest) {
  return runBff(async () => {
    const body = await request.json();
    return apiClient.post("/forecast/price", body);
  });
}
