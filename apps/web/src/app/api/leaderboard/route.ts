import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const period = searchParams.get("period") || "all";
  const limit = searchParams.get("limit") || "20";
  return runBff(() => apiClient.get("/gamification/leaderboard", { period, limit }));
}
