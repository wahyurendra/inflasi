import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "";

  try {
    const params: Record<string, string> = {};
    if (commodity) {
      params.commodity = commodity;
    }

    const result = await apiClient.get("/intelligence/comparison", params);
    return NextResponse.json(result);
  } catch (error) {
    console.error("Comparison error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
