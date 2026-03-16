import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const period = searchParams.get("period") || "all";
  const limit = searchParams.get("limit") || "20";

  try {
    const result = await apiClient.get("/gamification/leaderboard", { period, limit });
    return NextResponse.json(result);
  } catch (error) {
    console.error("Leaderboard error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
