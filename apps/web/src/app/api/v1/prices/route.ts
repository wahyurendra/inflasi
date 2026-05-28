import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const commodityId = searchParams.get("commodityId");
    const regionId = searchParams.get("regionId");
    const days = searchParams.get("days") || "7";
    const limit = searchParams.get("limit") || "100";

    const params: Record<string, string> = { days, limit };
    if (commodityId) params.commodityId = commodityId;
    if (regionId) params.regionId = regionId;

    const result = await apiClient.get("/prices/list", params);

    return NextResponse.json(result);
  } catch {
    return NextResponse.json(
      { error: "Service unavailable", data: [], meta: { count: 0 } },
      { status: 503 }
    );
  }
}
