import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "CABAI_RAWIT";
  const region = searchParams.get("region") || "00";
  const horizon = searchParams.get("horizon") || "14";

  try {
    const params: Record<string, string> = { commodity, region, horizon };

    const result = await apiClient.get("/forecast/prices", params);

    return NextResponse.json(result);
  } catch (error) {
    console.error("Forecast error:", error);
    return NextResponse.json({ data: [], commodity, region, error: "Database error" }, { status: 500 });
  }
}
