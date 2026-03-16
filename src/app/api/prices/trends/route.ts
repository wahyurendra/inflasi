import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const commodity = searchParams.get("commodity");
  const region = searchParams.get("region") || "00";
  const days = searchParams.get("days") || "30";

  if (!commodity) {
    return NextResponse.json({ error: "commodity parameter required" }, { status: 400 });
  }

  try {
    const params: Record<string, string> = { commodity, region, days };

    const result = await apiClient.get("/prices/trends", params);

    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ commodity: null, region: null, data: [], summary: null, source: "mock" });
  }
}
