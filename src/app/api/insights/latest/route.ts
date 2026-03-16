import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const tipe = request.nextUrl.searchParams.get("type") || "harian";

  try {
    const params: Record<string, string> = { type: tipe };

    const result = await apiClient.get("/insights/latest", params);

    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ data: null, source: "mock" });
  }
}
