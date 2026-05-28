import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const tanggal = request.nextUrl.searchParams.get("tanggal");

  try {
    const params: Record<string, string> = {};
    if (tanggal) params.tanggal = tanggal;

    const result = await apiClient.get("/analytics/risk-scores", params);

    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ data: [], source: "mock" });
  }
}
