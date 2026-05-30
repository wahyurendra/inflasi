import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";
import { optionalAuth, runBff, withAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const regionId = searchParams.get("region_id");
  if (!regionId) {
    return NextResponse.json({ detail: "region_id required" }, { status: 400 });
  }
  const activeOnly = searchParams.get("active_only") ?? "true";
  const authToken = optionalAuth(request);
  return runBff(() =>
    apiClient.get(
      "/markets",
      { region_id: regionId, active_only: activeOnly },
      { authToken },
    ),
  );
}

export async function POST(request: NextRequest) {
  return runBff(async () => {
    const authToken = withAuth(request);
    const body = await request.json();
    return apiClient.post("/markets", body, { authToken });
  });
}
