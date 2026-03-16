import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sort = searchParams.get("sort") || "weekly_change";
  const limit = searchParams.get("limit") || "8";

  try {
    const params: Record<string, string> = { sort, limit };

    const result = await apiClient.get("/commodities/ranking", params);

    return NextResponse.json(result);
  } catch (error) {
    console.error("Commodity ranking error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
