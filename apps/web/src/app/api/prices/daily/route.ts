import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const commodity = searchParams.get("commodity");
  const region = searchParams.get("region") || "00";
  const days = searchParams.get("days") || "30";

  try {
    const params: Record<string, string> = { region, days };
    if (commodity) params.commodity = commodity;

    const result = await apiClient.get("/prices/daily", params);

    return NextResponse.json(result);
  } catch {
    // API not available — return empty
    return NextResponse.json({ data: [], count: 0, source: "mock" });
  }
}
