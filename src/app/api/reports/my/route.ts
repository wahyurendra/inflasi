import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const params: Record<string, string> = {};
  params.page = searchParams.get("page") || "1";
  params.limit = searchParams.get("limit") || "20";

  try {
    const opts = { userId: session.user.id, userRole: session.user.role };
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
