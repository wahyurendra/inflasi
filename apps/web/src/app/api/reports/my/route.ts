import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const authToken = request.headers.get("authorization") ?? undefined;
  if (!authToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const params: Record<string, string> = {};
  params.page = searchParams.get("page") || "1";
  params.limit = searchParams.get("limit") || "20";

  try {
    const opts = { authToken };
    const data = await apiClient.get("/reports/my", params, opts);
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      data: [],
      total: 0,
      page: 1,
      totalPages: 0,
      source: "mock",
    });
  }
}
