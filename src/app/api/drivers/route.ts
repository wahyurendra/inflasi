import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "CABAI_RAWIT";
  const region = searchParams.get("region") || "00";

  try {
    const result = await apiClient.get("/drivers/analysis", { commodity, region });
    return NextResponse.json(result);
  } catch (error) {
    console.error("Drivers error:", error);
    return NextResponse.json({
      commodity_code: commodity,
      region_code: region,
      drivers: [],
      error: "Analytics service error",
    }, { status: 503 });
  }
}
